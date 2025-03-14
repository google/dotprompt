# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0
import json

import pybars

# from dotpromptz.handlebarz import SafeString
import pytest
from pybars import Compiler  # type: ignore

from dotpromptz.helpers import (
    history_helper,
    if_equals,
    json_helper,
    media_helper,
    role_helper,
    section_helper,
    unless_equals,
)
from dotpromptz.safe_string import SafeString


def test_json_helper() -> None:
    """
    Test the `json_helper` function.

    Verifies that:
    - The serialized output is a SafeString.
    - The JSON serialization works correctly with and without indentation.
    """
    result = json_helper({'key': 'value'}, {'hash': {}})
    assert isinstance(result, SafeString)
    assert json.loads(str(result)) == {'key': 'value'}

    result = json_helper({'key': 'value'}, {'hash': {'indent': 2}})
    assert '\n  "key": "value"\n' in str(result)


def test_role_helper() -> None:
    """
    Test the `role_helper` function.

    Verifies that:
    - The output is a SafeString.
    - The formatted string includes the role correctly.
    """
    result = role_helper('admin')
    assert isinstance(result, SafeString)
    assert str(result) == '<<<dotprompt:role:admin>>>'


def test_history_helper() -> None:
    """
    Test the `history_helper` function.

    Verifies that:
    - The output is a SafeString.
    - The output matches the predefined dotprompt history placeholder format.
    """
    result = history_helper()
    assert isinstance(result, SafeString)
    assert str(result) == '<<<dotprompt:history>>>'


def test_section_helper() -> None:
    """
    Test the `section_helper` function.

    Verifies that:
    - The output is a SafeString.
    - The section name is correctly wrapped in the predefined format for dotprompt.
    """
    result = section_helper('introduction')
    assert isinstance(result, SafeString)
    assert str(result) == '<<<dotprompt:section introduction>>>'


def test_media_helper() -> None:
    """
    Test the `media_helper` function.

    Verifies that:
    - The helper correctly formats the media URL and optional content type.
    - Handles cases where the content type is not provided.
    """
    result = media_helper(
        {'hash': {'url': 'https://example.com', 'contentType': 'image/png'}}
    )
    assert (
        str(result) == '<<<dotprompt:media:url https://example.com image/png>>>'
    )

    result = media_helper({'hash': {'url': 'https://example.com'}})
    assert (
        str(result) == '<<<dotprompt:media:url https://example.com >>>'.strip()
    )


def test_if_equals_in_template() -> None:
    compiler = Compiler()
    template = compiler.compile(
        '{{#ifEquals value "test"}}MATCH{{else}}NO_MATCH{{/ifEquals}}'
    )

    def if_equals(this, options, arg1, arg2):
        if arg1 == arg2:
            return options['fn'](this)
        return options['inverse'](this)

    result = template({'value': 'test'}, helpers={'ifEquals': if_equals})
    assert result == 'MATCH'

    result = template({'value': 'different'}, helpers={'ifEquals': if_equals})
    assert result == 'NO_MATCH'


def test_unless_equals() -> None:
    """
    Test the `unless_equals` function.

    Verifies that:
    - The `fn` function is called if the arguments are not equal.
    - The `inverse` function is called if the arguments are equal.
    """
    mock_context = {'value': 'test'}
    result = unless_equals(
        mock_context,
        'test',
        'different',
        {'fn': lambda x: 'MATCH', 'inverse': lambda x: 'NO_MATCH'},
    )
    assert result == 'MATCH'

    result = unless_equals(
        mock_context,
        'test',
        'test',
        {'fn': lambda x: 'MATCH', 'inverse': lambda x: 'NO_MATCH'},
    )
    assert result == 'NO_MATCH'


def test_options_handling() -> None:
    """
    Test edge cases where media_helper handles missing options.

    Verifies that:
    - The function raises a KeyError when required options are absent.
    """
    with pytest.raises(KeyError):
        media_helper({'hash': {}})


def test_edge_cases() -> None:
    """
    Test the helpers with edge cases.
    """
    # Test helpers directly
    result = json_helper(None, {'hash': {}})
    assert str(result) == 'null'

    result = role_helper('')
    assert str(result) == '<<<dotprompt:role:>>>'

    result = section_helper('123')
    assert str(result) == '<<<dotprompt:section 123>>>'

    # Test helpers inside a compiled template
    compiler = pybars.Compiler()
    compiler._escape = lambda x: x  # Disable escaping globally

    source = 'JSON: {{json value}}\nRole: {{{role role_name}}}\nSection: {{{section section_name}}}'
    template = compiler.compile(source)

    helpers = {
        'json': lambda this, value, options=None: json_helper(
            value, options or {}
        ),
        'role': lambda this, role_name, options=None: role_helper(role_name),
        'section': lambda this, section_name, options=None: section_helper(
            section_name
        ),
    }

    data = {
        'value': None,
        'role_name': '',
        'section_name': '123',
    }

    output = template(data, helpers=helpers)

    assert 'JSON: null' in output
    assert 'Role: <<<dotprompt:role:>>>' in output
    assert 'Section: <<<dotprompt:section 123>>>' in output 
