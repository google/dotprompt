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

"""Compile a template and render it."""

from collections.abc import Callable, Iterable
from typing import Any

from dotpromptz_handlebars._render import compile_template, render_program
from dotpromptz_handlebars._types import (
    EscapeFunction,
    HelperFn,
    Node,
    Options,
    RuntimeOptions,
)


class Handlebars:
    """Compiles and renders Handlebars templates against input context dictionaries.

    Example:
        ```python
        # 1. Initialize compiler
        hb = Handlebars()

        # 2. Compile template string
        render = hb.compile('Hello {{user.name}}!')

        # 3. Render with context
        output = render({'user': {'name': 'Ada'}})
        # => Hello Ada!
        ```
    """

    escape_html: bool
    strict: bool
    reserved_data_keys: set[str] | None
    max_depth: int
    _helpers: dict[str, HelperFn]
    _partials: dict[str, Any]
    _templates: dict[str, list[Node]]

    def __init__(
        self,
        *,
        escape_html: bool = True,
        strict: bool = False,
        escape_fn: EscapeFunction | str | None = None,
        reserved_data_keys: Iterable[str] | None = None,
        max_depth: int = 100,
    ) -> None:
        """Creates a compiler instance.

        Args:
            escape_html: When true, `{{name}}` escapes HTML. Triple braces
                `{{{name}}}` and `{{&name}}` leave markup unescaped.
            strict: When true, printing a missing path raises StrictModeError.
                A missing path passed to if, each, with, or a helper evaluates as empty.
            escape_fn: EscapeFunction.NO_ESCAPE leaves markup unescaped.
                Overrides escape_html when specified.
            reserved_data_keys: Optional set of `@data` keys (e.g. `{'root'}`) that
                raise ValueError if read by the template when present in the user data dict.
            max_depth: Maximum template recursion/nesting depth (default 100).
        """
        if escape_fn is not None:
            escape_html = escape_fn not in (EscapeFunction.NO_ESCAPE, 'no_escape')
        self.escape_html = escape_html
        self.strict = strict
        self.reserved_data_keys = set(reserved_data_keys) if reserved_data_keys else None
        self.max_depth = max_depth
        self._helpers = {}
        self._partials = {}
        self._templates = {}
        self.register_helper('lookup', _lookup_helper)
        self.register_helper('log', _log_helper)

    def register_helper(self, name: str, fn: HelperFn) -> None:
        """Registers a helper callable for template invocations.

        Args:
            name: Helper name used in tags like `{{name arg}}` or `{{#name}}`.
            fn: Callable receiving `(args, options)`:
                - `args`: List of positional argument values evaluated from the template.
                - `options`: Helper Options containing `hash`, `fn`, `inverse`, `data`,
                  and `context`.

        Example:
            ```python
            # 1. Register uppercase helper
            hb.register_helper('upper', lambda args, opt: str(args[0]).upper())

            # 2. Render helper call
            output = hb.compile('{{upper name}}')({'name': 'world'})
            # => WORLD
            ```
        """
        self._helpers[name] = fn

    def unregister_helper(self, name: str) -> None:
        """Removes a helper. Invocations like `{{name arg}}` then raise ValueError."""
        self._helpers.pop(name, None)

    def register_partial(self, name: str, source: str) -> None:
        """Registers a partial template for `{{> name}}` inclusions.

        Args:
            name: Partial name.
            source: Handlebars template source string.
        """
        self._partials[name] = source

    def unregister_partial(self, name: str) -> None:
        """Removes a partial. Subsequent `{{> name}}` calls will raise ValueError."""
        self._partials.pop(name, None)

    def has_partial(self, name: str) -> bool:
        """Returns whether a partial is registered under this name."""
        return name in self._partials

    def register_template(self, name: str, source: str) -> None:
        """Compiles and stores a named template for later calls to `render(name, context)`."""
        self._templates[name] = compile_template(source, max_depth=self.max_depth)

    def render(
        self,
        name: str,
        context: Any = None,
        options: RuntimeOptions | dict[str, Any] | None = None,
        *,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Renders the template registered under name.

        Args:
            name: The name passed to `register_template`.
            context: The input dictionary. `{{name}}` reads keys from here.
            options: Optional runtime options dict. `options['data']` is what `{{@name}}` reads.
            data: Optional `{{@name}}` data dictionary passed as a keyword argument.

        Returns:
            The rendered string.

        Raises:
            ValueError: If the template name was not registered.
        """
        program = self._templates.get(name)
        if program is None:
            raise ValueError(f'unknown template {name}')
        return self._render_program(program, context, options, data=data)

    def compile(self, source: str) -> Callable[..., str]:
        """Compiles a template string into a reusable render function.

        Args:
            source: Handlebars template string.

        Returns:
            A render callable `render(context=None, options=None, *, data=None)`
            that evaluates the compiled template into a rendered string.

        Example:
            ```python
            # 1. Compile template
            render = hb.compile('Hello {{name}}!')

            # 2. Execute render
            output = render({'name': 'World'})
            # => Hello World!
            ```
        """
        program = compile_template(source, max_depth=self.max_depth)

        def render(
            context: Any = None,
            options: RuntimeOptions | dict[str, Any] | None = None,
            *,
            data: dict[str, Any] | None = None,
        ) -> str:
            return self._render_program(program, context, options, data=data)

        return render

    def _render_program(
        self,
        program: list[Node],
        context: Any,
        options: RuntimeOptions | dict[str, Any] | None,
        *,
        data: dict[str, Any] | None,
    ) -> str:
        if data is None and isinstance(options, dict):
            data = options.get('data')
        return render_program(
            program,
            context,
            data=data,
            helpers=self._helpers,
            partials=self._partials,
            escape_html=self.escape_html,
            strict=self.strict,
            reserved_data_keys=self.reserved_data_keys,
            max_depth=self.max_depth,
        )


def _lookup_helper(args: list[Any], options: Options) -> Any:
    collection, key = (args + [None, None])[:2]
    if not collection and collection != 0:
        return collection
    if isinstance(collection, dict):
        return collection.get(key)
    if isinstance(collection, list):
        try:
            index = int(key)
        except (TypeError, ValueError):
            return None
        if 0 <= index < len(collection):
            return collection[index]
    return None


def _log_helper(args: list[Any], options: Options) -> str:
    print('[Handlebars]', *(args or ['']))
    return ''
