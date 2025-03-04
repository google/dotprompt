# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Handlebars helper functions for dotprompt."""

import json
from collections.abc import Callable

from handlebars import Handlebars  # type: ignore

# TODO: All of these implementations are subject to change. I have included only
# a basic implementation for now since I couldn't get the handlebars library to
# work, I've used a stub in its place.

# TODO: Do we need a "SafeString" in Python to wrap the rendered output returned
# by these helpers?

RenderCallable = Callable[[str], str]
HelperCallable = Callable[[str, RenderCallable, int | None], str]

def register_helpers(env: Handlebars) -> None:
    """Register all dotprompt helpers with the Handlebars environment.

    Args:
        env: Handlebars engine instance.

    Returns:
        None
    """
    env.register_helper('json', json_helper)
    env.register_helper('role', role_helper)
    env.register_helper('history', history_helper)
    env.register_helper('section', section_helper)
    env.register_helper('media', media_helper)
    env.register_helper('ifEquals', if_equals_helper)
    env.register_helper('unlessEquals', unless_equals_helper)


def json_helper(
    text: str, render: RenderCallable, indent: int | None = None
) -> str:
    """Serialize a value to JSON with optional indentation.

    Args:
        text: The text to parse as JSON.
        render: Function to render the template.
        indent: Optional indentation level.

    Returns:
        JSON string representation of the value.
    """
    try:
        value = json.loads(render(text))
        if isinstance(indent, int):
            return json.dumps(value, indent=indent)
        return json.dumps(value)
    except Exception as e:
        return f'Error serializing JSON: {e}'


def role_helper(text: str, render: RenderCallable) -> str:
    """Generate a role marker.

    Args:
        text: The role name.
        render: Function to render the template.

    Returns:
        Role marker string.
    """
    role = render(text)
    return '<<>>'


def history_helper(text: str, render: RenderCallable) -> str:
    """Generate a history marker.

    Args:
        text: The text to render.
        render: Function to render the template.

    Returns:
        History marker string.
    """
    return '<<>>'


def section_helper(text: str, render: RenderCallable) -> str:
    """Generate a section marker.

    Args:
        text: The section name.
        render: Function to render the template.

    Returns:
        Section marker string.
    """
    name = render(text)
    return '<<>>'


def media_helper(text: str, render: RenderCallable) -> str:
    """Generate a media marker.

    Args:
        text: The media URL and optional content type.
        render: Function to render the template.

    Returns:
        Media marker string.
    """
    parts = render(text).split()
    url = parts[0]
    content_type = parts[1] if len(parts) > 1 else None
    if content_type is not None:
        return '<<>>'
    return '<<>>'


def if_equals_helper(text: str, render: RenderCallable) -> str:
    """Compare two values and render the block if they are equal.

    Args:
        text: The values to compare and template to render.
        render: Function to render the template.

    Returns:
        Rendered content based on comparison.
    """
    parts = text.split('|')
    if len(parts) != 3:
        return ''
    arg1 = render(parts[0].strip())
    arg2 = render(parts[1].strip())
    template = parts[2].strip()
    if arg1 == arg2:
        return render(template)
    return ''


def unless_equals_helper(text: str, render: RenderCallable) -> str:
    """Compare two values and render the block if they are not equal.

    Args:
        text: The values to compare and template to render.

    Returns:
        Rendered content based on comparison.
    """
    parts = text.split('|')
    if len(parts) != 3:
        return ''
    arg1 = render(parts[0].strip())
    arg2 = render(parts[1].strip())
    template = parts[2].strip()
    if arg1 != arg2:
        return render(template)
    return ''
