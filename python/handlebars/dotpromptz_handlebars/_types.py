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

"""Type definitions and data structures for Handlebars."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, TypedDict

Context = dict[str, Any]


@dataclass(slots=True)
class TagToken:
    """A Handlebars mustache tag token discovered during scanning."""

    body: str
    triple: bool = False
    strip_before: bool = False
    strip_after: bool = False
    indent: str = ''
    raw_block: bool = False


@dataclass(slots=True)
class Text:
    """Characters copied into the output unchanged."""

    value: str


@dataclass(slots=True)
class Mustache:
    """A {{name}} or {{{name}}} tag."""

    call: dict[str, Any]
    raw: bool = False


@dataclass(slots=True)
class Block:
    """A {{#name}} body and its else body."""

    call: dict[str, Any]
    body: list['Node']
    inverse: list['Node']


@dataclass(slots=True)
class Partial:
    """A {{> name}} inclusion."""

    name: str
    context_path: str | None
    hash: dict[str, Any] = field(default_factory=dict)
    indent: str = ''


@dataclass(slots=True)
class PartialBlock:
    """A {{#> name}} block. The body renders when the partial is missing."""

    name: str
    body: list['Node']
    context_path: str | None = None
    hash: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class InlinePartial:
    """A partial defined inside the template with {{#*inline}}."""

    name: str
    body: list['Node']


@dataclass(slots=True)
class ElseNode:
    """An {{else}} branch holding the inverse body until folded into the parent block."""

    body: list['Node']


Node = Text | Mustache | Block | Partial | PartialBlock | InlinePartial | ElseNode
Program = list[Node]
Token = TagToken | str


class RuntimeOptions(TypedDict, total=False):
    """The second argument to a compiled template."""

    data: dict[str, Any] | None


class EscapeFunction(str, Enum):
    """How {{name}} treats characters like < and &."""

    HTML_ESCAPE = 'html_escape'
    NO_ESCAPE = 'no_escape'


class SafeString(str):
    """A helper return value that is inserted as-is."""


class TemplateRecursionError(RecursionError, ValueError):
    """Raised when template nesting or recursive partials exceed the maximum depth."""


class BlockFn(Protocol):
    """Callable for rendering a block body or inverse body."""

    def __call__(self, context: Any | None = None) -> SafeString:
        """Render the block body with the given context."""
        ...


class ContextDict(dict[str, Any]):
    """Context dictionary supporting backward-compatible __call__ for legacy helpers."""

    def __call__(self) -> dict[str, Any]:
        """Return self for backward compatibility with handlebarrz options.context()."""
        return self


class Options:
    """What a helper receives besides its positional arguments."""

    hash: dict[str, Any]
    fn: BlockFn
    inverse: BlockFn
    data: dict[str, Any]
    context: Any
    is_block: bool

    def __init__(
        self,
        *,
        hash: dict[str, Any],
        fn: BlockFn,
        inverse: BlockFn,
        data: dict[str, Any],
        context: Any,
        is_block: bool = False,
    ) -> None:
        """Stores the hash args, block bodies, and the data frame.

        Args:
            hash: Named arguments from the helper call.
            fn: Renders the block body.
            inverse: Renders the else body.
            data: The frame `{{@name}}` reads.
            context: The current input scope.
            is_block: True when the helper is the {{#name}} form, so it can
                render fn or inverse. An inline call leaves this false.
        """
        self.hash = hash
        self.fn = fn
        self.inverse = inverse
        self.data = data
        self.context = ContextDict(context) if isinstance(context, Mapping) else context
        self.is_block = is_block

    def hash_value(self, key: str) -> Any:
        """Returns a named argument, or '' when the helper call omitted it."""
        if key not in self.hash:
            return ''
        value = self.hash[key]
        return '' if value is None else value


HelperFn = Callable[[list[Any], Options], Any]
HelperOptions = Options
