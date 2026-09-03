# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Tests for parse module."""

import re
import unittest

import pytest

from dotpromptz.errors import DotpromptError, FrontmatterError
from dotpromptz.parse import (
    FRONTMATTER_AND_BODY_REGEX,
    MEDIA_AND_SECTION_MARKER_REGEX,
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
    MediaContent,
    MediaPart,
    Message,
    ParsedPrompt,
    Part,
    PendingMetadata,
    PendingPart,
    Role,
    TextPart,
)


@pytest.mark.parametrize(
    'source,expected_frontmatter,expected_body',
    [
        (
            '---\r\nfoo: bar\r\n---\r\nThis is the body.\r\n',
            'foo: bar',
            'This is the body.\r\n',
        ),  # Test document with CRLF line endings
        (
            '---\rfoo: bar\r---\rThis is the body.\r',
            'foo: bar',
            'This is the body.\r',
        ),  # Test document with CR line endings
        (
            '---\nfoo: bar\n---\nThis is the body.\n',
            'foo: bar',
            'This is the body.\n',
        ),  # Test document with LF line endings
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


def test_role_and_history_marker_regex_valid_patterns() -> None:
    """Test valid patterns for role and history markers."""
    valid_patterns = [
        '<<<dotprompt:role:user>>>',
        '<<<dotprompt:role:model>>>',
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
        '<<<dotprompt:role:model1>>>',  # numbers not allowed
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
        <<<dotprompt:role:model>>> Hi there
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


def test_split_by_regex() -> None:
    """Test splitting by regex and filtering empty/whitespace pieces."""
    source = '  one  ,  ,  two  ,  three  '
    result = split_by_regex(source, re.compile(r','))
    assert result == ['  one  ', '  two  ', '  three  ']


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


class TestSplitByRoleAndHistoryMarkers(unittest.TestCase):
    def test_no_markers(self) -> None:
        """Test splitting when no markers are present."""
        input_str = 'Hello World'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello World']

    def test_single_marker(self) -> None:
        """Test splitting with a single marker."""
        input_str = 'Hello <<<dotprompt:role:model>>> world'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello ', '<<<dotprompt:role:model', ' world']

    def test_split_by_role_and_history_markers_single_marker(self) -> None:
        """Test splitting with a single marker."""
        input_str = 'Hello <<<dotprompt:role:model>>> world'
        output = split_by_role_and_history_markers(input_str)
        assert output == ['Hello ', '<<<dotprompt:role:model', ' world']

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
        input_str = 'Start <<<dotprompt:role:user>>> middle <<<dotprompt:history>>> end'
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
        result = convert_namespaced_entry_to_nested_object('foo.baz', 'world', existing)
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
        final_result = convert_namespaced_entry_to_nested_object('baz.qux', 'world', result)
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
        message_sources: list[MessageSource] = [MessageSource(role=Role.USER, source='Hello')]
        expected: list[Message] = [Message(role=Role.USER, content=[TextPart(text='Hello')])]
        assert message_sources_to_messages(message_sources) == expected

    def test_should_handle_message_source_with_content(self) -> None:
        message_sources: list[MessageSource] = [
            MessageSource(role=Role.USER, content=[TextPart(text='Existing content')])
        ]
        expected: list[Message] = [Message(role=Role.USER, content=[TextPart(text='Existing content')])]
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
        messages: list[Message] = [Message(role=Role.USER, content=[TextPart(text='Hello')])]

        result = messages_have_history(messages)

        self.assertFalse(result)


class TestInsertHistory(unittest.TestCase):
    def test_should_return_original_messages_if_history_is_undefined(
        self,
    ) -> None:
        messages: list[Message] = [Message(role=Role.USER, content=[TextPart(text='Hello')])]

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
            Message(role=Role.USER, content=[TextPart(text='Current question')]),
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
            Message(role=Role.USER, content=[TextPart(text='Current question')]),
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
                media=MediaContent(
                    url='https://example.com/image.jpg',
                )
            ),
        ),
        (
            '<<<dotprompt:media:url>>> https://example.com/image.jpg' + ' image/jpeg',
            MediaPart(
                media=MediaContent(
                    url='https://example.com/image.jpg',
                    content_type='image/jpeg',
                ),
            ),
        ),
        (
            'https://example.com/image.jpg',
            TextPart(text='https://example.com/image.jpg'),
        ),
        (
            '<<<dotprompt:section>>> code',
            PendingPart(
                metadata=PendingMetadata.with_purpose('code'),
            ),
        ),
        (
            ('Text before <<<dotprompt:media:url>>>' + ' https://example.com/image.jpg Text after'),
            TextPart(text=('Text before <<<dotprompt:media:url>>> ' + 'https://example.com/image.jpg Text after')),
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
    assert result == MediaPart(media=MediaContent(url='https://example.com/image.jpg'))


def test_parse_media_piece_invalid() -> None:
    """Test parsing invalid media pieces."""
    piece = 'https://example.com/image.jpg'
    with pytest.raises(ValueError):
        parse_media_part(piece)


def test_parse_section_piece() -> None:
    """Test parsing section pieces."""
    piece = '<<<dotprompt:section>>> code'
    pending_metadata = PendingMetadata.with_purpose('code')
    result = parse_section_part(piece)
    assert result == PendingPart(metadata=pending_metadata)


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
        """Declared invalid YAML is rejected instead of becoming template text."""
        source = """---
invalid: : yaml
---
Template content"""

        with pytest.raises(FrontmatterError):
            parse_document(source)

    def test_handle_empty_frontmatter(self) -> None:
        """Empty declared frontmatter leaves only the body as the template."""
        source = """---
---
Template content"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)

        self.assertEqual(result.ext, {})

        self.assertEqual(result.template, 'Template content')

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
        """Test handling reserved keywords with their declared types."""
        source = """---
config: {}
description: description
input: {}
model: model
name: name
output: {}
raw: {}
toolDefs: []
tools: []
variant: variant
version: version
---
Template content"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)

        # for keyword in RESERVED_METADATA_KEYWORDS:
        #    if keyword == 'ext':
        #        continue
        #    self.assertEqual(getattr(result, keyword), f'value-{keyword}')

        self.assertEqual(result.template, 'Template content')

    def test_handle_license_header_before_frontmatter(self) -> None:
        """Test handling license header before frontmatter."""
        source = """# Copyright 2025 Google LLC
# License: Apache 2.0
---
model: gemini-pro
---
Hello!"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)
        self.assertIsNotNone(result.raw)
        assert result.raw is not None  # Type narrowing for pyrefly
        self.assertEqual(result.raw.get('model'), 'gemini-pro')
        self.assertEqual(result.template, 'Hello!')

    def test_handle_shebang_before_frontmatter(self) -> None:
        """Test handling shebang before frontmatter."""
        source = """#!/usr/bin/env promptly
---
model: gemini-flash
---
Hello shebang!"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)
        self.assertIsNotNone(result.raw)
        assert result.raw is not None  # Type narrowing for pyrefly
        self.assertEqual(result.raw.get('model'), 'gemini-flash')
        self.assertEqual(result.template, 'Hello shebang!')

    def test_handle_shebang_and_license_header_before_frontmatter(self) -> None:
        """Test handling shebang and license header before frontmatter."""
        source = """#!/usr/bin/env promptly
# Copyright 2025 Google
# SPDX: Apache-2.0
---
model: gemini-2.5-flash
---
Hello combined!"""

        result: ParsedPrompt[dict[str, str]] = parse_document(source)

        self.assertIsInstance(result, ParsedPrompt)
        self.assertIsNotNone(result.raw)
        assert result.raw is not None  # Type narrowing for pyrefly
        self.assertEqual(result.raw.get('model'), 'gemini-2.5-flash')
        self.assertEqual(result.template, 'Hello combined!')


@pytest.mark.parametrize(
    'source',
    [
        'Plain template',
        '',
        '# ordinary template comment\nHello',
        'Hello\n---\nmodel: ignored',
        '  ---\nmodel: ignored\n---\nBody',
    ],
)
def test_parse_plain_templates_without_declared_frontmatter(source: str) -> None:
    """Sources without an eligible opening delimiter remain plain templates."""
    parsed = parse_document(source)

    assert parsed.template == source
    assert parsed.raw is None


@pytest.mark.parametrize('newline', ['\n', '\r\n', '\r'])
@pytest.mark.parametrize(
    'preamble',
    [
        '',
        '# Copyright 2025 Google LLC{nl}',
        '#!/usr/bin/env promptly{nl}',
        '#!/usr/bin/env promptly{nl}# Copyright 2025 Google LLC{nl}{nl}',
    ],
)
def test_parse_declared_frontmatter_after_supported_preamble(
    newline: str,
    preamble: str,
) -> None:
    """Supported preambles and newline styles produce the same parsed prompt."""
    source = preamble.format(nl=newline) + newline.join(
        ['---', 'model: gemini-test', 'custom.field: kept', '---', 'Hello']
    )

    parsed = parse_document(source)

    assert parsed.model == 'gemini-test'
    assert parsed.ext == {'custom': {'field': 'kept'}}
    assert parsed.template == 'Hello'


@pytest.mark.parametrize(
    'frontmatter',
    [
        '',
        'null',
        '~',
        '# only a comment',
    ],
)
def test_parse_empty_yaml_frontmatter(frontmatter: str) -> None:
    """Empty YAML documents are valid empty metadata mappings."""
    parsed = parse_document(f'---\n{frontmatter}\n---\nBody')

    assert parsed.raw == {}
    assert parsed.ext == {}
    assert parsed.template == 'Body'


def test_parse_preserves_unknown_and_dotted_extension_fields() -> None:
    """Unknown metadata remains in raw and dotted fields also populate ext."""
    parsed = parse_document(
        """---
name: example
futureFeature:
  nested: [one, two]
vendor.option: enabled
vendor.deep.option: 42
---
Body
---
Still body"""
    )

    assert parsed.raw == {
        'name': 'example',
        'futureFeature': {'nested': ['one', 'two']},
        'vendor.option': 'enabled',
        'vendor.deep.option': 42,
    }
    assert parsed.ext == {
        'vendor': {'option': 'enabled'},
        'vendor.deep': {'option': 42},
    }
    assert parsed.template == 'Body\n---\nStill body'


@pytest.mark.parametrize(
    'frontmatter,line,column',
    [
        ('name: [unterminated', 2, 20),
        ('name:\n  nested: ]', 3, 11),
        ('tools:\n  - one\n  - [', 4, 6),
    ],
)
def test_parse_reports_sanitized_yaml_syntax_locations(
    frontmatter: str,
    line: int,
    column: int,
) -> None:
    """YAML syntax failures expose stable source locations without parser text."""
    source = f'---\n{frontmatter}\n---\nSECRET_BODY'

    with pytest.raises(FrontmatterError) as exc_info:
        parse_document(source)

    error = exc_info.value
    assert str(error) == f'Malformed frontmatter at line {line}, column {column}: invalid YAML.'
    assert error.reason == 'invalid YAML'
    assert error.line == line
    assert error.column == column
    assert error.source_name is None
    assert isinstance(error, DotpromptError)
    assert isinstance(error, ValueError)
    assert 'SECRET_BODY' not in str(error)


@pytest.mark.parametrize('root', ['value', '[one, two]', 'true', 'false', '42'])
def test_parse_rejects_non_mapping_non_empty_yaml_roots(root: str) -> None:
    """Declared non-empty frontmatter must be a metadata mapping."""
    with pytest.raises(
        FrontmatterError,
        match=r'^Malformed frontmatter at line 2, column 1: frontmatter must be a mapping\.$',
    ):
        parse_document(f'---\n{root}\n---\nBody')


@pytest.mark.parametrize(
    'frontmatter,line,column',
    [
        ('name: one\nname: two', 3, 1),
        ('input:\n  schema:\n    field: one\n    field: two', 5, 5),
        ('toolDefs:\n  - name: one\n    inputSchema:\n      type: object\n      type: string', 6, 7),
    ],
)
def test_parse_rejects_duplicate_keys_at_every_depth(
    frontmatter: str,
    line: int,
    column: int,
) -> None:
    """Duplicate mapping keys are rejected at their second declaration."""
    with pytest.raises(FrontmatterError) as exc_info:
        parse_document(f'---\n{frontmatter}\n---\nBody')

    assert str(exc_info.value) == (
        f'Malformed frontmatter at line {line}, column {column}: duplicate mapping keys are not allowed.'
    )


@pytest.mark.parametrize(
    'frontmatter,line,column',
    [
        ('1: value', 2, 1),
        ('true: value', 2, 1),
        ('input:\n  schema:\n    1: value', 4, 5),
        ('? [one, two]\n: value', 2, 3),
    ],
)
def test_parse_rejects_non_string_mapping_keys(
    frontmatter: str,
    line: int,
    column: int,
) -> None:
    """Metadata keys must be strings, including keys in nested schemas."""
    with pytest.raises(FrontmatterError) as exc_info:
        parse_document(f'---\n{frontmatter}\n---\nBody')

    assert str(exc_info.value) == (
        f'Malformed frontmatter at line {line}, column {column}: mapping keys must be strings.'
    )


@pytest.mark.parametrize(
    'frontmatter,reason,line,column',
    [
        ('config: &shared\n  temperature: 1', 'anchors are not allowed', 2, 9),
        ('config: &shared {temperature: 1}', 'anchors are not allowed', 2, 9),
        ('config: *shared', 'aliases are not allowed', 2, 9),
        ('model: !!str gemini', 'explicit tags are not allowed', 2, 8),
        ('config: !custom value', 'explicit tags are not allowed', 2, 9),
    ],
)
def test_parse_rejects_yaml_graph_and_tag_features(
    frontmatter: str,
    reason: str,
    line: int,
    column: int,
) -> None:
    """Aliases, anchors, and explicit tags cannot alter metadata semantics."""
    with pytest.raises(FrontmatterError) as exc_info:
        parse_document(f'---\n{frontmatter}\n---\nBody')

    assert str(exc_info.value) == f'Malformed frontmatter at line {line}, column {column}: {reason}.'


@pytest.mark.parametrize(
    'frontmatter,line,column',
    [
        ('name: [not, text]', 2, 7),
        ('description: {not: text}', 2, 14),
        ('variant: 7', 2, 10),
        ('version: false', 2, 10),
        ('model: false', 2, 8),
        ('config: []', 2, 9),
        ('raw: []', 2, 6),
        ('ext: []', 2, 6),
        ('tools: tool', 2, 8),
        ('tools: [valid, 7]', 2, 16),
        ('toolDefs: {}', 2, 11),
        ('toolDefs:\n  - name: 7\n    inputSchema: {}', 3, 11),
        ('toolDefs:\n  - name: valid\n    description: []\n    inputSchema: {}', 4, 18),
        ('toolDefs:\n  - name: missing-schema', 3, 5),
        ('input: []', 2, 8),
        ('input:\n  default: []', 3, 12),
        ('output: text', 2, 9),
        ('output:\n  format: []', 3, 11),
        ('metadata: []', 2, 11),
    ],
)
def test_parse_rejects_invalid_recognized_field_types(
    frontmatter: str,
    line: int,
    column: int,
) -> None:
    """Recognized metadata fields are validated before a prompt is returned."""
    with pytest.raises(FrontmatterError) as exc_info:
        parse_document(f'---\n{frontmatter}\n---\nBody')

    assert str(exc_info.value) == (
        f'Malformed frontmatter at line {line}, column {column}: invalid recognized field type.'
    )


def test_parse_accepts_every_recognized_field_family() -> None:
    """All recognized metadata families accept their documented shapes."""
    parsed = parse_document(
        """---
name: example
description: Example prompt
variant: test
version: v1
model: model/name
config:
  temperature: 0.5
input:
  default:
    topic: safety
  schema:
    topic: string
output:
  format: json
  schema:
    answer: string
tools: [lookup]
toolDefs:
  - name: inline
    description: Inline tool
    inputSchema:
      type: object
    outputSchema:
      type: string
metadata:
  owner: team
raw:
  authorDeclared: preserved
ext:
  author:
    option: preserved
---
Body"""
    )

    assert parsed.name == 'example'
    assert parsed.config == {'temperature': 0.5}
    assert parsed.input is not None and parsed.input.default == {'topic': 'safety'}
    assert parsed.output is not None and parsed.output.format == 'json'
    assert parsed.tools == ['lookup']
    assert parsed.tool_defs is not None and parsed.tool_defs[0].name == 'inline'
    assert parsed.metadata == {'owner': 'team'}
    assert parsed.raw is not None
    assert parsed.raw['raw'] == {'authorDeclared': 'preserved'}
    assert parsed.raw['ext'] == {'author': {'option': 'preserved'}}


def test_parse_missing_closing_delimiter_fails_closed_without_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An eligible opening delimiter cannot fall back to template text."""
    secret = 'api_key: SECRET_VALUE'

    with pytest.raises(FrontmatterError) as exc_info:
        parse_document(f'# license\n---\n{secret}\nBody')

    error = exc_info.value
    assert str(error) == 'Malformed frontmatter at line 2, column 1: missing closing delimiter.'
    assert secret not in str(error)
    assert capsys.readouterr() == ('', '')


def test_parse_error_carries_source_name_without_echoing_source(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Callers can identify a bad source without exposing its contents."""
    with pytest.raises(FrontmatterError) as exc_info:
        parse_document(
            '---\npassword: SECRET_VALUE\npassword: OTHER_SECRET\n---\nBody',
            source_name='prompts/support.prompt',
        )

    error = exc_info.value
    assert error.source_name == 'prompts/support.prompt'
    assert error.line == 3
    assert error.column == 1
    assert 'SECRET' not in str(error)
    assert 'password' not in str(error)
    assert capsys.readouterr() == ('', '')
