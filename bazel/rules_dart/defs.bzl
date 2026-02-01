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

DartPackageInfo = provider(
    doc = "Information about a Dart package for dependency tracking and transitive resolution.",
    fields = {
        "name": "Package name",
        "version": "Package version",
        "lib_root": "Path to lib directory (File)",
        "srcs": "Depset of source files (direct)",
        "data": "Depset of data files (direct)",
        "transitive_srcs": "Depset of all transitive source files",
        "transitive_data": "Depset of all transitive data files",
        "transitive_packages": "Depset of transitive package infos",
    },
)

def _dart_library_impl(ctx):
    package_name = ctx.attr.package_name

    # Collect transitive info
    transitive_packages_list = []
    transitive_srcs_list = []
    transitive_data_list = []

    for dep in ctx.attr.deps:
        if DartPackageInfo in dep:
            transitive_packages_list.append(dep[DartPackageInfo].transitive_packages)
            transitive_srcs_list.append(dep[DartPackageInfo].transitive_srcs)
            transitive_data_list.append(dep[DartPackageInfo].transitive_data)

    # Current target files
    current_srcs = depset(ctx.files.srcs)
    current_data = depset(ctx.files.data)

    transitive_srcs_list.append(current_srcs)
    transitive_data_list.append(current_data)

    current_info = None
    if package_name:
        # Determine lib root from sources
        # We assume the first source file in lib/ determines the root
        lib_root = None
        for f in ctx.files.srcs:
            # Check if file is in a 'lib' directory
            # This is a heuristic. For generated repos, it's reliable.
            # For local code, it might be tricky if srcs are scattered.
            # We'll use the package's root directory.
            lib_root = f.dirname
            break

        # If no sources, we can't determine lib_root easily, but maybe from pubspec?
        if not lib_root and ctx.file.pubspec:
            lib_root = ctx.file.pubspec.dirname + "/lib"

        if lib_root:
            current_info = struct(
                name = package_name,
                version = "0.0.0",  # TODO: Parse from pubspec if needed
                lib_root = lib_root,
                srcs = current_srcs,
            )

    # Add current package to transitive set if it exists
    if current_info:
        transitive_packages_list.append(depset([current_info]))

    # Include pubspec in files for runfiles propagation
    all_files = ctx.files.srcs + ctx.files.data
    if ctx.file.pubspec:
        all_files = all_files + [ctx.file.pubspec]

    runfiles = ctx.runfiles(files = all_files)

    # Merge in transitive runfiles from dependencies
    for dep in ctx.attr.deps:
        if DefaultInfo in dep:
            runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)

    return [
        DefaultInfo(
            files = depset(all_files),
            runfiles = runfiles,
        ),
        DartPackageInfo(
            name = package_name,
            version = "0.0.0",
            lib_root = current_info.lib_root if current_info else None,
            srcs = current_srcs,
            data = current_data,
            transitive_srcs = depset(transitive = transitive_srcs_list),
            transitive_data = depset(transitive = transitive_data_list),
            transitive_packages = depset(transitive = transitive_packages_list),
        ),
    ]

_dart_library = rule(
    implementation = _dart_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "data": attr.label_list(allow_files = True),
        "deps": attr.label_list(providers = [DartPackageInfo]),
        "package_name": attr.string(),
        "pubspec": attr.label(allow_single_file = True),
    },
)

def dart_library(name, srcs = [], deps = [], pubspec = None, package_name = None, visibility = None, **kwargs):
    """Creates a Dart library target."""
    _dart_library(
        name = name,
        srcs = srcs,
        deps = deps,
        pubspec = pubspec,
        package_name = package_name,
        visibility = visibility,
        **kwargs
    )

