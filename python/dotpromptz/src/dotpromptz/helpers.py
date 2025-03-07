# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Handlebars helper functions for dotprompt."""

import json
from collections.abc import Callable
from typing import Any, TypedDict

from handlebars import Handlebars

from dotpromptz.safe_string import SafeString
from dotpromptz.util import unquote

RenderCallable = Callable[[str], str]
RendererCallable = Callable[[dict[str, Any]], str]


def render(template: str, data: dict[str, Any]) -> str:
    """Render a template with the given data.

    Args:
        template: The template to render.
        data: The data to render the template with.

    Returns:
        The rendered template.
    """
    renderer: RendererCallable = Handlebars.compile(template)
    return renderer(data)


def register_helpers() -> None:
    """Register the helper functions with the Handlebars object."""
    Handlebars.registerHelper('json', json_helper)
    Handlebars.registerHelper('role', role_helper)
    Handlebars.registerHelper('history', history_helper)
    Handlebars.registerHelper('section', section_helper)
    Handlebars.registerHelper('media', media_helper)
    Handlebars.registerHelper('ifEquals', if_equals_helper)
    Handlebars.registerHelper('unlessEquals', unless_equals_helper)


class JSONHelperHash(TypedDict, total=False):
    """Helper options hash configuration."""

    indent: int | None


class JSONHelperOptions(TypedDict, total=False):
    """Options for the JSON helper."""

    hash: JSONHelperHash


def json_helper(serializable: Any, options: JSONHelperOptions) -> SafeString:
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


def media_helper(options: dict) -> SafeString:
    """Generate a media marker.'

    Args:
        context: The context of the media.
        options: Dictionary of options.

    Returns:
        Media marker string.
    """
    obj = options.get('hash', {})
    url = obj.get('url', '')
    content_type = obj.get('contentType', '')
    content_type_padded = f' {content_type}' if content_type else ''
    return SafeString(f'<<<dotprompt:media:url {url}{content_type_padded}>>>')


def if_equals_helper(this: Any, arg1: Any, arg2: Any, options: dict) -> str:
    """Compare two values and render the block if they are equal.

    Args:
        this: The context of the template.
        arg1: The first value to compare.
        arg2: The second value to compare.
        options: Dictionary of options.

    Returns:
        Rendered content based on comparison.
    """
    return options['fn'](this) if arg1 == arg2 else options['inverse'](this)


def unless_equals_helper(this: Any, arg1: Any, arg2: Any, options: dict) -> str:
    """Compare two values and render the block if they are not equal.

    Args:
        this: The context of the template.
        arg1: The first value to compare.
        arg2: The second value to compare.
        options: Dictionary of options.

    Returns:
        Rendered content based on comparison.
    """
    return options['fn'](this) if arg1 != arg2 else options['inverse'](this)
