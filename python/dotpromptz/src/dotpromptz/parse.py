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

"""Parses dotprompt templates and extracts metadata.

This module is responsible for parsing dotprompt templates. It handles extracting
metadata from YAML frontmatter and converting the template content into a
structured format, specifically a list of messages and their parts (text,
media, or metadata).

Key functionalities include:

- Extracting YAML frontmatter and the main template body.
- Parsing the YAML frontmatter into a structured metadata object, handling
  reserved keywords and namespaced entries.
- Splitting the template body into message sources based on role and history
  markers.
- Converting message sources into structured messages, processing media and
  section markers within the content.
- Handling the insertion of historical messages into the conversation flow.
"""

import re
from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Any, TypeVar

import yaml
from pydantic import ValidationError
from yaml.composer import ComposerError
from yaml.events import AliasEvent, NodeEvent
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from dotpromptz.errors import FrontmatterError
from dotpromptz.typing import (
    DataArgument,
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

T = TypeVar('T')


@dataclass
class MessageSource:
    """A message with a source string and optional content and metadata."""

    role: Role
    source: str | None = None
    content: list[Part] | None = None
    metadata: dict[str, Any] | None = field(default_factory=dict)


# Prefixes for the role markers in the template.
ROLE_MARKER_PREFIX = '<<<dotprompt:role:'

# Prefixes for the history markers in the template.
HISTORY_MARKER_PREFIX = '<<<dotprompt:history'

# Prefixes for the media markers in the template.
MEDIA_MARKER_PREFIX = '<<<dotprompt:media:'

# Prefixes for the section markers in the template.
SECTION_MARKER_PREFIX = '<<<dotprompt:section'

# Regular expression to match YAML frontmatter delineated by `---` markers.
# Allows blank lines and license headers (lines starting with #) before the first ---.
FRONTMATTER_AND_BODY_REGEX = re.compile(
    r'^(?:(?:#[^\n]*|[ \t]*)\n)*---\s*(?:\r\n|\r|\n)([\s\S]*?)(?:\r\n|\r|\n)---\s*(?:\r\n|\r|\n)([\s\S]*)$'
)
DELIMITER_REGEX = re.compile(r'^---[ \t]*$')
LINE_BREAK_REGEX = re.compile(r'\r\n|\r|\n')

# Regular expression to match <<<dotprompt:role:xxx>>> and
# <<<dotprompt:history>>> markers in the template.
#
# Examples of matching patterns:
# - <<<dotprompt:role:user>>>
# - <<<dotprompt:role:system>>>
# - <<<dotprompt:history>>>
#
# Note: Only lowercase letters are allowed after 'role:'.
ROLE_AND_HISTORY_MARKER_REGEX = re.compile(r'(<<<dotprompt:(?:role:[a-z]+|history))>>>')

# Regular expression to match <<<dotprompt:media:url>>> and
# <<<dotprompt:section>>> markers in the template.
#
# Examples of matching patterns:
# - <<<dotprompt:media:url>>>
# - <<<dotprompt:section>>>
MEDIA_AND_SECTION_MARKER_REGEX = re.compile(r'(<<<dotprompt:(?:media:url|section).*?)>>>')

# List of reserved keywords that are handled specially in the metadata of a
# .prompt file. These keys are processed differently from extension metadata.
RESERVED_METADATA_KEYWORDS = [
    # NOTE: KEEP SORTED
    'config',
    'description',
    'ext',
    'input',
    'model',
    'name',
    'output',
    'raw',
    'toolDefs',
    'tools',
    'variant',
    'version',
]


@dataclass(frozen=True)
class FrontmatterSource:
    """The declared frontmatter and template body."""

    declared: bool
    frontmatter: str
    body: str
    content_line: int


class RestrictedFrontmatterLoader(yaml.SafeLoader):
    """Safe YAML loader for the portable Dotprompt metadata subset."""

    def compose_node(self, parent: Node | None, index: int) -> Node | None:
        """Reject graph and type features before constructing values."""
        event = self.peek_event()
        if isinstance(event, AliasEvent):
            raise ComposerError(None, None, 'aliases are not allowed', event.start_mark)
        if isinstance(event, NodeEvent):
            if event.anchor is not None:
                raise ComposerError(None, None, 'anchors are not allowed', event.start_mark)
            if getattr(event, 'tag', None) is not None:
                raise ComposerError(None, None, 'explicit tags are not allowed', event.start_mark)
        return super().compose_node(parent, index)

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Hashable, Any]:
        """Construct a mapping while rejecting ambiguous keys."""
        result: dict[Hashable, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode) or key_node.tag != 'tag:yaml.org,2002:str':
                raise ComposerError(None, None, 'mapping keys must be strings', key_node.start_mark)
            key = self.construct_object(key_node, deep=True)
            if key in result:
                raise ComposerError(None, None, 'duplicate mapping keys are not allowed', key_node.start_mark)
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def split_by_regex(source: str, regex: re.Pattern[str]) -> list[str]:
    """Splits string by regexp while filtering out empty/whitespace-only pieces.

    Args:
        source: The source string to split into parts.
        regex: The regular expression to use for splitting.

    Returns:
        An array of non-empty string pieces.
    """

    def filter_empty(s: str) -> bool:
        return bool(s.strip())

    return list(filter(filter_empty, regex.split(source)))


