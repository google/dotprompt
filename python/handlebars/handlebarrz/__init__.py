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

"""Backward-compatibility shim for already-published dotpromptz<=0.1.6 and genkit<=0.12.0.

Why this shim exists:
1. `genkit<=0.12.0` on PyPI depends on `dotpromptz>=0.1.6,<0.2.0`.
2. `dotpromptz==0.1.6` on PyPI depends on `dotpromptz-handlebars>=0.1.8` without an
   upper bound, and internally runs `from handlebarrz import Handlebars`.
3. When `dotpromptz-handlebars 0.2.0` is released, any fresh install of `genkit<=0.12.0`
   will resolve to `dotpromptz-handlebars 0.2.0`. Without this `handlebarrz` alias module,
   all existing `genkit<=0.12.0` installations crash with `ModuleNotFoundError: No module named 'handlebarrz'`.

Deprecation & Removal lifecycle:
- In Genkit 0.13.0, Genkit will update its dependency to `dotpromptz>=0.2.0,<0.3.0`
  (which imports from `dotpromptz_handlebars`).
- Once Genkit 0.13.0 has soaked in production and users have migrated off `genkit<=0.12.0`,
  this `handlebarrz` alias package can be safely deleted in `dotpromptz-handlebars>=0.3.0`.
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
