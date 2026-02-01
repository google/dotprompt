# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Generic Dart Bazel rules.

This module provides reusable Bazel rules for building and testing Dart code.
The Dart SDK is automatically downloaded via the dart_sdk repository rule
in repositories.bzl, similar to how rules_go and rules_rust work.

Key Rules:
    - dart_library: Creates a Dart library target
    - dart_binary: Creates an executable Dart binary
    - dart_test: Runs Dart tests

Usage in BUILD files:
    load("@rules_dart//:defs.bzl", "dart_library", "dart_test")

    dart_library(
        name = "my_lib",
        srcs = glob(["lib/**/*.dart"]),
    )

    dart_test(
        name = "my_test",
        main = "test/my_test.dart",
        deps = [":my_lib"],
    )

Note: Dart tests require the package dependencies to be resolved first.
Run `dart pub get` in the package directory before running Bazel tests.
"""

# Path to the downloaded Dart SDK binary
# We use Label() to ensure it resolves relative to the rules_dart module,
# making it portable regardless of how the consuming workspace names the repo.
DART_SDK = Label("@dart_sdk//:dart_bin")

def _runfiles_path(file):
    """Get the runfiles-relative path for a file.

    For external repo files, short_path starts with '../<repo_name>/'.
    In runfiles, these are located at '<repo_name>/' (without the ..).
    """
    sp = file.short_path
    if sp.startswith("../"):
        return sp[3:]  # Strip leading "../"
    return sp

def dart_library(name, srcs = [], deps = [], pubspec = None, visibility = None, **kwargs):
    """Creates a Dart library target.

    This is a lightweight wrapper that creates a filegroup for Dart sources.
    Dart's module system handles the actual compilation.

    Args:
        name: Name of the library target.
        srcs: List of Dart source files.
        deps: List of dependencies (other dart_library targets).
        pubspec: The pubspec.yaml file (optional).
        visibility: Visibility declaration.
        **kwargs: Additional arguments passed to native.filegroup.
    """
    all_srcs = srcs + deps
    if pubspec and pubspec not in all_srcs:
        all_srcs.append(pubspec)

    native.filegroup(
        name = name,
        srcs = all_srcs,
        visibility = visibility,
        **kwargs
    )

def _dart_binary_impl(ctx):
    """Cross-platform implementation for dart_binary."""
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_short_path = _runfiles_path(dart_bin)
    main_path = ctx.file.main.path

    if is_windows:
        content = """@echo off
setlocal
cd /d "%BUILD_WORKSPACE_DIRECTORY%"

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
)

"%DART_BIN%" run {main} %*
""".format(dart_path = dart_short_path.replace("/", "\\"), main = main_path.replace("/", "\\"))
    else:
        content = """#!/bin/bash
set -e
cd "$BUILD_WORKSPACE_DIRECTORY"

RUNFILES="${{RUNFILES:-$0.runfiles}}"
DART_BIN="$RUNFILES/{dart_path}"

if [ ! -f "$DART_BIN" ]; then
    DART_BIN="dart"
fi

exec "$DART_BIN" run {main} "$@"
""".format(dart_path = dart_short_path, main = main_path)

    ctx.actions.write(runner_script, content, is_executable = True)

    runfiles = ctx.runfiles(
        files = [dart_bin, ctx.file.main] + ctx.files.srcs + ctx.files.deps,
    )

    return [DefaultInfo(
        executable = runner_script,
        runfiles = runfiles,
    )]

_dart_binary_rule = rule(
    implementation = _dart_binary_impl,
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def dart_binary(name, main, srcs = [], deps = [], visibility = None, **kwargs):
    """Creates a Dart binary target.

    Args:
        name: Name of the binary target.
        main: Main Dart file to execute.
        srcs: Additional Dart source files.
        deps: List of dependencies.
        visibility: Visibility declaration.
        **kwargs: Additional arguments.
    """
    _dart_binary_rule(
        name = name,
        main = main,
        srcs = srcs,
        deps = deps,
        visibility = visibility,
        **kwargs
    )

def _dart_test_impl(ctx):
    """Cross-platform implementation for dart_test."""
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_short_path = _runfiles_path(dart_bin)
    main_path = ctx.file.main.path
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Compute relative path of test file from package directory
    # main_path is like "dart/dotprompt/test/foo_test.dart"
    # pkg_dir is like "dart/dotprompt"
    # We need just "test/foo_test.dart" for the dart test command
    if pkg_dir and main_path.startswith(pkg_dir + "/"):
        test_file = main_path[len(pkg_dir) + 1:]
    else:
        test_file = main_path

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    echo ERROR: Dart SDK not found at %DART_BIN%
    exit /b 1
)

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
set "TEMP_DIR=%TEMP%\\dart_test_%RANDOM%"
mkdir "%TEMP_DIR%"

set "HOME=%TEMP_DIR%"
set "PUB_CACHE=%TEMP_DIR%\\.pub-cache"
mkdir "%PUB_CACHE%"

xcopy "%WORKSPACE_ROOT%" "%TEMP_DIR%" /E /I /Q >nul
cd /d "%TEMP_DIR%\\{pkg_dir}"

call "%DART_BIN%" pub get --offline 2>nul || call "%DART_BIN%" pub get
"%DART_BIN%" test {main}
set "RESULT=%errorlevel%"

cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" 2>nul
exit /b %RESULT%
""".format(dart_path = dart_short_path.replace("/", "\\"), pkg_dir = pkg_dir.replace("/", "\\"), main = test_file.replace("/", "\\"))
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$TEST_SRCDIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$RUNFILES/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $DART_BIN" >&2
    exit 1
