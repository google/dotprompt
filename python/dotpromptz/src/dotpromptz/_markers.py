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

"""In-band markers used to turn a rendered template string into messages.

## Overview

The `role`, `history`, `section` and `media` helpers emit markers into the
rendered string, which `to_messages` then splits back apart into messages and
parts. The rendered string also contains user-supplied variable values
verbatim (HTML escaping is off), so every marker carries a random per-render
nonce and the splitter only honors markers with that nonce. Anything else that
merely looks like a marker (for example typed by an end user) stays plain text.

```
template            rendered string                              messages
--------            ---------------                              --------
{{role "system"}}   <<<dotprompt:{nonce}:role:system>>>Be safe.  system: Be safe.
Be safe.            <<<dotprompt:{nonce}:role:user>>>Q: <<<...   user:   Q: <<<...
{{role "user"}}            ^ trusted marker              ^ user text, no nonce
Q: {{q}}
```

## Terminology

| Term        | Meaning                                                          |
|-------------|------------------------------------------------------------------|
| marker      | `<<<dotprompt:{nonce}:{body}>>>`                                 |
| nonce       | 32 lowercase hex chars (128 bits) from `secrets`, one per render |
| body        | `role:{name}`, `history`, `section {name}`,                      |
|             | `media:url {url} [{contentType}]`                                |
| data frame  | The Handlebars `{{@name}}` dict; holds the nonce during render   |

## Key Operations

- `generate_marker_nonce`: makes a fresh nonce for one render.
- `format_marker`: builds a marker string (used by the helpers).
- `role_and_history_marker_regex`, `media_and_section_marker_regex`: build the
  splitter regexes for one nonce.
- `split_by_markers`: splits a string into `TextPiece` and `MarkerPiece`
  items, classifying them by position rather than content.

## Caveats

- Helpers read the nonce from the data frame under `MARKER_NONCE_DATA_KEY`.
  `Dotprompt` writes it after the caller's `context`, so callers cannot
  override it. Rendering the helpers outside `Dotprompt` raises.
- A marker emitted by a custom helper (or written literally in the template)
  without the current nonce is plain text.
- Media and section bodies can carry user-supplied values (URLs, section
  names), so their regex matches across newlines up to the first `>>>`.
- This module is internal. `__all__` lists its names for in-package use; the
  legacy star-import shims (`dotpromptz.parse`, `dotpromptz.helpers`, ...)
  must not re-export them.
"""

import re
import secrets
from dataclasses import dataclass
from typing import TypeAlias

__all__ = [
    'MARKER_NONCE_DATA_KEY',
    'MarkerPiece',
    'Piece',
    'TextPiece',
    'format_marker',
    'generate_marker_nonce',
    'media_and_section_marker_regex',
    'role_and_history_marker_regex',
    'split_by_markers',
]

MARKER_NONCE_DATA_KEY = '__dotpromptMarkerNonce'
"""Key under which the per-render nonce is stored in the Handlebars data frame.

Written last when building the frame so `DataArgument.context` can't override it.
"""

# Checked with fullmatch: `$` alone would also accept a trailing newline.
_NONCE_PATTERN = re.compile(r'[0-9a-f]{32}')


def generate_marker_nonce() -> str:
    """Generate a fresh 128-bit marker nonce.

    Call once per render so a nonce seen in one rendered prompt is useless for
    any other.

    Returns:
        32 lowercase hex characters from a CSPRNG.

    Examples:
        ```python
        nonce = generate_marker_nonce()
        assert len(nonce) == 32
        ```
    """
    return secrets.token_hex(16)


def _check_nonce(nonce: str) -> None:
    """Reject anything that is not a well-formed nonce.

    The nonce is interpolated into a regex, so it must stay strictly hex.

    Args:
        nonce: The nonce to check.

    Raises:
        ValueError: If the nonce is not 32 lowercase hex characters.
    """
    if not _NONCE_PATTERN.fullmatch(nonce):
        raise ValueError('dotprompt: invalid marker nonce')


def format_marker(nonce: str, body: str) -> str:
    """Format a marker with the given nonce and body.

    Args:
        nonce: The per-render nonce.
        body: The marker body, e.g. `role:user` or `media:url https://...`.

    Returns:
        The marker string `<<<dotprompt:{nonce}:{body}>>>`.

    Raises:
        ValueError: If the nonce is malformed.

    Examples:
        ```python
        format_marker('0123456789abcdef0123456789abcdef', 'role:user')
        # => '<<<dotprompt:0123456789abcdef0123456789abcdef:role:user>>>'
        ```
    """
    _check_nonce(nonce)
    return f'<<<dotprompt:{nonce}:{body}>>>'


def role_and_history_marker_regex(nonce: str) -> re.Pattern[str]:
    """Build the regex matching role and history markers for `nonce`.

    The single capture group is the marker body (`role:user`, `history`).
    Only lowercase letters are allowed in role names.

    Args:
        nonce: The per-render nonce.

    Returns:
        A compiled pattern with exactly one capture group.

    Raises:
        ValueError: If the nonce is malformed.
    """
    _check_nonce(nonce)
    return re.compile(rf'<<<dotprompt:{nonce}:(role:[a-z]+|history)>>>')


def media_and_section_marker_regex(nonce: str) -> re.Pattern[str]:
    """Build the regex matching media and section markers for `nonce`.

    The single capture group is the marker body
    (`media:url https://... image/png`, `section code`). The body is lazily
    matched up to the first `>>>` and may span newlines: it can carry
    user-supplied values (e.g. a media URL), and a newline there must not stop
    the trusted marker from matching and leak it, nonce included, as text.

    Args:
        nonce: The per-render nonce.

    Returns:
        A compiled pattern with exactly one capture group.

    Raises:
        ValueError: If the nonce is malformed.
    """
    _check_nonce(nonce)
    return re.compile(rf'<<<dotprompt:{nonce}:((?:media:url|section) .*?)>>>', re.DOTALL)


@dataclass(frozen=True)
class TextPiece:
    """Literal text between markers."""

    text: str


@dataclass(frozen=True)
class MarkerPiece:
    """A trusted marker; `body` is the part after the nonce."""

    body: str


Piece: TypeAlias = TextPiece | MarkerPiece
"""A piece of a rendered string: either literal text or a trusted marker."""


def split_by_markers(source: str, regex: re.Pattern[str]) -> list[Piece]:
    """Split `source` on the markers matched by `regex`.

    Pieces are classified by position rather than content. `re.split` with one
    capture group puts text at even indices and captures at odd ones:

    ```
    'Hi <<<dotprompt:N:role:user>>> there'
     -> ['Hi ', 'role:user', ' there']
          0 text  1 marker   2 text
    ```

    This matters because a text piece can itself look like a marker body.
    Whitespace-only text pieces are dropped.

    Args:
        source: The string to split.
        regex: A pattern with exactly one capture group (the marker body),
            e.g. from `role_and_history_marker_regex`.

    Returns:
        Text and marker pieces in source order.

    Examples:
        ```python
        split_by_markers(
            'Hi ' + format_marker(nonce, 'history'),
            role_and_history_marker_regex(nonce),
        )
        # => [TextPiece(text='Hi '), MarkerPiece(body='history')]
        ```
    """
    pieces: list[Piece] = []
    for i, s in enumerate(regex.split(source)):
        if i % 2 == 1:
            pieces.append(MarkerPiece(body=s))
        elif s.strip():
            pieces.append(TextPiece(text=s))
    return pieces
