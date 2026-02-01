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

"""Dart toolchain definition and provider.

This module defines the Dart toolchain abstraction, allowing:
- Multiple SDK versions in the same workspace
- Cross-compilation targets
- Proper platform-based toolchain resolution

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Dart Toolchain Resolution                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MODULE.bazel                                                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  dart = use_extension("@rules_dart//:extensions.bzl", "dart")          │ │
│  │  dart.toolchain(version = "3.7.0")                                     │ │
│  │  dart.toolchain(version = "3.6.0")  # Multiple versions supported      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                  │
│                           ▼                                                  │
│  Toolchain Resolution (based on --platforms)                                │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  exec_compatible_with: linux, x86_64                                   │ │
│  │  target_compatible_with: linux                                         │ │
│  │  → Selects: @dart_sdk_3_7_0_linux_x64//:toolchain                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                  │
│                           ▼                                                  │
│  DartToolchainInfo Provider                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  dart_bin:  File (path to dart executable)                            │ │
│  │  dart_sdk:  Depset (SDK files)                                        │ │
│  │  version:   String ("3.7.0")                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Usage:
    # In MODULE.bazel
    dart = use_extension("@rules_dart//:extensions.bzl", "dart")
    dart.toolchain(version = "3.7.0")
    use_repo(dart, "dart_toolchains")

    # In BUILD (usually auto-generated)
    load("@rules_dart//:toolchain.bzl", "dart_toolchain")

    dart_toolchain(
        name = "dart_3.7.0",
        dart_bin = "@dart_sdk//:dart_bin",
        dart_sdk = "@dart_sdk//:sdk",
        version = "3.7.0",
    )

    toolchain(
        name = "dart_linux_x64",
        exec_compatible_with = ["@platforms//os:linux", "@platforms//cpu:x86_64"],
        toolchain = ":dart_3.7.0",
        toolchain_type = "@rules_dart//:toolchain_type",
    )
"""

# Toolchain type for Dart
DART_TOOLCHAIN_TYPE = Label("//:toolchain_type")

# Provider for Dart toolchain information
DartToolchainInfo = provider(
    doc = "Information about a Dart toolchain.",
    fields = {
        "dart_bin": "File: The dart executable.",
        "dart_sdk": "Depset: All SDK files.",
        "version": "String: The SDK version (e.g., '3.7.0').",
        "dartaotruntime": "File: The dartaotruntime executable for AOT snapshots.",
        "dart2js": "File: The dart2js compiler (optional, may be None).",
    },
)

def _dart_toolchain_impl(ctx):
    """Implementation of dart_toolchain rule."""
    dart_bin = ctx.executable.dart_bin
    dartaotruntime = ctx.executable.dartaotruntime if ctx.attr.dartaotruntime else None

    toolchain_info = DartToolchainInfo(
        dart_bin = dart_bin,
        dart_sdk = depset(ctx.files.dart_sdk),
        version = ctx.attr.version,
        dartaotruntime = dartaotruntime,
        dart2js = None,  # TODO(#issue): Add dart2js path
    )

    return [
        platform_common.ToolchainInfo(dart = toolchain_info),
        toolchain_info,
    ]

dart_toolchain = rule(
    implementation = _dart_toolchain_impl,
    doc = "Defines a Dart toolchain.",
    attrs = {
        "dart_bin": attr.label(
            doc = "The dart executable.",
            executable = True,
            cfg = "exec",
            mandatory = True,
            allow_single_file = True,
        ),
        "dart_sdk": attr.label(
            doc = "The full Dart SDK filegroup.",
            mandatory = True,
        ),
        "version": attr.string(
            doc = "The Dart SDK version string (e.g., '3.7.0').",
            mandatory = True,
        ),
        "dartaotruntime": attr.label(
            doc = "The dartaotruntime executable for running AOT snapshots.",
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
    },
    provides = [platform_common.ToolchainInfo, DartToolchainInfo],
)

def _current_dart_toolchain_impl(ctx):
    """Returns the currently resolved Dart toolchain."""
    toolchain = ctx.toolchains[DART_TOOLCHAIN_TYPE]
    if not toolchain:
        fail("No Dart toolchain registered. Did you forget to register @rules_dart//:all_toolchains?")

    dart_info = toolchain.dart
    return [
        DefaultInfo(files = dart_info.dart_sdk),
        dart_info,
    ]

current_dart_toolchain = rule(
    implementation = _current_dart_toolchain_impl,
    doc = "Returns the currently resolved Dart toolchain for the target platform.",
    toolchains = [DART_TOOLCHAIN_TYPE],
)

def dart_register_toolchains(version = None, name = "dart_default"):
    """Registers Dart toolchains for the given version.

    This macro should be called from WORKSPACE or MODULE.bazel to register
    the Dart toolchain for all supported platforms.

    Args:
        version: The Dart SDK version. If None, uses the default.
        name: Base name for the toolchain repos.
    """

    # Platform configurations
    platforms = [
        ("linux", "x86_64"),
        ("linux", "aarch64"),
        ("macos", "x86_64"),
        ("macos", "aarch64"),
        ("windows", "x86_64"),
    ]

    toolchain_names = []
    for os, cpu in platforms:
        toolchain_name = "{name}_{os}_{cpu}".format(name = name, os = os, cpu = cpu)
        toolchain_names.append(toolchain_name)

        native.register_toolchains("@{name}//:{toolchain_name}".format(
            name = name,
            toolchain_name = toolchain_name,
        ))

    return toolchain_names
