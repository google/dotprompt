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

Only markers carrying the per-render nonce are honored; see
`dotpromptz._markers` for the marker format and why the nonce is needed.

## Compatibility (dotpromptz 1.x)

This module is re-exported by the legacy `dotpromptz.parse` path, which stays
stable for all of 1.x.

| Name                                  | Status                                     |
|---------------------------------------|--------------------------------------------|
| `to_messages`, `to_parts`,            | `nonce` is a required keyword-only         |
| `message_sources_to_messages`         | argument. Pre-nonce positional calls such  |
|                                       | as `to_messages(rendered, data)` raise     |
|                                       | `TypeError` instead of misbinding `data`.  |
| `ROLE_MARKER_PREFIX`,                 | Deprecated. Kept with their original       |
| `HISTORY_MARKER_PREFIX`,              | values; they describe the pre-nonce marker |
| `MEDIA_MARKER_PREFIX`,                | format `<<<dotprompt:{body}>>>` and are    |
| `SECTION_MARKER_PREFIX`,              | not used for rendering.                    |
| `ROLE_AND_HISTORY_MARKER_REGEX`,      |                                            |
| `MEDIA_AND_SECTION_MARKER_REGEX`      |                                            |
| `split_by_regex`,                     | Deprecated; emit `DeprecationWarning`.     |
| `split_by_role_and_history_markers`,  | Original behavior, pre-nonce markers only, |
| `split_by_media_and_section_markers`  | not used for rendering.                    |
"""

import re
import warnings
from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

import yaml
from pydantic import ValidationError
from yaml.composer import ComposerError
from yaml.events import AliasEvent, NodeEvent
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

# Imported as a module (not `from ... import`) so the legacy star-import shim
# doesn't re-export marker internals; see compat_shims_test.py.
from dotpromptz import _markers
from dotpromptz._errors import FrontmatterError
from dotpromptz._typing import (
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


# Marker bodies and body prefixes; see `dotpromptz._markers` for the full
# marker format.
_ROLE_MARKER_BODY_PREFIX = 'role:'
_HISTORY_MARKER_BODY = 'history'
_MEDIA_MARKER_BODY_PREFIX = 'media:url '
_SECTION_MARKER_BODY_PREFIX = 'section '

# Regular expression to match YAML frontmatter delineated by `---` markers.
# Allows blank lines and license headers (lines starting with #) before the first ---.
FRONTMATTER_AND_BODY_REGEX = re.compile(
    r'^(?:(?:#[^\n]*|[ \t]*)\n)*---\s*(?:\r\n|\r|\n)([\s\S]*?)(?:\r\n|\r|\n)---\s*(?:\r\n|\r|\n)([\s\S]*)$'
)
DELIMITER_REGEX = re.compile(r'^---[ \t]*$')
LINE_BREAK_REGEX = re.compile(r'\r\n|\r|\n')

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


class _FrontmatterReason(str, Enum):
    """Every reason this module reports on a FrontmatterError.

    Membership is the allowlist. PyYAML's own messages can quote the broken
    source, so parse_document echoes a parser message only when it matches a
    member here and falls back to INVALID_YAML otherwise.
    """

    ALIASES = 'aliases are not allowed'
    ANCHORS = 'anchors are not allowed'
    EXPLICIT_TAGS = 'explicit tags are not allowed'
    NON_STRING_KEYS = 'mapping keys must be strings'
    DUPLICATE_KEYS = 'duplicate mapping keys are not allowed'
    INVALID_YAML = 'invalid YAML'
    NOT_A_MAPPING = 'frontmatter must be a mapping'
    INVALID_FIELD_TYPE = 'invalid recognized field type'
    MISSING_CLOSING_DELIMITER = 'missing closing delimiter'


class RestrictedFrontmatterLoader(yaml.SafeLoader):
    """Safe YAML loader for the portable Dotprompt metadata subset."""

    def compose_node(self, parent: Node | None, index: int) -> Node | None:
        """Reject graph and type features before constructing values."""
        event = self.peek_event()
        if isinstance(event, AliasEvent):
            raise ComposerError(None, None, _FrontmatterReason.ALIASES.value, event.start_mark)
        if isinstance(event, NodeEvent):
            if event.anchor is not None:
                raise ComposerError(None, None, _FrontmatterReason.ANCHORS.value, event.start_mark)
            if getattr(event, 'tag', None) is not None:
                raise ComposerError(None, None, _FrontmatterReason.EXPLICIT_TAGS.value, event.start_mark)
        return super().compose_node(parent, index)

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Hashable, Any]:
        """Construct a mapping while rejecting ambiguous keys."""
        result: dict[Hashable, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, ScalarNode) or key_node.tag != 'tag:yaml.org,2002:str':
                raise ComposerError(None, None, _FrontmatterReason.NON_STRING_KEYS.value, key_node.start_mark)
            key = self.construct_object(key_node, deep=True)
            if key in result:
                raise ComposerError(None, None, _FrontmatterReason.DUPLICATE_KEYS.value, key_node.start_mark)
            result[key] = self.construct_object(value_node, deep=deep)
        return result


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
            _FrontmatterReason.MISSING_CLOSING_DELIMITER.value,
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
            _FrontmatterReason.MISSING_CLOSING_DELIMITER.value,
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
        try:
            # Only strings we wrote survive. PyYAML's own messages can quote
            # the broken source, so they degrade to a fixed reason.
            reason = _FrontmatterReason(getattr(error, 'problem', None)).value
        except ValueError:
            reason = _FrontmatterReason.INVALID_YAML.value
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
            _FrontmatterReason.NOT_A_MAPPING.value,
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
                _FrontmatterReason.INVALID_FIELD_TYPE.value,
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
            _FrontmatterReason.INVALID_FIELD_TYPE.value,
            identified=identified,
            line=node.start_mark.line if node is not None else 0,
            column=node.start_mark.column if node is not None else 0,
            source_name=source_name,
        ) from None


def to_messages(
    rendered_string: str,
    data: DataArgument[Any] | None = None,
    *,
    nonce: str,
) -> list[Message]:
    """Converts a rendered template string into an array of messages.

    Processes role markers and history placeholders to structure the
    conversation. Only markers carrying `nonce` are honored; anything else
    that looks like a marker stays text.

    Args:
        rendered_string: The rendered template string to convert
        data: Optional data containing message history
        nonce: The marker nonce used when rendering the template. Keyword-only
            so a pre-nonce positional call `to_messages(rendered, data)` fails
            with `TypeError` rather than treating `data` as the nonce.

    Returns:
        List of structured messages

    Raises:
        ValueError: If the nonce is malformed.

    Examples:
        ```python
        nonce = _markers.generate_marker_nonce()
        rendered = _markers.format_marker(nonce, 'role:system') + 'Be safe.'
        to_messages(rendered, nonce=nonce)
        # => [Message(role=Role.SYSTEM, content=[TextPart(text='Be safe.')])]
        ```
    """
    current_message = MessageSource(role=Role.USER, source='')
    message_sources = [current_message]

    for piece in _markers.split_by_markers(rendered_string, _markers.role_and_history_marker_regex(nonce)):
        if isinstance(piece, _markers.TextPiece):
            current_message.source = (current_message.source or '') + piece.text

        elif piece.body.startswith(_ROLE_MARKER_BODY_PREFIX):
            role = piece.body[len(_ROLE_MARKER_BODY_PREFIX) :]

            if current_message.source and current_message.source.strip():
                # If the current message has content, create a new message
                current_message = MessageSource(role=Role(role), source='')
                message_sources.append(current_message)
            else:
                # Otherwise, update the role of the current message
                current_message.role = Role(role)

        elif piece.body == _HISTORY_MARKER_BODY:
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

    messages = message_sources_to_messages(message_sources, nonce=nonce)
    return insert_history(messages, data.messages if data else None)


def message_sources_to_messages(
    message_sources: list[MessageSource],
    *,
    nonce: str,
) -> list[Message]:
    """Processes an array of message sources into an array of messages.

    Args:
        message_sources: List of message sources
        nonce: The marker nonce used when rendering the sources (keyword-only)

    Returns:
        List of structured messages
    """
    messages: list[Message] = []
    for m in message_sources:
        if m.content or m.source:
            message = Message(
                role=m.role,
                content=(m.content if m.content is not None else to_parts(m.source or '', nonce=nonce)),
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


def to_parts(source: str, *, nonce: str) -> list[Part]:
    """Converts a source string into an array of parts.

    Also processes media and section markers carrying `nonce`.

    Args:
        source: The source string to convert into parts
        nonce: The marker nonce used when rendering the source (keyword-only)

    Returns:
        Array of structured parts (text, media, or metadata)

    Raises:
        ValueError: If the nonce is malformed.
    """
    return [
        parse_part(piece) for piece in _markers.split_by_markers(source, _markers.media_and_section_marker_regex(nonce))
    ]


def parse_part(piece: _markers.Piece | str) -> Part:
    """Parses a part from a split piece of rendered template.

    Args:
        piece: The piece to parse; text pieces become text parts and marker
            pieces become media or pending (section) parts. A plain `str` is
            the deprecated pre-nonce form (a piece from
            `split_by_media_and_section_markers`) and is parsed with the legacy
            prefixes, emitting a DeprecationWarning.

    Returns:
        Part, PendingPart, TextPart, or MediaPart
    """
    if isinstance(piece, str):
        _warn_legacy('parse_part(str)')
        if piece.startswith(MEDIA_MARKER_PREFIX):
            return _media_part_from_fields(piece)
        if piece.startswith(SECTION_MARKER_PREFIX):
            return _section_part_from_fields(piece)
        return parse_text_part(piece)
    if isinstance(piece, _markers.MarkerPiece):
        if piece.body.startswith(_MEDIA_MARKER_BODY_PREFIX):
            return parse_media_part(piece.body)
        return parse_section_part(piece.body)
    return parse_text_part(piece.text)


def parse_media_part(body: str) -> MediaPart:
    """Parses a media part from a marker body.

    Args:
        body: The marker body, `media:url <url> [<contentType>]`. The deprecated
            pre-nonce form `<<<dotprompt:media:url <url> [<contentType>]` is
            still accepted (with a DeprecationWarning).

    Returns:
        Media part

    Raises:
        ValueError: If the media body is invalid
    """
    if body.startswith(MEDIA_MARKER_PREFIX):
        _warn_legacy('parse_media_part with a pre-nonce marker')
    elif not body.startswith(_MEDIA_MARKER_BODY_PREFIX):
        raise ValueError(f'Invalid media piece: {body}; expected prefix {_MEDIA_MARKER_BODY_PREFIX!r}')
    return _media_part_from_fields(body)


def _media_part_from_fields(body: str) -> MediaPart:
    """Builds a media part from `<prefix> <url> [<contentType>]`.

    Shared by the nonced body form and the deprecated pre-nonce form, which
    differ only in the first space-separated field.

    Args:
        body: The media body in either form.

    Returns:
        Media part

    Raises:
        ValueError: If the body doesn't have 2 or 3 space-separated fields.
    """
    fields = body.split(' ')
    n = len(fields)
    if n == 3:
        _, url, content_type = fields
    elif n == 2:
        _, url = fields
        content_type = None
    else:
        raise ValueError(f'Invalid media piece: {body}; expected 2 or 3 fields, found {n}')

    media_content = MediaContent(
        url=url,
        content_type=(content_type if content_type and content_type.strip() else None),
    )
    return MediaPart(media=media_content)


def parse_section_part(body: str) -> PendingPart:
    """Parses a section part from a marker body.

    Args:
        body: The marker body, `section <name>`. The deprecated pre-nonce form
            `<<<dotprompt:section <name>` is still accepted (with a
            DeprecationWarning).

    Returns:
        Section part

    Raises:
        ValueError: If the section body is invalid
    """
    if body.startswith(SECTION_MARKER_PREFIX):
        _warn_legacy('parse_section_part with a pre-nonce marker')
    elif not body.startswith(_SECTION_MARKER_BODY_PREFIX):
        raise ValueError(f'Invalid section piece: {body}; expected prefix {_SECTION_MARKER_BODY_PREFIX!r}')
    return _section_part_from_fields(body)


def _section_part_from_fields(body: str) -> PendingPart:
    """Builds a pending part from `<prefix> <name>` (nonced or pre-nonce form).

    Args:
        body: The section body in either form.

    Returns:
        Section part

    Raises:
        ValueError: If the body doesn't have exactly 2 space-separated fields.
    """
    fields = body.split(' ')
    if len(fields) == 2:
        section_type = fields[1]
    else:
        raise ValueError(f'Invalid section piece: {body}; expected 2 fields, found {len(fields)}')

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


# ---------------------------------------------------------------------------
# Deprecated legacy marker helpers.
#
# Kept only so `from dotpromptz.parse import ...` keeps working for all of 1.x.
# They describe the pre-nonce marker format `<<<dotprompt:{body}>>>`, which
# the render path no longer honors, and nothing in dotpromptz uses them:
# changing or calling them has no effect on rendering. The constants keep
# their original values; the functions keep their original signatures and
# behavior but emit a DeprecationWarning.
# ---------------------------------------------------------------------------

# Deprecated: pre-nonce role marker prefix; not used for rendering.
ROLE_MARKER_PREFIX = '<<<dotprompt:role:'

# Deprecated: pre-nonce history marker prefix; not used for rendering.
HISTORY_MARKER_PREFIX = '<<<dotprompt:history'

# Deprecated: pre-nonce media marker prefix; not used for rendering.
MEDIA_MARKER_PREFIX = '<<<dotprompt:media:'

# Deprecated: pre-nonce section marker prefix; not used for rendering.
SECTION_MARKER_PREFIX = '<<<dotprompt:section'

# Deprecated: matches pre-nonce `<<<dotprompt:role:xxx>>>` and
# `<<<dotprompt:history>>>` markers; not used for rendering.
ROLE_AND_HISTORY_MARKER_REGEX = re.compile(r'(<<<dotprompt:(?:role:[a-z]+|history))>>>')

# Deprecated: matches pre-nonce `<<<dotprompt:media:url ...>>>` and
# `<<<dotprompt:section ...>>>` markers; not used for rendering.
MEDIA_AND_SECTION_MARKER_REGEX = re.compile(r'(<<<dotprompt:(?:media:url|section).*?)>>>')

_LEGACY_MARKER_WARNING = (
    '{name} is deprecated and may be removed in a future major release. It only understands the pre-nonce '
    'marker format and does not reflect how rendered prompts are parsed.'
)


def _warn_legacy(name: str) -> None:
    """Emit the DeprecationWarning for a legacy marker helper.

    Args:
        name: The public name of the deprecated helper.
    """
    # stacklevel=3: skip this function and the deprecated helper itself.
    warnings.warn(_LEGACY_MARKER_WARNING.format(name=name), DeprecationWarning, stacklevel=3)


def _legacy_split_by_regex(source: str, regex: re.Pattern[str]) -> list[str]:
    """Original `split_by_regex` behavior, without the warning.

    Args:
        source: The source string to split into parts.
        regex: The regular expression to use for splitting.

    Returns:
        An array of non-empty string pieces.
    """
    return [s for s in regex.split(source) if s.strip()]


def split_by_regex(source: str, regex: re.Pattern[str]) -> list[str]:
    """Splits string by regexp while filtering out empty/whitespace-only pieces.

    Deprecated: legacy helper kept for `dotpromptz.parse` compatibility. It is
    not used for rendering, and marker pieces and text pieces are returned
    as indistinguishable strings.

    Args:
        source: The source string to split into parts.
        regex: The regular expression to use for splitting.

    Returns:
        An array of non-empty string pieces.
    """
    _warn_legacy('split_by_regex')
    return _legacy_split_by_regex(source, regex)


def split_by_role_and_history_markers(rendered_string: str) -> list[str]:
    """Splits a rendered string into pieces based on role and history markers.

    Deprecated: legacy helper kept for `dotpromptz.parse` compatibility. It
    only recognizes the pre-nonce `<<<dotprompt:role:...>>>` and
    `<<<dotprompt:history>>>` markers and is not used for rendering; output
    from the current renderer is not split by it.

    Empty/whitespace-only pieces are filtered out.

    Args:
        rendered_string: The template string to split.

    Returns:
        Array of non-empty string pieces.
    """
    _warn_legacy('split_by_role_and_history_markers')
    return _legacy_split_by_regex(rendered_string, ROLE_AND_HISTORY_MARKER_REGEX)


def split_by_media_and_section_markers(source: str) -> list[str]:
    """Split the source into pieces based on media and section markers.

    Deprecated: legacy helper kept for `dotpromptz.parse` compatibility. It
    only recognizes the pre-nonce `<<<dotprompt:media:url ...>>>` and
    `<<<dotprompt:section ...>>>` markers and is not used for rendering;
    output from the current renderer is not split by it.

    Empty/whitespace-only pieces are filtered out.

    Args:
        source: The source string to split into parts

    Returns:
        An array of string parts
    """
    _warn_legacy('split_by_media_and_section_markers')
    return _legacy_split_by_regex(source, MEDIA_AND_SECTION_MARKER_REGEX)
