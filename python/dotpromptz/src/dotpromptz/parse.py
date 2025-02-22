# Copyright 2024 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Parse prompt template content."""

import re
import sys
from typing import Any

import yaml

from dotpromptz.interfaces import (
    DataArgument,
    MediaPart,
    Message,
    ParsedPrompt,
    Part,
    PromptMetadata,
)

# Regular expression to match YAML frontmatter delineated by `---` markers at
# the start of a .prompt content block.
FRONTMATTER_AND_BODY_REGEX = re.compile(
    r'^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$', re.MULTILINE
)

# List of reserved keywords that are handled specially in the metadata.  These
# keys are processed differently from extension metadata.
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

# Regular expression to match <<<dotprompt:role:xxx>>> and
# <<<dotprompt:history>>> markers in the template.
ROLE_AND_HISTORY_MARKER_REGEX = re.compile(
    r'(<<<dotprompt:(?:role:[a-z]+|history))>>>'
)

# Regular expression to match <<<dotprompt:media:url>>> and
# <<<dotprompt:section>>> markers in the template.
MEDIA_AND_SECTION_MARKER_REGEX = re.compile(
    r'(<<<dotprompt:(?:media:url|section).*?)>>>'
)

# Default metadata structure with empty extension and configuration objects.
BASE_METADATA: PromptMetadata = {
    'ext': {},
    'metadata': {},
    'config': {},
}


def split_by_regex(source: str, regex: re.Pattern) -> list[str]:
    """Split a string by a regular expression.

    Filters out empty/whitespace-only pieces.

    Args:
        source: The source string to split into parts.
        regex: The regular expression to use for splitting.

    Returns:
        A list of non-empty string pieces.
    """
    return [s for s in regex.split(source) if s.strip()]


def split_by_role_and_history_markers(rendered_string: str) -> list[str]:
    """Split a rendered template string.

    Splits based on role and history markers.

    Args:
        rendered_string: The template string to split.

    Returns:
        List of non-empty string pieces.
    """
    return split_by_regex(rendered_string, ROLE_AND_HISTORY_MARKER_REGEX)


def split_by_media_and_section_markers(source: str) -> list[str]:
    """Split the source into pieces based on media and section markers.

    Args:
        source: The source string to split into parts.

    Returns:
        A list of string parts.
    """
    return split_by_regex(source, MEDIA_AND_SECTION_MARKER_REGEX)


def convert_namespaced_entry_to_nested_object(
    key: str, value: Any, obj: dict[str, dict[str, Any]] | None = None
) -> dict[str, dict[str, Any]]:
    """Process a namespaced key-value pair into a nested object structure.

    For example, 'foo.bar': 'value' becomes { foo: { bar: 'value' } }

    Args:
        key: The dotted namespace key (e.g., 'foo.bar')
        value: The value to assign
        obj: The object to add the namespaced value to

    Returns:
        The updated target object
    """
    if obj is None:
        obj = {}
    last_dot_index = key.rfind('.')
    if last_dot_index == -1:
        return obj
    ns = key[:last_dot_index]
    field = key[last_dot_index + 1 :]
    if ns not in obj:
        obj[ns] = {}
    obj[ns][field] = value
    return obj


def extract_frontmatter_and_body(source: str) -> tuple[str, str]:
    """Extract the YAML frontmatter and body from a document.

    Args:
        source: The source document containing frontmatter and template.

    Returns:
        A tuple containing the frontmatter and body.
    """
    match = FRONTMATTER_AND_BODY_REGEX.match(source)
    if match:
        return match.group(1), match.group(2)
    return '', ''


def parse_document(source: str) -> ParsedPrompt:
    """Parse a document containing YAML frontmatter.

    The frontmatter contains metadata and configuration for the prompt.

    Args:
        source: The source document containing frontmatter and template.

    Returns:
        Parsed prompt with metadata and template content.
    """
    frontmatter, body = extract_frontmatter_and_body(source)
    if frontmatter:
        try:
            parsed_metadata = yaml.safe_load(frontmatter)
            raw = (
                dict(parsed_metadata)
                if isinstance(parsed_metadata, dict)
                else {}
            )
            pruned = BASE_METADATA.copy()
            ext: dict[str, Any] = {}

            for k, v in raw.items():
                if k in RESERVED_METADATA_KEYWORDS:
                    pruned[k] = v
                elif '.' in k:
                    convert_namespaced_entry_to_nested_object(k, v, ext)
            return {**pruned, 'raw': raw, 'ext': ext, 'template': body.strip()}
        except Exception as error:
            print(
                'Dotprompt: Error parsing YAML frontmatter:',
                error,
                file=sys.stderr,
            )
            return {**BASE_METADATA, 'template': source.strip()}
    return {**BASE_METADATA, 'template': source}


def transform_messages_to_history(messages: list[Message]) -> list[Message]:
    """Transform an array of messages.

    Adds history metadata to each message.

    Args:
        messages: Array of messages to transform.

    Returns:
        Array of messages with history metadata added.
    """
    for msg in messages:
        if 'metadata' not in msg:
            msg['metadata'] = {}
    return messages


def insert_history(
    messages: list[Message], history: list[Message] | None = None
) -> list[Message]:
    """Insert historical messages into the conversation.

    Places messages at the appropriate position.

    Args:
        messages: Current array of messages.
        history: Historical messages to insert.

    Returns:
        Messages with history inserted.
    """
    if history is None:
        history = []
    return history + messages


def to_messages(
    rendered_string: str, data: DataArgument | None = None
) -> list[Message]:
    """Convert a rendered template string into an array of messages.

    Processes role markers and history placeholders to structure the
    conversation.

    Args:
        rendered_string: The rendered template string to convert.
        data: Optional data containing message history.

    Returns:
        Array of structured messages.
    """
    current_message: Message = {'role': 'user', 'source': ''}
    messages: list[Message] = []

    parts = split_by_role_and_history_markers(rendered_string)
    for part in parts:
        if part.startswith('<<<dotprompt:role:'):
            if current_message['source'].strip():
                messages.append(current_message)
            role = part.replace('<<<dotprompt:role:', '').replace('>>>', '')
            current_message = {'role': role, 'source': ''}
        elif part.startswith('<<<dotprompt:history'):
            if current_message['source'].strip():
                messages.append(current_message)
            if data and 'history' in data:
                history_messages = transform_messages_to_history(
                    data['history']
                )
                messages = insert_history(messages, history_messages)
            current_message = {'role': 'user', 'source': ''}
        else:
            current_message['source'] += part

    if current_message['source'].strip():
        messages.append(current_message)

    return messages


def to_parts(source: str) -> list[Part | MediaPart]:
    """Convert a source string into an array of parts.

    Processes media and section markers.

    Args:
        source: The source string to convert into parts.

    Returns:
        Array of structured parts (text, media, or metadata).
    """
    parts: list[Part | MediaPart] = []
    pieces = split_by_media_and_section_markers(source)

    for i, piece in enumerate(pieces):
        if piece.startswith('<<<dotprompt:media:url'):
            if i + 1 < len(pieces):
                parts.append(MediaPart(url=pieces[i + 1].strip()))
        elif not piece.startswith('<<<dotprompt:'):
            parts.append(Part(type='text', content=piece))

    return parts