def _generate_package_config(ctx, deps, output_file):
    """Generates .dart_tool/package_config.json."""
    packages = []
    seen_packages = {}

    # Collect all transitive packages
    transitive_infos = []
    for dep in deps:
        if DartPackageInfo in dep:
            transitive_infos.append(dep[DartPackageInfo].transitive_packages)

    all_packages = depset(transitive = transitive_infos).to_list()

    for pkg in all_packages:
        if pkg.name in seen_packages:
            continue
        seen_packages[pkg.name] = True

        # Calculate relative path from output_file to lib_root
        # output_file is .dart_tool/package_config.json
        # lib_root is .../lib
        # We need relative path.
        # Since we can't easily compute relative paths between arbitrary artifacts in Starlark phase
        # without strict root knowledge, we might use absolute paths or runfiles paths.
        # Dart supports "rootUri" as relative.

        # For now, let's use a simplified approach:
        # We assume we are running in the runfiles tree.
        # The runfiles tree structure mirrors the repo structure.
        # So we can use the workspace-relative path.

        # pkg.lib_root is a string (dirname)
        # We need to construct the URI.

        # If it's an external repo: ../repo_name/lib
        # If it's local: package/path/lib

        # We need to handle the fact that lib_root is a path string here.
        # In _dart_library_impl, lib_root was f.dirname.

        # The package_config.json is inside .dart_tool/
        # So we need ../ to get to workspace root.

        root_uri = "../" + pkg.lib_root.rsplit("/", 1)[0]  # Parent of lib
        package_uri = "lib/"

        packages.append({
            "name": pkg.name,
            "rootUri": root_uri,
            "packageUri": package_uri,
            "languageVersion": "3.0",
        })

    config = {
        "configVersion": 2,
        "packages": packages,
        "generated": "2026-01-01T00:00:00.000000Z",
        "generator": "bazel",
        "generatorVersion": "0.1.0",
    }

    ctx.actions.write(
        output = output_file,
        content = json.encode(config),
    )

def _dart_binary_impl(ctx):
    """Cross-platform implementation for dart_binary."""
    is_windows = ctx.target_platform_has_constraint(ctx.attr._windows_constraint[platform_common.ConstraintValueInfo])

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_short_path = _runfiles_path(dart_bin)
    main_path = ctx.file.main.path

    # Generate package config
    package_config = ctx.actions.declare_file(".dart_tool/package_config.json")
    _generate_package_config(ctx, ctx.attr.deps, package_config)

    if is_windows:
        content = """@echo off
setlocal
cd /d "%BUILD_WORKSPACE_DIRECTORY%"

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
)

"%DART_BIN%" run --packages="%RUNFILES%\\_main\\{package_config}" {main} %*
""".format(
            dart_path = dart_short_path.replace("/", "\\"),
            main = main_path.replace("/", "\\"),
            package_config = package_config.short_path.replace("/", "\\"),
        )
    else:
        content = """#!/bin/bash
set -e
cd "$BUILD_WORKSPACE_DIRECTORY"

RUNFILES="${{RUNFILES:-$0.runfiles}}"
DART_BIN="$RUNFILES/{dart_path}"

if [ ! -f "$DART_BIN" ]; then
    DART_BIN="dart"
fi

exec "$DART_BIN" run --packages="$RUNFILES/_main/{package_config}" {main} "$@"
""".format(
            dart_path = dart_short_path,
            main = main_path,
            package_config = package_config.short_path,
        )

    ctx.actions.write(runner_script, content, is_executable = True)

    runfiles = ctx.runfiles(
        files = [dart_bin, ctx.file.main, package_config] + ctx.files.srcs + ctx.files.deps,
    )

    # Also collect transitive runfiles from deps
    for dep in ctx.attr.deps:
        runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)

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

    # Generate package config
    package_config = ctx.actions.declare_file(".dart_tool/package_config.json")
    _generate_package_config(ctx, ctx.attr.deps, package_config)

    # Compute relative path of test file from package directory
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

REM Run pub get to resolve dependencies (including path deps)
call "%DART_BIN%" pub get --offline 2>nul || call "%DART_BIN%" pub get

REM Sharding support
set "SHARD_ARGS="
if defined TEST_TOTAL_SHARDS (
    set "SHARD_ARGS=--total-shards=%TEST_TOTAL_SHARDS% --shard-index=%TEST_SHARD_INDEX%"
)

