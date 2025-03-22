# Copyright 2025 Google LLC
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

import unittest
from typing import Any

from handlebarrz import Template


class HelpersTest(unittest.TestCase):
    def test_basic_helper(self) -> None:
        """Test basic helper function."""
        template = Template()

        # Define a simple helper that uppercases a string
        def uppercase_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            if params:
                return params[0].upper()
            return ''

        # Register the helper
        template.register_helper('uppercase', uppercase_helper)

        # Register a template that uses the helper
        template_str = '{{uppercase name}}'
        template.register_template('helper-test', template_str)

        # Data to render
        data = {'name': 'john'}

        # Render the template
        result = template.render('helper-test', data)
        self.assertEqual(result, 'JOHN')

    def test_helper_with_hash_args(self) -> None:
        """Test helper with hash arguments."""
        template = Template()

        # Define a helper that formats text
        def format_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            text = params[0] if params else ''
            prefix = hash_args.get('prefix', '')
            suffix = hash_args.get('suffix', '')
            return f'{prefix}{text}{suffix}'

        # Register the helper
        template.register_helper('format', format_helper)

        # Register a template that uses the helper with hash arguments
        template_str = '{{format name prefix="Hello, " suffix="!"}}'
        template.register_template('format-test', template_str)

        # Data to render
        data = {'name': 'John'}

        # Render the template
        result = template.render('format-test', data)
        self.assertEqual(result, 'Hello, John!')

    def test_helper_with_context(self) -> None:
        """Test helper that uses the current context."""
        template = Template()

        # Define a helper that creates a list from context
        def list_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            prefix = hash_args.get('prefix', '')
            result = []
            if 'items' in context:
                items = context['items']
                for item in items:
                    result.append(f'{prefix}{item}')
            return ', '.join(result)

        # Register the helper
        template.register_helper('list', list_helper)

        # Register a template that uses the helper
        template_str = '{{list prefix="Item: "}}'
        template.register_template('list-test', template_str)

        # Data to render
        data = {'items': ['apple', 'banana', 'orange']}

        # Render the template
        result = template.render('list-test', data)
        self.assertEqual(result, 'Item: apple, Item: banana, Item: orange')

    def test_block_helper_implementation(self) -> None:
        """Test implementation of a custom block helper."""
        template = Template()

        # Define a block helper for creating lists
        def list_block_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            if not params:
                return ''

            list_type = hash_args.get('type', 'ul')
            items = params[0]

            if list_type == 'ul':
                return f'<ul>{items}</ul>'
            elif list_type == 'ol':
                return f'<ol>{items}</ol>'
            else:
                return items

        # Register the helper
        template.register_helper('list_block', list_block_helper)

        # Register a template that uses the helper more directly
        template_str = """
        {{#each items as |item|}}
            {{list_block (concat "<li>" item "</li>") type="ul"}}
        {{/each}}
        """

        # Register a concat helper to create the item HTML
        def concat_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            return ''.join([str(p) for p in params])

        template.register_helper('concat', concat_helper)

        template.register_template('list-block-test', template_str)

        # Data to render
        data = {'items': ['apple', 'banana', 'orange']}

        # Render the template
        result = template.render('list-block-test', data)

        # Check that each list item is in the result
        self.assertIn('<ul><li>apple</li></ul>', result)
        self.assertIn('<ul><li>banana</li></ul>', result)
        self.assertIn('<ul><li>orange</li></ul>', result)

    def test_subexpression(self) -> None:
        """Test subexpressions in helpers."""
        template = Template()

        # Define helpers for testing subexpressions
        def add_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            if len(params) >= 2:
                try:
                    # Return result as string
                    return str(int(params[0]) + int(params[1]))
                except (ValueError, TypeError):
                    return '0'
            return '0'

        def multiply_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            if len(params) >= 2:
                try:
                    # Return result as string
                    return str(int(params[0]) * int(params[1]))
                except (ValueError, TypeError):
                    return '0'
            return '0'

        # Register the helpers
        template.register_helper('add', add_helper)
        template.register_helper('multiply', multiply_helper)

        # Register a template with nested subexpressions
        template_str = '{{multiply (add 2 3) 4}}'
        template.register_template('subexpr-test', template_str)

        # Render the template
        result = template.render('subexpr-test', {})

        # 2 + 3 = 5, 5 * 4 = 20
        self.assertEqual(result, '20')

    def test_helper_with_escaped_values(self) -> None:
        """Test helper that handles HTML escaping."""
        template = Template()

        # Define a helper that doesn't escape HTML
        def html_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            if params:
                return params[0]
            return ''

        # Register the helper
        template.register_helper('html', html_helper)

        # Register templates with and without the helper
        template.register_template('escaped', '{{value}}')
        template.register_template('helper-escaped', '{{html value}}')

        # Data with HTML content
        data = {'value': "<script>alert('test');</script>"}

        # Regular template should escape HTML
        result_escaped = template.render('escaped', data)
        # The helper should output exactly what it's given
        result_helper = template.render('helper-escaped', data)

        self.assertIn(
            '&lt;script&gt;alert(&#x27;test&#x27;);&lt;/script&gt;',
            result_escaped,
        )
        self.assertIn(
            "<script>alert('test');</script>",
            result_helper,
        )
