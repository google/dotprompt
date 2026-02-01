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

"""Additional Flutter rules covering CLI features.

This module provides rules that wrap Flutter CLI commands not covered by defs.bzl:

┌──────────────────────────────────────────────────────────────────────────────────┐
│                        Flutter CLI Command Coverage                              │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Build Commands (flutter build)                                                  │
│  ├── flutter_web_app          → flutter build web [--wasm]                       │
│  ├── flutter_android_apk      → flutter build apk [--split-per-abi]             │
│  ├── flutter_android_bundle   → flutter build appbundle                          │
│  ├── flutter_ios_app          → flutter build ios/ipa                            │
│  ├── flutter_macos_app        → flutter build macos                              │
│  ├── flutter_linux_app        → flutter build linux                              │
│  └── flutter_windows_app      → flutter build windows                            │
│                                                                                  │
│  Development Commands                                                            │
│  ├── flutter_run              → flutter run (with device selection)              │
│  └── flutter_dev_server       → flutter run --web-port (persistent server)       │
│                                                                                  │
│  Analysis Commands                                                               │
│  ├── flutter_analyze          → flutter analyze                                  │
│  └── flutter_format_check     → dart format --set-exit-if-changed                │
│                                                                                  │
│  Dependency Commands                                                             │
│  ├── flutter_pub_get          → flutter pub get                                  │
│  ├── flutter_pub_upgrade      → flutter pub upgrade                              │
│  └── flutter_pub_outdated     → flutter pub outdated                             │
│                                                                                  │
│  Code Generation                                                                 │
│  ├── flutter_build_runner     → dart run build_runner build                      │
│  └── flutter_gen_l10n         → flutter gen-l10n                                 │
│                                                                                  │
│  Documentation                                                                   │
│  └── flutter_doc              → dart doc                                         │
│                                                                                  │
│  Packaging                                                                       │
│  └── flutter_pub_publish      → flutter pub publish                              │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

Usage:
    load("@rules_flutter//:flutter.bzl", "flutter_web_app", "flutter_analyze", ...)
"""

load("//private:helpers.bzl", "runfiles_path", "to_windows_path")

# =============================================================================
# flutter_web_app - Comprehensive web build with WASM support
# =============================================================================

