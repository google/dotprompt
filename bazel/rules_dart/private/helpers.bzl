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

"""Common helper functions for rules_dart.

This module provides shared utilities used across all dart rules,
including path manipulation and platform detection helpers.

Architecture:
┌──────────────────────────────────────────────────────────────────────────┐
│                         Helper Functions                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  runfiles_path(file)                                                     │
│  ├── Handles external repo path resolution                              │
│  └── Strips leading "../" from short_path for Bzlmod compatibility      │
│                                                                          │
│  is_windows(ctx)                                                         │
│  └── Platform detection using constraint value                          │
│                                                                          │
│  relative_path(path, base)                                               │
│  └── Compute relative path from base directory                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
"""

def runfiles_path(file):
    """Get the runfiles-relative path for a file.

    For external repo files, short_path starts with '../<repo_name>/'.
    In runfiles, these are located at '<repo_name>/' (without the ..).

    This is critical for Bzlmod compatibility where external repos have
    names like 'rules_dart++dart+dart_sdk'.

    Args:
        file: A File object from ctx.executable or ctx.file

    Returns:
        String path suitable for use in runfiles directory

    Example:
        >>> # For external repo file:
        >>> file.short_path  # "../rules_dart++dart+dart_sdk/bin/dart"
        >>> runfiles_path(file)  # "rules_dart++dart+dart_sdk/bin/dart"
    """
    sp = file.short_path
    if sp.startswith("../"):
        return sp[3:]  # Strip leading "../"
    return sp

def is_windows(ctx):
    """Detect if the target platform is Windows.

    Uses Bazel's platform constraint mechanism for reliable detection.

    Args:
        ctx: Rule context

    Returns:
        True if targeting Windows, False otherwise
    """
    return ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

def relative_path(path, base):
    """Compute the relative path from a base directory.

    Used to convert full paths like 'dart/dotprompt/test/foo_test.dart'
    to relative paths like 'test/foo_test.dart' when running from
    within the package directory.

    Args:
        path: Full path to the file
        base: Base directory path

    Returns:
        Path relative to base, or original path if not a child of base

    Example:
        >>> relative_path("dart/dotprompt/test/foo.dart", "dart/dotprompt")
        "test/foo.dart"
    """
    if base and path.startswith(base + "/"):
        return path[len(base) + 1:]
    return path

def to_windows_path(path):
    """Convert a Unix-style path to Windows format.

    Args:
        path: Unix-style path with forward slashes

    Returns:
        Windows-style path with backslashes
    """
    return path.replace("/", "\\")
