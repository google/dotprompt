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

"""Tests for what the legacy star-import shims (`dotpromptz.parse`, ...) expose.

The shims do `from dotpromptz._x import *`, so whatever `_x` exports becomes
importable from the legacy path. These tests pin that surface: the marker
internals in `dotpromptz._markers` must not leak, and the names that were
public before the marker nonce change must stay importable.
"""

import importlib
from types import ModuleType

import pytest

from dotpromptz import _helpers, _markers, _parse

SHIMS = [
    'dotpromptz.dotprompt',
    'dotpromptz.errors',
    'dotpromptz.helpers',
    'dotpromptz.parse',
    'dotpromptz.picoschema',
    'dotpromptz.resolvers',
    'dotpromptz.typing',
    'dotpromptz.util',
]

PARSE_PUBLIC = [
    'DELIMITER_REGEX',
    'FRONTMATTER_AND_BODY_REGEX',
    'LINE_BREAK_REGEX',
    'RESERVED_METADATA_KEYWORDS',
    'FrontmatterSource',
    'MessageSource',
    'RestrictedFrontmatterLoader',
    'convert_namespaced_entry_to_nested_object',
    'extract_frontmatter_and_body',
    'frontmatter_error',
    'identify_frontmatter',
    'insert_history',
    'message_sources_to_messages',
    'messages_have_history',
    'node_at_location',
    'parse_document',
    'parse_media_part',
    'parse_part',
    'parse_section_part',
    'parse_text_part',
    'to_messages',
    'to_parts',
    'transform_messages_to_history',
]

HELPERS_PUBLIC = [
    'BUILTIN_HELPERS',
    'history_helper',
    'if_equals_helper',
    'json_helper',
    'media_helper',
    'register_all_helpers',
    'role_helper',
    'section_helper',
    'unless_equals_helper',
]


def _shim(name: str) -> ModuleType:
    return importlib.import_module(name)


def test_markers_all_lists_every_public_name_it_defines() -> None:
    # Guards the leak test below: a new `_markers` name must be added to
    # `__all__` to be checked. Imported names (modules, `dataclass`, ...) are
    # skipped; values without `__module__` (constants) count as defined here.
    defined = {
        name
        for name, value in vars(_markers).items()
        if not name.startswith('_')
        and not isinstance(value, ModuleType)
        and getattr(value, '__module__', _markers.__name__) == _markers.__name__
    }
    # `Piece` is a union type alias, whose `__module__` is `types`.
    assert defined | {'Piece'} == set(_markers.__all__)


@pytest.mark.parametrize('shim', SHIMS)
@pytest.mark.parametrize('name', _markers.__all__)
def test_shims_do_not_expose_marker_internals(shim: str, name: str) -> None:
    # `from <shim> import <name>` is a getattr on the shim module (there are no
    # submodules with these names), so this is the importability check.
    assert not hasattr(_shim(shim), name)


@pytest.mark.parametrize('name', PARSE_PUBLIC)
def test_parse_shim_still_exposes_public_names(name: str) -> None:
    assert getattr(_shim('dotpromptz.parse'), name) is getattr(_parse, name)


@pytest.mark.parametrize('name', HELPERS_PUBLIC)
def test_helpers_shim_still_exposes_public_names(name: str) -> None:
    assert getattr(_shim('dotpromptz.helpers'), name) is getattr(_helpers, name)


def test_dotprompt_shim_still_exposes_dotprompt() -> None:
    from dotpromptz._dotprompt import Dotprompt

    assert _shim('dotpromptz.dotprompt').Dotprompt is Dotprompt
