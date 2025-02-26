# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Smoke tests for package structure."""

import unittest

import js2py
from handlebars import Handlebars  # type:ignore

# TODO: Replace this with proper imports once we have a proper implementation.
from dotpromptz import package_name as dotpromptz_package_name


def square(n: int | float) -> int | float:
    return n * n


def test_package_names() -> None:
    assert dotpromptz_package_name() == "dotpromptz"


# TODO: Failing test on purpose to be removed after we complete
# this runtime and stop skipping all failures.
# def test_skip_failures() -> None:
#    assert dotpromptz_package_name() == 'skip.failures'


def test_square() -> None:
    assert square(2) == 4
    assert square(3) == 9
    assert square(4) == 16


class TestDependencies(unittest.TestCase):
    def test_js2py_basic_functionality(self) -> None:
        """Test basic functionality of js2py."""
        # Simple JavaScript code to be executed
        js_code = "function add(a, b) { return a + b; }"
        # Create a JavaScript context
        context = js2py.EvalJs()
        # Execute the JavaScript code
        context.execute(js_code)
        # Call the JavaScript function and check the output
        result = context.add(3, 4)
        assert result == 7, "Expected result is 7"

    def test_js2py_variable_handling(self) -> None:
        """Test JavaScript variable assignment and access."""
        js_code = 'let greeting = "Hello, World!";'
        context = js2py.EvalJs()
        context.execute(js_code)
        assert context.greeting == "Hello, World!", "Variable value mismatch"

    def test_template_rendering(self) -> None:
        template = Handlebars.compile("Name: {{name}}")
        result = template({"name": "Jane"})
        assert result == "Name: Jane"

    def test_template_nested_data(self) -> None:
        """Test template rendering with nested data structures."""
        template = Handlebars.compile("User: {{profile.first}} {{profile.last}}")
        data = {"profile": {"first": "Alice", "last": "Smith"}}
        result = template(data)
        assert result == "User: Alice Smith", "Nested data rendering failed"

    def test_handlebars_helpers(self) -> None:
        """Test custom helper functions."""
        # Create JS helper using arguments to capture options
        helper_js = js2py.eval_js(
            """
            function() {
                // Get options from last argument
                var options = arguments[arguments.length - 1];
                // Use current context (this) and options.fn
                return options.fn(this).toUpperCase() + '!!!';
            }
        """
        )

        # Register helper
        Handlebars.registerHelper("shout", helper_js)

        # Compile and test template
        template = Handlebars.compile("{{#shout}}Important: {{message}}{{/shout}}")
        result = template({"message": "hello world"})
        self.assertEqual(result, "IMPORTANT: HELLO WORLD!!!")

    def test_handlebars_partials(self) -> None:
        """Test template partials inclusion."""
        # Register the partial directly using the Handlebars JS object
        Handlebars.registerPartial("bio", "Age: {{age}} | Country: {{country}}")

        # Compile and test the template
        template = Handlebars.compile("{{> bio}}")
        result = template({"age": 30, "country": "Canada"})
        self.assertEqual(result, "Age: 30 | Country: Canada")

    def test_handlebars_comments(self) -> None:
        """Test template comments handling."""
        template = Handlebars.compile("Hello {{! This is a comment }}World!")
        assert template({}) == "Hello World!"

    def test_handlebars_html_escape(self) -> None:
        """Test automatic HTML escaping."""
        template = Handlebars.compile("{{content}}")
        result = template({"content": "<script>alert()</script>"})
        assert result == "&lt;script&gt;alert()&lt;/script&gt;"
