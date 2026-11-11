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

`dotpromptz<=0.1.6` runs `from handlebarrz import Handlebars` and depends on
`dotpromptz-handlebars>=0.1.8` with no upper bound, so a fresh install of one of
those releases gets the newest dotpromptz-handlebars. Without this module it
crashes with `ModuleNotFoundError: No module named 'handlebarrz'`. Those
releases never stop pulling the newest wheel, so this stays for all of 1.x.
"""

from dotpromptz_handlebars import (
    BlockFn,
    Context,
    ContextDict,
    EscapeFunction,
    Handlebars,
    HelperFn,
    HelperOptions,
    RuntimeOptions,
    SafeString,
    StrictModeError,
    TemplateRecursionError,
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
    'BlockFn',
    'Context',
    'ContextDict',
    'EscapeFunction',
    'Handlebars',
    'HelperFn',
    'HelperOptions',
    'RuntimeOptions',
    'SafeString',
    'StrictModeError',
    'Template',
    'TemplateRecursionError',
    'create_helper',
    'html_escape',
    'no_escape',
    'package_name',
]
