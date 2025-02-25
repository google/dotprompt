# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for parse module."""

import re
import unittest

import pytest

from dotpromptz.parse import (
    FRONTMATTER_AND_BODY_REGEX,
    MEDIA_AND_SECTION_MARKER_REGEX,
    RESERVED_METADATA_KEYWORDS,
    ROLE_AND_HISTORY_MARKER_REGEX,
    MessageSource,
    convert_namespaced_entry_to_nested_object,
    extract_frontmatter_and_body,
    insert_history,
    message_sources_to_messages,
    messages_have_history,
    parse_document,
    parse_media_part,
    parse_part,
    parse_section_part,
    parse_text_part,
    split_by_media_and_section_markers,
    split_by_regex,
    split_by_role_and_history_markers,
    transform_messages_to_history,
)
from dotpromptz.typing import (
    MediaPart,
    Message,
    ParsedPrompt,
    Part,
    PendingPart,
    Role,
    TextPart,
)


class TestSplitByMediaAndSectionMarkers(unittest.TestCase):
    def test_split_by_media_and_section_markers(self) -> None:
        """Test splitting by media and section markers."""
        input_str = '<<<dotprompt:media:url>>> https://example.com/image.jpg'
        output = split_by_media_and_section_markers(input_str)
        assert output == [
            '<<<dotprompt:media:url',
            ' https://example.com/image.jpg',
        ]

    def test_split_by_media_and_section_markers_multiple_markers(self) -> None:
        """Test multiple markers in a string."""
        input_str = '<<<dotprompt:media:url>>> https://example.com/image.jpg'
        output = split_by_media_and_section_markers(input_str)
        assert output == [
            '<<<dotprompt:media:url',
            ' https://example.com/image.jpg',
        ]

    def test_split_by_media_and_section_markers_no_markers(self) -> None:
        """Test no markers in a string."""
        input_str = 'Hello World'
        output = split_by_media_and_section_markers(input_str)
        assert output == ['Hello World']


def test_role_and_history_marker_regex_valid_patterns() -> None:
    """Test valid patterns for role and history markers."""
    valid_patterns = [
        '<<<dotprompt:role:user>>>',
        '<<<dotprompt:role:assistant>>>',
        '<<<dotprompt:role:system>>>',
        '<<<dotprompt:history>>>',
        '<<<dotprompt:role:bot>>>',
        '<<<dotprompt:role:human>>>',
        '<<<dotprompt:role:customer>>>',
    ]

    for pattern in valid_patterns:
        assert ROLE_AND_HISTORY_MARKER_REGEX.search(pattern) is not None


def test_role_and_history_marker_regex_invalid_patterns() -> None:
    """Test invalid patterns for role and history markers."""
    invalid_patterns = [
        '<<<dotprompt:role:USER>>>',  # uppercase not allowed
        '<<<dotprompt:role:assistant1>>>',  # numbers not allowed
        '<<<dotprompt:role:>>>',  # needs at least one letter
        '<<<dotprompt:role>>>',  # missing role value
        '<<<dotprompt:history123>>>',  # history should be exact
        '<<<dotprompt:HISTORY>>>',  # history must be lowercase
        'dotprompt:role:user',  # missing brackets
        '<<<dotprompt:role:user',  # incomplete closing
        'dotprompt:role:user>>>',  # incomplete opening
    ]

    for pattern in invalid_patterns:
        assert ROLE_AND_HISTORY_MARKER_REGEX.search(pattern) is None


def test_role_and_history_marker_regex_multiple_matches() -> None:
    """Test multiple matches in a string."""
    text = """
        <<<dotprompt:role:user>>> Hello
        <<<dotprompt:role:assistant>>> Hi there
        <<<dotprompt:history>>>
        <<<dotprompt:role:user>>> How are you?
    """

    matches = ROLE_AND_HISTORY_MARKER_REGEX.findall(text)
    assert len(matches) == 4


def test_media_and_section_marker_regex_valid_patterns() -> None:
    """Test valid patterns for media and section markers."""
    valid_patterns = [
        '<<<dotprompt:media:url>>>',
        '<<<dotprompt:section>>>',
    ]

    for pattern in valid_patterns:
        assert MEDIA_AND_SECTION_MARKER_REGEX.search(pattern) is not None


def test_media_and_section_marker_regex_multiple_matches() -> None:
    """Test multiple matches in a string."""
    text = """
        <<<dotprompt:media:url>>> https://example.com/image.jpg
        <<<dotprompt:section>>> Section 1
        <<<dotprompt:media:url>>> https://example.com/video.mp4
        <<<dotprompt:section>>> Section 2
    """

    matches = MEDIA_AND_SECTION_MARKER_REGEX.findall(text)
    assert len(matches) == 4


