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

from collections.abc import Callable
from enum import Enum
from typing import Any, TypedDict

from dotpromptz_handlebars._render import compile_template, render_program

Context = dict[str, Any]


class RuntimeOptions(TypedDict, total=False):
    """The second argument to a compiled template."""

    data: dict[str, Any] | None


class EscapeFunction(str, Enum):
    """How {{name}} treats characters like < and &."""

    HTML_ESCAPE = 'html_escape'
    NO_ESCAPE = 'no_escape'


class SafeString(str):
    """A helper return value that is inserted as-is."""


class Options:
    """What a helper receives besides its positional arguments."""

    def __init__(self, *, hash, fn, inverse, data, context, is_block=False):
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
        self.context = context
        self.is_block = is_block

    def hash_value(self, key):
        """Returns a named argument, or '' when the helper call omitted it."""
        if key not in self.hash:
            return ''
        value = self.hash[key]
        return '' if value is None else value


HelperFn = Callable[[list[Any], Options], Any]
HelperOptions = Options


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

    def __init__(self, *, escape_html=True, strict=False, escape_fn=None):
        """Creates a compiler instance.

        Args:
            escape_html: When true, `{{name}}` escapes HTML. Triple braces
                `{{{name}}}` and `{{&name}}` leave markup unescaped.
            strict: When true, printing a missing path raises StrictModeError.
                A missing path passed to if, each, with, or a helper evaluates as empty.
            escape_fn: EscapeFunction.NO_ESCAPE leaves markup unescaped.
                Overrides escape_html when specified.
        """
        if escape_fn is not None:
            escape_html = escape_fn not in (EscapeFunction.NO_ESCAPE, 'no_escape')
        self.escape_html = escape_html
        self.strict = strict
        self._helpers = {}
        self._partials = {}
        self._templates = {}
        self.register_helper('lookup', _lookup_helper)
        self.register_helper('log', _log_helper)
        self.register_helper('raw', _raw_helper)

    def register_helper(self, name, fn):
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

    def unregister_helper(self, name):
        """Removes a helper. Invocations like `{{name arg}}` then raise ValueError."""
        self._helpers.pop(name, None)

    def register_partial(self, name, source):
        """Registers a partial template for `{{> name}}` inclusions.

        Args:
            name: Partial name.
            source: Handlebars template source string.
        """
        self._partials[name] = source

    def unregister_partial(self, name):
        """Removes a partial. Subsequent `{{> name}}` calls will raise ValueError."""
        self._partials.pop(name, None)

    def has_partial(self, name):
        """Returns whether a partial is registered under this name."""
        return name in self._partials

    def register_template(self, name, source):
        """Compiles and stores a named template for later calls to `render(name, context)`."""
        self._templates[name] = compile_template(source)

    def render(self, name, context=None, options=None, *, data=None):
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

    def compile(self, source):
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
        program = compile_template(source)

        def render(context=None, options=None, *, data=None):
            return self._render_program(program, context, options, data=data)

        return render

    def _render_program(self, program, context, options, *, data):
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
        )


def _lookup_helper(args, options):
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


def _log_helper(args, options):
    print('[Handlebars]', *(args or ['']))
    return ''


def _raw_helper(args, options):
    return options.fn()
