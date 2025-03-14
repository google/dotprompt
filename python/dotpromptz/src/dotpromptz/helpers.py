# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Handlebars helper functions for dotprompt."""

import json as json_module
from typing import Any, Callable

from pybars import Compiler  # type: ignore[import-untyped]

from dotpromptz.safe_string import SafeString


def json_helper(serializable: Any, options: dict[str, Any]) -> SafeString:
    """
    Serialize a value to JSON with optional indentation.

    Args:
        serializable (Any): The Python object to be serialized into JSON.
        options (dict[str, Any]): A dictionary of options, which can include an 'indent' key under 'hash'
                                  for specifying the level of indentation for the JSON output.

    Returns:
        SafeString: The JSON serialized string, marked safe for display usage.
    """
    indent = options.get('hash', {}).get('indent', 0)
    return SafeString(json_module.dumps(serializable, indent=indent))


def role_helper(role: str) -> SafeString:
    """
    Wrap a role string in a SafeString formatted for dotprompt.

    Args:
        role (str): The role string to be wrapped.

    Returns:
        SafeString: A formatted SafeString with the role embedded.
    """
    return SafeString(f'<<<dotprompt:role:{role}>>>')


def history_helper() -> SafeString:
    """
    Return a SafeString containing the dotprompt history placeholder.

    Args:
        None

    Returns:
        SafeString: A placeholder string for dotprompt history.
    """
    return SafeString('<<<dotprompt:history>>>')


def section_helper(name: str) -> SafeString:
    """
    Wrap a section name in a SafeString formatted for dotprompt.

    Args:
        name (str): The name of the section to be wrapped.

    Returns:
        SafeString: A formatted SafeString with the section name.
    """
    return SafeString(f'<<<dotprompt:section {name}>>>')


def media_helper(options: dict[str, Any]) -> SafeString:
    """
    Wrap a media URL and optional content type in a SafeString.

    Args:
        options (dict[str, Any]): A dictionary containing the 'hash' key. 'hash' should contain:
                                  - 'url' (str): The media URL.
                                  - 'contentType' (str, optional): The content type of the media. Defaults to an empty string.

    Returns:
        SafeString: A formatted SafeString for the media URL and content type.
    """
    url = options['hash']['url']
    content_type = options['hash'].get('contentType', '')
    return SafeString(f'<<<dotprompt:media:url {url} {content_type}>>>'.strip())


def if_equals(
    this: Any,
    options: dict[str, Callable[[Any], Any]],
    value: Any,
    test_value: Any,
) -> Any:
    """
    Conditional helper for equality check.

    Args:
        this (Any): The current scope or context.
        value (Any): The first argument to compare.
        test_value (Any): The second argument to compare.
        options (dict[str, Callable[[Any], Any]]): A dictionary containing Handlebars options:
            - 'fn': A function to call if arg1 equals arg2.
            - 'inverse': A function to call if arg1 does not equal arg2.

    Returns:
        Any: The result of calling 'fn' or 'inverse' based on equality check.
    """
    if value == test_value:
        return options['fn'](this)
    return options['inverse'](this)


def unless_equals(
    this: Any, arg1: Any, arg2: Any, options: dict[str, Callable[[Any], Any]]
) -> Any:
    """
    Conditional helper for inequality check.

    Args:
        this (Any): The current scope or context.
        arg1 (Any): The first argument to compare.
        arg2 (Any): The second argument to compare.
        options (dict[str, Callable[[Any], Any]]): A dictionary containing Handlebars options:
            - 'fn': A function to call if arg1 does not equal arg2.
            - 'inverse': A function to call if arg1 equals arg2.

    Returns:
        Any: The result of calling 'fn' or 'inverse' based on inequality check.
    """
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
compiler = Compiler()
compiler._helpers.update(helpers)
