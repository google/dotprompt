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

"""Keep structural prompt syntax separate from rendered data."""

from __future__ import annotations

import re
import secrets
from collections.abc import Iterable, Mapping
from typing import Any

from handlebarrz import HelperFn, HelperOptions

STRUCTURAL_MARKER_PREFIX = '<<<dotprompt:'
ROLE_AND_HISTORY_MARKER_REGEX = re.compile(r'(<<<dotprompt:(?:role:[a-z]+|history))>>>')
MEDIA_AND_SECTION_MARKER_REGEX = re.compile(r'(<<<dotprompt:(?:media:url|section).*?)>>>')
STRUCTURAL_HELPER_NAMES = frozenset({'history', 'media', 'role', 'section'})


class TrustedBlockHelperOptions(HelperOptions):
    """Preserve trusted literal nodes rendered inside a custom block."""

    def __init__(self, options: HelperOptions, marker_trust: StructuralMarkerTrust) -> None:
        self._source_options = options
        self._trust = marker_trust

    def context(self) -> dict[str, Any]:
        return self._source_options.context()

    def hash_value(self, key: str) -> Any:
        return self._source_options.hash_value(key)

    def fn(self) -> str:
        return self._source_options.fn().replace(
            self._trust.trusted_prefix,
            self._trust.block_prefix,
        )

    def inverse(self) -> str:
        return self._source_options.inverse().replace(
            self._trust.trusted_prefix,
            self._trust.block_prefix,
        )


def _replace_complete_markers(source: str, replacement_prefix: str) -> str:
    """Replace complete structural markers while preserving their payload."""

    def replace(match: re.Match[str]) -> str:
        return match.group(0).replace(STRUCTURAL_MARKER_PREFIX, replacement_prefix, 1)

    source = ROLE_AND_HISTORY_MARKER_REGEX.sub(replace, source)
    return MEDIA_AND_SECTION_MARKER_REGEX.sub(replace, source)


