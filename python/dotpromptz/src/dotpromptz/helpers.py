# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Custom helpers for the Handlebars template engine."""

import json
from typing import Any

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

    Usage in template:
    {{role "system"}}
    """
    if not params or len(params) < 1:
        return ''

    role_name = str(params[0])
    return f'<<<dotprompt:role:{role_name}>>>'


def history_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Create a dotprompt history marker.

    Usage in template:
    {{history}}
    """
    return '<<<dotprompt:history>>>'


def section_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Create a dotprompt section marker.

    Usage in template:
    {{section "name"}}
    """
    if not params or len(params) < 1:
        return ''

    section_name = str(params[0])
    return f'<<<dotprompt:section {section_name}>>>'


def media_helper(
    params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Create a dotprompt media marker.

    Usage in template:
    {{media url="https://example.com/image.png" contentType="image/png"}}
    """
    url = hash.get('url', '')
    if not url:
        return ''

    content_type = hash.get('contentType', '')
    if content_type:
        return f'<<<dotprompt:media:url {url} {content_type}>>>'
    else:
        return f'<<<dotprompt:media:url {url}>>>'


def if_equals_helper(params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Render content if the first two parameters are equal."""
    if len(params) < 2:
        return ""

    value1, value2 = params[0], params[1]

    if value1 == value2:
        return str(ctx.get("fn", lambda: "")())  # Ensure return type is str

    return ""



def unless_equals_helper(params: list[Any], hash: dict[str, Any], ctx: dict[str, Any]
) -> str:
    """Check if two values are not equal and render content if true."""
    if len(params) < 2:
        return ""

    value1, value2 = params[0], params[1]

    if value1 != value2:
        return ctx["fn"]() if "fn" in ctx and callable(ctx["fn"]) else ""  # Render block content

    return ""


def register_all_helpers(handlebars: Handlebars) -> None:
    """Register all custom helpers with the handlebars instance."""
    handlebars.register_helper('history', history_helper)
    handlebars.register_helper('json', json_helper)
    handlebars.register_helper('media', media_helper)
    handlebars.register_helper('role', role_helper)
    handlebars.register_helper('section', section_helper)
