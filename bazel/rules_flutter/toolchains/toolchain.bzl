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

"""Flutter toolchain definitions.

This module provides a formal toolchain model for Flutter, following Bazel
best practices from mature rulesets like rules_go and rules_rust.

## Toolchain Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Flutter Toolchain Model                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Toolchain Type: @rules_flutter//:toolchain_type                           │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ flutter_linux   │  │ flutter_macos   │  │ flutter_windows │             │
│  │ _x64_toolchain  │  │ _arm64_toolchain│  │ _x64_toolchain  │             │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤             │
│  │ exec: linux     │  │ exec: macos     │  │ exec: windows   │             │
│  │ target: any     │  │ target: any     │  │ target: any     │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│           │                   │                   │                        │
│           └───────────────────┼───────────────────┘                        │
│                               ▼                                            │
│                    FlutterToolchainInfo                                    │
│                    ├── flutter_bin                                         │
│                    ├── dart_bin                                            │
│                    ├── sdk_root                                            │
│                    ├── version                                             │
│                    └── channel                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```python
# MODULE.bazel
bazel_dep(name = "rules_flutter", version = "0.2.0")

flutter = use_extension("@rules_flutter//:extensions.bzl", "flutter")
flutter.sdk(version = "3.22.0", channel = "stable")
use_repo(flutter, "flutter_sdk")

register_toolchains("@rules_flutter//toolchains:all")
```

In BUILD files, rules automatically resolve the toolchain:

```python
flutter_library(
    name = "my_lib",
    srcs = glob(["lib/**/*.dart"]),
)
# Automatically uses the resolved flutter toolchain
```
"""

# =============================================================================
# Provider
# =============================================================================

FlutterToolchainInfo = provider(
    doc = "Information about a Flutter toolchain.",
    fields = {
        "flutter_bin": "File: The flutter executable.",
        "dart_bin": "File: The dart executable.",
        "sdk_root": "File: Root directory of the Flutter SDK.",
        "version": "String: Flutter version (e.g., '3.22.0').",
        "channel": "String: Flutter channel (stable, beta, dev, master).",
        "dart_version": "String: Dart SDK version.",
        "target_platforms": "List[String]: Supported target platforms.",
    },
)

# =============================================================================
# Toolchain Rule
# =============================================================================

def _flutter_toolchain_impl(ctx):
    """Implementation of flutter_toolchain rule."""
    toolchain_info = FlutterToolchainInfo(
        flutter_bin = ctx.executable.flutter_bin,
        dart_bin = ctx.executable.dart_bin,
        sdk_root = ctx.file.sdk_root,
        version = ctx.attr.version,
        channel = ctx.attr.channel,
        dart_version = ctx.attr.dart_version,
        target_platforms = ctx.attr.target_platforms,
    )

    # Check if we are building for a supported platform
    # This is a basic implementation of platform transitions support
    # in the future we can use actual transitions

    return [
        platform_common.ToolchainInfo(
            flutter_toolchain = toolchain_info,
        ),
        toolchain_info,
    ]

flutter_toolchain = rule(
    implementation = _flutter_toolchain_impl,
    doc = "Defines a Flutter toolchain.",
    attrs = {
        "flutter_bin": attr.label(
            doc = "The flutter executable.",
            executable = True,
            cfg = "exec",
            mandatory = True,
            allow_single_file = True,
        ),
        "dart_bin": attr.label(
            doc = "The dart executable.",
            executable = True,
            cfg = "exec",
            mandatory = True,
            allow_single_file = True,
        ),
        "sdk_root": attr.label(
            doc = "Root directory of the Flutter SDK.",
            mandatory = True,
            allow_single_file = True,
        ),
        "version": attr.string(
            doc = "Flutter version.",
            default = "",
        ),
        "channel": attr.string(
            doc = "Flutter channel.",
            default = "stable",
            values = ["stable", "beta", "dev", "master"],
        ),
        "dart_version": attr.string(
            doc = "Dart SDK version.",
            default = "",
        ),
        "target_platforms": attr.string_list(
            doc = "Supported target platforms.",
            default = ["android", "ios", "web", "macos", "linux", "windows"],
        ),
    },
    provides = [platform_common.ToolchainInfo, FlutterToolchainInfo],
)

# =============================================================================
# Toolchain Access
# =============================================================================

def _get_flutter_toolchain(ctx):
    """Get the Flutter toolchain from context.

    Args:
        ctx: Rule context with toolchain configured.

    Returns:
        FlutterToolchainInfo provider.
    """
    return ctx.toolchains["@rules_flutter//:toolchain_type"].flutter_toolchain

