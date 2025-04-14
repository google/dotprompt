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


class PartialsTest(unittest.TestCase):
    def test_basic_partial(self) -> None:
        """Test basic partial template inclusion."""
        template = Template()

        # Register a partial template
        template.register_partial('user', '{{name}} ({{title}})')

        # Register a template that uses the partial
        template_str = 'User: {{> user}}'
        template.register_template('partial-test', template_str)

        # Data to render
        data = {'name': 'John Doe', 'title': 'Developer'}

        # Render the template
        result = template.render('partial-test', data)
        self.assertEqual(result, 'User: John Doe (Developer)')

    def test_partial_with_context(self) -> None:
        """Test partial with specific context."""
        template = Template()

        # Register a partial template
        template.register_partial('person', '{{name}} ({{occupation}})')

        # Register a template that uses the partial with a different context.
        template_str = '{{#each people}}{{> person}}{{#unless @last}}, {{/unless}}{{/each}}'
        template.register_template('people-list', template_str)

        # Data to render
        data = {
            'people': [
                {'name': 'John', 'occupation': 'Developer'},
                {'name': 'Jane', 'occupation': 'Designer'},
                {'name': 'Bob', 'occupation': 'Manager'},
            ]
        }

        # Render the template
        result = template.render('people-list', data)
        self.assertEqual(result, 'John (Developer), Jane (Designer), Bob (Manager)')

    def test_partial_with_parameter(self) -> None:
        """Test partial with parameters."""
        template = Template()

        # Register a partial template
        template.register_partial('formatted', '{{text}} ({{format}})')

        # Register a template that uses the partial with parameters
        template_str = '{{> formatted text="Hello" format="greeting"}}'
        template.register_template('param-partial', template_str)

        # Data to render
        data: dict[str, Any] = {}

        # Render the template
        result = template.render('param-partial', data)
        self.assertEqual(result, 'Hello (greeting)')

    def test_nested_partials(self) -> None:
        """Test nested partial templates."""
        template = Template()

        # Register nested partials
        template.register_partial('wrapper', '<div>{{> content}}</div>')
        template.register_partial('content', '<span>{{message}}</span>')

        # Register a template that uses nested partials
        template_str = '{{> wrapper}}'
        template.register_template('nested-partial', template_str)

        # Data to render
        data = {'message': 'Hello, World!'}

        # Render the template
        result = template.render('nested-partial', data)
        self.assertEqual(result, '<div><span>Hello, World!</span></div>')

    def test_inline_partials(self) -> None:
        """Test inline partial definitions."""
        template = Template()

        # Register a template with inline partial definitions
        template_str = """
        {{#*inline "header"}}
        <header>{{title}}</header>
        {{/inline}}

        {{#*inline "footer"}}
        <footer>{{copyright}}</footer>
        {{/inline}}

        <div class="page">
            {{> header}}
            <main>{{content}}</main>
            {{> footer}}
        </div>
        """
        template.register_template('inline-partial', template_str)

        # Data to render
        data = {
            'title': 'My Page',
            'content': 'Page content goes here',
            'copyright': '© 2025',
        }

        # Render the template and normalize whitespace for comparison
        result = ''.join(template.render('inline-partial', data).split())
        expected = ''.join(
            """
        <div class="page">
            <header>My Page</header>
            <main>Page content goes here</main>
            <footer>© 2025</footer>
        </div>
        """.split()
        )

        self.assertEqual(result, expected)

    def test_partial_blocks(self) -> None:
        """Test partial blocks with fallback content."""
        template = Template()

        # Register a partial
        template.register_partial('item', '<item>{{> @partial-block}}</item>')

        # Register a template that uses partial block
        template_str = """
        {{#> item}}
            Default content
        {{/item}}
        """
        template.register_template('partial-block', template_str)

        # Data to render
        data: dict[str, Any] = {}

        # Render the template and normalize whitespace
        result = ''.join(template.render('partial-block', data).split())
        expected = '<item>Defaultcontent</item>'

        self.assertEqual(result, expected)

    def test_dynamic_partials(self) -> None:
        """Test dynamically selected partials."""
        template = Template()

        # Register different partial templates
        template.register_partial('user', 'User: {{name}}')
        template.register_partial('admin', 'Admin: {{name}} ({{role}})')

        # Register a template that dynamically selects partials
        template_str = '{{> (lookup_partial userType) }}'
        template.register_template('dynamic-partial', template_str)

        # Helper to dynamically select a partial name
        def lookup_partial_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            partial_type = params[0] if params else 'user'
            return partial_type

        # Register the helper
        template.register_helper('lookup_partial', lookup_partial_helper)

        # Test with user data
        user_data = {'userType': 'user', 'name': 'John Doe'}
        user_result = template.render('dynamic-partial', user_data)
        self.assertEqual(user_result, 'User: John Doe')

        # Test with admin data
        admin_data = {
            'userType': 'admin',
            'name': 'Jane Smith',
            'role': 'Super Admin',
        }
        admin_result = template.render('dynamic-partial', admin_data)
        self.assertEqual(admin_result, 'Admin: Jane Smith (Super Admin)')

    def test_has_partial_exists(self) -> None:
        """Test has_partial returns True for an existing partial."""
        template = Template()
        template.register_partial('my_partial', 'Partial content')
        self.assertTrue(template.has_partial('my_partial'))

    def test_has_partial_not_exists(self) -> None:
        """Test has_partial returns False for a non-existent partial."""
        template = Template()
        self.assertFalse(template.has_partial('non_existent_partial'))


if __name__ == '__main__':
    unittest.main()