def _strings_in(value: Any) -> Iterable[str]:
    """Yield strings from the supported JSON-shaped runtime values."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _strings_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings_in(item)


def _replace_json_strings(value: Any, replacements: tuple[tuple[str, str], ...]) -> Any:
    """Copy a JSON-shaped value while replacing substrings in its strings."""
    if isinstance(value, str):
        for old, new in replacements:
            value = value.replace(old, new)
        return value
    if isinstance(value, dict):
        return {
            _replace_json_strings(key, replacements): _replace_json_strings(item, replacements)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_json_strings(item, replacements) for item in value]
    return value


class StructuralMarkerTrust:
    """Track trusted marker producers for one render."""

    def __init__(self, *, sources: Iterable[str], runtime_values: Iterable[Any]) -> None:
        occupied = list(sources)
        for value in runtime_values:
            occupied.extend(_strings_in(value))

        self.namespace = id(self)
        self.trusted_prefix = self._unique_token('trusted', occupied)
        occupied.append(self.trusted_prefix)
        self.data_prefix = self._unique_token('data', occupied)
        occupied.append(self.data_prefix)
        self.data_close = self._unique_token('close', occupied)
        occupied.append(self.data_close)
        self.block_prefix = self._unique_token('block', occupied)

    def _unique_token(self, label: str, occupied: list[str]) -> str:
        """Choose a token outside known source and runtime strings."""
        seed = secrets.token_hex(16)
        suffix = 0
        while True:
            discriminator = '' if suffix == 0 else f'-{suffix}'
            candidate = f'__dotprompt_{label}_{self.namespace:x}_{seed}{discriminator}__'
            if not any(candidate in value for value in occupied):
                return candidate
            suffix += 1

    def protect_runtime(self, value: Any) -> Any:
        """Make marker syntax in JSON-shaped runtime values inert."""
        return _replace_json_strings(
            value,
            (
                (self.trusted_prefix, self.data_prefix),
                (STRUCTURAL_MARKER_PREFIX, self.data_prefix),
            ),
        )

    def protect_helper_value(self, value: Any) -> Any:
        """Make a structural helper parameter inert inside its marker."""
        value = self.protect_runtime(value)
        return _replace_json_strings(value, (('>>>', self.data_close),))

    def protect_custom_output(self, value: str) -> str:
        """Keep every marker emitted by a custom helper inert."""
        return (
            value.replace(self.trusted_prefix, self.data_prefix)
            .replace(STRUCTURAL_MARKER_PREFIX, self.data_prefix)
            .replace(self.block_prefix, self.trusted_prefix)
        )

    def custom_helper_options(self, options: HelperOptions) -> HelperOptions:
        """Track literal output rendered through block callbacks."""
        return TrustedBlockHelperOptions(options, self)

    def trust_template(self, source: str) -> str:
        """Trust complete markers in literal output nodes."""
        output: list[str] = []
        cursor = 0
        source_length = len(source)

        while cursor < source_length:
            expression_start = source.find('{{', cursor)
            if expression_start < 0:
                output.append(_replace_complete_markers(source[cursor:], self.trusted_prefix))
                break

            output.append(_replace_complete_markers(source[cursor:expression_start], self.trusted_prefix))

            if source.startswith('{{{{', expression_start):
                opening_end = source.find('}}}}', expression_start + 4)
                if opening_end < 0:
                    output.append(source[expression_start:])
                    break
                opening_end += 4
                opening = source[expression_start + 4 : opening_end - 4].strip()
                raw_name = opening.removeprefix('#').split(maxsplit=1)[0]
                closing = f'{{{{/{raw_name}}}}}'
                closing_start = source.find(closing, opening_end)
                if not raw_name or closing_start < 0:
                    output.append(source[expression_start:])
                    break
                raw_end = closing_start + len(closing)
                output.append(source[expression_start:raw_end])
                cursor = raw_end
                continue

            closing = '}}}' if source.startswith('{{{', expression_start) else '}}'
            expression_end = source.find(closing, expression_start + len(closing))
            if expression_end < 0:
                output.append(source[expression_start:])
                break
            expression_end += len(closing)
            output.append(source[expression_start:expression_end])
            cursor = expression_end

        return ''.join(output)

    def structural_helper(self, name: str, original: HelperFn) -> HelperFn:
        """Create a trusted wrapper for a built-in structural helper."""

        def helper(params: list[Any], options: HelperOptions) -> str:
            if name == 'history':
                return f'{self.trusted_prefix}history>>>'
            if name == 'role':
                if not params:
                    return ''
                role = self.protect_helper_value(str(params[0]))
                return f'{self.trusted_prefix}role:{role}>>>'
            if name == 'section':
                if not params:
                    return ''
                section = self.protect_helper_value(str(params[0]))
                return f'{self.trusted_prefix}section {section}>>>'
            if name == 'media':
                url = options.hash_value('url')
                if not url:
                    return ''
                url = self.protect_helper_value(str(url))
                content_type = options.hash_value('contentType')
                if content_type:
                    content_type = self.protect_helper_value(str(content_type))
                    return f'{self.trusted_prefix}media:url {url} {content_type}>>>'
                return f'{self.trusted_prefix}media:url {url}>>>'
            return original(params, options)

        return helper

    def prepare_rendered(self, rendered: str) -> tuple[str, str]:
        """Expose trusted markers and hide every untrusted marker."""
        inert_prefix = self._unique_token('rendered', [rendered, self.trusted_prefix, self.data_prefix])
        rendered = rendered.replace(STRUCTURAL_MARKER_PREFIX, inert_prefix)
        rendered = rendered.replace(self.trusted_prefix, STRUCTURAL_MARKER_PREFIX)
        return rendered, inert_prefix

    def restore_text(self, value: str, inert_prefix: str) -> str:
        """Restore marker-looking data after structural parsing."""
        return (
            value.replace(inert_prefix, STRUCTURAL_MARKER_PREFIX)
            .replace(
                self.data_prefix,
                STRUCTURAL_MARKER_PREFIX,
            )
            .replace(self.data_close, '>>>')
        )
