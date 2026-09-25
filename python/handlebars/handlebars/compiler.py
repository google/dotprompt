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

from handlebars._render import compile_template, render_program

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

    def __init__(self, *, hash, fn, inverse, data, context):
        """Stores the hash args, block bodies, and the data frame.

        Args:
            hash: Named arguments from the helper call.
            fn: Renders the block body.
            inverse: Renders the else body.
            data: The frame `{{@name}}` reads.
            context: The current input scope.
        """
        self.hash = hash
        self.fn = fn
        self.inverse = inverse
        self.data = data
        self.context = context

    def hash_value(self, key):
        """Returns a named argument, or '' when the helper call omitted it."""
        if key not in self.hash:
            return ''
        value = self.hash[key]
        return '' if value is None else value


HelperFn = Callable[[list[Any], Options], Any]
HelperOptions = Options


class Handlebars:
    """Compiles a template and renders it with an input dict."""

    def __init__(self, *, escape_html=True, strict=False, escape_fn=None):
        """Creates a compiler.

        Args:
            escape_html: When true, `{{name}}` escapes HTML. Triple braces
                and `{{&name}}` still leave markup as written.
            strict: When true, a missing path raises StrictModeError.
            escape_fn: EscapeFunction.NO_ESCAPE leaves markup as written.
                This wins over escape_html.
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

    def register_helper(self, name, fn):
        """Registers a helper the template can call by name."""
        self._helpers[name] = fn

    def unregister_helper(self, name):
        """Removes a helper. A later call to that name renders nothing."""
        self._helpers.pop(name, None)

    def register_partial(self, name, source):
        """Registers a partial template. {{> name}} renders it."""
        self._partials[name] = source

    def unregister_partial(self, name):
        """Removes a partial. {{> name}} then renders nothing."""
        self._partials.pop(name, None)

    def has_partial(self, name):
        """Returns whether register_partial was called for this name."""
        return name in self._partials

    def register_template(self, name, source):
        """Stores a named template so render(name, context) can fill it in."""
        self._templates[name] = compile_template(source)

    def render(self, name, context=None, options=None, *, data=None):
        """Renders the template registered under name.

        Args:
            name: The name passed to register_template.
            context: The input dict. {{name}} reads keys from here.
            options: A runtime options dict. options['data'] is what {{@name}} reads.
            data: The same {{@name}} dict, when passed as a keyword.

        Returns:
            The rendered string.

        Raises:
            ValueError: The name was never registered.
        """
        program = self._templates.get(name)
        if program is None:
            raise ValueError(f'unknown template {name}')
        return self._render_program(program, context, options, data=data)

    def compile(self, source):
        """Returns a function that renders this template."""
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
    if isinstance(collection, dict):
        return collection.get(key, '')
    if isinstance(collection, list):
        try:
            index = int(key)
        except (TypeError, ValueError):
            return ''
        if 0 <= index < len(collection):
            return collection[index]
    return ''


def _log_helper(args, options):
    print('[Handlebars]', *(args or ['']))
    return ''
