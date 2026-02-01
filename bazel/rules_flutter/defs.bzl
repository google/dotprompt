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

"""Flutter rules for Bazel.

Production-ready, BCR-publishable Flutter rules supporting all platforms:
- flutter_library: Reusable Flutter libraries
- flutter_binary: Run Flutter apps in development mode
- flutter_test: Widget and unit testing
- flutter_application: Multi-platform app builds

Supported Platforms:
┌──────────────────────────────────────────────────────────────────────────────┐
│  Platform     │ Output              │ Build Command                         │
├───────────────┼─────────────────────┼───────────────────────────────────────┤
│  android      │ APK                 │ flutter build apk                     │
│  android_aab  │ App Bundle          │ flutter build appbundle               │
│  ios          │ IPA                 │ flutter build ios                     │
│  web          │ Web bundle          │ flutter build web                     │
│  macos        │ .app                │ flutter build macos                   │
│  linux        │ Binary              │ flutter build linux                   │
│  windows      │ .exe                │ flutter build windows                 │
└──────────────────────────────────────────────────────────────────────────────┘

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Flutter Bazel Integration                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  flutter_library         flutter_application                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────────┐ │
│  │ lib/**/*.dart   │    │                                                 │ │
│  │ assets/         │    │  target_platform:                               │ │
│  │ pubspec.yaml    │────┤  ├── android → APK/AAB                         │ │
│  └─────────────────┘    │  ├── ios → IPA                                  │ │
│                         │  ├── web → JS bundle                            │ │
│                         │  ├── macos → .app                               │ │
│                         │  ├── linux → binary                             │ │
│                         │  └── windows → .exe                             │ │
│                         └─────────────────────────────────────────────────┘ │
│                                                                              │
│  flutter_test                                                                │
│  ┌─────────────────┐                                                         │
│  │ test/**/*.dart  │────▶ flutter test (with coverage support)             │
│  │ golden files    │                                                         │
│  └─────────────────┘                                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Usage:
    load("@rules_flutter//:defs.bzl", "flutter_library", "flutter_application", "flutter_test")
"""

load("@rules_dart//:defs.bzl", "DartPackageInfo")
load("//aspects:ide.bzl", "FlutterIdeInfo")
load("//private:helpers.bzl", "runfiles_path", "to_windows_path")

# =============================================================================
# Providers
# =============================================================================

FlutterLibraryInfo = provider(
    doc = "Information about a Flutter library.",
    fields = {
        "sources": "Depset of source files.",
        "assets": "Depset of asset files.",
        "pubspec": "File: pubspec.yaml.",
        "transitive_sources": "Depset of all transitive sources.",
        "transitive_assets": "Depset of all transitive assets.",
    },
)

# =============================================================================
# flutter_library
# =============================================================================

def _flutter_library_impl(ctx):
    """Implementation of flutter_library rule."""
    sources = depset(ctx.files.srcs)
    assets = depset(ctx.files.assets)

    # Collect transitive dependencies
    transitive_sources = [sources]
    transitive_assets = [assets]

    for dep in ctx.attr.deps:
        if FlutterLibraryInfo in dep:
            transitive_sources.append(dep[FlutterLibraryInfo].transitive_sources)
            transitive_assets.append(dep[FlutterLibraryInfo].transitive_assets)
        elif DartPackageInfo in dep:
            transitive_sources.append(dep[DartPackageInfo].transitive_srcs)
            transitive_assets.append(dep[DartPackageInfo].transitive_data)

    all_files = ctx.files.srcs + ctx.files.assets
    if ctx.file.pubspec:
        all_files = all_files + [ctx.file.pubspec]

    return [
        DefaultInfo(files = depset(all_files)),
        FlutterLibraryInfo(
            sources = sources,
            assets = assets,
            pubspec = ctx.file.pubspec,
            transitive_sources = depset(transitive = transitive_sources),
            transitive_assets = depset(transitive = transitive_assets),
        ),
        FlutterIdeInfo(
            source_roots = depset([ctx.label.package + "/lib"]),
            test_roots = depset([ctx.label.package + "/test"]),
            asset_roots = depset([ctx.label.package + "/assets"]),
            package_name = ctx.label.name,
            package_uri = "package:{}/".format(ctx.label.name),
            sdk_path = "",
            dart_sdk_path = "",
            analysis_options = None,
            pubspec = ctx.file.pubspec,
            dependencies = [],
            dev_dependencies = [],
        ),
    ]