if defined COVERAGE_OUTPUT_FILE (
    echo Running with coverage...
    set "COVERAGE_DIR=%TEMP_DIR%\\coverage"
    call "%DART_BIN%" test %SHARD_ARGS% --coverage="!COVERAGE_DIR!" {main}
    
    if exist "!COVERAGE_DIR!\\coverage.json" (
        call "%DART_BIN%" run coverage:format_coverage ^
            --lcov ^
            --in="!COVERAGE_DIR!" ^
            --out="%COVERAGE_OUTPUT_FILE%" ^
            --report-on=lib
    )
) else (
    "%DART_BIN%" test %SHARD_ARGS% {main}
)
set "RESULT=%errorlevel%"

cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" 2>nul
exit /b %RESULT%
""".format(
            dart_path = dart_short_path.replace("/", "\\"),
            pkg_dir = pkg_dir.replace("/", "\\"),
            main = test_file.replace("/", "\\"),
        )
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

# Run pub get to resolve dependencies (including path deps)
"$DART_BIN" pub get --offline 2>/dev/null || "$DART_BIN" pub get

# Sharding support
SHARD_ARGS=""
if [[ -n "$TEST_TOTAL_SHARDS" ]]; then
    SHARD_ARGS="--total-shards=$TEST_TOTAL_SHARDS --shard-index=$TEST_SHARD_INDEX"
fi

if [ -n "$COVERAGE_OUTPUT_FILE" ]; then
    echo "Running with coverage..."
    COVERAGE_DIR="$TEMP_DIR/coverage"
    "$DART_BIN" test $SHARD_ARGS --coverage="$COVERAGE_DIR" {main}
    
    if [ -f "$COVERAGE_DIR/coverage.json" ]; then
        "$DART_BIN" run coverage:format_coverage \\
            --lcov \\
            --in="$COVERAGE_DIR" \\
            --out="$COVERAGE_OUTPUT_FILE" \\
            --report-on=lib
    fi
else
    "$DART_BIN" test $SHARD_ARGS {main}
fi
""".format(
            dart_path = dart_short_path,
            pkg_dir = pkg_dir,
            main = test_file,
        )

    ctx.actions.write(runner_script, content, is_executable = True)

    runfiles = ctx.runfiles(
        files = [dart_bin, ctx.file.main, package_config] + ctx.files.srcs + ctx.files.deps + ctx.files.data,
    )

    # Also collect transitive runfiles from deps
    for dep in ctx.attr.deps:
        runfiles = runfiles.merge(dep[DefaultInfo].default_runfiles)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_dart_test = rule(
    implementation = _dart_test_impl,
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(providers = [DartPackageInfo]),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    test = True,
)

