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

"""Custom helpers for the Handlebars template engine.

## Key helpers:

| Helper         | Description                                         |
|----------------|-----------------------------------------------------|
| `history`      | Create a dotprompt history marker.                  |
| `ifEquals`     | Compare two values and return content if equal.     |
| `json`         | Convert a value to a JSON string.                   |
| `media`        | Create a dotprompt media marker.                    |
| `role`         | Create a dotprompt role marker.                     |
| `section`      | Create a dotprompt section marker.                  |
| `unlessEquals` | Compare two values and return content unless equal. |

## Convenience functions:

| Function               | Description                               |
|------------------------|-------------------------------------------|
| `register_all_helpers` | Registers all the helpers in this module. |

## Marker helpers

`role`, `history`, `section` and `media` emit nonce-carrying markers (see
`dotpromptz._markers`). They read the per-render nonce from the Handlebars data
frame, which `Dotprompt` populates for every render, and raise if it is
missing rather than emit a marker the parser would not honor.
"""

import json
from typing import Any

# Imported as a module (not `from ... import`) so the legacy star-import shim
# doesn't re-export marker internals; see compat_shims_test.py.
from dotpromptz import _markers
from dotpromptz_handlebars import Handlebars, HelperFn, HelperOptions, SafeString


def _marker_nonce(options: HelperOptions) -> str:
    """Read the per-render marker nonce from the Handlebars data frame.

    Data frames are inherited by blocks (`#each`, `#if`, ...) and partials, so
    this only fails if the helper runs outside `Dotprompt` rendering.

    Args:
        options: Handlebars helper options.

    Returns:
        The nonce for the current render.

    Raises:
        RuntimeError: If no nonce is present in the data frame.
    """
    nonce = options.data.get(_markers.MARKER_NONCE_DATA_KEY)
    if not isinstance(nonce, str):
        raise RuntimeError('dotprompt: marker helpers (role, history, section, media) must be rendered via Dotprompt')
    return nonce


def json_helper(params: list[Any], options: HelperOptions) -> str:
    """Convert a value to a JSON string.

    Args:
        params: List of values to convert to JSON
        options: Handlebars helper options.

    Returns:
        JSON string representation of the value.

    Raises:
        TypeError: If the value cannot be serialized to JSON.
        ValueError: If the value contains invalid data for JSON serialization.
    """
    if not params or len(params) < 1:
        return ''

    obj = params[0]
    indent = options.hash_value('indent') or 0
    try:
        if isinstance(indent, str):
            indent = int(indent)
    except (ValueError, TypeError):
        indent = 0

    # The JSON text is the value the caller asked to insert, quotes included.
    if indent == 0:
        return SafeString(json.dumps(obj, separators=(',', ':')))
    return SafeString(json.dumps(obj, indent=indent))


def role_helper(params: list[Any], options: HelperOptions) -> str:
    """Create a dotprompt role marker.

    Example:
        ```handlebars
        {{role "system"}}
        ```

    Args:
        params: List of values.
        options: Handlebars helper options.

    Returns:
        Role marker of the form `<<<dotprompt:{nonce}:role:...>>>`.

    Raises:
        RuntimeError: If rendered outside `Dotprompt` (no nonce).
    """
    if not params or len(params) < 1:
        return ''

    role_name = str(params[0])
    return SafeString(_markers.format_marker(_marker_nonce(options), f'role:{role_name}'))


def history_helper(params: list[Any], options: HelperOptions) -> str:
    """Create a dotprompt history marker.

    Example:
        ```handlebars
        {{history}}
        ```

    Args:
        params: List of values.
        options: Handlebars helper options.

    Returns:
        History marker of the form `<<<dotprompt:{nonce}:history>>>`.

    Raises:
        RuntimeError: If rendered outside `Dotprompt` (no nonce).
    """
    return SafeString(_markers.format_marker(_marker_nonce(options), 'history'))


def section_helper(params: list[Any], options: HelperOptions) -> str:
    """Create a dotprompt section marker.

    Example:
        ```handlebars
        {{section "name"}}
        ```

    Args:
        params: List of values.
        options: Handlebars helper options.

    Returns:
        Section marker of the form `<<<dotprompt:{nonce}:section ...>>>`.

    Raises:
        RuntimeError: If rendered outside `Dotprompt` (no nonce).
    """
    if not params or len(params) < 1:
        return ''

    section_name = str(params[0])
    return SafeString(_markers.format_marker(_marker_nonce(options), f'section {section_name}'))


def media_helper(params: list[Any], options: HelperOptions) -> str:
    """Create a dotprompt media marker.

    Example:
        ```handlebars
        {{media url="https://example.com/image.png" contentType="image/png"}}
        ```

    Args:
        params: List of values.
        options: Handlebars helper options.

    Returns:
        Media marker of the form `<<<dotprompt:{nonce}:media:url ...>>>`.

    Raises:
        RuntimeError: If rendered outside `Dotprompt` (no nonce).
    """
    url = options.hash_value('url')
    if not url:
        return ''

    content_type = options.hash_value('contentType')
    body = f'media:url {url} {content_type}' if content_type else f'media:url {url}'
    return SafeString(_markers.format_marker(_marker_nonce(options), body))


def if_equals_helper(params: list[Any], options: HelperOptions) -> str:
    """Compares two values and returns appropriate content.

    Example:
        ```handlebars
        {{#ifEquals arg1 arg2}}
            <p>arg1 is equal to arg2</p>
        {{else}}
            <p>arg1 is not equal to arg2</p>
        {{/ifEquals}}
        ```
    Args:
        params: List containing the two values to compare.
        options: Handlebars helper options.

    Returns:
        Rendered content based on equality check.
    """
    if len(params) < 2:
        return ''

    a, b = params[0], params[1]
    return options.fn() if a == b else options.inverse()


def unless_equals_helper(params: list[Any], options: HelperOptions) -> str:
    """Compares two values and returns appropriate content.

    Example:
        ```handlebars
        {{#unlessEquals arg1 arg2}}
            <p>arg1 is not equal to arg2</p>
        {{else}}
            <p>arg1 is equal to arg2</p>
        {{/unlessEquals}}
        ```
    Args:
        params: List containing the two values to compare.
        options: Handlebars helper options.

    Returns:
        Rendered content based on inequality check.
    """
    if len(params) < 2:
        return ''

    a, b = params[0], params[1]
    return options.fn() if a != b else options.inverse()


BUILTIN_HELPERS: dict[str, HelperFn] = {
    'history': history_helper,
    'ifEquals': if_equals_helper,
    'json': json_helper,
    'media': media_helper,
    'role': role_helper,
    'section': section_helper,
    'unlessEquals': unless_equals_helper,
}


def register_all_helpers(handlebars: Handlebars) -> None:
    """Register all builtin helpers with the handlebars instance.

    Args:
        handlebars: An instance of the Handlebars template engine.

    Returns:
        None.
    """
    for name, fn in BUILTIN_HELPERS.items():
        handlebars.register_helper(name, fn)