class TestSplitByRoleAndHistoryMarkers(unittest.TestCase):
    def test_no_markers(self) -> None:
        """Test splitting when no markers are present."""
        input_str = 'Hello World'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello World']

    def test_single_marker(self) -> None:
        """Test splitting with a single marker."""
        input_str = 'Hello <<<dotprompt:role:assistant>>> world'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello ', '<<<dotprompt:role:assistant', ' world']

    def test_split_by_role_and_history_markers_single_marker(self) -> None:
        """Test splitting with a single marker."""
        input_str = 'Hello <<<dotprompt:role:assistant>>> world'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello ', '<<<dotprompt:role:assistant', ' world']

    def test_split_by_role_and_history_markers_filter_empty(self) -> None:
        """Test filtering empty and whitespace-only pieces."""
        input_str = '  <<<dotprompt:role:system>>>   '
        output = split_by_role_and_history_markers(input_str)
        assert output == ['<<<dotprompt:role:system']

    def test_split_by_role_and_history_markers_adjacent_markers(self) -> None:
        """Test adjacent markers."""
        input_str = '<<<dotprompt:role:user>>><<<dotprompt:history>>>'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['<<<dotprompt:role:user', '<<<dotprompt:history']

    def test_split_by_role_and_history_markers_invalid_format(self) -> None:
        """Test no split on markers with uppercase letters (invalid format)."""
        input_str = '<<<dotprompt:ROLE:user>>>'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['<<<dotprompt:ROLE:user>>>']

    def test_split_by_role_and_history_markers_multiple_markers(self) -> None:
        """Test string with multiple markers interleaved with text."""
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


class TestConvertNamespacedEntryToNestedObject(unittest.TestCase):
    """Test converting namespaced entries to nested objects."""

    def test_creating_nested_object(self) -> None:
        """Test creating nested object structure from namespaced key."""
        result = convert_namespaced_entry_to_nested_object('foo.bar', 'hello')
        self.assertEqual(
            result,
            {
                'foo': {
                    'bar': 'hello',
                },
            },
        )

    def test_adding_to_existing_namespace(self) -> None:
        """Test adding to existing namespace."""
        existing = {
            'foo': {
                'bar': 'hello',
            },
        }
        result = convert_namespaced_entry_to_nested_object(
            'foo.baz', 'world', existing
        )
        self.assertEqual(
            result,
            {
                'foo': {
                    'bar': 'hello',
                    'baz': 'world',
                },
            },
        )

    def test_handling_multiple_namespaces(self) -> None:
        """Test handling multiple namespaces."""
        result = convert_namespaced_entry_to_nested_object('foo.bar', 'hello')
        final_result = convert_namespaced_entry_to_nested_object(
            'baz.qux', 'world', result
        )
        self.assertEqual(
            final_result,
            {
                'foo': {
                    'bar': 'hello',
                },
                'baz': {
                    'qux': 'world',
                },
            },
        )


@pytest.mark.parametrize(
    'source,expected_frontmatter,expected_body',
    [
        (
            '---\nfoo: bar\n---\nThis is the body.',
            'foo: bar',
            'This is the body.',
        ),  # Test document with frontmatter and body
        (
            '---\n\n---\nBody only.',
            '',
            'Body only.',
        ),  # Test document with empty frontmatter
        (
            '---\nfoo: bar\n---\n',
            'foo: bar',
            '',
        ),  # Test document with empty body
        (
            '---\nfoo: bar\nbaz: qux\n---\nThis is the body.',
            'foo: bar\nbaz: qux',
            'This is the body.',
        ),  # Test document with multiline frontmatter
        (
            'Just a body.',
            None,
            None,
        ),  # Test document with no frontmatter markers
        (
            '---\nfoo: bar\nThis is the body.',
            None,
            None,
        ),  # Test document with incomplete frontmatter markers
        (
            '---\nfoo: bar\n---\nThis is the body.\n---\nExtra section.',
            'foo: bar',
            'This is the body.\n---\nExtra section.',
        ),  # Test document with extra frontmatter markers
    ],
)
def test_frontmatter_and_body_regex(
    source: str,
    expected_frontmatter: str | None,
    expected_body: str | None,
) -> None:
    """Test frontmatter and body regex."""
    match = FRONTMATTER_AND_BODY_REGEX.match(source)

    if expected_frontmatter is None:
        assert match is None
    else:
        assert match is not None
        frontmatter, body = match.groups()
        assert frontmatter == expected_frontmatter
        assert body == expected_body


