# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Handlebars helper functions for dotprompt."""

import json as json_module
from collections.abc import Callable
from typing import Any

from django.utils.safestring import SafeString
from pybars import Compiler  # type: ignore[import-not-found]


def json_helper(serializable: Any, options: dict[str, Any]) -> SafeString:
    """Serialize a value to JSON with optional indentation."""
    indent = options.get('hash', {}).get('indent', 0)
    return SafeString(json_module.dumps(serializable, indent=indent))


def role_helper(role: str) -> SafeString:
    """Wrap a role string in a SafeString formatted for dotprompt."""
    return SafeString(f'<<<dotprompt:role:{role}>>>')


def history_helper() -> SafeString:
    """Return a SafeString containing the dotprompt history placeholder."""
    return SafeString('<<<dotprompt:history>>>')


def section_helper(name: str) -> SafeString:
    """Wrap a section name in a SafeString formatted for dotprompt."""
    return SafeString(f'<<<dotprompt:section {name}>>>')


def media_helper(options: dict[str, Any]) -> SafeString:
    """Wrap a media URL and optional content type in a SafeString."""
    url = options['hash']['url']
    content_type = options['hash'].get('contentType', '')
    return SafeString(f'<<<dotprompt:media:url {url} {content_type}>>>'.strip())


def if_equals(
    this: Any, arg1: Any, arg2: Any, options: dict[str, Callable[[Any], Any]]
) -> Any:
    """Conditional helper for equality check."""
    if arg1 == arg2:
        return options['fn'](this)
    return options['inverse'](this)


def unless_equals(
    this: Any, arg1: Any, arg2: Any, options: dict[str, Callable[[Any], Any]]
) -> Any:
    """Conditional helper for inequality check."""
    if arg1 != arg2:
        return options['fn'](this)
    return options['inverse'](this)


# Register helpers with pybars3
helpers = {
    'json': json_helper,
    'role': role_helper,
    'history': history_helper,
    'section': section_helper,
    'media': media_helper,
    'ifEquals': if_equals,
    'unlessEquals': unless_equals,
}

# Example template usage remains unchanged
compiler = Compiler(helpers=helpers)
