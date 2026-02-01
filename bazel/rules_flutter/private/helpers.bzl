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

"""Private helper functions for rules_flutter.

This module contains common utilities used across Flutter rules.
These are internal implementation details and should not be used directly.
"""

def runfiles_path(file):
    """Get runfiles-relative path for a file.

    External repository files have short_path starting with "../repo_name/..."
    but in runfiles they appear as "repo_name/...".

    Args:
        file: A File object.

    Returns:
        String path relative to runfiles root.
    """
    short_path = file.short_path
    if short_path.startswith("../"):
        return short_path[3:]
    return short_path

def relative_path(path, base):
    """Compute relative path from base to path.

    Args:
        path: Target path.
        base: Base path.

    Returns:
        Relative path from base to path.
    """
    if path.startswith(base + "/"):
        return path[len(base) + 1:]
    return path

def to_windows_path(path):
    """Convert Unix path to Windows path.

    Args:
        path: Unix-style path with forward slashes.

    Returns:
        Windows-style path with backslashes.
    """
    return path.replace("/", "\\")
