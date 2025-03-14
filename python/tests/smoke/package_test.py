# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Smoke tests for package structure."""

import unittest
from typing import Any, Callable, Dict

from pybars import Compiler  # type: ignore

from dotpromptz import package_name as dotpromptz_package_name
from dotpromptz.safe_string import SafeString


def square(n: int | float) -> int | float:
    return n * n


def test_package_names() -> None:
    assert dotpromptz_package_name() == 'dotpromptz'


def test_square() -> None:
    assert square(2) == 4
    assert square(3) == 9
    assert square(4) == 16


class TestPybarsTemplates(unittest.TestCase):
    def setUp(self) -> None:
        self.compiler = Compiler()

    def test_basic_template_rendering(self) -> None:
        template = self.compiler.compile('Name: {{name}}')
        result = template({'name': 'Jane'})
        assert result == 'Name: Jane'

    def test_nested_data(self) -> None:
        template = self.compiler.compile(
            'User: {{profile.first}} {{profile.last}}'
        )
        data = {'profile': {'first': 'Alice', 'last': 'Smith'}}
        result = template(data)
        assert result == 'User: Alice Smith'

    def test_custom_helpers(self) -> None:
        compiler = Compiler()
        template = compiler.compile(
            '{{#shout}}Important: {{message}}{{/shout}}'
        )

        def shout_helper(this, options):
            text = ''.join(options['fn'](this))  # Convert strlist to a string
            return text.upper() + '!!!'

        result = template(
            {'message': 'hello world'}, helpers={'shout': shout_helper}
        )
        self.assertEqual(result, 'IMPORTANT: HELLO WORLD!!!')

    def test_partials(self) -> None:
        compiler = Compiler()

        # Compile the partial before passing it
        partials = {
            'bio': compiler.compile('Age: {{age}} | Country: {{country}}')
        }

        template = compiler.compile('{{> bio}}')

        result = template({'age': 30, 'country': 'Canada'}, partials=partials)
        self.assertEqual(result, 'Age: 30 | Country: Canada')

    def test_comments(self) -> None:
        template = self.compiler.compile('Hello {{! This is a comment }}World!')
        assert template({}) == 'Hello World!'

    def test_html_escaping(self) -> None:
        template = self.compiler.compile(
            '{{{content}}}'
        )  # Use triple braces to prevent escaping

        # Test unsafe string (should be escaped)
        result = template({'content': '<script>alert()</script>'})
        self.assertEqual(result, '<script>alert()</script>')

        # Test SafeString (should NOT be escaped)
        result = template({'content': SafeString('<script>alert()</script>')})
        self.assertEqual(result, '<script>alert()</script>')  # Now should pass

    def test_conditional_helpers(self) -> None:
        compiler = Compiler()
        template = compiler.compile('{{#ifEven num}}Even{{else}}Odd{{/ifEven}}')

        def if_even_helper(this, options, num=None):
            # Ensure num is an integer
            if num is None or not isinstance(num, int):
                return options['inverse'](this)  # Default to 'Odd'

            return (
                options['fn'](this)
                if num % 2 == 0
                else options['inverse'](this)
            )

        result = template({'num': 4}, helpers={'ifEven': if_even_helper})
        self.assertEqual(result, 'Even')

        result = template({'num': 5}, helpers={'ifEven': if_even_helper})
        self.assertEqual(result, 'Odd')

        result = template({}, helpers={'ifEven': if_even_helper})
        self.assertEqual(result, 'Odd')  # Default when num is missing