_flutter_library = rule(
    implementation = _flutter_library_impl,
    doc = "A Flutter library with sources and assets.",
    attrs = {
        "srcs": attr.label_list(
            doc = "Dart source files.",
            allow_files = [".dart"],
        ),
        "assets": attr.label_list(
            doc = "Asset files (images, fonts, etc.).",
            allow_files = True,
        ),
        "pubspec": attr.label(
            doc = "pubspec.yaml file.",
            allow_single_file = [".yaml"],
        ),
        "deps": attr.label_list(
            doc = "Dependencies on other flutter_library targets.",
            providers = [[FlutterLibraryInfo], [DartPackageInfo]],
        ),
    },
    provides = [FlutterLibraryInfo],
)

def flutter_library(name, srcs = [], assets = [], deps = [], pubspec = None, visibility = None, **kwargs):
    """Create a Flutter library.

    Args:
        name: Target name.
        srcs: Dart source files.
        assets: Asset files (images, fonts, etc.).
        deps: Dependencies on other flutter_library targets.
        pubspec: pubspec.yaml file.
        visibility: Target visibility.
        **kwargs: Additional arguments.
    """
    _flutter_library(
        name = name,
        srcs = srcs,
        assets = assets,
        deps = deps,
        pubspec = pubspec,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_test
# =============================================================================

def _flutter_test_impl(ctx):
    """Implementation of flutter_test rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    main_path = ctx.file.main.path
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Compute test file relative path
    if pkg_dir and main_path.startswith(pkg_dir + "/"):
        test_file = main_path[len(pkg_dir) + 1:]
    else:
        test_file = main_path

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"

if not exist "%FLUTTER_BIN%" (
    echo ERROR: Flutter SDK not found at %FLUTTER_BIN%
    exit /b 1
)

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
set "TEMP_DIR=%TEMP%\\flutter_test_%RANDOM%"
mkdir "%TEMP_DIR%"

set "HOME=%TEMP_DIR%"
set "PUB_CACHE=%TEMP_DIR%\\.pub-cache"
mkdir "%PUB_CACHE%"

xcopy "%WORKSPACE_ROOT%" "%TEMP_DIR%" /E /I /Q >nul
cd /d "%TEMP_DIR%\\{pkg_dir}"

call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
"%FLUTTER_BIN%" test {main}
set "RESULT=%errorlevel%"

cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" 2>nul
exit /b %RESULT%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            main = to_windows_path(test_file),
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

FLUTTER_BIN="$RUNFILES/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    echo "ERROR: Flutter SDK not found at $FLUTTER_BIN" >&2
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

"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" test {main}
""".format(flutter_path = flutter_path, pkg_dir = pkg_dir, main = test_file)

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin, ctx.file.main] + ctx.files.srcs + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_test = rule(
    implementation = _flutter_test_impl,
    doc = "Flutter widget/unit test.",
    attrs = {
        "main": attr.label(allow_single_file = True, mandatory = True),
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
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
    test = True,
)

def flutter_test(name, main, srcs = [], deps = [], data = [], visibility = None, package_dir = None, shard_count = None, **kwargs):
    """Create a Flutter test target.

    Args:
        name: Target name.
        main: Main test file.
        srcs: Additional source files.
        deps: Dependencies.
        data: Runtime data files.
        visibility: Target visibility.
        package_dir: Package directory containing pubspec.yaml.
        shard_count: Number of test shards for parallel execution.
        **kwargs: Additional arguments.
    """
    _flutter_test(
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

# =============================================================================
# flutter_application
# =============================================================================

# Build commands for each platform
_BUILD_COMMANDS = {
    "android": "build apk",
    "android_aab": "build appbundle",
    "ios": "build ios --no-codesign",
    "web": "build web",
    "macos": "build macos",
    "linux": "build linux",
    "windows": "build windows",
}

# Output patterns for each platform
_OUTPUT_PATTERNS = {
    "android": "build/app/outputs/flutter-apk/app-release.apk",
    "android_aab": "build/app/outputs/bundle/release/app-release.aab",
    "ios": "build/ios/iphoneos/Runner.app",
    "web": "build/web",
    "macos": "build/macos/Build/Products/Release/*.app",
    "linux": "build/linux/x64/release/bundle",
    "windows": "build/windows/x64/runner/Release",
}

def _flutter_application_impl(ctx):
    """Implementation of flutter_application rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    target_platform = ctx.attr.target_platform
    build_mode = ctx.attr.build_mode
    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + "_build" + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    build_cmd = _BUILD_COMMANDS.get(target_platform, "build apk")
    output_pattern = _OUTPUT_PATTERNS.get(target_platform, "build/app/outputs/flutter-apk/app-release.apk")

    # Add build mode flag
    if build_mode == "debug":
        build_cmd = build_cmd + " --debug"
    elif build_mode == "profile":
        build_cmd = build_cmd + " --profile"
    else:
        build_cmd = build_cmd + " --release"

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"

if not exist "%FLUTTER_BIN%" (
    echo ERROR: Flutter SDK not found at %FLUTTER_BIN%
    exit /b 1
)

if defined BUILD_WORKSPACE_DIRECTORY (
    set "WORKSPACE_ROOT=%BUILD_WORKSPACE_DIRECTORY%"
) else (
    set "WORKSPACE_ROOT=%RUNFILES%\\_main"
)

cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

echo Building Flutter application for {target_platform}...
call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
call "%FLUTTER_BIN%" {build_cmd}

if %errorlevel% equ 0 (
    echo.
    echo Build successful!
    echo Output: {output_pattern}
)
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            target_platform = target_platform,
            build_cmd = build_cmd,
            output_pattern = to_windows_path(output_pattern),
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
    # Try system Flutter
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

echo "Building Flutter application for {target_platform}..."
"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" {build_cmd}

echo ""
echo "Build successful!"
echo "Output: {output_pattern}"
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            target_platform = target_platform,
            build_cmd = build_cmd,
            output_pattern = output_pattern,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_application = rule(
    implementation = _flutter_application_impl,
    doc = "Flutter application build.",
    attrs = {
        "deps": attr.label_list(
            doc = "flutter_library dependencies.",
            mandatory = True,
        ),
        "target_platform": attr.string(
            doc = "Target platform: android, android_aab, ios, web, macos, linux, windows.",
            default = "android",
            values = ["android", "android_aab", "ios", "web", "macos", "linux", "windows"],
        ),
        "build_mode": attr.string(
            doc = "Build mode: debug, profile, release.",
            default = "release",
            values = ["debug", "profile", "release"],
        ),
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

def flutter_application(
        name,
        deps,
        target_platform = "android",
        build_mode = "release",
        data = [],
        visibility = None,
        package_dir = None,
        **kwargs):
    """Create a Flutter application build target.

    Supports all Flutter target platforms:
    - android: Android APK
    - android_aab: Android App Bundle
    - ios: iOS IPA
    - web: Web application
    - macos: macOS application
    - linux: Linux application
    - windows: Windows application

    Args:
        name: Target name.
        deps: flutter_library dependencies.
        target_platform: Target platform.
        build_mode: Build mode (debug, profile, release).
        data: Runtime data files.
        visibility: Target visibility.
        package_dir: Package directory containing pubspec.yaml.
        **kwargs: Additional arguments.
    """
    _flutter_application(
        name = name,
        deps = deps,
        target_platform = target_platform,
        build_mode = build_mode,
        data = data,
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_binary (development mode)
# =============================================================================

def _flutter_binary_impl(ctx):
    """Implementation of flutter_binary rule (development mode)."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package
    device = ctx.attr.device

    device_arg = "-d {}".format(device) if device else ""

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"

if not exist "%FLUTTER_BIN%" (
    echo ERROR: Flutter SDK not found at %FLUTTER_BIN%
    exit /b 1
)

if defined BUILD_WORKSPACE_DIRECTORY (
    set "WORKSPACE_ROOT=%BUILD_WORKSPACE_DIRECTORY%"
) else (
    set "WORKSPACE_ROOT=%RUNFILES%\\_main"
)

cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
"%FLUTTER_BIN%" run {device_arg} %*
exit /b %errorlevel%
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            device_arg = device_arg,
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
"$FLUTTER_BIN" run {device_arg} "$@"
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            device_arg = device_arg,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.deps + ctx.files.data
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_binary = rule(
    implementation = _flutter_binary_impl,
    doc = "Flutter application runner (development mode).",
    attrs = {
        "deps": attr.label_list(doc = "flutter_library dependencies."),
        "device": attr.string(doc = "Target device (chrome, macos, linux, windows, etc.)."),
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

def flutter_binary(name, deps = [], device = None, data = [], visibility = None, package_dir = None, **kwargs):
    """Run a Flutter application in development mode.

    This runs `flutter run` for hot-reload development.

    Args:
        name: Target name.
        deps: flutter_library dependencies.
        device: Target device (chrome, macos, linux, windows, etc.).
        data: Runtime data files.
        visibility: Target visibility.
        package_dir: Package directory containing pubspec.yaml.
        **kwargs: Additional arguments.
    """
    _flutter_binary(
        name = name,
        deps = deps,
        device = device,
        data = data,
        package_dir = package_dir,
        visibility = visibility,
        **kwargs
    )
