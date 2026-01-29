# Copyright 2025 Google LLC
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

r"""Utility functions for dotpromptz.

This module provides general-purpose utility functions used throughout the
dotpromptz package, including data transformation and security validation.

## Key Functions

| Function                | Description                                              |
|-------------------------|----------------------------------------------------------|
| `remove_undefined_fields` | Recursively remove None values from dicts/lists       |
| `unquote`               | Strip quote characters from string literals              |
| `validate_prompt_name`  | Security validation for prompt names (path traversal)    |

## Security: Path Traversal Prevention

The `validate_prompt_name` function implements multiple security layers to
prevent path traversal attacks (CWE-22). This is critical because prompt names
are often used to construct file paths when loading prompts from disk.

### Attack Vectors Blocked

```
Attack Vector              Example Input           Protection Layer
─────────────────────────────────────────────────────────────────────
Basic traversal            ../../../etc/passwd     Segment validation
URL-encoded traversal      %2e%2e/secret           URL decoding
Double-encoded             %252e%252e/secret       Iterative decoding
Unicode homograph          ․․/secret (U+2024)      Unicode normalization
Absolute Unix path         /etc/passwd             Prefix check
Absolute Windows path      C:\Windows\secret       Drive letter check
UNC network path           \\server\share          UNC prefix check
Null byte injection        foo\x00../bar           Null byte check
Current directory ref      ./config                ./ pattern check
```

### Validation Flow

```
Input: "foo/../bar"
        │
        ▼
┌───────────────────┐
│  URL decode (3x)  │  Catches %2e%2e and %252e%252e
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Unicode normalize │  NFC normalization for homographs
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Segment analysis  │  Check each path component for ".."
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│  Path type check  │  Block absolute/UNC/special paths
└─────────┬─────────┘
          │
          ▼
       Valid? ──No──▶ ValueError
          │
         Yes
          │
          ▼
       Continue
```

## Usage Example

```python
from dotpromptz.util import remove_undefined_fields, validate_prompt_name

# Clean up a metadata dict
metadata = {'name': 'test', 'version': None, 'config': {'key': None}}
clean = remove_undefined_fields(metadata)
# Result: {'name': 'test', 'config': {}}

# Validate a prompt name before loading
try:
    validate_prompt_name('prompts/greeting')  # OK
    validate_prompt_name('../secret')  # Raises ValueError
except ValueError as e:
    print(f'Invalid prompt name: {e}')
```
"""

import re
import unicodedata
from typing import Any
from urllib.parse import unquote as url_unquote

import structlog

logger = structlog.get_logger(__name__)


def remove_undefined_fields(obj: Any) -> Any:
    """Remove undefined fields (None values) from an object recursively.

    This function handles dictionaries, lists, and primitive types.  For
    dictionaries, it removes keys with None values and processes nested
    structures.  For lists, it removes None elements and processes nested
    structures.  For primitive types and None, it returns the value as is.

    Args:
        obj: The object to process.

    Returns:
        The object with undefined fields removed.
    """
    if obj is None or not isinstance(obj, dict | list):
        return obj

    # Lists.
    if isinstance(obj, list):
        return [remove_undefined_fields(item) for item in obj if item is not None]

    # Dicts.
    result = {}
    for key, value in obj.items():
        if value is not None:
            result[key] = remove_undefined_fields(value)
    return result


_QUOTE_PAIRS: set[tuple[str, str]] = {('"', '"'), ("'", "'")}


def unquote(value: str, pairs: set[tuple[str, str]] | None = None) -> str:
    """Remove quotes from a string literal representation.

    Args:
        value: The string to remove quotes from.
        pairs: Set of quote pairs to remove. When None, uses default pairs
            ("", "") and ("'", "'").

    Returns:
        The string with quotes removed.
    """
    if pairs is None:
        pairs = _QUOTE_PAIRS

    str_value = str(value)
    for start, end in pairs:
        if str_value.startswith(start) and str_value.endswith(end):
            return str_value[len(start) : -len(end)]

    return str_value


