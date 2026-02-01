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

"""Remote Build Execution (RBE) configuration for rules_dart.

This module provides configuration for running Dart builds on remote
execution services like Google Cloud Build or BuildBuddy.

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Remote Build Execution                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Local Machine                    Remote Executor                            │
│  ┌────────────────────────┐      ┌────────────────────────────────────────┐ │
│  │  bazel build //...     │      │  Container with:                       │ │
│  │  --config=remote       │ ──▶  │  - Dart SDK (downloaded hermetically)  │ │
│  │                        │      │  - No external dependencies            │ │
│  └────────────────────────┘      │  - All inputs from runfiles            │ │
│                                  └────────────────────────────────────────┘ │
│                                                                              │
│  Key Requirements for RBE Compatibility:                                     │
│  1. Hermetic SDK download (no system Dart)                                  │
│  2. All dependencies as explicit inputs                                     │
│  3. Pure Starlark actions (no shell dependencies)                           │
│  4. Consistent path handling (runfiles)                                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Usage:
    # In .bazelrc
    build:remote --remote_executor=grpcs://remote.buildbuddy.io
    build:remote --remote_cache=grpcs://remote.buildbuddy.io

    # Run with RBE
    bazel build --config=remote //...
"""

# RBE platform configuration
# These should match the execution platform's capabilities
RBE_CONTAINER_IMAGE = "gcr.io/cloud-marketplace/google/debian11@sha256:..."

def dart_rbe_platform(name, container_image = None, **kwargs):  # buildifier: disable=unused-variable
    """Define an RBE platform configuration for Dart builds.

    Args:
        name: Name of the platform target
        container_image: Docker image with RBE tools (Dart SDK is downloaded)
        **kwargs: Additional platform arguments

    Note:
        This is currently a placeholder. The implementation would create
        platform and toolchain_type mappings.
    """

    # Currently a placeholder - actual implementation would create
    # platform and toolchain_type mappings
    pass  # buildifier: disable=unused-variable

# RBE execution requirements for Dart actions
RBE_EXECUTION_REQUIREMENTS = {
    # Dart actions are network-safe (only pub.dev for deps)
    "no-sandbox": "1",
    # Request Linux x64 platform
    "OSFamily": "Linux",
    "Arch": "x86_64",
}

def get_rbe_execution_requirements(ctx):
    """Get RBE execution requirements for Dart actions.

    Args:
        ctx: Rule context

    Returns:
        Dict of execution requirements for RBE compatibility
    """
    requirements = dict(RBE_EXECUTION_REQUIREMENTS)

    # Add worker support if enabled
    if hasattr(ctx.attr, "_use_workers") and ctx.attr._use_workers:
        requirements["supports-workers"] = "1"
        requirements["requires-worker-protocol"] = "json"

    return requirements

# Recommended .bazelrc settings for RBE
RBE_BAZELRC_TEMPLATE = """
# Remote Build Execution configuration for rules_dart
# Add this to your .bazelrc

# Remote cache (read-only by default for safety)
build:remote-cache --remote_cache=grpcs://your-rbe-endpoint.com
build:remote-cache --remote_upload_local_results=false

# Full remote execution
build:remote --remote_executor=grpcs://your-rbe-endpoint.com
build:remote --remote_instance_name=default
build:remote --jobs=500

# Platform configuration
build:remote --host_platform=@rules_dart//platforms:rbe_linux_x64
build:remote --platforms=@rules_dart//platforms:rbe_linux_x64

# Dart-specific settings for RBE
build:remote --strategy=DartCompile=remote
build:remote --strategy=DartTest=remote

# Disable sandbox for better RBE performance
build:remote --spawn_strategy=remote

# Increase timeout for remote actions
build:remote --remote_timeout=3600

# Authentication (provider-specific)
# build:remote --google_default_credentials=true
# build:remote --remote_header=x-buildbuddy-api-key=YOUR_KEY
"""