def _flutter_web_app_impl(ctx):
    """Implementation of flutter_web_app rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + "_build" + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Build command with options
    build_args = ["build", "web"]

    if ctx.attr.wasm:
        build_args.append("--wasm")

    if ctx.attr.build_mode == "release":
        build_args.append("--release")
    elif ctx.attr.build_mode == "profile":
        build_args.append("--profile")

    if ctx.attr.tree_shake_icons:
        build_args.append("--tree-shake-icons")

    if ctx.attr.source_maps:
        build_args.append("--source-maps")

    if ctx.attr.dart2js_optimization:
        build_args.extend(["--dart2js-optimization", ctx.attr.dart2js_optimization])

    if ctx.attr.pwa_strategy:
        build_args.extend(["--pwa-strategy", ctx.attr.pwa_strategy])

    if ctx.attr.base_href:
        build_args.extend(["--base-href", ctx.attr.base_href])

    if ctx.attr.web_renderer:
        build_args.extend(["--web-renderer", ctx.attr.web_renderer])

    build_cmd = " ".join(build_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"

if not exist "%FLUTTER_BIN%" (
    set "FLUTTER_BIN=flutter"
)

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

echo Building Flutter web application...
call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
call "%FLUTTER_BIN%" {build_cmd}

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Output: build/web
    if "{wasm}" == "True" (
        echo Mode: WebAssembly (WASM)
    ) else (
        echo Mode: JavaScript
    )
)
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            build_cmd = build_cmd,
            wasm = str(ctx.attr.wasm),
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

echo "Building Flutter web application..."
"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" {build_cmd}

echo ""
echo "Build successful!"
echo "Output: build/web"
{wasm_message}
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            build_cmd = build_cmd,
            wasm_message = 'echo "Mode: WebAssembly (WASM)"' if ctx.attr.wasm else 'echo "Mode: JavaScript"',
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_web_app = rule(
    implementation = _flutter_web_app_impl,
    doc = "Flutter web application build with comprehensive options.",
    attrs = {
        "deps": attr.label_list(doc = "flutter_library dependencies."),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "build_mode": attr.string(
            default = "release",
            values = ["debug", "profile", "release"],
            doc = "Build mode.",
        ),
        "wasm": attr.bool(
            default = False,
            doc = "Build with WebAssembly (WASM) instead of JavaScript.",
        ),
        "tree_shake_icons": attr.bool(
            default = True,
            doc = "Tree shake icons to reduce bundle size.",
        ),
        "source_maps": attr.bool(
            default = False,
            doc = "Generate source maps for debugging.",
        ),
        "dart2js_optimization": attr.string(
            default = "",
            doc = "Dart2JS optimization level (O0, O1, O2, O3, O4).",
        ),
        "pwa_strategy": attr.string(
            default = "",
            doc = "PWA caching strategy (offline-first, none).",
        ),
        "base_href": attr.string(
            default = "",
            doc = "Base URL path for the application.",
        ),
        "web_renderer": attr.string(
            default = "",
            values = ["", "auto", "canvaskit", "html", "skwasm"],
            doc = "Web renderer to use.",
        ),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_web_app(
        name,
        deps = [],
        data = [],
        package_dir = None,
        build_mode = "release",
        wasm = False,
        tree_shake_icons = True,
        source_maps = False,
        dart2js_optimization = "",
        pwa_strategy = "",
        base_href = "",
        web_renderer = "",
        visibility = None,
        **kwargs):
    """Build a Flutter web application.

    Supports both JavaScript and WebAssembly (WASM) compilation.

    Args:
        name: Target name.
        deps: flutter_library dependencies.
        data: Runtime data files.
        package_dir: Package directory containing pubspec.yaml.
        build_mode: Build mode (debug, profile, release).
        wasm: If True, compile to WebAssembly instead of JavaScript.
        tree_shake_icons: Remove unused icons to reduce bundle size.
        source_maps: Generate source maps for debugging.
        dart2js_optimization: Optimization level (O0-O4).
        pwa_strategy: PWA caching strategy.
        base_href: Base URL path for the application.
        web_renderer: Web renderer (auto, canvaskit, html, skwasm).
        visibility: Target visibility.
        **kwargs: Additional arguments.

    Example:
        flutter_web_app(
            name = "web_app",
            deps = [":app_lib"],
            wasm = True,
            web_renderer = "skwasm",
        )
    """
    _flutter_web_app(
        name = name,
        deps = deps,
        data = data,
        package_dir = package_dir,
        build_mode = build_mode,
        wasm = wasm,
        tree_shake_icons = tree_shake_icons,
        source_maps = source_maps,
        dart2js_optimization = dart2js_optimization,
        pwa_strategy = pwa_strategy,
        base_href = base_href,
        web_renderer = web_renderer,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_analyze - Static analysis
# =============================================================================

def _flutter_analyze_impl(ctx):
    """Implementation of flutter_analyze rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    analyze_args = ["analyze"]
    if ctx.attr.fatal_infos:
        analyze_args.append("--fatal-infos")
    if ctx.attr.fatal_warnings:
        analyze_args.append("--fatal-warnings")

    analyze_cmd = " ".join(analyze_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

"%FLUTTER_BIN%" {analyze_cmd}
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            analyze_cmd = analyze_cmd,
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

"$FLUTTER_BIN" {analyze_cmd}
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            analyze_cmd = analyze_cmd,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.srcs
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_analyze_test = rule(
    implementation = _flutter_analyze_impl,
    doc = "Run Flutter static analysis.",
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "fatal_infos": attr.bool(default = False, doc = "Treat info level issues as fatal."),
        "fatal_warnings": attr.bool(default = True, doc = "Treat warnings as fatal."),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    test = True,
)

def flutter_analyze(name, srcs = [], package_dir = None, fatal_infos = False, fatal_warnings = True, visibility = None, **kwargs):
    """Run Flutter static analysis.

    Args:
        name: Target name.
        srcs: Source files to include in analysis context.
        package_dir: Package directory containing pubspec.yaml.
        fatal_infos: Treat info level issues as fatal.
        fatal_warnings: Treat warnings as fatal.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_analyze_test(
        name = name,
        srcs = srcs,
        package_dir = package_dir,
        fatal_infos = fatal_infos,
        fatal_warnings = fatal_warnings,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_format_check - Code formatting validation
# =============================================================================

def _flutter_format_check_impl(ctx):
    """Implementation of flutter_format_check rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

dart format --set-exit-if-changed --output=none .
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

dart format --set-exit-if-changed --output=none .
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.srcs
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_format_check_test = rule(
    implementation = _flutter_format_check_impl,
    doc = "Check Flutter/Dart code formatting.",
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    test = True,
)

def flutter_format_check(name, srcs = [], package_dir = None, visibility = None, **kwargs):
    """Check Flutter/Dart code formatting.

    Args:
        name: Target name.
        srcs: Source files to check.
        package_dir: Package directory containing pubspec.yaml.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_format_check_test(
        name = name,
        srcs = srcs,
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_pub_get - Dependency resolution
# =============================================================================

def _flutter_pub_get_impl(ctx):
    """Implementation of flutter_pub_get rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    pub_args = ["pub", "get"]
    if ctx.attr.offline:
        pub_args.append("--offline")

    pub_cmd = " ".join(pub_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

"%FLUTTER_BIN%" {pub_cmd}
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            pub_cmd = pub_cmd,
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

"$FLUTTER_BIN" {pub_cmd}
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            pub_cmd = pub_cmd,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin]
    if ctx.file.pubspec:
        all_files.append(ctx.file.pubspec)
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_pub_get = rule(
    implementation = _flutter_pub_get_impl,
    doc = "Run flutter pub get.",
    attrs = {
        "pubspec": attr.label(allow_single_file = True),
        "package_dir": attr.string(),
        "offline": attr.bool(default = False, doc = "Use cached packages only."),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_pub_get(name, pubspec = None, package_dir = None, offline = False, visibility = None, **kwargs):
    """Run flutter pub get to resolve dependencies.

    Args:
        name: Target name.
        pubspec: pubspec.yaml file.
        package_dir: Package directory containing pubspec.yaml.
        offline: Use cached packages only.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_pub_get(
        name = name,
        pubspec = pubspec,
        package_dir = package_dir,
        offline = offline,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_build_runner - Code generation
# =============================================================================

def _flutter_build_runner_impl(ctx):
    """Implementation of flutter_build_runner rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    build_args = ["run", "build_runner", "build"]
    if ctx.attr.delete_conflicting_outputs:
        build_args.append("--delete-conflicting-outputs")

    build_cmd = " ".join(build_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

"%FLUTTER_BIN%" pub get
dart {build_cmd}
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            build_cmd = build_cmd,
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

"$FLUTTER_BIN" pub get
dart {build_cmd}
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            build_cmd = build_cmd,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.srcs
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_build_runner = rule(
    implementation = _flutter_build_runner_impl,
    doc = "Run build_runner for code generation.",
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "delete_conflicting_outputs": attr.bool(
            default = True,
            doc = "Delete conflicting outputs during generation.",
        ),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_build_runner(name, srcs = [], package_dir = None, delete_conflicting_outputs = True, visibility = None, **kwargs):
    """Run build_runner for code generation.

    Useful for packages using json_serializable, freezed, auto_route, etc.

    Args:
        name: Target name.
        srcs: Source files that trigger regeneration.
        package_dir: Package directory containing pubspec.yaml.
        delete_conflicting_outputs: Delete conflicting outputs.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_build_runner(
        name = name,
        srcs = srcs,
        package_dir = package_dir,
        delete_conflicting_outputs = delete_conflicting_outputs,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_gen_l10n - Localization generation
# =============================================================================

def _flutter_gen_l10n_impl(ctx):
    """Implementation of flutter_gen_l10n rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

"%FLUTTER_BIN%" gen-l10n
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

"$FLUTTER_BIN" gen-l10n
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.arb_files
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_gen_l10n = rule(
    implementation = _flutter_gen_l10n_impl,
    doc = "Generate localization files from ARB.",
    attrs = {
        "arb_files": attr.label_list(allow_files = [".arb"]),
        "package_dir": attr.string(),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_gen_l10n(name, arb_files = [], package_dir = None, visibility = None, **kwargs):
    """Generate localization files from ARB files.

    Args:
        name: Target name.
        arb_files: ARB localization files.
        package_dir: Package directory containing pubspec.yaml.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_gen_l10n(
        name = name,
        arb_files = arb_files,
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_clean - Clean build artifacts
# =============================================================================

def _flutter_clean_impl(ctx):
    """Implementation of flutter_clean rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

"%FLUTTER_BIN%" clean
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

"$FLUTTER_BIN" clean
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    runfiles = ctx.runfiles(files = [flutter_bin])

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_clean = rule(
    implementation = _flutter_clean_impl,
    doc = "Clean Flutter build artifacts.",
    attrs = {
        "package_dir": attr.string(),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_clean(name, package_dir = None, visibility = None, **kwargs):
    """Clean Flutter build artifacts.

    Args:
        name: Target name.
        package_dir: Package directory containing pubspec.yaml.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_clean(
        name = name,
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_doctor - Check Flutter installation
# =============================================================================

def _flutter_doctor_impl(ctx):
    """Implementation of flutter_doctor rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)

    doctor_args = ["doctor"]
    if ctx.attr.verbose:
        doctor_args.append("-v")

    doctor_cmd = " ".join(doctor_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

"%FLUTTER_BIN%" {doctor_cmd}
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            doctor_cmd = doctor_cmd,
        )
    else:
        content = """#!/bin/bash

FLUTTER_BIN="{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

"$FLUTTER_BIN" {doctor_cmd}
""".format(
            flutter_path = flutter_path,
            doctor_cmd = doctor_cmd,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    runfiles = ctx.runfiles(files = [flutter_bin])

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_doctor = rule(
    implementation = _flutter_doctor_impl,
    doc = "Run flutter doctor.",
    attrs = {
        "verbose": attr.bool(default = False, doc = "Enable verbose output."),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_doctor(name, verbose = False, visibility = None, **kwargs):
    """Run flutter doctor to check installation.

    Args:
        name: Target name.
        verbose: Enable verbose output.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_doctor(
        name = name,
        verbose = verbose,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_android_apk - Android APK builds
# =============================================================================

def _flutter_android_apk_impl(ctx):
    """Implementation of flutter_android_apk rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + "_build" + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Build command with options
    build_args = ["build", "apk"]

    if ctx.attr.build_mode == "release":
        build_args.append("--release")
    elif ctx.attr.build_mode == "profile":
        build_args.append("--profile")
    elif ctx.attr.build_mode == "debug":
        build_args.append("--debug")

    if ctx.attr.split_per_abi:
        build_args.append("--split-per-abi")

    if ctx.attr.target_platform:
        build_args.extend(["--target-platform", ctx.attr.target_platform])

    if ctx.attr.obfuscate:
        build_args.append("--obfuscate")
        if ctx.attr.split_debug_info:
            build_args.extend(["--split-debug-info", ctx.attr.split_debug_info])

    if ctx.attr.tree_shake_icons:
        build_args.append("--tree-shake-icons")

    if ctx.attr.flavor:
        build_args.extend(["--flavor", ctx.attr.flavor])

    if ctx.attr.dart_define:
        for define in ctx.attr.dart_define:
            build_args.extend(["--dart-define", define])

    build_cmd = " ".join(build_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

echo Building Android APK...
call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
call "%FLUTTER_BIN%" {build_cmd}

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Output: build/app/outputs/flutter-apk/
)
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            build_cmd = build_cmd,
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

echo "Building Android APK..."
"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" {build_cmd}

echo ""
echo "Build successful!"
echo "Output: build/app/outputs/flutter-apk/"
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            build_cmd = build_cmd,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_android_apk = rule(
    implementation = _flutter_android_apk_impl,
    doc = "Build Android APK with comprehensive options.",
    attrs = {
        "deps": attr.label_list(doc = "flutter_library dependencies."),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "build_mode": attr.string(
            default = "release",
            values = ["debug", "profile", "release"],
        ),
        "split_per_abi": attr.bool(
            default = False,
            doc = "Generate separate APKs per ABI (armeabi-v7a, arm64-v8a, x86_64).",
        ),
        "target_platform": attr.string(
            default = "",
            doc = "Target platform(s): android-arm, android-arm64, android-x86, android-x64.",
        ),
        "obfuscate": attr.bool(default = False, doc = "Enable code obfuscation."),
        "split_debug_info": attr.string(default = "", doc = "Directory for debug symbols."),
        "tree_shake_icons": attr.bool(default = True, doc = "Remove unused icons."),
        "flavor": attr.string(default = "", doc = "Build flavor."),
        "dart_define": attr.string_list(default = [], doc = "Compile-time variables."),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_android_apk(
        name,
        deps = [],
        data = [],
        package_dir = None,
        build_mode = "release",
        split_per_abi = False,
        target_platform = "",
        obfuscate = False,
        split_debug_info = "",
        tree_shake_icons = True,
        flavor = "",
        dart_define = [],
        visibility = None,
        **kwargs):
    """Build an Android APK.

    This is the primary way to generate Android mobile apps with Flutter/Bazel.

    Args:
        name: Target name.
        deps: flutter_library dependencies.
        data: Runtime data files.
        package_dir: Package directory containing pubspec.yaml.
        build_mode: Build mode (debug, profile, release).
        split_per_abi: Generate separate APKs per ABI.
        target_platform: Target platform(s).
        obfuscate: Enable code obfuscation.
        split_debug_info: Directory for debug symbols when obfuscating.
        tree_shake_icons: Remove unused icons.
        flavor: Build flavor for multi-flavor apps.
        dart_define: Compile-time variables (KEY=VALUE).
        visibility: Target visibility.
        **kwargs: Additional arguments.

    Example:
        # Basic APK build
        flutter_android_apk(
            name = "app_apk",
            deps = [":app_lib"],
        )

        # Split APKs per ABI (smaller downloads)
        flutter_android_apk(
            name = "app_split_apks",
            deps = [":app_lib"],
            split_per_abi = True,
        )

        # Release with obfuscation
        flutter_android_apk(
            name = "app_release",
            deps = [":app_lib"],
            obfuscate = True,
            split_debug_info = "build/symbols",
        )
    """
    _flutter_android_apk(
        name = name,
        deps = deps,
        data = data,
        package_dir = package_dir,
        build_mode = build_mode,
        split_per_abi = split_per_abi,
        target_platform = target_platform,
        obfuscate = obfuscate,
        split_debug_info = split_debug_info,
        tree_shake_icons = tree_shake_icons,
        flavor = flavor,
        dart_define = dart_define,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_android_bundle - Android App Bundle (AAB)
# =============================================================================

def _flutter_android_bundle_impl(ctx):
    """Implementation of flutter_android_bundle rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + "_build" + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Build command
    build_args = ["build", "appbundle"]

    if ctx.attr.build_mode == "release":
        build_args.append("--release")
    elif ctx.attr.build_mode == "profile":
        build_args.append("--profile")

    if ctx.attr.obfuscate:
        build_args.append("--obfuscate")
        if ctx.attr.split_debug_info:
            build_args.extend(["--split-debug-info", ctx.attr.split_debug_info])

    if ctx.attr.tree_shake_icons:
        build_args.append("--tree-shake-icons")

    if ctx.attr.flavor:
        build_args.extend(["--flavor", ctx.attr.flavor])

    for define in ctx.attr.dart_define:
        build_args.extend(["--dart-define", define])

    build_cmd = " ".join(build_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

echo Building Android App Bundle (AAB)...
call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
call "%FLUTTER_BIN%" {build_cmd}

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Output: build/app/outputs/bundle/release/app-release.aab
    echo.
    echo Upload this AAB to Google Play Console for distribution.
)
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            build_cmd = build_cmd,
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

echo "Building Android App Bundle (AAB)..."
"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" {build_cmd}

echo ""
echo "Build successful!"
echo "Output: build/app/outputs/bundle/release/app-release.aab"
echo ""
echo "Upload this AAB to Google Play Console for distribution."
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            build_cmd = build_cmd,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_android_bundle = rule(
    implementation = _flutter_android_bundle_impl,
    doc = "Build Android App Bundle (AAB) for Google Play.",
    attrs = {
        "deps": attr.label_list(doc = "flutter_library dependencies."),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "build_mode": attr.string(default = "release", values = ["profile", "release"]),
        "obfuscate": attr.bool(default = False),
        "split_debug_info": attr.string(default = ""),
        "tree_shake_icons": attr.bool(default = True),
        "flavor": attr.string(default = ""),
        "dart_define": attr.string_list(default = []),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_android_bundle(
        name,
        deps = [],
        data = [],
        package_dir = None,
        build_mode = "release",
        obfuscate = False,
        split_debug_info = "",
        tree_shake_icons = True,
        flavor = "",
        dart_define = [],
        visibility = None,
        **kwargs):
    """Build an Android App Bundle (AAB) for Google Play distribution.

    AABs are the preferred format for Google Play as they enable:
    - Smaller downloads (Dynamic Delivery)
    - Automatic ABI splitting
    - Better optimization

    Args:
        name: Target name.
        deps: flutter_library dependencies.
        data: Runtime data files.
        package_dir: Package directory containing pubspec.yaml.
        build_mode: Build mode (profile, release).
        obfuscate: Enable code obfuscation.
        split_debug_info: Directory for debug symbols.
        tree_shake_icons: Remove unused icons.
        flavor: Build flavor.
        dart_define: Compile-time variables.
        visibility: Target visibility.
        **kwargs: Additional arguments.

    Example:
        flutter_android_bundle(
            name = "app_bundle",
            deps = [":app_lib"],
            obfuscate = True,
            split_debug_info = "build/symbols",
        )
    """
    _flutter_android_bundle(
        name = name,
        deps = deps,
        data = data,
        package_dir = package_dir,
        build_mode = build_mode,
        obfuscate = obfuscate,
        split_debug_info = split_debug_info,
        tree_shake_icons = tree_shake_icons,
        flavor = flavor,
        dart_define = dart_define,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_ios_app - iOS builds
# =============================================================================

def _flutter_ios_app_impl(ctx):
    """Implementation of flutter_ios_app rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    if is_windows:
        # iOS builds require macOS
        fail("iOS builds require macOS. Windows is not supported for iOS builds.")

    runner_script = ctx.actions.declare_file(ctx.label.name + "_build.sh")

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Determine build type (ios vs ipa)
    if ctx.attr.ipa:
        build_args = ["build", "ipa"]
    else:
        build_args = ["build", "ios"]

    if ctx.attr.build_mode == "release":
        build_args.append("--release")
    elif ctx.attr.build_mode == "profile":
        build_args.append("--profile")
    elif ctx.attr.build_mode == "debug":
        build_args.append("--debug")

    if not ctx.attr.codesign:
        build_args.append("--no-codesign")

    if ctx.attr.obfuscate:
        build_args.append("--obfuscate")
        if ctx.attr.split_debug_info:
            build_args.extend(["--split-debug-info", ctx.attr.split_debug_info])

    if ctx.attr.tree_shake_icons:
        build_args.append("--tree-shake-icons")

    if ctx.attr.flavor:
        build_args.extend(["--flavor", ctx.attr.flavor])

    if ctx.attr.export_options_plist:
        build_args.extend(["--export-options-plist", ctx.attr.export_options_plist])

    for define in ctx.attr.dart_define:
        build_args.extend(["--dart-define", define])

    build_cmd = " ".join(build_args)

    content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

echo "Building iOS application..."
"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" {build_cmd}

echo ""
echo "Build successful!"
{output_message}
""".format(
        flutter_path = flutter_path,
        pkg_dir = pkg_dir,
        build_cmd = build_cmd,
        output_message = 'echo "Output: build/ios/ipa/"' if ctx.attr.ipa else 'echo "Output: build/ios/iphoneos/Runner.app"',
    )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_ios_app = rule(
    implementation = _flutter_ios_app_impl,
    doc = "Build iOS application.",
    attrs = {
        "deps": attr.label_list(doc = "flutter_library dependencies."),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "build_mode": attr.string(default = "release", values = ["debug", "profile", "release"]),
        "ipa": attr.bool(default = False, doc = "Build IPA for distribution instead of .app."),
        "codesign": attr.bool(default = False, doc = "Enable code signing."),
        "obfuscate": attr.bool(default = False),
        "split_debug_info": attr.string(default = ""),
        "tree_shake_icons": attr.bool(default = True),
        "flavor": attr.string(default = ""),
        "export_options_plist": attr.string(default = "", doc = "Path to ExportOptions.plist."),
        "dart_define": attr.string_list(default = []),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_ios_app(
        name,
        deps = [],
        data = [],
        package_dir = None,
        build_mode = "release",
        ipa = False,
        codesign = False,
        obfuscate = False,
        split_debug_info = "",
        tree_shake_icons = True,
        flavor = "",
        export_options_plist = "",
        dart_define = [],
        visibility = None,
        **kwargs):
    """Build an iOS application.

    Requires macOS with Xcode installed.

    Args:
        name: Target name.
        deps: flutter_library dependencies.
        data: Runtime data files.
        package_dir: Package directory containing pubspec.yaml.
        build_mode: Build mode (debug, profile, release).
        ipa: Build IPA for App Store/TestFlight distribution.
        codesign: Enable code signing (requires provisioning profile).
        obfuscate: Enable code obfuscation.
        split_debug_info: Directory for debug symbols.
        tree_shake_icons: Remove unused icons.
        flavor: Build flavor.
        export_options_plist: Path to ExportOptions.plist for IPA export.
        dart_define: Compile-time variables.
        visibility: Target visibility.
        **kwargs: Additional arguments.

    Example:
        # Development build (no signing)
        flutter_ios_app(
            name = "app_ios_debug",
            deps = [":app_lib"],
            build_mode = "debug",
        )

        # Release IPA for TestFlight
        flutter_ios_app(
            name = "app_ios_release",
            deps = [":app_lib"],
            ipa = True,
            codesign = True,
            export_options_plist = "ios/ExportOptions.plist",
        )
    """
    _flutter_ios_app(
        name = name,
        deps = deps,
        data = data,
        package_dir = package_dir,
        build_mode = build_mode,
        ipa = ipa,
        codesign = codesign,
        obfuscate = obfuscate,
        split_debug_info = split_debug_info,
        tree_shake_icons = tree_shake_icons,
        flavor = flavor,
        export_options_plist = export_options_plist,
        dart_define = dart_define,
        visibility = visibility,
        **kwargs
    )

def flutter_dev_server(
        name,
        deps = [],
        data = [],
        package_dir = None,
        device = "chrome",
        web_port = None,
        visibility = None,
        **kwargs):
    """Run a Flutter development server (hot reload).

    This wraps `flutter run` with specific device targeting, commonly used for
    web development (chrome) or specific device IDs.

    Args:
        name: Target name.
        deps: flutter_library dependencies.
        data: Runtime data files.
        package_dir: Package directory containing pubspec.yaml.
        device: Target device (chrome, macos, linux, windows, etc.).
        web_port: Port to serve the web application on (if device is chrome/web-server).
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_dev_server(
        name = name,
        deps = deps,
        data = data,
        package_dir = package_dir,
        device = device,
        web_port = str(web_port) if web_port else "",
        visibility = visibility,
        **kwargs
    )

def _flutter_dev_server_impl(ctx):
    """Implementation of flutter_dev_server rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    device = ctx.attr.device
    web_port = ctx.attr.web_port

    run_args = ["run"]
    if device:
        run_args.append("-d " + device)
    if web_port:
        run_args.append("--web-port=" + web_port)

    run_cmd = " ".join(run_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
"%FLUTTER_BIN%" {run_cmd} %*
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            run_cmd = run_cmd,
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" {run_cmd} "$@"
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            run_cmd = run_cmd,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_dev_server = rule(
    implementation = _flutter_dev_server_impl,
    doc = "Flutter development server runner.",
    attrs = {
        "deps": attr.label_list(doc = "flutter_library dependencies."),
        "device": attr.string(doc = "Target device."),
        "web_port": attr.string(doc = "Web port."),
        "data": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)