def split_by_role_and_history_markers(rendered_string: str) -> list[str]:
    """Splits a rendered string into pieces based on role and history markers.

    Empty/whitespace-only pieces are filtered out.

    Args:
        rendered_string: The template string to split.

    Returns:
        Array of non-empty string pieces.
    """
    return split_by_regex(rendered_string, ROLE_AND_HISTORY_MARKER_REGEX)


def split_by_media_and_section_markers(source: str) -> list[str]:
    """Split the source into pieces based on media and section markers.

    Empty/whitespace-only pieces are filtered out.

    Args:
        source: The source string to split into parts

    Returns:
        An array of string parts
    """
    return split_by_regex(source, MEDIA_AND_SECTION_MARKER_REGEX)


def convert_namespaced_entry_to_nested_object(
    key: str,
    value: Any,
    obj: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Processes a namespaced key-value pair into a nested object structure.

    For example, 'foo.bar': 'value' becomes { foo: { bar: 'value' } }.

    Args:
        key: The dotted namespace key (e.g., 'foo.bar')
        value: The value to assign
        obj: The object to add the namespaced value to

    Returns:
        The updated target object
    """
    # NOTE: Goes only a single level deep.
    if obj is None:
        obj = {}

    last_dot_index = key.rindex('.')
    ns = key[:last_dot_index]
    field = key[last_dot_index + 1 :]

    # Ensure the namespace exists.
    obj.setdefault(ns, {})
    obj[ns][field] = value

    return obj


def identify_frontmatter(source: str, *, source_name: str | None = None) -> FrontmatterSource:
    """Identify declared frontmatter without interpreting its contents."""
    lines = LINE_BREAK_REGEX.split(source)
    line_breaks = list(LINE_BREAK_REGEX.finditer(source))

    opening_index: int | None = None
    for index, line in enumerate(lines):
        if DELIMITER_REGEX.fullmatch(line):
            opening_index = index
            break
        if line.strip() and not line.startswith('#'):
            return FrontmatterSource(False, '', source, 1)

    if opening_index is None:
        return FrontmatterSource(False, '', source, 1)
    if opening_index >= len(line_breaks):
        raise FrontmatterError(
            'missing closing delimiter',
            line=opening_index + 1,
            column=1,
            source_name=source_name,
        ) from None

    closing_index: int | None = None
    for index in range(opening_index + 1, len(lines)):
        if DELIMITER_REGEX.fullmatch(lines[index]):
            closing_index = index
            break

    if closing_index is None:
        raise FrontmatterError(
            'missing closing delimiter',
            line=opening_index + 1,
            column=1,
            source_name=source_name,
        ) from None

    frontmatter_start = line_breaks[opening_index].end()
    if closing_index == opening_index + 1:
        frontmatter_end = frontmatter_start
    else:
        frontmatter_end = line_breaks[closing_index - 1].start()

    if closing_index < len(line_breaks):
        body_start = line_breaks[closing_index].end()
    else:
        body_start = len(source)

    return FrontmatterSource(
        True,
        source[frontmatter_start:frontmatter_end],
        source[body_start:],
        opening_index + 2,
    )


def extract_frontmatter_and_body(source: str) -> tuple[str, str]:
    """Extracts the YAML frontmatter and body from a document.

    Args:
        source: The source document containing frontmatter and template

    Returns:
        A tuple containing the frontmatter and body If the pattern does not
        match, both the values returned will be empty.
    """
    identified = identify_frontmatter(source)
    if identified.declared:
        return identified.frontmatter, identified.body
    return '', ''


def frontmatter_error(
    reason: str,
    *,
    identified: FrontmatterSource,
    line: int,
    column: int,
    source_name: str | None,
) -> FrontmatterError:
    """Create an error located in the complete prompt source."""
    return FrontmatterError(
        reason,
        line=identified.content_line + line,
        column=column + 1,
        source_name=source_name,
    )


def node_at_location(node: Node, location: tuple[str | int, ...]) -> Node:
    """Find the YAML node associated with a validation location."""
    current = node
    yaml_names = {
        'input_schema': 'inputSchema',
        'output_schema': 'outputSchema',
        'tool_defs': 'toolDefs',
    }
    for part in location:
        if isinstance(part, str):
            part = yaml_names.get(part, part)
        if isinstance(current, MappingNode) and isinstance(part, str):
            match = next(
                (
                    value_node
                    for key_node, value_node in current.value
                    if isinstance(key_node, ScalarNode) and key_node.value == part
                ),
                None,
            )
            if match is None:
                break
            current = match
        elif isinstance(current, SequenceNode) and isinstance(part, int) and part < len(current.value):
            current = current.value[part]
        else:
            break
    return current


def parse_document(source: str, *, source_name: str | None = None) -> ParsedPrompt[T]:
    """Parses document containing YAML frontmatter and template content.

    The frontmatter contains metadata and configuration for the prompt.

    Args:
        source: The source document containing frontmatter and template
        source_name: Optional identifier attached to frontmatter errors.

    Returns:
        Parsed prompt with metadata and template content
    """
    identified = identify_frontmatter(source, source_name=source_name)
    if not identified.declared:
        # No frontmatter, return a basic ParsedPrompt with just the template
        return ParsedPrompt(ext={}, config=None, metadata={}, tool_defs=None, template=source)

    try:
        parsed_metadata = yaml.load(identified.frontmatter, Loader=RestrictedFrontmatterLoader)
        if parsed_metadata is None:
            parsed_metadata = {}
    except yaml.YAMLError as error:
        mark = getattr(error, 'problem_mark', None)
        reason = getattr(error, 'problem', None) or 'invalid YAML'
        allowed_reasons = {
            'aliases are not allowed',
            'anchors are not allowed',
            'duplicate mapping keys are not allowed',
            'explicit tags are not allowed',
            'mapping keys must be strings',
        }
        if reason not in allowed_reasons:
            reason = 'invalid YAML'
        raise frontmatter_error(
            reason,
            identified=identified,
            line=mark.line if mark is not None else 0,
            column=mark.column if mark is not None else 0,
            source_name=source_name,
        ) from None

    if not isinstance(parsed_metadata, dict):
        try:
            root = yaml.compose(identified.frontmatter, Loader=RestrictedFrontmatterLoader)
        except yaml.YAMLError:
            root = None
        line = root.start_mark.line if root is not None else 0
        column = root.start_mark.column if root is not None else 0
        raise frontmatter_error(
            'frontmatter must be a mapping',
            identified=identified,
            line=line,
            column=column,
            source_name=source_name,
        ) from None

    raw = dict(parsed_metadata)
    ext: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if key not in RESERVED_METADATA_KEYWORDS and '.' in key:
            convert_namespaced_entry_to_nested_object(key, value, ext)

    root = yaml.compose(identified.frontmatter, Loader=RestrictedFrontmatterLoader)
    for field_name in ('config', 'ext', 'raw'):
        value = raw.get(field_name)
        if value is not None and not isinstance(value, dict):
            node = node_at_location(root, (field_name,)) if root is not None else None
            raise frontmatter_error(
                'invalid recognized field type',
                identified=identified,
                line=node.start_mark.line if node is not None else 0,
                column=node.start_mark.column if node is not None else 0,
                source_name=source_name,
            ) from None

    try:
        return ParsedPrompt(
            name=raw.get('name'),
            description=raw.get('description'),
            variant=raw.get('variant'),
            version=raw.get('version'),
            model=raw.get('model'),
            input=raw.get('input'),
            output=raw.get('output'),
            tool_defs=raw.get('toolDefs'),
            tools=raw.get('tools'),
            ext=ext,
            config=raw.get('config'),
            metadata=raw.get('metadata', {}),
            raw=raw,
            template=identified.body.strip(),
        )
    except ValidationError as error:
        detail = error.errors(include_url=False, include_context=False, include_input=False)[0]
        location = tuple(part for part in detail['loc'] if isinstance(part, (str, int)))
        node = node_at_location(root, location) if root is not None else None
        raise frontmatter_error(
            'invalid recognized field type',
            identified=identified,
            line=node.start_mark.line if node is not None else 0,
            column=node.start_mark.column if node is not None else 0,
            source_name=source_name,
        ) from None


def to_messages(
    rendered_string: str,
    data: DataArgument[Any] | None = None,
) -> list[Message]:
    """Converts a rendered template string into an array of messages.

    Processes role markers and history placeholders to structure the
    conversation.

    Args:
        rendered_string: The rendered template string to convert
        data: Optional data containing message history

    Returns:
        List of structured messages
    """
    current_message = MessageSource(role=Role.USER, source='')
    message_sources = [current_message]

    for piece in split_by_role_and_history_markers(rendered_string):
        if piece.startswith(ROLE_MARKER_PREFIX):
            role = piece[len(ROLE_MARKER_PREFIX) :]

            if current_message.source and current_message.source.strip():
                # If the current message has content, create a new message
                current_message = MessageSource(role=Role(role), source='')
                message_sources.append(current_message)
            else:
                # Otherwise, update the role of the current message
                current_message.role = Role(role)

        elif piece.startswith(HISTORY_MARKER_PREFIX):
            # Add the history messages to the message sources
            msgs: list[Message] = []
            if data and data.messages:
                msgs = data.messages
            history_messages = transform_messages_to_history(msgs)
            if history_messages:
                message_sources.extend(
                    [
                        MessageSource(
                            role=msg.role,
                            content=msg.content,
                            metadata=msg.metadata,
                        )
                        for msg in history_messages
                    ]
                )

            # Add a new message source for the model
            current_message = MessageSource(role=Role.MODEL, source='')
            message_sources.append(current_message)

        else:
            # Otherwise, add the piece to the current message source
            current_message.source = (current_message.source or '') + piece

    messages = message_sources_to_messages(message_sources)
    return insert_history(messages, data.messages if data else None)


def message_sources_to_messages(
    message_sources: list[MessageSource],
) -> list[Message]:
    """Processes an array of message sources into an array of messages.

    Args:
        message_sources: List of message sources

    Returns:
        List of structured messages
    """
    messages: list[Message] = []
    for m in message_sources:
        if m.content or m.source:
            message = Message(
                role=m.role,
                content=(m.content if m.content is not None else to_parts(m.source or '')),
            )

            if m.metadata:
                message.metadata = m.metadata

            messages.append(message)

    return messages


def transform_messages_to_history(
    messages: list[Message],
) -> list[Message]:
    """Adds history metadata to an array of messages.

    Args:
        messages: Array of messages to transform

    Returns:
        Array of messages with history metadata added
    """
    return [
        Message(
            role=message.role,
            content=message.content,
            metadata={**(message.metadata or {}), 'purpose': 'history'},
        )
        for message in messages
    ]


def messages_have_history(messages: list[Message]) -> bool:
    """Checks if the messages have history metadata.

    Args:
        messages: The messages to check

    Returns:
        True if the messages have history metadata, False otherwise
    """
    return any(msg.metadata and msg.metadata.get('purpose') == 'history' for msg in messages)


def insert_history(
    messages: list[Message],
    history: list[Message] | None = None,
) -> list[Message]:
    """Inserts historical messages into the conversation.

    The history is inserted at:
    - The end of the conversation if there is no history or no user message.
    - Before the last user message if there is a user message.

    The history is not inserted:
    - If it already exists in the messages.
    - If there is no user message.

    Args:
        messages: Current array of messages
        history: Historical messages to insert

    Returns:
        Messages with history inserted
    """
    # If we have no history or find an existing instance of history, return the
    # original messages unmodified.
    if not history or messages_have_history(messages):
        return messages

    if len(messages) == 0:
        return history

    last_message = messages[-1]
    if last_message.role == 'user':
        # If the last message is a user message, insert the history before it.
        messages = messages[:-1]
        messages.extend(history)
        messages.append(last_message)
    else:
        # Otherwise, append the history to the end of the messages.
        messages.extend(history)
    return messages


def to_parts(source: str) -> list[Part]:
    """Converts a source string into an array of parts.

    Also processes media and section markers.

    Args:
        source: The source string to convert into parts

    Returns:
        Array of structured parts (text, media, or metadata)
    """
    return [parse_part(piece) for piece in split_by_media_and_section_markers(source)]


def parse_part(piece: str) -> Part:
    """Parses a part from a piece of rendered template.

    Args:
        piece: The piece to parse

    Returns:
        Part, PendingPart, TextPart, or MediaPart
    """
    if piece.startswith(MEDIA_MARKER_PREFIX):
        return parse_media_part(piece)
    elif piece.startswith(SECTION_MARKER_PREFIX):
        return parse_section_part(piece)
    else:
        return parse_text_part(piece)


def parse_media_part(piece: str) -> MediaPart:
    """Parses a media part from a piece of rendered template.

    Args:
        piece: The piece to parse

    Returns:
        Media part

    Raises:
        ValueError: If the media piece is invalid
    """
    if not piece.startswith(MEDIA_MARKER_PREFIX):
        raise ValueError(f'Invalid media piece: {piece}; expected prefix {MEDIA_MARKER_PREFIX}')

    fields = piece.split(' ')
    n = len(fields)
    if n == 3:
        _, url, content_type = fields
    elif n == 2:
        _, url = fields
        content_type = None
    else:
        raise ValueError(f'Invalid media piece: {piece}; expected 2 or 3 fields, found {n}')

    media_content = MediaContent(
        url=url,
        content_type=(content_type if content_type and content_type.strip() else None),
    )
    return MediaPart(media=media_content)


def parse_section_part(piece: str) -> PendingPart:
    """Parses a section part from a piece of rendered template.

    Args:
        piece: The piece to parse

    Returns:
        Section part

    Raises:
        ValueError: If the section piece is invalid
    """
    if not piece.startswith(SECTION_MARKER_PREFIX):
        raise ValueError(f'Invalid section piece: {piece}; expected prefix {SECTION_MARKER_PREFIX}')

    fields = piece.split(' ')
    if len(fields) == 2:
        section_type = fields[1]
    else:
        raise ValueError(f'Invalid section piece: {piece}; expected 2 fields, found {len(fields)}')

    # Use the helper method to set purpose
    pending_metadata = PendingMetadata.with_purpose(section_type)
    return PendingPart(metadata=pending_metadata)


def parse_text_part(piece: str) -> TextPart:
    """Parses a text part from a piece of rendered template.

    Args:
        piece: The piece to parse

    Returns:
        Text part
    """
    return TextPart(text=piece)
