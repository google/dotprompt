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

"""Handlebars the way a .prompt calls it.

compile(template) returns a function. Call it with the input dict.
Pass data= for {{@name}} values. Escaping is on unless you turn it off.
"""

from handlebars._render import StrictModeError, compile_template


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


class Handlebars:
    """Compiles a template and renders it with an input dict."""

    def __init__(self, *, escape_html=True, strict=False):
        """Creates a compiler.

        Args:
            escape_html: When true, `{{name}}` escapes HTML. Triple braces
                and `{{&name}}` still leave markup as written.
            strict: When true, a missing path raises StrictModeError.
        """
        self.escape_html = escape_html
        self.strict = strict
        self._helpers = {}
        self._partials = {}
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

    def compile(self, source):
        """Returns a function that renders this template."""
        program = compile_template(source)

        def render(context=None, *, data=None):
            from handlebars._render import render_program

            return render_program(
                program,
                context,
                data=data,
                helpers=self._helpers,
                partials=self._partials,
                escape_html=self.escape_html,
                strict=self.strict,
            )

        return render


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


__all__ = ['Handlebars', 'Options', 'SafeString', 'StrictModeError']