fi

WORKSPACE_ROOT="$RUNFILES/_main"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

export HOME="$TEMP_DIR"
export PUB_CACHE="$TEMP_DIR/.pub-cache"
mkdir -p "$PUB_CACHE"

cp -R "$WORKSPACE_ROOT"/. "$TEMP_DIR/"
cd "$TEMP_DIR/{pkg_dir}"

"$DART_BIN" pub get --offline 2>/dev/null || "$DART_BIN" pub get
"$DART_BIN" test {main}
""".format(dart_path = dart_short_path, pkg_dir = pkg_dir, main = test_file)

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [dart_bin, ctx.file.main] + ctx.files.srcs + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_dart_test = rule(
    implementation = _dart_test_impl,
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    test = True,
)

def dart_test(name, main, srcs = [], deps = [], data = [], visibility = None, package_dir = None, **kwargs):
    """Creates a Dart test target."""
    _dart_test(
        name = name,
        main = main,
        srcs = srcs,
        deps = deps,
        data = data,
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )

def _dart_format_check_impl(ctx):
    """Cross-platform implementation for dart_format_check."""
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_short_path = _runfiles_path(dart_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    if is_windows:
        content = """@echo off
setlocal

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    echo ERROR: Dart SDK not found at %DART_BIN%
    exit /b 1
)

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

"%DART_BIN%" format --set-exit-if-changed --output=none lib\\ test\\ 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Code is not properly formatted. Run 'dart format .' to fix.
    exit /b 1
)
""".format(dart_path = dart_short_path.replace("/", "\\"), pkg_dir = pkg_dir.replace("/", "\\"))
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$TEST_SRCDIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$RUNFILES/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $DART_BIN" >&2
    exit 1
fi

WORKSPACE_ROOT="$RUNFILES/_main"
cd "$WORKSPACE_ROOT/{pkg_dir}"

"$DART_BIN" format --set-exit-if-changed --output=none lib/ test/ 2>/dev/null || {{
    echo "ERROR: Code is not properly formatted. Run 'dart format .' to fix." >&2
    exit 1
}}
""".format(dart_path = dart_short_path, pkg_dir = pkg_dir)

    ctx.actions.write(runner_script, content, is_executable = True)
    runfiles = ctx.runfiles(files = [dart_bin] + ctx.files.srcs)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_dart_format_check_test = rule(
    implementation = _dart_format_check_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    test = True,
)

def dart_format_check(name, srcs = [], package_dir = None, visibility = None, **kwargs):
    """Creates a Dart format check target for CI."""
    _dart_format_check_test(
        name = name,
        srcs = srcs,
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )

def _dart_analyze_impl(ctx):
    """Cross-platform implementation for dart_analyze."""
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_short_path = _runfiles_path(dart_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    echo ERROR: Dart SDK not found at %DART_BIN%
    exit /b 1
)

set "TEMP_DIR=%TEMP%\\dart_analyze_%RANDOM%"
mkdir "%TEMP_DIR%"

set "HOME=%TEMP_DIR%"
set "PUB_CACHE=%TEMP_DIR%\\.pub-cache"
mkdir "%PUB_CACHE%"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
xcopy "%WORKSPACE_ROOT%" "%TEMP_DIR%" /E /I /Q >nul
cd /d "%TEMP_DIR%\\{pkg_dir}"

