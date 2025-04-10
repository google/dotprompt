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

"""Parse dotprompt templates and extract metadata."""

import re
from dataclasses import dataclass, field
from typing import Any, TypeVar

import yaml

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

# Regular expression to match YAML frontmatter delineated by `---` markers at
# the start of a .prompt content block.
FRONTMATTER_AND_BODY_REGEX = re.compile(r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$')

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


def extract_frontmatter_and_body(source: str) -> tuple[str, str]:
    """Extracts the YAML frontmatter and body from a document.

    Args:
        source: The source document containing frontmatter and template

    Returns:
        A tuple containing the frontmatter and body If the pattern does not
        match, both the values returned will be empty.
    """
    match = FRONTMATTER_AND_BODY_REGEX.match(source)
    if match:
        frontmatter, body = match.groups()
        return frontmatter, body
    return '', ''


def parse_document(source: str) -> ParsedPrompt[T]:
    """Parses document containing YAML frontmatter and template content.

    The frontmatter contains metadata and configuration for the prompt.

    Args:
        source: The source document containing frontmatter and template

    Returns:
        Parsed prompt with metadata and template content
    """
    frontmatter, body = extract_frontmatter_and_body(source)
    if not frontmatter:
        # No frontmatter, return a basic ParsedPrompt with just the template
        return ParsedPrompt(ext={}, config=None, metadata={}, toolDefs=None, template=source)

    try:
        parsed_metadata = yaml.safe_load(frontmatter)
        if parsed_metadata is None:
            parsed_metadata = {}

        raw = dict(parsed_metadata)
        pruned: dict[str, Any] = {'ext': {}, 'config': {}, 'metadata': {}}
        ext: dict[str, dict[str, Any]] = {}

        # Process each key in the raw metadata
        for key, value in raw.items():
            if key in RESERVED_METADATA_KEYWORDS:
                pruned[key] = value
            elif '.' in key:
                convert_namespaced_entry_to_nested_object(key, value, ext)

        try:
            return ParsedPrompt(
                name=raw.get('name'),
                description=raw.get('description'),
                variant=raw.get('variant'),
                version=raw.get('version'),
                input=raw.get('input'),
                output=raw.get('output'),
                toolDefs=raw.get('toolDefs'),
                tools=raw.get('tools'),
                ext=ext,
                config=pruned.get('config'),
                metadata=pruned.get('metadata', {}),
                raw=raw,
                template=body.strip(),
            )
        except Exception:
            # Return a basic ParsedPrompt with just the template
            return ParsedPrompt(
                ext={},
                config=None,
                metadata={},
                toolDefs=None,
                template=body.strip(),
            )
    except Exception as e:
        # TODO: Should this be an error?
        print(f'Dotprompt: Error parsing YAML frontmatter: {e}')
        # Return a basic ParsedPrompt with just the template
        return ParsedPrompt(
            ext={},
            config=None,
            metadata={},
            toolDefs=None,
            template=source.strip(),
        )


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
                message_sources.extend([
                    MessageSource(
                        role=msg.role,
                        content=msg.content,
                        metadata=msg.metadata,
                    )
                    for msg in history_messages
                ])

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
        contentType=(content_type if content_type and content_type.strip() else None),
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