# =============================================================================
# Declare Toolchain
# =============================================================================

def _declare_flutter_toolchains():
    """Internal macro to declare all Flutter toolchains.

    This is a private helper macro called from toolchains/BUILD.bazel.
    """

    # Linux x64
    flutter_toolchain(
        name = "flutter_linux_x64",
        flutter_bin = "@flutter_sdk//:flutter_bin",
        dart_bin = "@flutter_sdk//:dart_bin",
        sdk_root = "@flutter_sdk//:version",
        target_platforms = ["android", "web", "linux"],
    )

    native.toolchain(
        name = "flutter_linux_x64_toolchain",
        exec_compatible_with = [
            "@platforms//os:linux",
            "@platforms//cpu:x86_64",
        ],
        toolchain = ":flutter_linux_x64",
        toolchain_type = "@rules_flutter//:toolchain_type",
    )

    # Linux arm64
    flutter_toolchain(
        name = "flutter_linux_arm64",
        flutter_bin = "@flutter_sdk//:flutter_bin",
        dart_bin = "@flutter_sdk//:dart_bin",
        sdk_root = "@flutter_sdk//:version",
        target_platforms = ["android", "web", "linux"],
    )

    native.toolchain(
        name = "flutter_linux_arm64_toolchain",
        exec_compatible_with = [
            "@platforms//os:linux",
            "@platforms//cpu:arm64",
        ],
        toolchain = ":flutter_linux_arm64",
        toolchain_type = "@rules_flutter//:toolchain_type",
    )

    # macOS x64
    flutter_toolchain(
        name = "flutter_macos_x64",
        flutter_bin = "@flutter_sdk//:flutter_bin",
        dart_bin = "@flutter_sdk//:dart_bin",
        sdk_root = "@flutter_sdk//:version",
        target_platforms = ["android", "ios", "web", "macos"],
    )

    native.toolchain(
        name = "flutter_macos_x64_toolchain",
        exec_compatible_with = [
            "@platforms//os:macos",
            "@platforms//cpu:x86_64",
        ],
        toolchain = ":flutter_macos_x64",
        toolchain_type = "@rules_flutter//:toolchain_type",
    )

    # macOS arm64 (Apple Silicon)
    flutter_toolchain(
        name = "flutter_macos_arm64",
        flutter_bin = "@flutter_sdk//:flutter_bin",
        dart_bin = "@flutter_sdk//:dart_bin",
        sdk_root = "@flutter_sdk//:version",
        target_platforms = ["android", "ios", "web", "macos"],
    )

    native.toolchain(
        name = "flutter_macos_arm64_toolchain",
        exec_compatible_with = [
            "@platforms//os:macos",
            "@platforms//cpu:arm64",
        ],
        toolchain = ":flutter_macos_arm64",
        toolchain_type = "@rules_flutter//:toolchain_type",
    )

    # Windows x64
    flutter_toolchain(
        name = "flutter_windows_x64",
        flutter_bin = "@flutter_sdk//:flutter_bin",
        dart_bin = "@flutter_sdk//:dart_bin",
        sdk_root = "@flutter_sdk//:version",
        target_platforms = ["android", "web", "windows"],
    )

    native.toolchain(
        name = "flutter_windows_x64_toolchain",
        exec_compatible_with = [
            "@platforms//os:windows",
            "@platforms//cpu:x86_64",
        ],
        toolchain = ":flutter_windows_x64",
        toolchain_type = "@rules_flutter//:toolchain_type",
    )

    # Windows arm64
    flutter_toolchain(
        name = "flutter_windows_arm64",
        flutter_bin = "@flutter_sdk//:flutter_bin",
        dart_bin = "@flutter_sdk//:dart_bin",
        sdk_root = "@flutter_sdk//:version",
        target_platforms = ["android", "web", "windows"],
    )

    native.toolchain(
        name = "flutter_windows_arm64_toolchain",
        exec_compatible_with = [
            "@platforms//os:windows",
            "@platforms//cpu:arm64",
        ],
        toolchain = ":flutter_windows_arm64",
        toolchain_type = "@rules_flutter//:toolchain_type",
    )

# Export for use in rules
get_flutter_toolchain = _get_flutter_toolchain

# Export for use in BUILD.bazel (public alias for private macro)
declare_flutter_toolchains = _declare_flutter_toolchains
