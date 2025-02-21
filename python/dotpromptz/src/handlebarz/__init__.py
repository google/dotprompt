# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Handlebars template engine stub while we don't have a working implementation
of handlebars."""

from collections.abc import Callable
from typing import Any

# Defines a function that takes a string and returns a string.
RenderCallable = Callable[[str], str]

# Defines a helper function that takes a string and a render function and
# returns a string.
HelperCallable = Callable[[str, RenderCallable], str]


def render(
    template: str,
    data: dict[str, Any],
    partials: dict[str, str],
    helpers: dict[str, HelperCallable],
) -> str:
    """Render a template with the given data, partials, and helpers.

    Args:
        template: The template to render.
        data: The data to render the template with.
        partials: The partials to render the template with.
        helpers: The helpers to render the template with.

    Returns:
        The rendered template.
    """
    # TODO: Implement the rendering logic.
    return 'TODO'


__all__ = ['render', 'RenderCallable', 'HelperCallable']