call "%DART_BIN%" pub get --offline 2>nul || call "%DART_BIN%" pub get
"%DART_BIN%" analyze --fatal-infos --fatal-warnings
set "RESULT=%errorlevel%"

cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" 2>nul
exit /b %RESULT%
""".format(dart_path = dart_short_path.replace("/", "\\"), pkg_dir = pkg_dir.replace("/", "\\"))
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$TEST_SRCDIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$RUNFILES/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $DART_BIN" >&2
    exit 1
fi

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT
export HOME="$TEMP_DIR"
export PUB_CACHE="$TEMP_DIR/.pub-cache"
mkdir -p "$PUB_CACHE"

WORKSPACE_ROOT="$RUNFILES/_main"
cp -R "$WORKSPACE_ROOT"/. "$TEMP_DIR/"
cd "$TEMP_DIR/{pkg_dir}"

"$DART_BIN" pub get --offline 2>/dev/null || "$DART_BIN" pub get
"$DART_BIN" analyze --fatal-infos --fatal-warnings
""".format(dart_path = dart_short_path, pkg_dir = pkg_dir)

    ctx.actions.write(runner_script, content, is_executable = True)
    runfiles = ctx.runfiles(files = [dart_bin] + ctx.files.srcs + ctx.files.data)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_dart_analyze_test = rule(
    implementation = _dart_analyze_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    test = True,
)

def dart_analyze(name, srcs = [], data = [], package_dir = None, visibility = None, **kwargs):
    """Creates a Dart static analysis target."""
    pkg_dir = package_dir or native.package_name()
    _dart_analyze_test(
        name = name,
        srcs = srcs,
        data = data + ["//" + pkg_dir + ":pubspec.yaml"] if pkg_dir else data + [":pubspec.yaml"],
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )

