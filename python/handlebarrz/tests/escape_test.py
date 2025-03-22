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

from handlebarrz import EscapeFunction, Template


class EscapeTest(unittest.TestCase):
    def test_html_escaping_default(self) -> None:
        """Test default HTML escaping behavior."""
        template = Template()

        # Register a simple template with a variable
        template_str = '{{value}}'
        template.register_template('escape-test', template_str)

        # Data with HTML characters
        data = {'value': "<script>alert('XSS');</script>"}

        # Render the template
        result = template.render('escape-test', data)

        # HTML should be escaped by default
        self.assertIn(
            '&lt;script&gt;alert(&#x27;XSS&#x27;);&lt;/script&gt;', result
        )
        self.assertNotIn('<script>', result)

    def test_triple_stache_no_escape(self) -> None:
        """Test triple mustache syntax for no escaping."""
        template = Template()

        # Register a template with triple mustache
        template_str = '{{{value}}}'
        template.register_template('no-escape', template_str)

        # Data with HTML characters
        data = {'value': '<b>Bold Text</b>'}

        # Render the template
        result = template.render('no-escape', data)

        # HTML should not be escaped with triple stache
        self.assertIn('<b>Bold Text</b>', result)
        self.assertNotIn('&lt;b&gt;', result)

    def test_ampersand_no_escape(self) -> None:
        """Test ampersand syntax for no escaping."""
        template = Template()

        # Register a template with ampersand syntax
        template_str = '{{&value}}'
        template.register_template('ampersand-no-escape', template_str)

        # Data with HTML characters
        data = {'value': '<i>Italic Text</i>'}

        # Render the template
        result = template.render('ampersand-no-escape', data)

        # HTML should not be escaped with ampersand
        self.assertIn('<i>Italic Text</i>', result)
        self.assertNotIn('&lt;i&gt;', result)

    def test_set_escape_function(self) -> None:
        """Test setting a custom escape function."""
        template = Template()

        # Set escape function to no_escape
        template.set_escape_function(EscapeFunction.NO_ESCAPE)

        # Register a template with regular mustache
        template_str = '{{value}}'
        template.register_template('custom-escape', template_str)

        # Data with HTML characters
        data = {'value': '<div>Content</div>'}

        # Render the template
        result = template.render('custom-escape', data)

        # HTML should not be escaped because of the custom setting
        self.assertIn('<div>Content</div>', result)
        self.assertNotIn('&lt;div&gt;', result)

    def test_escape_in_attributes(self) -> None:
        """Test escaping in HTML attributes."""
        template = Template()

        # Register a template with an attribute
        template_str = '<a href="{{url}}" title="{{title}}">{{text}}</a>'
        template.register_template('attr-escape', template_str)

        # Data with special characters
        data = {
            'url': 'https://example.com?q=1&s=2',
            'title': 'Title with "quotes"',
            'text': 'Link Text',
        }

        # Render the template
        result = template.render('attr-escape', data)

        # Special characters in attributes should be properly escaped
        # The actual encoding uses &#x3D; for = signs
        self.assertIn('q&#x3D;1&amp;s&#x3D;2', result)
        self.assertIn('&quot;quotes&quot;', result)
        self.assertIn('>Link Text<', result)

    def test_safe_string(self) -> None:
        """Test safe string handling with a helper."""
        template = Template()

        # Define a helper that returns a safe string
        def safe_html_helper(
            params: list[str],
            hash_args: dict[str, str],
            context: dict[str, Any],
        ) -> str:
            if params:
                # Marked as safe, should not be escaped
                return f'<span class="safe">{params[0]}</span>'
            return ''

        # Register the helper
        template.register_helper('safe_html', safe_html_helper)

        # Register a template that uses the safe HTML helper
        template_str = '{{safe_html value}}'
        template.register_template('safe-string-test', template_str)

        # Data to render
        data = {'value': 'Test Content'}

        # Render the template
        result = template.render('safe-string-test', data)

        # Helper output should be rendered without escaping
        self.assertIn('<span class="safe">Test Content</span>', result)