def dart_test(name, main, srcs = [], deps = [], data = [], visibility = None, package_dir = None, shard_count = None, **kwargs):
    """Creates a Dart test target.

    Args:
        name: Target name.
        main: Main test file.
        srcs: Additional source files.
        deps: Dependencies.
        data: Runtime data files.
        visibility: Target visibility.
        package_dir: Package directory containing pubspec.yaml.
        shard_count: Number of parallel test shards (for large test suites).
        **kwargs: Additional arguments passed to the test rule.
    """
    _dart_test(
        name = name,
        main = main,
        srcs = srcs,
        deps = deps,
        data = data,
        package_dir = package_dir,
        visibility = visibility,
        shard_count = shard_count,
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
        pubspec = None,
        output_extensions = [],
        extra_args = [],
        visibility = None,
        **kwargs):
    """Internal helper to instantiate _dart_compile_rule."""
    pkg_dir = package_dir or native.package_name() or "."
    effective_pubspec = pubspec or (pkg_dir + "/pubspec.yaml" if pkg_dir != "." else "pubspec.yaml")

    _dart_compile_rule(
        name = name,
        command = command,
        main = main,
        srcs = srcs,
        deps = deps,
        package_dir = package_dir,
        pubspec = effective_pubspec,
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
    pubspec_files = [ctx.file.pubspec] if ctx.file.pubspec else []
    all_inputs = srcs + deps + pubspec_files + [dart_bin, ctx.file.main]

    runner_script_name = ctx.label.name + "_builder" + (".bat" if is_windows else ".sh")
    runner_script = ctx.actions.declare_file(runner_script_name)

    dart_path = dart_bin.path
    out_path = out_file.path
    main_path = ctx.file.main.path

    # Determine package directory: use explicit attr, or derive from label package
    # For targets at workspace root (empty package), use "." to indicate current directory
    pkg_dir = ctx.attr.package_dir or ctx.label.package or "."

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

REM cd to package dir for pub get
cd /d "%TEMP_DIR%\\%PKG_DIR%"
call "%DART%" pub get
cd /d "%TEMP_DIR%"

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

# cd to package dir for pub get
cd "$TEMP_DIR/$PKG_DIR"
"$DART" pub get
cd "$TEMP_DIR"

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

    # Note: Worker support is disabled for shell-script based execution.
    # To enable persistent workers, the action would need to implement the
    # Bazel worker protocol (JSON requests/responses via stdin/stdout).
    # See: https://bazel.build/remote/persistent
    #
    # For now, we rely on Bazel's action caching for build performance.
    # TODO(#124): Implement proper persistent worker binary for Dart compilation.

    ctx.actions.run(
        executable = runner_script,
        outputs = outputs,
        inputs = all_inputs,
        tools = [dart_bin],
        mnemonic = "DartCompile",
        progress_message = "Compiling Dart %{label}",
        # Explicitly disable worker strategy for shell-script based execution.
        # Shell scripts don't implement the Bazel worker protocol (flagfile pattern).
        # TODO(#124): Implement proper persistent worker binary for Dart compilation.
        execution_requirements = {
            "no-remote": "1",  # Shell scripts need local execution
            "supports-workers": "0",  # Disable worker strategy
        },
    )

    return [DefaultInfo(executable = out_file, files = depset(outputs))]

_dart_native_binary_rule = rule(
    implementation = _dart_compile_impl,
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
        "package_dir": attr.string(),
        "pubspec": attr.label(allow_single_file = True, doc = "The pubspec.yaml file for the package."),
        "dart_sdk": attr.label(default = Label("@dart_sdk//:dart_bin"), executable = True, cfg = "exec", allow_single_file = True),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
        "command": attr.string(default = "exe"),
        "output_extensions": attr.string_list(default = [".exe"]),
        "extra_args": attr.string_list(default = []),
    },
    executable = True,
)

def dart_native_binary(name, main, srcs = [], deps = [], package_dir = None, pubspec = None, visibility = None, **kwargs):
    """Compiles a Dart program to a native executable.

    Args:
        name: Name of the target.
        main: Main Dart file.
        srcs: Source files.
        deps: Dependencies.
        package_dir: Package directory containing pubspec.yaml.
        pubspec: Path to pubspec.yaml (defaults to pubspec.yaml in the package).
        visibility: Target visibility.
        **kwargs: Additional arguments passed to the underlying rule.
    """
    pkg_dir = package_dir or native.package_name() or "."
    effective_pubspec = pubspec or (pkg_dir + "/pubspec.yaml" if pkg_dir != "." else "pubspec.yaml")

    _dart_native_binary_rule(
        name = name,
        main = main,
        srcs = srcs,
        deps = deps,
        package_dir = package_dir,
        pubspec = effective_pubspec,
        visibility = visibility,
        **kwargs
    )

_dart_compile_rule = rule(
    implementation = _dart_compile_impl,
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
        "package_dir": attr.string(),
        "pubspec": attr.label(allow_single_file = True, doc = "The pubspec.yaml file for the package."),
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
        package_dir: Package directory containing pubspec.yaml.
        visibility: Target visibility.
        minified: Whether to minify the output (default True).
        **kwargs: Additional arguments passed to the underlying rule.
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
        deps: Dependencies.
        package_dir: Package directory containing pubspec.yaml.
        visibility: Target visibility.
        **kwargs: Additional arguments passed to the underlying rule.
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
        srcs: Source files.
        deps: Dependencies.
        package_dir: Package directory containing pubspec.yaml.
        visibility: Target visibility.
        **kwargs: Additional arguments passed to the underlying rule.
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