def validate_prompt_name(name: str) -> None:
    """Validate that a prompt name doesn't contain path traversal sequences.

    This function implements multiple layers of validation to prevent path
    traversal attacks (CWE-22):
    1. URL decoding - catches %2e%2e encoded dots
    2. Unicode normalization - catches homograph bypass attempts
    3. Segment-based validation - checks each path component for leading dots

    Args:
        name: The prompt name to validate

    Raises:
        ValueError: If name contains path traversal attempts
    """
    if not name:
        raise ValueError('Prompt name cannot be empty')

    # Check for whitespace-only names
    if not name.strip():
        raise ValueError(f"Invalid prompt name: '{name}'")

    # Check for null bytes
    if '\x00' in name:
        raise ValueError(f"Invalid prompt name: '{name}'")

    # Check for null byte escape sequence pattern (backslash followed by zero)
    # This catches suspicious escape sequences even if not actual null bytes
    if r'\0' in name:
        raise ValueError(f"Invalid prompt name: null byte escape sequence not allowed: '{name}'")

    # SECURITY FIX 1: Decode URL-encoded input BEFORE validation
    # This catches bypasses like %2e%2e which decodes to ..
    # SECURITY: Decode iteratively to catch double-encoding bypasses (%252e%252e)
    decoded = name
    for _ in range(3):  # Max 3 iterations to prevent DoS
        new_decoded = url_unquote(decoded)
        if new_decoded == decoded:
            break
        decoded = new_decoded
    # Check for remaining encoded characters (potential double-encoding bypass)
    if '%' in decoded:
        raise ValueError(f"Invalid prompt name: encoded characters not allowed: '{name}'")
    name = decoded

    # SECURITY FIX 2: Normalize Unicode BEFORE validation
    # This catches homograph attacks where visually similar characters
    # are used to bypass validation
    # Note: NFC doesn't convert all Unicode dots, so we check for suspicious patterns
    normalized = unicodedata.normalize('NFC', name)

    # Check for current directory reference patterns
    if './' in normalized or '.\\' in normalized:
        raise ValueError(f"Invalid path: current directory reference not allowed: '{name}'")

    # SECURITY FIX 3: Check for path traversal using segment-based validation
    # This catches:
    # - Segments that are only dots: "..", "...", "....", etc.
    # - Segments STARTING with "..": "..config", "..hidden" (leading parent reference)
    # - Segments ENDING with ".." when followed by non-alphanumeric: "safe..", "0.."
    # Allows: "a..b", "file..txt", "...test", "test..." (legitimate filename patterns)
    segments = normalized.replace('\\', '/').split('/')
    for seg in segments:
        # Check if segment is ONLY dots (2 or more)
        if len(seg) >= 2 and all(c == '.' for c in seg):
            raise ValueError(f"Path traversal not allowed: '{name}'")

        # Check if segment STARTS with ".." (potential bypass: "..config", "..hidden")
        # Allow segments starting with 3+ dots like "...test" which are legitimate filenames
        # Block only if it starts with exactly ".." (2 dots) not "...", "...." etc
        if len(seg) > 2 and seg[0] == '.' and seg[1] == '.' and seg[2] != '.':
            # Starts with exactly ".." followed by non-dot - check if valid pattern
            if not re.match(r'^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$', seg):
                raise ValueError(f"Path traversal not allowed: '{name}'")

        # Check if segment ENDS with ".." (potential bypass: "safe..", "0..", "test..")
        # But allow alphanumeric..alphanumeric patterns like "a..b" or "file..txt"
        # Also allow trailing three-or-more dots like "test..." (valid filename pattern)
        if seg.endswith('..') and len(seg) > 2:
            # Allow if: alphanumeric..alphanumeric (has chars after ..) OR ends with 3+ dots
            has_chars_after = bool(re.match(r'^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$', seg))
            has_trailing_triple = bool(re.match(r'.*\.\.\.+$', seg))
            if not has_chars_after and not has_trailing_triple:
                raise ValueError(f"Path traversal not allowed: '{name}'")

    # Check for absolute paths (Unix-style) - use normalized to catch URL-encoded
    if normalized.startswith('/'):
        raise ValueError(f"Invalid path: absolute paths not allowed: '{name}'")

    # Check for trailing slash (after normalization to catch both / and \)
    normalized_for_slash_check = normalized.replace('\\', '/')
    if normalized_for_slash_check.endswith('/'):
        raise ValueError(f"Invalid path: trailing slash not allowed: '{name}'")

    # Check for Windows absolute paths (e.g., C:/, C:\) - use normalized to catch URL-encoded
    # Only block when first char is a letter AND second is : (avoids false positive on 'a:b')
    if len(normalized) > 1 and normalized[1] == ':' and normalized[0].isalpha():
        raise ValueError(f"Invalid prompt name: '{name}'")

    # Check for UNC network paths (\\server\share) - use normalized to catch URL-encoded
    if normalized.startswith('\\\\'):
        raise ValueError(f"Invalid prompt name: '{name}'")
