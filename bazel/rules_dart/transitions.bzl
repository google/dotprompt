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

"""Platform transitions for cross-compilation in rules_dart.

This module provides transition rules for building Dart binaries for
different target platforms from the current execution platform.

## Platform Transitions Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Platform Transition Flow                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Host Platform (macOS arm64)                                                     │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────┐                                                                 │
│  │ Transition  │─── target_platform = linux-x64                                 │
│  └─────────────┘                                                                 │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                    Dart SDK (linux-x64)                                      │ │
│  │  • Uses linux-x64 dart executable                                           │ │
│  │  • Compiles to linux-x64 native binary                                      │ │
│  │  • Output runs on linux-x64 (not on host)                                   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Supported Target Platforms:                                                     │
│  • linux-x64, linux-arm64                                                       │
│  • macos-x64, macos-arm64                                                       │
│  • windows-x64                                                                   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```python
load("@rules_dart//:transitions.bzl", "dart_cross_binary")

# Build a linux binary from macOS
dart_cross_binary(
    name = "app_linux",
    target = ":app",
    target_platform = "linux-x64",
)

# Build for multiple platforms
[dart_cross_binary(
    name = "app_" + platform.replace("-", "_"),
    target = ":app",
    target_platform = platform,
) for platform in ["linux-x64", "linux-arm64", "macos-x64", "macos-arm64", "windows-x64"]]
```

Note: Cross-compilation requires the target platform's SDK to be available.
For Remote Build Execution (RBE), the remote workers must have the correct SDK.
"""

# =============================================================================
# Platform Constraint Mappings
# =============================================================================

# Map from platform string to constraint values
PLATFORM_CONSTRAINTS = {
    "linux-x64": {
        "os": "@platforms//os:linux",
        "cpu": "@platforms//cpu:x86_64",
    },
    "linux-arm64": {
        "os": "@platforms//os:linux",
        "cpu": "@platforms//cpu:aarch64",
    },
    "macos-x64": {
        "os": "@platforms//os:macos",
        "cpu": "@platforms//cpu:x86_64",
    },
    "macos-arm64": {
        "os": "@platforms//os:macos",
        "cpu": "@platforms//cpu:aarch64",
    },
    "windows-x64": {
        "os": "@platforms//os:windows",
        "cpu": "@platforms//cpu:x86_64",
    },
}

# =============================================================================
# Transition Implementation
# =============================================================================

def _dart_platform_transition_impl(_settings, attr):  # buildifier: disable=unused-variable
    """Implementation of the platform transition.

    Args:
        _settings: Current settings (unused, reserved for future use).
        attr: Rule attributes.

    Returns:
        Dict of new settings.
    """
    target_platform = attr.target_platform
    if target_platform not in PLATFORM_CONSTRAINTS:
        fail("Unknown target platform: {}. Valid platforms: {}".format(
            target_platform,
            ", ".join(PLATFORM_CONSTRAINTS.keys()),
        ))

    # Get constraints (used for validation, platform label used for transition)
    _constraints = PLATFORM_CONSTRAINTS[target_platform]  # buildifier: disable=unused-variable

    # Return updated platform settings
    return {
        "//command_line_option:platforms": [
            Label("@rules_dart//platforms:{}".format(target_platform.replace("-", "_"))),
        ],
    }

dart_platform_transition = transition(
    implementation = _dart_platform_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

# =============================================================================
# Cross-compilation Rule
# =============================================================================

def _dart_cross_binary_impl(ctx):
    """Implementation of dart_cross_binary rule."""

    # The actual binary is built by the transitioned target
    target = ctx.attr.target[0]

    # Get the default outputs from the transitioned target
    default_info = target[DefaultInfo]

    # Return the transitioned outputs
    return [
        DefaultInfo(
            files = default_info.files,
            runfiles = default_info.runfiles,
            executable = default_info.files_to_run.executable if default_info.files_to_run else None,
        ),
    ]

dart_cross_binary = rule(
    implementation = _dart_cross_binary_impl,
    doc = """Build a Dart binary for a different target platform.

    This rule applies a platform transition to build natives for a different
    OS/architecture than the current host.

    Example:
        ```python
        dart_native_binary(
            name = "app",
            main = "bin/main.dart",
        )

        dart_cross_binary(
            name = "app_linux_x64",
            target = ":app",
            target_platform = "linux-x64",
        )
        ```

    Note: The target platform SDK must be available. For local builds, this
    typically requires RBE or a Docker container with the target SDK.
    """,
    attrs = {
        "target": attr.label(
            doc = "The dart_native_binary target to cross-compile.",
            mandatory = True,
            cfg = dart_platform_transition,
        ),
        "target_platform": attr.string(
            doc = "Target platform (linux-x64, linux-arm64, macos-x64, macos-arm64, windows-x64).",
            mandatory = True,
            values = list(PLATFORM_CONSTRAINTS.keys()),
        ),
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
    },
)

# =============================================================================
# Platform Definitions
# =============================================================================

def _declare_dart_platforms():
    """Declare platform definitions for Dart cross-compilation.

    This is a private helper function. Call it in your BUILD file:

    ```python
    load("@rules_dart//:transitions.bzl", "declare_dart_platforms")

    declare_dart_platforms()
    ```
    """
    for platform_name, constraints in PLATFORM_CONSTRAINTS.items():
        native.platform(
            name = platform_name.replace("-", "_"),
            constraint_values = [
                constraints["os"],
                constraints["cpu"],
            ],
        )

def declare_dart_platforms(name = None):
    """Public wrapper for declaring platform definitions.

    Args:
        name: Unused, required by macro convention for tooling compatibility.
    """
    _unused = name  # buildifier: disable=unused-variable
    _declare_dart_platforms()

# =============================================================================
# Multi-platform Build
# =============================================================================

def dart_multi_platform_binary(
        name,
        target,
        platforms = ["linux-x64", "linux-arm64", "macos-x64", "macos-arm64", "windows-x64"],
        visibility = None):
    """Build a Dart binary for multiple platforms.

    Creates one target per platform with a predictable naming scheme.

    Args:
        name: Base name for targets.
        target: The dart_native_binary to build.
        platforms: List of target platforms.
        visibility: Target visibility.

    Example:
        ```python
        dart_native_binary(
            name = "app",
            main = "bin/main.dart",
        )

        dart_multi_platform_binary(
            name = "releases",
            target = ":app",
        )
        ```

        Creates: releases_linux_x64, releases_linux_arm64, etc.
    """
    for platform in platforms:
        dart_cross_binary(
            name = "{}_{}".format(name, platform.replace("-", "_")),
            target = target,
            target_platform = platform,
            visibility = visibility,
        )

    # Create a filegroup for all platforms
    native.filegroup(
        name = name,
        srcs = [":{}_{}".format(name, p.replace("-", "_")) for p in platforms],
        visibility = visibility,
    )
