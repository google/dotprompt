# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the parse.py module."""

import re

import pytest

from dotpromptz.parse import (
    MEDIA_AND_SECTION_MARKER_REGEX,
    ROLE_AND_HISTORY_MARKER_REGEX,
    convert_namespaced_entry_to_nested_object,
    extract_frontmatter_and_body,
    insert_history,
    parse_document,
    split_by_regex,
    split_by_role_and_history_markers,
    to_messages,
    to_parts,
    transform_messages_to_history,
)


class TestFrontMatterAndBodyRegex:
    """Tests for FRONTMATTER_AND_BODY_REGEX."""


class TestRoleAndHistoryMarkerRegex:
    """Tests for ROLE_AND_HISTORY_MARKER_REGEX."""

    @pytest.mark.parametrize(
        'pattern',
        [
            '<<<dotprompt:role:user>>>',
            '<<<dotprompt:role:assistant>>>',
            '<<<dotprompt:role:system>>>',
            '<<<dotprompt:history>>>',
            '<<<dotprompt:role:bot>>>',
            '<<<dotprompt:role:human>>>',
            '<<<dotprompt:role:customer>>>',
        ],
    )
    def test_valid_patterns(self, pattern):
        """Test that valid patterns match the regex."""
        assert ROLE_AND_HISTORY_MARKER_REGEX.search(pattern) is not None

    @pytest.mark.parametrize(
        'pattern',
        [
            '<<<dotprompt:role:USER>>>',  # uppercase not allowed
            '<<<dotprompt:role:assistant1>>>',  # numbers not allowed
            '<<<dotprompt:role:>>>',  # needs at least one letter
            '<<<dotprompt:role>>>',  # missing role value
            '<<<dotprompt:history123>>>',  # history should be exact
            '<<<dotprompt:HISTORY>>>',  # history must be lowercase
            'dotprompt:role:user',  # missing brackets
            '<<<dotprompt:role:user',  # incomplete closing
            'dotprompt:role:user>>>',  # incomplete opening
        ],
    )
    def test_invalid_patterns(self, pattern):
        """Test that invalid patterns do not match the regex."""
        assert ROLE_AND_HISTORY_MARKER_REGEX.search(pattern) is None

    def test_multiple_occurrences(self):
        """Test that multiple markers in a string are all matched."""
        text = """
            <<<dotprompt:role:user>>> Hello
            <<<dotprompt:role:assistant>>> Hi there
            <<<dotprompt:history>>>
            <<<dotprompt:role:user>>> How are you?
        """
        matches = ROLE_AND_HISTORY_MARKER_REGEX.findall(text)
        assert len(matches) == 4


class TestMediaAndSectionMarkerRegex:
    """Tests for MEDIA_AND_SECTION_MARKER_REGEX."""

    @pytest.mark.parametrize(
        'pattern',
        [
            '<<<dotprompt:media:url>>>',
            '<<<dotprompt:section>>>',
        ],
    )
    def test_valid_patterns(self, pattern):
        """Test that valid patterns match the regex."""
        assert MEDIA_AND_SECTION_MARKER_REGEX.search(pattern) is not None

    def test_media_and_section_markers(self):
        """Test that multiple markers in a string are all matched."""
        text = """
            <<<dotprompt:media:url>>> https://example.com/image.jpg
            <<<dotprompt:section>>> Section 1
            <<<dotprompt:media:url>>> https://example.com/video.mp4
            <<<dotprompt:section>>> Section 2
        """
        matches = MEDIA_AND_SECTION_MARKER_REGEX.findall(text)
        assert len(matches) == 4


