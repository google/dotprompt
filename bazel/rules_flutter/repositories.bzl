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

"""Flutter SDK repository rules.

Provides hermetic Flutter SDK download for Bazel.

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Flutter SDK Repository                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  flutter.configure(version = "3.27.0", channel = "stable")                   │
│       │                                                                      │
│       ▼                                                                      │
│  Platform Detection                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Linux x64   → flutter_linux_3.27.0-stable.tar.xz                       ││
│  │ macOS x64   → flutter_macos_3.27.0-stable.zip                          ││
│  │ macOS arm64 → flutter_macos_arm64_3.27.0-stable.zip                    ││
│  │ Windows x64 → flutter_windows_3.27.0-stable.zip                        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│       │                                                                      │
│       ▼                                                                      │
│  @flutter_sdk//:flutter_bin                                                  │
│  @flutter_sdk//:dart_bin                                                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Usage in MODULE.bazel:
    flutter = use_extension("@rules_flutter//:extensions.bzl", "flutter")
    flutter.configure(version = "3.27.0", channel = "stable")
    use_repo(flutter, "flutter_sdk")
"""

# Flutter SDK download URLs
_FLUTTER_STORAGE_BASE = "https://storage.googleapis.com/flutter_infra_release/releases"

def _get_flutter_url(version, channel, os, arch):
    """Construct the Flutter SDK download URL.

    Args:
        version: Flutter version (e.g., "3.27.0")
        channel: Flutter channel (stable, beta, dev, master)
        os: Operating system (linux, macos, windows)
        arch: Architecture (x64, arm64)

    Returns:
        Download URL for the Flutter SDK archive.
    """
    if os == "linux":
        filename = "flutter_linux_{version}-{channel}.tar.xz".format(
            version = version,
            channel = channel,
        )
    elif os == "macos":
        if arch == "arm64":
            filename = "flutter_macos_arm64_{version}-{channel}.zip".format(
                version = version,
                channel = channel,
            )
        else:
            filename = "flutter_macos_{version}-{channel}.zip".format(
                version = version,
                channel = channel,
            )
    elif os == "windows":
        filename = "flutter_windows_{version}-{channel}.zip".format(
            version = version,
            channel = channel,
        )
    else:
        fail("Unsupported OS: {}".format(os))

    return "{base}/{channel}/{os}/{filename}".format(
        base = _FLUTTER_STORAGE_BASE,
        channel = channel,
        os = os,
        filename = filename,
    )

def _flutter_sdk_impl(repository_ctx):
    """Repository rule implementation for Flutter SDK."""
    version = repository_ctx.attr.version
    channel = repository_ctx.attr.channel
    sdk_home = repository_ctx.attr.sdk_home

    if not sdk_home:
        sdk_home = repository_ctx.os.environ.get("FLUTTER_HOME")

    if sdk_home:
        # Use local Flutter SDK
        repository_ctx.report_progress("Using local Flutter SDK at {}".format(sdk_home))
        sdk_path = repository_ctx.path(sdk_home)
        if not sdk_path.exists:
            fail("FLUTTER_HOME or sdk_home points to non-existent path: {}".format(sdk_home))

        # Symlink essential directories to match the flattened structure of downloaded SDK
        # We need 'bin' at the root for the aliases to work
        repository_ctx.symlink(sdk_path.get_child("bin"), "bin")

        # Symlink other common top-level directories/files if they exist
        for item in ["packages", "dev", "examples", "version", "LICENSE"]:
            if sdk_path.get_child(item).exists:
                repository_ctx.symlink(sdk_path.get_child(item), item)

        # For version, if we can read it, use it to update the BUILD file info
        if sdk_path.get_child("version").exists:
            version = repository_ctx.read(sdk_path.get_child("version")).strip()

        # Detect OS for local SDK to set aliases correctly
        os_name = repository_ctx.os.name.lower()
        if "win" in os_name:
            os = "windows"
        elif "mac" in os_name or "darwin" in os_name:
            os = "macos"
        elif "linux" in os_name:
            os = "linux"
        else:
            os = "unknown"  # Fallback

    else:
        # Detect platform
        os = repository_ctx.os.name
        if os.startswith("linux"):
            os_name = "linux"
        elif os.startswith("mac"):
            os_name = "macos"
        elif os.startswith("windows"):
            os_name = "windows"
        else:
            fail("Unsupported operating system: {}".format(os))

        # Detect architecture
        if os_name == "windows":
            arch_name = "x64"  # Windows only supports x64
        else:
            arch_result = repository_ctx.execute(["uname", "-m"])
            if arch_result.return_code == 0:
                arch = arch_result.stdout.strip()
                if arch in ["arm64", "aarch64"]:
                    arch_name = "arm64"
                else:
                    arch_name = "x64"
            else:
                arch_name = "x64"

        # Download Flutter SDK
        url = _get_flutter_url(version, channel, os_name, arch_name)

        repository_ctx.download_and_extract(
            url = url,
            stripPrefix = "flutter",
        )

    # Disable analytics if requested
    disable_analytics = repository_ctx.attr.disable_analytics
    if disable_analytics:
        # Create a script to disable analytics on first use
        # Flutter uses `flutter config --no-analytics` and `dart --disable-analytics`
        analytics_script = '''#!/bin/bash
# Disable Flutter and Dart analytics
"$1/bin/flutter" config --no-analytics 2>/dev/null || true
"$1/bin/dart" --disable-analytics 2>/dev/null || true
'''
        repository_ctx.file("disable_analytics.sh", analytics_script, executable = True)

        analytics_script_bat = '''@echo off
REM Disable Flutter and Dart analytics
"%~1\\bin\\flutter.bat" config --no-analytics 2>nul
"%~1\\bin\\dart.bat" --disable-analytics 2>nul
'''
        repository_ctx.file("disable_analytics.bat", analytics_script_bat, executable = True)

    # Generate BUILD.bazel
    build_content = '''# Generated by flutter_sdk repository rule
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

package(default_visibility = ["//visibility:public"])

exports_files(glob(["**"]))

# Flutter binary
alias(
    name = "flutter_bin",
    actual = select({
        "@platforms//os:windows": "bin/flutter.bat",
        "//conditions:default": "bin/flutter",
    }),
)

# Dart binary from Flutter SDK
alias(
    name = "dart_bin",
    actual = select({
        "@platforms//os:windows": "bin/dart.bat",
        "//conditions:default": "bin/dart",
    }),
)

# Full SDK
filegroup(
    name = "sdk",
    srcs = glob(["**"]),
)
'''

    repository_ctx.file("BUILD.bazel", build_content)

flutter_sdk = repository_rule(
    implementation = _flutter_sdk_impl,
    attrs = {
        "version": attr.string(
            default = "3.27.0",
            doc = "Flutter SDK version.",
        ),
        "channel": attr.string(
            default = "stable",
            doc = "Flutter channel (stable, beta, dev, master).",
            values = ["stable", "beta", "dev", "master"],
        ),
        "sdk_home": attr.string(
            doc = "Path to local Flutter SDK (overrides download).",
        ),
        "disable_analytics": attr.bool(
            default = True,
            doc = "Disable Flutter and Dart analytics for hermetic builds.",
        ),
    },
    environ = ["FLUTTER_HOME"],
    doc = "Downloads and configures the Flutter SDK.",
)