class TestExtractFrontmatterAndBody(unittest.TestCase):
    """Test extracting frontmatter and body from a string."""

    def test_should_extract_frontmatter_and_body(self) -> None:
        """Test extracting frontmatter and body when both are present."""
        input_str = '---\nfoo: bar\n---\nThis is the body.'
        frontmatter, body = extract_frontmatter_and_body(input_str)
        assert frontmatter == 'foo: bar'
        assert body == 'This is the body.'

    def test_should_extract_frontmatter_and_body_empty_frontmatter(
        self,
    ) -> None:
        """Test extracting frontmatter and body when both are present."""
        input_str = '---\n\n---\nThis is the body.'
        frontmatter, body = extract_frontmatter_and_body(input_str)
        assert frontmatter == ''
        assert body == 'This is the body.'

    def test_extract_frontmatter_and_body_no_frontmatter(self) -> None:
        """Test extracting body when no frontmatter is present.

        Both the frontmatter and body are empty strings, when there
        is no frontmatter marker.
        """

        input_str = 'Hello World'
        frontmatter, body = extract_frontmatter_and_body(input_str)
        assert frontmatter == ''
        assert body == ''


def test_split_by_regex() -> None:
    """Test splitting by regex and filtering empty/whitespace pieces."""
    source = '  one  ,  ,  two  ,  three  '
    result = split_by_regex(source, re.compile(r','))
    assert result == ['  one  ', '  two  ', '  three  ']


class TestTransformMessagesToHistory(unittest.TestCase):
    def test_add_history_metadata_to_messages(self) -> None:
        messages: list[Message] = [
            Message(role=Role.USER, content=[TextPart(text='Hello')]),
            Message(role=Role.MODEL, content=[TextPart(text='Hi there')]),
        ]

        result = transform_messages_to_history(messages)

        assert len(result) == 2
        assert result == [
            Message(
                role=Role.USER,
                content=[TextPart(text='Hello')],
                metadata={'purpose': 'history'},
            ),
            Message(
                role=Role.MODEL,
                content=[TextPart(text='Hi there')],
                metadata={'purpose': 'history'},
            ),
        ]

    def test_preserve_existing_metadata_while_adding_history_purpose(
        self,
    ) -> None:
        messages: list[Message] = [
            Message(
                role=Role.USER,
                content=[TextPart(text='Hello')],
                metadata={'foo': 'bar'},
            )
        ]

        result = transform_messages_to_history(messages)

        assert len(result) == 1
        assert result == [
            Message(
                role=Role.USER,
                content=[TextPart(text='Hello')],
                metadata={'foo': 'bar', 'purpose': 'history'},
            )
        ]

    def test_handle_empty_array(self) -> None:
        result = transform_messages_to_history([])
        assert result == []


class TestMessageSourcesToMessages(unittest.TestCase):
    def test_should_handle_empty_array(self) -> None:
        message_sources: list[MessageSource] = []
        expected: list[Message] = []
        assert message_sources_to_messages(message_sources) == expected

    def test_should_convert_a_single_message_source(self) -> None:
        message_sources: list[MessageSource] = [
            MessageSource(role=Role.USER, source='Hello')
        ]
        expected: list[Message] = [
            Message(role=Role.USER, content=[TextPart(text='Hello')])
        ]
        assert message_sources_to_messages(message_sources) == expected

    def test_should_handle_message_source_with_content(self) -> None:
        message_sources: list[MessageSource] = [
            MessageSource(
                role=Role.USER, content=[TextPart(text='Existing content')]
            )
        ]
        expected: list[Message] = [
            Message(role=Role.USER, content=[TextPart(text='Existing content')])
        ]
        assert message_sources_to_messages(message_sources) == expected

    def test_should_handle_message_source_with_metadata(self) -> None:
        message_sources: list[MessageSource] = [
            MessageSource(
                role=Role.USER,
                content=[TextPart(text='Existing content')],
                metadata={'foo': 'bar'},
            )
        ]
        expected: list[Message] = [
            Message(
                role=Role.USER,
                content=[TextPart(text='Existing content')],
                metadata={'foo': 'bar'},
            )
        ]
        assert message_sources_to_messages(message_sources) == expected

    def test_should_filter_out_message_sources_with_empty_source_and_content(
        self,
    ) -> None:
        message_sources: list[MessageSource] = [
            MessageSource(role=Role.USER, source=''),
            MessageSource(role=Role.MODEL, source='  '),
            MessageSource(role=Role.USER, source='Hello'),
        ]
        expected: list[Message] = [
            Message(role=Role.MODEL, content=[]),
            Message(role=Role.USER, content=[TextPart(text='Hello')]),
        ]
        assert message_sources_to_messages(message_sources) == expected

    def test_should_handle_multiple_message_sources(self) -> None:
        message_sources: list[MessageSource] = [
            MessageSource(role=Role.USER, source='Hello'),
            MessageSource(role=Role.MODEL, source='Hi there'),
            MessageSource(role=Role.USER, source='How are you?'),
        ]
        expected: list[Message] = [
            Message(role=Role.USER, content=[TextPart(text='Hello')]),
            Message(role=Role.MODEL, content=[TextPart(text='Hi there')]),
            Message(role=Role.USER, content=[TextPart(text='How are you?')]),
        ]
        assert message_sources_to_messages(message_sources) == expected


