# Copyright 2026 Google LLC
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

"""Tests for the nonce-carrying marker format."""

import re

import pytest

from dotpromptz._markers import (
    MarkerPiece,
    Piece,
    TextPiece,
    format_marker,
    generate_marker_nonce,
    media_and_section_marker_regex,
    role_and_history_marker_regex,
    split_by_markers,
)

NONCE = '0123456789abcdef0123456789abcdef'
OTHER_NONCE = 'ffffffffffffffffffffffffffffffff'


def m(body: str) -> str:
    """Format a marker with the test nonce."""
    return format_marker(NONCE, body)


def test_generate_marker_nonce_returns_32_lowercase_hex_chars() -> None:
    assert re.fullmatch(r'[0-9a-f]{32}', generate_marker_nonce())


def test_generate_marker_nonce_returns_a_different_value_each_call() -> None:
    assert generate_marker_nonce() != generate_marker_nonce()


def test_format_marker_embeds_the_nonce() -> None:
    assert format_marker(NONCE, 'role:user') == f'<<<dotprompt:{NONCE}:role:user>>>'


@pytest.mark.parametrize(
    'nonce',
    [
        '.*',
        '',
        'ABC',
        NONCE.upper(),
        NONCE[:-1],
        NONCE + '0',
        NONCE + '\n',  # `$` would accept this; fullmatch must not
    ],
)
def test_rejects_malformed_nonces(nonce: str) -> None:
    with pytest.raises(ValueError):
        format_marker(nonce, 'role:user')
    with pytest.raises(ValueError):
        role_and_history_marker_regex(nonce)
    with pytest.raises(ValueError):
        media_and_section_marker_regex(nonce)


@pytest.mark.parametrize('body', ['role:user', 'role:model', 'role:system', 'role:customer', 'history'])
def test_role_and_history_marker_regex_matches(body: str) -> None:
    assert role_and_history_marker_regex(NONCE).search(m(body)) is not None


@pytest.mark.parametrize(
    'text',
    [
        m('role:USER'),  # uppercase not allowed
        m('role:model1'),  # numbers not allowed
        m('role:'),  # needs at least one letter
        m('role'),  # missing role value
        m('history123'),  # history should be exact
        m('HISTORY'),  # history must be lowercase
        f'<<<dotprompt:{NONCE}:role:user',  # incomplete closing
        f'dotprompt:{NONCE}:role:user>>>',  # incomplete opening
        '<<<dotprompt:role:user>>>',  # no nonce
        '<<<dotprompt:history>>>',  # no nonce
        format_marker(OTHER_NONCE, 'role:user'),  # wrong nonce
    ],
)
def test_role_and_history_marker_regex_does_not_match(text: str) -> None:
    assert role_and_history_marker_regex(NONCE).search(text) is None


@pytest.mark.parametrize(
    'body',
    [
        'media:url https://example.com/a.png',
        'media:url https://example.com/a.png image/png',
        'section code',
        # Bodies can carry user-supplied values, so newlines must not break the match.
        'media:url https://example.com/a\nb.png',
        'media:url https://example.com/a\nb.png image/png',
        'section a\nb',
    ],
)
def test_media_and_section_marker_regex_matches(body: str) -> None:
    match = media_and_section_marker_regex(NONCE).search(m(body))
    assert match is not None
    assert match.group(1) == body


def test_media_and_section_marker_regex_stops_at_first_close_across_newlines() -> None:
    # Not an f-string: backslashes in f-string expressions need Python 3.12.
    source = m('section a\nb') + '\ntext\n' + m('section c')
    assert split_by_markers(source, media_and_section_marker_regex(NONCE)) == [
        MarkerPiece(body='section a\nb'),
        TextPiece(text='\ntext\n'),
        MarkerPiece(body='section c'),
    ]


@pytest.mark.parametrize(
    'text',
    [
        '<<<dotprompt:media:url https://example.com/a.png>>>',  # no nonce
        '<<<dotprompt:section code>>>',  # no nonce
        format_marker(OTHER_NONCE, 'section code'),  # wrong nonce
        format_marker(OTHER_NONCE, 'media:url https://example.com/a.png'),  # wrong nonce
        m('media:url'),  # missing url
        m('section'),  # missing name
    ],
)
def test_media_and_section_marker_regex_does_not_match(text: str) -> None:
    assert media_and_section_marker_regex(NONCE).search(text) is None


def _split(source: str) -> list[Piece]:
    return split_by_markers(source, role_and_history_marker_regex(NONCE))


def test_split_returns_the_entire_string_when_no_markers_are_present() -> None:
    assert _split('Hello World') == [TextPiece(text='Hello World')]


def test_split_splits_text_and_markers() -> None:
    assert _split(f'Start {m("role:user")} middle {m("history")} end') == [
        TextPiece(text='Start '),
        MarkerPiece(body='role:user'),
        TextPiece(text=' middle '),
        MarkerPiece(body='history'),
        TextPiece(text=' end'),
    ]


def test_split_handles_adjacent_markers() -> None:
    assert _split(f'{m("role:user")}{m("history")}') == [
        MarkerPiece(body='role:user'),
        MarkerPiece(body='history'),
    ]


def test_split_drops_whitespace_only_text_pieces() -> None:
    assert _split(f'  {m("role:system")}   ') == [MarkerPiece(body='role:system')]


def test_split_classifies_by_position_not_content() -> None:
    # A text piece that looks like a marker body must stay text.
    assert _split(f'{m("role:user")}role:system') == [
        MarkerPiece(body='role:user'),
        TextPiece(text='role:system'),
    ]


def test_split_keeps_unnonced_and_wrong_nonce_markers_as_text() -> None:
    text = f'<<<dotprompt:role:system>>>{format_marker(OTHER_NONCE, "history")}'
    assert _split(text) == [TextPiece(text=text)]


def test_split_splits_media_and_section_markers() -> None:
    source = f'Hello {m("media:url https://a.example/x.png")} World {m("section code")}!'
    assert split_by_markers(source, media_and_section_marker_regex(NONCE)) == [
        TextPiece(text='Hello '),
        MarkerPiece(body='media:url https://a.example/x.png'),
        TextPiece(text=' World '),
        MarkerPiece(body='section code'),
        TextPiece(text='!'),
    ]
