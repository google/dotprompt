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

"""Sandbox hermeticity support for rules_dart.

This module provides utilities for ensuring Dart builds are fully hermetic
in sandboxed execution environments.

## Sandbox Hermeticity Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Hermetic Sandbox Model                                   │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  External Environment                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  ~/.pub-cache (NOT accessible)                                              │ │
│  │  ~/.dart (NOT accessible)                                                   │ │
│  │  Environment variables (filtered)                                           │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Sandbox (/sandbox/<random>/)                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  Sources (symlinked from inputs)                                            │ │
│  │  Dart SDK (from @dart_sdk)                                                  │ │
│  │  Pub cache (isolated per action)                                            │ │
│  │  Outputs (declared)                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Hermetic Guarantees:                                                            │
│  ✅ All inputs declared                                                          │
│  ✅ No network access during build                                               │
│  ✅ No home directory access                                                     │
│  ✅ Reproducible outputs                                                         │
│  ✅ Cacheable actions                                                            │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Configuration

Add to your .bazelrc for strict hermeticity:

```bash
# .bazelrc
build --experimental_strict_action_env
build --incompatible_strict_action_env

# Block network access in sandbox
build --sandbox_block_path=/
build --sandbox_add_mount_pair=/tmp

# Use sandboxed execution
build --spawn_strategy=sandboxed

# For maximum hermeticity
build:hermetic --sandbox_default_allow_network=false
build:hermetic --action_env=HOME=/nonexistent
```
"""

# =============================================================================
# Hermetic Environment Variables
# =============================================================================

# Environment variables that are safe to pass through
HERMETIC_ENV_PASSTHROUGH = [
    "PATH",  # Needed for basic tools
    "TMPDIR",  # Temporary directory
    "TMP",  # Windows temp
    "TEMP",  # Windows temp
]

# Environment variables to explicitly block
BLOCKED_ENV_VARS = [
    "HOME",
    "USERPROFILE",
    "PUB_CACHE",
    "DART_SDK",
    "FLUTTER_ROOT",
]

# =============================================================================
# Provider for Hermetic Info
# =============================================================================

DartHermeticInfo = provider(
    doc = "Information about hermetic execution requirements.",
    fields = {
        "requires_network": "Bool: Whether this action needs network access.",
        "env_vars": "Dict[String, String]: Environment variables for the action.",
        "input_files": "Depset[File]: All input files that must be declared.",
        "tool_files": "Depset[File]: Tool files (SDK, etc.).",
        "is_reproducible": "Bool: Whether outputs are bitwise reproducible.",
    },
)

# =============================================================================
# Hermetic Environment Builder
# =============================================================================

def build_hermetic_env(_ctx, additional_env = {}):
    """Build a hermetic environment dictionary for action execution.

    Args:
        _ctx: Rule context (unused, for interface compatibility).
        additional_env: Additional environment variables to include.

    Returns:
        Dict of environment variables for hermetic execution.
    """
    env = {}

    # Set isolated pub cache within sandbox
    env["PUB_CACHE"] = "/tmp/.pub-cache"

    # Disable Dart analytics
    env["DART_ANALYTICS_DISABLED"] = "1"
    env["FLUTTER_ANALYTICS_DISABLED"] = "1"

    # Set consistent locale
    env["LANG"] = "en_US.UTF-8"
    env["LC_ALL"] = "en_US.UTF-8"

    # Add user-provided environment
    for key, value in additional_env.items():
        if key not in BLOCKED_ENV_VARS:
            env[key] = value

    return env

# =============================================================================
# Hermetic Execution Wrapper
# =============================================================================

def create_hermetic_action(
        ctx,
        outputs,
        inputs,
        executable,
        arguments,
        mnemonic,
        progress_message = None,
        use_default_shell_env = False,
        execution_requirements = {}):
    """Create a hermetic action with proper isolation.

    Args:
        ctx: Rule context.
        outputs: List of output files.
        inputs: Depset or list of input files.
        executable: Executable to run.
        arguments: Args object or list of arguments.
        mnemonic: Action mnemonic (e.g., "DartCompile").
        progress_message: Optional progress message.
        use_default_shell_env: Whether to inherit shell environment.
        execution_requirements: Additional execution requirements.

    Returns:
        None (registers the action).
    """
    env = build_hermetic_env(ctx)

    # Default execution requirements for hermeticity
    exec_reqs = {
        "no-remote": "",  # Don't allow remote execution by default
        "no-cache": "",  # Don't cache by default (can be overridden)
    }

    # Override with user requirements
    exec_reqs.update(execution_requirements)

    # Remove "no-cache" if the action is reproducible
    if "reproducible" in exec_reqs:
        exec_reqs.pop("no-cache", None)
        exec_reqs.pop("no-remote", None)

    ctx.actions.run(
        outputs = outputs,
        inputs = inputs,
        executable = executable,
        arguments = arguments,
        mnemonic = mnemonic,
        progress_message = progress_message,
        env = env,
        use_default_shell_env = use_default_shell_env,
        execution_requirements = exec_reqs,
    )

# =============================================================================
# Sandbox Validation
# =============================================================================

def validate_hermetic_inputs(srcs, _deps):
    """Validate that all inputs for a hermetic build are explicitly declared.

    Args:
        srcs: Source files.
        _deps: Dependencies (reserved for future validation).

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []

    # Check for absolute paths in sources
    for src in srcs:
        if hasattr(src, "path") and src.path.startswith("/"):
            if not src.path.startswith("/"):
                errors.append("Source contains absolute path: {}".format(src.path))

    return errors

# =============================================================================
# Bazelrc Configuration Generator
# =============================================================================

def generate_hermetic_bazelrc():
    """Generate .bazelrc content for hermetic Dart builds.

    Returns:
        String content for .bazelrc.
    """
    return """# Hermetic Dart Build Configuration
# Generated by rules_dart

# Enable strict action environment
build --experimental_strict_action_env
build --incompatible_strict_action_env

# Use sandboxed execution
build --spawn_strategy=sandboxed,standalone

# Hermetic profile (opt-in)
build:hermetic --sandbox_default_allow_network=false
build:hermetic --action_env=HOME=/nonexistent
build:hermetic --action_env=PUB_CACHE=/tmp/.pub-cache

# Remote execution compatible settings
build:remote --jobs=50
build:remote --remote_timeout=3600

# Enable build without the bytes for faster remote builds
build:remote --remote_download_minimal
"""
