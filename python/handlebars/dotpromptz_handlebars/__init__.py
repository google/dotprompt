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

"""A pure Python Handlebars template engine."""

from dotpromptz_handlebars._compiler import (
    EscapeFunction,
    Handlebars,
    HelperFn,
    RuntimeOptions,
)
from dotpromptz_handlebars._render import StrictModeError
from dotpromptz_handlebars._types import (
    Block,
    BlockFn,
    Context,
    ContextDict,
    ElseNode,
    HelperOptions,
    InlinePartial,
    Mustache,
    Node,
    Partial,
    PartialBlock,
    Program,
    SafeString,
    TagToken,
    TemplateRecursionError,
    Text,
)

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
    'TemplateRecursionError',
    'Text',
]