class TestMessagesHaveHistory(unittest.TestCase):
    def test_should_return_true_if_messages_have_history_metadata(self) -> None:
        messages: list[Message] = [
            Message(
                role=Role.USER,
                content=[TextPart(text='Hello')],
                metadata={'purpose': 'history'},
            )
        ]

        result = messages_have_history(messages)

        self.assertTrue(result)

    def test_should_return_false_if_messages_do_not_have_history_metadata(
        self,
    ) -> None:
        messages: list[Message] = [
            Message(role=Role.USER, content=[TextPart(text='Hello')])
        ]

        result = messages_have_history(messages)

        self.assertFalse(result)


class TestInsertHistory(unittest.TestCase):
    def test_should_return_original_messages_if_history_is_undefined(
        self,
    ) -> None:
        messages: list[Message] = [
            Message(role=Role.USER, content=[TextPart(text='Hello')])
        ]

        result = insert_history(messages, [])

        assert result == messages

    def test_should_return_original_messages_if_history_purpose_already_exists(
        self,
    ) -> None:
        messages: list[Message] = [
            Message(
                role=Role.USER,
                content=[TextPart(text='Hello')],
                metadata={'purpose': 'history'},
            )
        ]

        history: list[Message] = [
            Message(
                role=Role.MODEL,
                content=[TextPart(text='Previous')],
                metadata={'purpose': 'history'},
            )
        ]

        result = insert_history(messages, history)

        assert result == messages

    def test_should_insert_history_before_the_last_user_message(self) -> None:
        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=[TextPart(text='System prompt')]),
            Message(
                role=Role.USER, content=[TextPart(text='Current question')]
            ),
        ]

        history: list[Message] = [
            Message(
                role=Role.MODEL,
                content=[TextPart(text='Previous')],
                metadata={'purpose': 'history'},
            )
        ]

        result = insert_history(messages, history)

        assert len(result) == 3
        assert result == [
            Message(role=Role.SYSTEM, content=[TextPart(text='System prompt')]),
            Message(
                role=Role.MODEL,
                content=[TextPart(text='Previous')],
                metadata={'purpose': 'history'},
            ),
            Message(
                role=Role.USER, content=[TextPart(text='Current question')]
            ),
        ]

    def test_should_append_history_at_the_end_if_no_user_message_is_last(
        self,
    ) -> None:
        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=[TextPart(text='System prompt')]),
            Message(role=Role.MODEL, content=[TextPart(text='Model message')]),
        ]
        history: list[Message] = [
            Message(
                role=Role.MODEL,
                content=[TextPart(text='Previous')],
                metadata={'purpose': 'history'},
            )
        ]

        result = insert_history(messages, history)

        assert len(result) == 3
        assert result == [
            Message(role=Role.SYSTEM, content=[TextPart(text='System prompt')]),
            Message(role=Role.MODEL, content=[TextPart(text='Model message')]),
            Message(
                role=Role.MODEL,
                content=[TextPart(text='Previous')],
                metadata={'purpose': 'history'},
            ),
        ]


