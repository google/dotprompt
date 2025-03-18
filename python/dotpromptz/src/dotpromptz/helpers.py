# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Custom helpers for the Handlebars template engine."""

import json
from typing import Any, cast

from handlebarrz import Handlebars


# JSON helper
def json_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Convert a value to a JSON string.

    Args:
        params: List of values to convert to JSON
        hash: Hash arguments including formatting options
        ctx: Current context

    Returns:
        JSON string representation of the value
    """
    if not params or len(params) < 1:
        return ''

    obj = params[0]
    indent = hash.get('indent', 0)

    try:
        if isinstance(indent, str):
            indent = int(indent)
    except (ValueError, TypeError):
        indent = 0

    try:
        return json.dumps(obj, indent=indent)
    except (TypeError, ValueError):
        return '{}'


# Dotprompt helpers
def role_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Create a dotprompt role marker.

    Example:

        ```handlebars
        {{role "system"}}
        ```

    Args:
        params: List of values.
        hash: Hash arguments including formatting options.
        ctx: Current context

    Returns:
        Role marker.
    """
    if not params or len(params) < 1:
        return ''

    role_name = str(params[0])
    return f'<<<dotprompt:role:{role_name}>>>'


def history_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Create a dotprompt history marker.

    Example:

        ```handlebars
        {{history}}
        ```

    Args:
        params: List of values.
        hash: Hash arguments including formatting options
        ctx: Current context

    Returns:
        History marker.
    """
    return '<<<dotprompt:history>>>'


def section_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Create a dotprompt section marker.

    Example:

        ```handlebars
        {{section "name"}}
        ```

    Args:
        params: List of values.
        hash: Hash arguments including formatting options
        ctx: Current context

    Returns:
        Section marker.
    """
    if not params or len(params) < 1:
        return ''

    section_name = str(params[0])
    return f'<<<dotprompt:section {section_name}>>>'


def media_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Create a dotprompt media marker.

    Example:

        ```handlebars
        {{media url="https://example.com/image.png" contentType="image/png"}}
        ```

    Args:
        params: List of values.
        hash: Hash arguments including formatting options
        ctx: Current context

    Returns:
        Media marker.
    """
    url = hash.get('url', '')
    if not url:
        return ''

    content_type = hash.get('contentType', '')
    if content_type:
        return f'<<<dotprompt:media:url {url} {content_type}>>>'
    else:
        return f'<<<dotprompt:media:url {url}>>>'


def if_equals_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Render block content if the first two parameters are equal, otherwise render the `else` block.

    This helper checks if the first two parameters are equal. If they are,
    it renders the main block (`fn`). If they are not, it renders the `else`
    block (`inverse`), if provided.

    Args:
        params (list[Any]): A list containing at least two values to compare.
        hash (dict[str, Any]): Additional named arguments passed to the helper.
        ctx (dict[str, Any]): The Handlebars context containing:
            - 'fn': Callable that renders the main block content.
            - 'inverse': Callable that renders the else block content.

    Returns:
        str: Rendered main block content if values are equal; otherwise,
             rendered else block content if available. Returns an empty string
             if no content is rendered.
    """
    if len(params) < 2:
        return ''

    value1, value2 = params[0], params[1]

    if value1 == value2:
        if 'fn' in ctx and callable(ctx['fn']):
            return cast(str, ctx['fn']())
        return 'Equal'

    if 'inverse' in ctx and callable(ctx['inverse']):
        return cast(str, ctx['inverse']())

    return ''


def unless_equals_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Render block content if the first two parameters are not equal, otherwise render the `else` block.

    This helper checks if the first two parameters are not equal. If they are
    not equal, it renders the main block (`fn`). If they are equal, it renders
    the `else` block (`inverse`), if provided.

    Args:
        params (list[Any]): A list containing at least two values to compare.
        hash (dict[str, Any]): Additional named arguments passed to the helper.
        ctx (dict[str, Any]): The Handlebars context containing:
            - 'fn': Callable that renders the main block content.
            - 'inverse': Callable that renders the else block content.

    Returns:
        str: Rendered main block content if values are not equal; otherwise,
             rendered else block content if available. Returns an empty string
             if no content is rendered.
    """
    if len(params) < 2:
        return ''

    value1, value2 = params[0], params[1]

    if value1 != value2:
        if 'fn' in ctx and callable(ctx['fn']):
            return cast(str, ctx['fn']())
        return 'Not Equal'

    if 'inverse' in ctx and callable(ctx['inverse']):
        return cast(str, ctx['inverse']())

    return ''


def register_all_helpers(handlebars: Handlebars) -> None:
    """Register all custom helpers with the handlebars instance."""
    handlebars.register_helper('history', history_helper)
    handlebars.register_helper('json', json_helper)
    handlebars.register_helper('media', media_helper)
    handlebars.register_helper('role', role_helper)
    handlebars.register_helper('section', section_helper)
    handlebars.register_helper('ifEquals', if_equals_helper)
    handlebars.register_helper('unlessEquals', unless_equals_helper)
