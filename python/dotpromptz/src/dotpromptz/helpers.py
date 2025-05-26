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

"""

import json
from typing import Any

from handlebarrz import Handlebars, Helper, HelperFn


def json_helper(params: list[Any], helper: Helper) -> str:
    """Convert a value to a JSON string.

    Args:
        params: List of values to convert to JSON
        helper: Handlebars helper.

    Returns:
        JSON string representation of the value.
    """
    if not params or len(params) < 1:
        return ''

    obj = params[0]
    indent = helper.hash_value('indent') or 0
    try:
        if isinstance(indent, str):
            indent = int(indent)
    except (ValueError, TypeError):
        indent = 0

    try:
        if indent == 0:
            return json.dumps(obj, separators=(',', ':'))
        return json.dumps(obj, indent=indent)
    except (TypeError, ValueError):
        return '{}'


def role_helper(params: list[Any], helper: Helper) -> str:
    """Create a dotprompt role marker.

    Example:
        ```handlebars
        {{role "system"}}
        ```

    Args:
        params: List of values.
        helper: Handlebars helper.

    Returns:
        Role marker of the form `<<<dotprompt:role:...>>>`.
    """
    if not params or len(params) < 1:
        return ''

    role_name = str(params[0])
    return f'<<<dotprompt:role:{role_name}>>>'


def history_helper(params: list[Any], helper: Helper) -> str:
    """Create a dotprompt history marker.

    Example:
        ```handlebars
        {{history}}
        ```

    Args:
        params: List of values.
        helper: Handlebars helper.

    Returns:
        History marker of the form `<<<dotprompt:history>>>`.
    """
    return '<<<dotprompt:history>>>'


def section_helper(params: list[Any], helper: Helper) -> str:
    """Create a dotprompt section marker.

    Example:
        ```handlebars
        {{section "name"}}
        ```

    Args:
        params: List of values.
        helper: Handlebars helper.

    Returns:
        Section marker of the form `<<<dotprompt:section ...>>>`.
    """
    if not params or len(params) < 1:
        return ''

    section_name = str(params[0])
    return f'<<<dotprompt:section {section_name}>>>'


def media_helper(params: list[Any], helper: Helper) -> str:
    """Create a dotprompt media marker.

    Example:
        ```handlebars
        {{media url="https://example.com/image.png" contentType="image/png"}}
        ```

    Args:
        params: List of values.
        helper: Handlebars helper.

    Returns:
        Media marker of the form `<<<dotprompt:media:url ...>>>`).
    """
    url = helper.hash_value('url')
    if not url:
        return ''

    content_type = helper.hash_value('contentType')
    if content_type:
        return f'<<<dotprompt:media:url {url} {content_type}>>>'
    else:
        return f'<<<dotprompt:media:url {url}>>>'


def if_equals_helper(params: list[Any], helper: Helper) -> str:
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
        helper: Handlebars helper.

    Returns:
        Rendered content based on equality check.
    """
    if len(params) < 2:
        return ''

    a, b = params[0], params[1]
    return helper.fn() if a == b else helper.inverse()


def unless_equals_helper(params: list[Any], helper: Helper) -> str:
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
        helper: Handlebars helper.

    Returns:
        Rendered content based on inequality check.
    """
    if len(params) < 2:
        return ''

    a, b = params[0], params[1]
    return helper.fn() if a != b else helper.inverse()


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
