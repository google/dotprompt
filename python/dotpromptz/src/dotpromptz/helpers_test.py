# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

#from dotpromptz.handlebarz import SafeString
from django.utils.safestring import SafeString

from dotpromptz.helpers import (
    history_helper,
    if_equals,
    json_helper,
    media_helper,
    role_helper,
    section_helper,
    unless_equals,
)


def test_json_helper() -> None:
    result = json_helper({'key': 'value'}, {'hash': {}})
    assert isinstance(result, SafeString)
    assert str(result) == '{"key": "value"}'

    result = json_helper({'key': 'value'}, {'hash': {'indent': 2}})
    assert '\n  "key": "value"\n' in str(result)

def test_role_helper() -> None:
    result = role_helper('admin')
    assert isinstance(result, SafeString)
    assert str(result) == '<<<dotprompt:role:admin>>>'

def test_history_helper() -> None:
    result = history_helper()
    assert isinstance(result, SafeString)
    assert str(result) == '<<<dotprompt:history>>>'

def test_section_helper() -> None:
    result = section_helper('introduction')
    assert isinstance(result, SafeString)
    assert str(result) == '<<<dotprompt:section introduction>>>'

def test_media_helper() -> None:
    result = media_helper({'hash': {'url': 'https://example.com', 'contentType': 'image/png'}})
    assert str(result) == '<<<dotprompt:media:url https://example.com image/png>>>'

    result = media_helper({'hash': {'url': 'https://example.com'}})
    assert str(result) == '<<<dotprompt:media:url https://example.com >>>'.strip()

def test_if_equals() -> None:
    mock_context = {'value': 'test'}
    result = if_equals(
        mock_context,
        'test',
        'test',
        {'fn': lambda x: 'MATCH', 'inverse': lambda x: 'NO_MATCH'}
    )
    assert result == 'MATCH'

    result = if_equals(
        mock_context,
        'test',
        'different',
        {'fn': lambda x: 'MATCH', 'inverse': lambda x: 'NO_MATCH'}
    )
    assert result == 'NO_MATCH'

def test_unless_equals() -> None:
    mock_context = {'value': 'test'}
    result = unless_equals(
        mock_context,
        'test',
        'different',
        {'fn': lambda x: 'MATCH', 'inverse': lambda x: 'NO_MATCH'}
    )
    assert result == 'MATCH'

    result = unless_equals(
        mock_context,
        'test',
        'test',
        {'fn': lambda x: 'MATCH', 'inverse': lambda x: 'NO_MATCH'}
    )
    assert result == 'NO_MATCH'

def test_options_handling() -> None:
    with pytest.raises(KeyError):
        media_helper({'hash': {}})

def test_edge_cases() -> None:
    result = json_helper(None, {'hash': {}})
    assert str(result) == 'null'

    result = role_helper('')
    assert str(result) == '<<<dotprompt:role:>>>'

    result = section_helper('123')
    assert str(result) == '<<<dotprompt:section 123>>>'