class TestSplitByRoleAndHistoryMarkers:
    """Tests for split_by_role_and_history_markers function."""

    def test_no_markers(self):
        """Test splitting a string with no markers."""
        input_str = 'Hello World'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello World']

    def test_single_marker(self):
        """Test splitting a string with a single marker."""
        input_str = 'Hello <<<dotprompt:role:assistant>>> world'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello ', '<<<dotprompt:role:assistant', ' world']

    def test_empty_and_whitespace(self):
        """Test that empty and whitespace-only pieces are filtered out."""
        input_str = '  <<<dotprompt:role:system>>>   '
        output = split_by_role_and_history_markers(input_str)
        assert output == ['<<<dotprompt:role:system']

    def test_adjacent_markers(self):
        """Test splitting adjacent markers."""
        input_str = '<<<dotprompt:role:user>>><<<dotprompt:history>>>'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['<<<dotprompt:role:user', '<<<dotprompt:history']

    def test_invalid_uppercase_format(self):
        """Test that uppercase markers are not split."""
        input_str = '<<<dotprompt:ROLE:user>>>'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['<<<dotprompt:ROLE:user>>>']

    def test_multiple_markers_with_text(self):
        """Test splitting multiple markers with interleaved text."""
        input_str = (
            'Start <<<dotprompt:role:user>>> middle <<<dotprompt:history>>> end'
        )
        output = split_by_role_and_history_markers(input_str)
        assert output == [
            'Start ',
            '<<<dotprompt:role:user',
            ' middle ',
            '<<<dotprompt:history',
            ' end',
        ]


class TestConvertNamespacedEntryToNestedObject:
    """Tests for convert_namespaced_entry_to_nested_object function."""

    def test_create_nested_object(self):
        """Test creating a new nested object from a namespaced key."""
        result = convert_namespaced_entry_to_nested_object('foo.bar', 'hello')
        assert result == {
            'foo': {
                'bar': 'hello',
            },
        }

    def test_add_to_existing_namespace(self):
        """Test adding to an existing namespace."""
        existing = {
            'foo': {
                'bar': 'hello',
            },
        }
        result = convert_namespaced_entry_to_nested_object(
            'foo.baz', 'world', existing
        )
        assert result == {
            'foo': {
                'bar': 'hello',
                'baz': 'world',
            },
        }

    def test_multiple_namespaces(self):
        """Test handling multiple namespaces."""
        result = convert_namespaced_entry_to_nested_object('foo.bar', 'hello')
        final_result = convert_namespaced_entry_to_nested_object(
            'baz.qux', 'world', result
        )
        assert final_result == {
            'foo': {
                'bar': 'hello',
            },
            'baz': {
                'qux': 'world',
            },
        }


class TestFrontmatterAndBodyRegex:
    """Tests for frontmatter and body extraction."""

    def test_match_document(self):
        """Test extracting frontmatter and body from a valid document."""
        source = '---\nfoo: bar\n---\nThis is the body.'
        frontmatter, body = extract_frontmatter_and_body(source)
        assert frontmatter == 'foo: bar'
        assert body == 'This is the body.'

    def test_no_match(self):
        """Test handling a document with no frontmatter."""
        source = 'This is just a body'
        frontmatter, body = extract_frontmatter_and_body(source)
        assert frontmatter == ''
        assert body == ''

    def test_empty_frontmatter(self):
        """Test handling empty frontmatter."""
        source = '---\n\n---\nBody only'
        frontmatter, body = extract_frontmatter_and_body(source)
        assert frontmatter == ''
        assert body == 'Body only'

    def test_empty_body(self):
        """Test handling empty body."""
        source = '---\nfoo: bar\n---\n'
        frontmatter, body = extract_frontmatter_and_body(source)
        assert frontmatter == 'foo: bar'
        assert body == ''


class TestParseDocument:
    """Tests for parse_document function."""

    def test_with_frontmatter(self):
        """Test parsing a document with frontmatter."""
        source = """---
name: test
description: A test prompt
foo.bar: value
---
This is the template"""
        result = parse_document(source)
        assert result['name'] == 'test'
        assert result['description'] == 'A test prompt'
        assert result['ext']['foo']['bar'] == 'value'
        assert result['template'] == 'This is the template'

    def test_without_frontmatter(self):
        """Test parsing a document without frontmatter."""
        source = 'Just a template'
        result = parse_document(source)
        assert result['template'] == 'Just a template'
        assert result['ext'] == {}
        assert result['config'] == {}

    def test_with_invalid_yaml(self):
        """Test parsing a document with invalid YAML frontmatter."""
        source = """---
invalid: [yaml
---
Template"""
        result = parse_document(source)
        assert result['template'] == source.strip()
        assert result['ext'] == {}
        assert result['config'] == {}


