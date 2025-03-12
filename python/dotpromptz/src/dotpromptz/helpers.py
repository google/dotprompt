# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Handlebars helper functions for dotprompt."""

import json
from typing import Any

from dotpromptz.handlebarz import Handlebars, SafeString
from dotpromptz.handlebarz.typing import Context, HelperOptions
from dotpromptz.util import unquote


def register_helpers() -> None:
    """Register the helper functions with the Handlebars object."""
    Handlebars.register_helper('json', json_helper)
    Handlebars.register_helper('role', role_helper)
    Handlebars.register_helper('history', history_helper)
    Handlebars.register_helper('section', section_helper)
    Handlebars.register_helper('media', media_helper)
    Handlebars.register_helper('ifEquals', if_equals_helper)
    Handlebars.register_helper('unlessEquals', unless_equals_helper)


def json_helper(serializable: Any, options: HelperOptions[Any]) -> SafeString:
    """Serialize a value to JSON with optional indentation.

    Args:
        serializable: The value to serialize to JSON.
        options: Typed dictionary of options.

    Returns:
        JSON string representation of the value.
    """
    indent = options.get('hash', {}).get('indent', 0)
    return SafeString(json.dumps(serializable, indent=indent))


def role_helper(role: str) -> SafeString:
    """Generate a role marker.

    Args:
        role: The role name.

    Returns:
        Role marker string.
    """
    role = unquote(role)
    return SafeString(f'<<<dotprompt:role:{role}>>>')


def history_helper() -> SafeString:
    """Generate a history marker.

    Returns:
        History marker string.
    """
    return SafeString('<<<dotprompt:history>>>')


def section_helper(name: str) -> SafeString:
    """Generate a section marker.

    Args:
        name: The section name.

    Returns:
        Section marker string.
    """
    name = unquote(name)
    return SafeString(f'<<<dotprompt:section {name}>>>')


def media_helper(options: HelperOptions[Any] | None = None) -> SafeString:
    """Generate a media marker.

    Args:
        options: Dictionary of options.

    Returns:
        Media marker string.
    """
    if not isinstance(options, dict) or options is None:
        raise ValueError('missing hash options `url` and `contentType`?')

    obj = options.get('hash', {})
    url = obj.get('url', '')
    if not url:
        raise KeyError('missing url in hash options')

    content_type = obj.get('contentType', '')
    content_type_padded = f' {content_type}' if content_type else ''
    return SafeString(f'<<<dotprompt:media:url {url}{content_type_padded}>>>')


def if_equals_helper(
    context: Context, a: Any, b: Any, options: HelperOptions[Any]
) -> str:
    """Compare two values and render the block if they are equal.

    Args:
        context: The context of the template.
        a: The first value to compare.
        b: The second value to compare.
        options: Dictionary of options.

    Returns:
        Rendered content based on comparison.
    """
    return (
        options['fn'](context, None)
        if a == b
        else options['inverse'](context, None)
    )


def unless_equals_helper(
    context: Context, a: Any, b: Any, options: HelperOptions[Any]
) -> str:
    """Compare two values and render the block if they are not equal.

    Args:
        context: The context of the template.
        a: The first value to compare.
        b: The second value to compare.
        options: Dictionary of options.

    Returns:
        Rendered content based on comparison.
    """
    return (
        options['fn'](context, None)
        if a != b
        else options['inverse'](context, None)
    )
