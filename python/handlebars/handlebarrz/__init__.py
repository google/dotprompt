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

"""Compatibility shim for already-published dotpromptz 0.1.x releases.

`dotpromptz==0.1.6` on PyPI depends on `dotpromptz-handlebars>=0.1.8` without
an upper bound and imports `from handlebarrz import Handlebars`. This shim keeps
those legacy installations working.

Remove this shim in a future stable release (e.g. 1.0.0) after users have had
sufficient time to upgrade to `dotpromptz>=0.2.0`.
"""

from dotpromptz_handlebars import (
    Block,
    BlockFn,
    Context,
    ContextDict,
    ElseNode,
    EscapeFunction,
    Handlebars,
    HelperFn,
    HelperOptions,
    InlinePartial,
    Mustache,
    Node,
    Partial,
    PartialBlock,
    Program,
    RuntimeOptions,
    SafeString,
    StrictModeError,
    TagToken,
    TemplateRecursionError,
    Text,
)
from dotpromptz_handlebars._render import _ESCAPE

# Backward-compatibility aliases previously exported by native handlebarrz
Template = Handlebars


def html_escape(text: str) -> str:
    """Escape HTML characters matching Handlebars.js escaping rules."""
    return text.translate(_ESCAPE)


def no_escape(text: str) -> str:
    """Return text without escaping."""
    return text


def create_helper(fn: HelperFn) -> HelperFn:
    """Identity wrapper for backward compatibility with Rust helper creator."""
    return fn


def package_name() -> str:
    """Return the package name for smoke testing."""
    return 'handlebarrz'


__all__ = [
    'Block',
    'BlockFn',
    'Context',
    'ContextDict',
    'ElseNode',
    'EscapeFunction',
    'Handlebars',
    'HelperFn',
    'HelperOptions',
    'InlinePartial',
    'Mustache',
    'Node',
    'Partial',
    'PartialBlock',
    'Program',
    'RuntimeOptions',
    'SafeString',
    'StrictModeError',
    'TagToken',
    'Template',
    'TemplateRecursionError',
    'Text',
    'create_helper',
    'html_escape',
    'no_escape',
    'package_name',
]