class TestSplitByRegex:
    """Tests for split_by_regex function."""

    def test_split_and_filter(self):
        """Test splitting by regex and filtering empty pieces."""
        source = '  one  ,  ,  two  ,  three  '
        result = split_by_regex(source, re.compile(r','))
        assert result == ['  one  ', '  two  ', '  three  ']


class TestToMessages:
    """Tests for to_messages function."""

    def test_basic_message_conversion(self):
        """Test basic conversion of a string to messages."""
        rendered_string = 'Hello <<<dotprompt:role:assistant>>> Hi there'
        messages = to_messages(rendered_string)
        assert len(messages) == 2
        assert messages[0] == {'role': 'user', 'source': 'Hello '}
        assert messages[1] == {'role': 'assistant', 'source': ' Hi there'}

    def test_with_history(self):
        """Test message conversion with history."""
        rendered_string = """
            <<<dotprompt:role:user>>> Initial message
            <<<dotprompt:history>>>
            <<<dotprompt:role:user>>> Final message
        """
        history = [
            {'role': 'user', 'source': 'Past message', 'metadata': {}},
            {'role': 'assistant', 'source': 'Past response', 'metadata': {}},
        ]
        messages = to_messages(rendered_string, {'history': history})
        assert len(messages) == 4
        assert messages[0]['source'] == ' Initial message'
        assert messages[1]['source'] == 'Past message'
        assert messages[2]['source'] == 'Past response'
        assert messages[3]['source'] == ' Final message'

    def test_empty_string(self):
        """Test converting an empty string to messages."""
        messages = to_messages('')
        assert len(messages) == 1
        assert messages[0] == {'role': 'user', 'source': ''}


class TestTransformMessagesToHistory:
    """Tests for transform_messages_to_history function."""

    def test_add_metadata(self):
        """Test adding metadata to messages."""
        messages = [
            {'role': 'user', 'source': 'Hello'},
            {'role': 'assistant', 'source': 'Hi'},
            {
                'role': 'user',
                'source': 'How are you?',
                'metadata': {'existing': True},
            },
        ]
        result = transform_messages_to_history(messages)
        assert all('metadata' in msg for msg in result)
        assert result[2]['metadata']['existing'] is True


class TestInsertHistory:
    """Tests for insert_history function."""

    def test_insert_history(self):
        """Test inserting history into messages."""
        messages = [{'role': 'user', 'source': 'Current'}]
        history = [
            {'role': 'user', 'source': 'Past'},
            {'role': 'assistant', 'source': 'Response'},
        ]
        result = insert_history(messages, history)
        assert len(result) == 3
        assert result[0]['source'] == 'Past'
        assert result[1]['source'] == 'Response'
        assert result[2]['source'] == 'Current'

    def test_no_history(self):
        """Test inserting with no history."""
        messages = [{'role': 'user', 'source': 'Message'}]
        result = insert_history(messages)
        assert len(result) == 1
        assert result[0]['source'] == 'Message'


class TestToParts:
    """Tests for to_parts function."""

    def test_convert_to_parts(self):
        """Test converting a string with markers to parts."""
        source = """
            Some text
            <<<dotprompt:media:url>>> https://example.com/image.jpg
            More text
            <<<dotprompt:section>>> Section 1
            Final text
        """
        parts = to_parts(source)
        assert len(parts) == 4
        assert parts[0].type == 'text'
        assert parts[0].content.strip() == 'Some text'
        assert parts[1].type == 'media'
        assert parts[1].url == 'https://example.com/image.jpg'
        assert parts[2].type == 'text'
        assert 'More text' in parts[2].content
        assert parts[3].type == 'text'
        assert 'Final text' in parts[3].content

    def test_empty_source(self):
        """Test converting an empty string to parts."""
        parts = to_parts('')
        assert len(parts) == 0

    def test_only_text(self):
        """Test converting a string with no markers to parts."""
        source = 'Just some text without any markers'
        parts = to_parts(source)
        assert len(parts) == 1
        assert parts[0].type == 'text'
        assert parts[0].content == source