def _dart_doc_impl(ctx):
    """Cross-platform implementation for dart_doc."""
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_short_path = _runfiles_path(dart_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package
    out_dir = ctx.attr.output_dir or "doc/api"

    if is_windows:
        content = """@echo off
setlocal

cd /d "%BUILD_WORKSPACE_DIRECTORY%\\{pkg_dir}"

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
)

call "%DART_BIN%" pub get
"%DART_BIN%" doc --output={out_dir}
echo Documentation generated at {pkg_dir}\\{out_dir}
""".format(dart_path = dart_short_path.replace("/", "\\"), pkg_dir = pkg_dir.replace("/", "\\"), out_dir = out_dir.replace("/", "\\"))
    else:
        content = """#!/bin/bash
set -e
cd "$BUILD_WORKSPACE_DIRECTORY/{pkg_dir}"

RUNFILES="${{RUNFILES:-$0.runfiles}}"
DART_BIN="$RUNFILES/{dart_path}"

if [ ! -f "$DART_BIN" ]; then
    DART_BIN="dart"
fi

"$DART_BIN" pub get
"$DART_BIN" doc --output={out_dir}
echo "Documentation generated at {pkg_dir}/{out_dir}"
""".format(dart_path = dart_short_path, pkg_dir = pkg_dir, out_dir = out_dir)

    ctx.actions.write(runner_script, content, is_executable = True)
    runfiles = ctx.runfiles(files = [dart_bin] + ctx.files.srcs)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_dart_doc_rule = rule(
    implementation = _dart_doc_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "output_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def dart_doc(name, srcs = [], package_dir = None, output_dir = None, visibility = None, **kwargs):
    """Creates a Dart documentation generation target."""
    _dart_doc_rule(
        name = name,
        srcs = srcs,
        package_dir = package_dir,
        output_dir = output_dir,
        visibility = visibility,
        **kwargs
    )

def _dart_tool_impl(ctx):
    """Implementation for cross-platform Dart tool runner."""
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_short_path = _runfiles_path(dart_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package
    command = ctx.attr.command
    args_str = " ".join(ctx.attr.tool_args)

    if is_windows:
        content = """@echo off
setlocal
cd /d "%BUILD_WORKSPACE_DIRECTORY%\\{pkg_dir}"

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
    echo Warning: Hermetic Dart SDK not found, falling back to system dart
)

echo Executing: %DART_BIN% {command} {args} %*
"%DART_BIN%" {command} {args} %*
""".format(
            dart_path = dart_short_path.replace("/", "\\"),
            pkg_dir = pkg_dir.replace("/", "\\"),
            command = command,
            args = args_str,
        )
    else:
        content = """#!/bin/bash
set -e
cd "${{BUILD_WORKSPACE_DIRECTORY}}/{pkg_dir}"

RUNFILES="${{RUNFILES:-$0.runfiles}}"
DART_BIN="$RUNFILES/{dart_path}"

if [ ! -f "$DART_BIN" ]; then
    echo "Warning: Hermetic Dart SDK not found, falling back to system dart" >&2
    DART_BIN="dart"
fi

echo "Executing: $DART_BIN {command} {args} $@"
exec "$DART_BIN" {command} {args} "$@"
""".format(
            dart_path = dart_short_path,
            pkg_dir = pkg_dir,
            command = command,
            args = args_str,
        )

    ctx.actions.write(runner_script, content, is_executable = True)

    runfiles = ctx.runfiles(files = [dart_bin])

    return [DefaultInfo(
        executable = runner_script,
        runfiles = runfiles,
    )]

_dart_tool_rule = rule(
    implementation = _dart_tool_impl,
    attrs = {
        "command": attr.string(mandatory = True),
        "tool_args": attr.string_list(default = []),
        "package_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def _dart_tool_target(name, command, args = [], package_dir = None, **kwargs):
    """Wrapper macro for _dart_tool_rule."""
    _dart_tool_rule(
        name = name,
        command = command,
        tool_args = args,
        package_dir = package_dir,
        **kwargs
    )

def _dart_compile(
        name,
        command,
        main,
        srcs = [],
        deps = [],
        package_dir = None,
        output_extensions = [],
        extra_args = [],
        visibility = None,
        **kwargs):
    """Internal helper to instantiate _dart_compile_rule."""

    _dart_compile_rule(
        name = name,
        command = command,
        main = main,
        srcs = srcs,
        deps = deps,
        package_dir = package_dir,
        output_extensions = output_extensions,
        extra_args = extra_args,
        visibility = visibility,
        **kwargs
    )

def _dart_compile_impl(ctx):
    command = ctx.attr.command
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    outputs = []
    if command == "exe":
        out_ext = ".exe" if is_windows else ""
        out_file = ctx.actions.declare_file(ctx.label.name + out_ext)
        outputs.append(out_file)
    else:
        for ext in ctx.attr.output_extensions:
            outputs.append(ctx.actions.declare_file(ctx.label.name + ext))
        out_file = outputs[0]

    dart_bin = ctx.executable.dart_sdk
    srcs = ctx.files.srcs
    deps = ctx.files.deps
    all_inputs = srcs + deps + [dart_bin, ctx.file.main]

    runner_script_name = ctx.label.name + "_builder" + (".bat" if is_windows else ".sh")
    runner_script = ctx.actions.declare_file(runner_script_name)

    dart_path = dart_bin.path
    out_path = out_file.path
    main_path = ctx.file.main.path
    pkg_dir = ctx.attr.package_dir or ctx.label.package
    extra_args = " ".join(ctx.attr.extra_args)

    if is_windows:
        content = """@echo off
setlocal
set "EXECROOT=%CD%"
set "DART=%EXECROOT%\\{dart_path}"
set "ABS_OUT=%EXECROOT%\\{out_path}"
set "MAIN={main_path}"
set "PKG_DIR={pkg_dir}"

set "TEMP_DIR=%TEMP%\\bazel_dart_build_%RANDOM%"
mkdir "%TEMP_DIR%"
xcopy . "%TEMP_DIR%" /E /I /Q >nul
cd /d "%TEMP_DIR%"

set "PUB_CACHE=%TEMP%\\pub_cache_%RANDOM%"
if not exist "%PUB_CACHE%" mkdir "%PUB_CACHE%"
set "HOME=%PUB_CACHE%"

if not "%PKG_DIR%"=="" (
  pushd "%PKG_DIR%"
  call "%DART%" pub get
  popd
) else (
  call "%DART%" pub get
)

echo Compiling...
call "%DART%" compile {command} {extra_args} -o "%ABS_OUT%" "%MAIN%"
if %errorlevel% neq 0 exit 1
""".format(
            dart_path = dart_path.replace("/", "\\"),
            main_path = main_path.replace("/", "\\"),
            out_path = out_path.replace("/", "\\"),
            pkg_dir = pkg_dir.replace("/", "\\"),
            command = command,
            extra_args = extra_args,
        )
    else:
        content = """#!/bin/bash
set -e
EXECROOT="$PWD"
DART="$EXECROOT/{dart_path}"
ABS_OUT="$EXECROOT/{out_path}"
MAIN="{main_path}"
PKG_DIR="{pkg_dir}"

TEMP_DIR=$(mktemp -d)
# Copy content to temp to allow writing to .dart_tool
cp -R . "$TEMP_DIR"
cd "$TEMP_DIR"

export PUB_CACHE=$(mktemp -d)
trap "rm -rf $TEMP_DIR $PUB_CACHE" EXIT

if [ -n "$PKG_DIR" ]; then
    pushd "$PKG_DIR" > /dev/null
    "$DART" pub get
    popd > /dev/null
else
    "$DART" pub get
fi

echo "Compiling..."
"$DART" compile {command} {extra_args} -o "$ABS_OUT" "$MAIN"
""".format(
            dart_path = dart_path,
            main_path = main_path,
            out_path = out_path,
            pkg_dir = pkg_dir,
            command = command,
            extra_args = extra_args,
        )

    ctx.actions.write(runner_script, content, is_executable = True)

    # Execution requirements for worker support
    # When --strategy=DartCompile=worker is set, Bazel will use persistent workers
    execution_requirements = {
        "supports-workers": "1",
        "requires-worker-protocol": "json",
    }

    ctx.actions.run(
        executable = runner_script,
        outputs = outputs,
        inputs = all_inputs,
        tools = [dart_bin],
        mnemonic = "DartCompile",
        arguments = [],
        execution_requirements = execution_requirements,
    )

    return [DefaultInfo(executable = out_file, files = depset(outputs))]

dart_native_binary = rule(
    implementation = _dart_compile_impl,
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
        "package_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
        "command": attr.string(default = "exe"),
        "output_extensions": attr.string_list(default = [".exe"]),
        "extra_args": attr.string_list(default = []),
    },
    executable = True,
)

_dart_compile_rule = rule(
    implementation = _dart_compile_impl,
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
        "package_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
        "command": attr.string(mandatory = True),
        "output_extensions": attr.string_list(mandatory = True),
        "extra_args": attr.string_list(default = []),
    },
    executable = False,
)

def dart_js_binary(name, main, srcs = [], deps = [], package_dir = None, visibility = None, minified = True, **kwargs):
    """Compiles a Dart program to JavaScript.

    Produces a .js file and a .js.map source map.

    Args:
        name: Name of the target.
        main: Main Dart file.
        srcs: Source files.
        deps: Dependencies.
        minified: Whether to minify the output (default True).
    """
    extra_args = ["-O4"] if minified else ["-O0"]
    _dart_compile(
        name = name,
        command = "js",
        main = main,
        srcs = srcs,
        deps = deps,
        package_dir = package_dir,
        output_extensions = [".js", ".js.map", ".js.deps"],
        extra_args = extra_args,
        visibility = visibility,
        **kwargs
    )

def dart_wasm_binary(name, main, srcs = [], deps = [], package_dir = None, visibility = None, **kwargs):
    """Compiles a Dart program to WebAssembly (`dart2wasm`).

    Produces a .wasm file and a .mjs JavaScript module wrapper.

    Args:
        name: Name of the target.
        main: Main Dart file.
        srcs: Source files.
    """
    _dart_compile(
        name = name,
        command = "wasm",
        main = main,
        srcs = srcs,
        deps = deps,
        package_dir = package_dir,
        output_extensions = [".wasm", ".mjs"],
        visibility = visibility,
        **kwargs
    )

def dart_aot_snapshot(name, main, srcs = [], deps = [], package_dir = None, visibility = None, **kwargs):
    """Compiles a Dart program to an AOT snapshot.

    Produces a .aot file. Runs with `dartaotruntime`.

    Args:
        name: Name of the target.
        main: Main Dart file.
    """
    _dart_compile(
        name = name,
        command = "aot-snapshot",
        main = main,
        srcs = srcs,
        deps = deps,
        package_dir = package_dir,
        output_extensions = [".aot"],
        visibility = visibility,
        **kwargs
    )

def dart_pub_get(name, package_dir = None, **kwargs):
    """Creates a target to run `dart pub get`.

    Useful for updating local lockfiles.
    """
    _dart_tool_target(
        name = name,
        command = "pub",
        args = ["get"],
        package_dir = package_dir,
        **kwargs
    )

def dart_pub_publish(name, package_dir = None, **kwargs):
    """Creates a target to run `dart pub publish`.

    Used for publishing packages to pub.dev.
    """
    _dart_tool_target(
        name = name,
        command = "pub",
        args = ["publish"],
        package_dir = package_dir,
        **kwargs
    )