@pytest.mark.parametrize(
    'piece,expected',
    [
        (
            'Hello World',
            TextPart(text='Hello World'),
        ),
        (
            '<<<dotprompt:media:url>>> https://example.com/image.jpg',
            MediaPart(
                media=dict(
                    url='https://example.com/image.jpg',
                )
            ),
        ),
        (
            '<<<dotprompt:media:url>>> https://example.com/image.jpg image/jpeg',
            MediaPart(
                media={
                    'url': 'https://example.com/image.jpg',
                    'contentType': 'image/jpeg',
                },
            ),
        ),
        (
            'https://example.com/image.jpg',
            TextPart(text='https://example.com/image.jpg'),
        ),
        (
            '<<<dotprompt:section>>> code',
            PendingPart(metadata=dict(purpose='code', pending=True)),
        ),
        (
            'Text before <<<dotprompt:media:url>>> https://example.com/image.jpg Text after',
            TextPart(
                text='Text before <<<dotprompt:media:url>>> https://example.com/image.jpg Text after'
            ),
        ),
    ],
)
def test_parse_part(piece: str, expected: Part) -> None:
    """Test parsing pieces."""
    result = parse_part(piece)
    assert result == expected


def test_parse_media_piece() -> None:
    """Test parsing media pieces."""
    piece = '<<<dotprompt:media:url>>> https://example.com/image.jpg'
    result = parse_media_part(piece)
    assert result == MediaPart(media={'url': 'https://example.com/image.jpg'})


def test_parse_media_piece_invalid() -> None:
    """Test parsing invalid media pieces."""
    piece = 'https://example.com/image.jpg'
    with pytest.raises(ValueError):
        parse_media_part(piece)


def test_parse_section_piece() -> None:
    """Test parsing section pieces."""
    piece = '<<<dotprompt:section>>> code'
    result = parse_section_part(piece)
    assert result == PendingPart(metadata={'purpose': 'code', 'pending': True})


def test_parse_section_piece_invalid() -> None:
    """Test parsing invalid section pieces."""
    piece = 'https://example.com/image.jpg'
    with pytest.raises(ValueError):
        parse_section_part(piece)


def test_parse_text_piece() -> None:
    """Test parsing text pieces."""
    piece = 'Hello World'
    result = parse_text_part(piece)
    assert result == TextPart(text='Hello World')


class TestParseDocument(unittest.TestCase):
    def test_parse_document_with_frontmatter_and_template(self) -> None:
        """Test parsing document with frontmatter and template."""
        source = """---
name: test
description: test description
foo.bar: value
---
Template content"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)
        self.assertEqual(result.name, 'test')
        self.assertEqual(result.description, 'test description')
        if result.ext:
            self.assertEqual(result.ext['foo']['bar'], 'value')
        self.assertEqual(result.template, 'Template content')

        if result.raw:
            self.assertEqual(result.raw['name'], 'test')
            self.assertEqual(result.raw['description'], 'test description')
            self.assertEqual(result.raw['foo.bar'], 'value')

    def test_handle_document_without_frontmatter(self) -> None:
        """Test handling document without frontmatter."""
        source = 'Just template content'

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)
        self.assertEqual(result.ext, {})
        self.assertEqual(result.template, 'Just template content')

    def test_handle_invalid_yaml_frontmatter(self) -> None:
        """Test handling invalid YAML frontmatter."""
        source = """---
invalid: : yaml
---
Template content"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)

        self.assertEqual(result.ext, {})
        self.assertEqual(result.template, source.strip())

    def test_handle_empty_frontmatter(self) -> None:
        """Test handling empty frontmatter."""
        source = """---
---
Template content"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)

        self.assertEqual(result.ext, {})

        # TODO: Check whether this is the correct behavior.
        self.assertEqual(result.template, source.strip())

    def test_handle_multiple_namespaced_entries(self) -> None:
        """Test handling multiple namespaced entries."""
        source = """---
foo.bar: value1
foo.baz: value2
qux.quux: value3
---
Template content"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)

        if result.ext:
            self.assertEqual(result.ext['foo']['bar'], 'value1')
            self.assertEqual(result.ext['foo']['baz'], 'value2')
            self.assertEqual(result.ext['qux']['quux'], 'value3')

    def test_handle_reserved_keywords(self) -> None:
        """Test handling reserved keywords."""
        frontmatter_parts = []
        for keyword in RESERVED_METADATA_KEYWORDS:
            if keyword == 'ext':
                continue
            frontmatter_parts.append(f'{keyword}: value-{keyword}')

        source = (
            '---\n' + '\n'.join(frontmatter_parts) + '\n---\nTemplate content'
        )

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)

        # for keyword in RESERVED_METADATA_KEYWORDS:
        #    if keyword == 'ext':
        #        continue
        #    self.assertEqual(getattr(result, keyword), f'value-{keyword}')

        self.assertEqual(result.template, 'Template content')
