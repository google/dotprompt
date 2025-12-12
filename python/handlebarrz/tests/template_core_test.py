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

import pytest

from handlebarrz import HelperOptions, Template


class TemplateCoreTest(unittest.TestCase):
    def test_template_creation(self) -> None:
        """Test basic Template instantiation."""
        template = Template()
        self.assertIsNotNone(template)

    def test_template_registration(self) -> None:
        """Test template registration and validation."""
        template = Template()

        # Register a simple template
        template_str = 'Hello, {{name}}!'
        template.register_template('greeting', template_str)

        # Verify template was registered successfully
        self.assertTrue(template.has_template('greeting'))

        # Verify non-existent template
        self.assertFalse(template.has_template('nonexistent'))

    def test_simple_rendering(self) -> None:
        """Test basic template rendering."""
        template = Template()

        # Register a simple template
        template_str = 'Hello, {{name}}!'
        template.register_template('greeting', template_str)

        # Data to render
        data = {'name': 'World'}

        # Render the template
        result = template.render('greeting', data)
        self.assertEqual(result, 'Hello, World!')

    def test_rendering_nonexistent_template(self) -> None:
        """Test behavior when rendering a non-existent template."""
        template = Template()

        # Attempt to render a non-existent template
        with pytest.raises(Exception) as exc_info:
            template.render('nonexistent', {})

        # Verify error message
        self.assertIn('Template not found', str(exc_info.value))
        self.assertIn('not found', str(exc_info.value))

    def test_strict_mode(self) -> None:
        """Test strict mode behavior."""
        # Create template and enable strict mode
        template = Template()
        template.strict_mode = True

        # Register a template that uses an undefined variable
        template_str = '{{undefined_var}}'
        template.register_template('strict-test', template_str)

        # Render should raise an error in strict mode
        with pytest.raises(ValueError):
            template.render('strict-test', {})

        # Non-strict mode should not raise an error
        non_strict = Template()
        non_strict.strict_mode = False
        non_strict.register_template('non-strict-test', template_str)
        result = non_strict.render('non-strict-test', {})
        self.assertEqual(result, '')

    def test_development_mode(self) -> None:
        """Test development mode behavior."""
        import os
        import tempfile

        # Create a temporary template file
        with tempfile.NamedTemporaryFile(suffix='.hbs', delete=False) as temp_file:
            temp_file.write(b'Hello {{name}}!')
            temp_path = temp_file.name

        try:
            # Create template and enable development mode
            template = Template()
            template.dev_mode = True

            # Register the template file
            template.register_template_file('dev-test', temp_path)

            # Initial rendering
            result = template.render('dev-test', {'name': 'World'})
            self.assertEqual(result, 'Hello World!')

            # Modify the template file
            with open(temp_path, 'w') as f:
                f.write('Modified {{name}}!')

            # In dev mode, the template should be automatically reloaded
            result = template.render('dev-test', {'name': 'World'})
            self.assertEqual(result, 'Modified World!')
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    def test_nested_context(self) -> None:
        """Test accessing nested context data."""
        template = Template()

        # Register a template with nested path
        template_str = '{{person.name.first}} {{person.name.last}}'
        template.register_template('nested', template_str)

        # Data with nested structure
        data = {'person': {'name': {'first': 'John', 'last': 'Doe'}}}

        # Render the template
        result = template.render('nested', data)
        self.assertEqual(result, 'John Doe')

    def test_array_access(self) -> None:
        """Test array/list access in templates."""
        template = Template()

        # Register a template with array access
        template_str = '{{items.[0]}}, {{items.[1]}}, {{items.[2]}}'
        template.register_template('array', template_str)

        # Data with array
        data = {'items': ['apple', 'banana', 'cherry']}

        # Render the template
        result = template.render('array', data)
        self.assertEqual(result, 'apple, banana, cherry')

    def test_context_functions(self) -> None:
        """Test calling functions in the context through helpers."""
        template = Template()

        def calculate_total(params: list[str], options: HelperOptions) -> str:
            """Test helper function."""
            return '42'

        # Register the helper
        template.register_helper('calculate_total', calculate_total)

        # Register a template that calls the helper
        template_str = '{{calculate_total}}'
        template.register_template('function', template_str)

        # Render the template
        result = template.render('function', {})
        self.assertEqual(result, '42')

    def test_parent_path_access(self) -> None:
        """Test accessing parent context paths."""
        template = Template()

        # Register a template with parent path access
        template_str = """{{#with person}}{{name}} ({{../company}}){{/with}}"""
        template.register_template('parent-path', template_str)

        # Data with nested structure
        data = {'person': {'name': 'John Doe'}, 'company': 'Acme Inc'}

        # Render the template
        result = template.render('parent-path', data)
        self.assertEqual(result, 'John Doe (Acme Inc)')

    def test_each_iteration(self) -> None:
        """Test each helper with basic iteration and index."""
        template = Template()

        # Test basic iteration
        template_str = """{{#each items}}{{this}}{{/each}}"""
        template.register_template('each-basic', template_str)

        data = {'items': ['apple', 'banana', 'cherry']}

        result = template.render('each-basic', data)
        expected = 'applebananacherry'
        self.assertEqual(result, expected)

        # Test with @index
        template_str = """{{#each items}}[{{@index}}:{{this}}]{{/each}}"""
        template.register_template('each-index', template_str)

        result = template.render('each-index', data)
        expected = '[0:apple][1:banana][2:cherry]'
        self.assertEqual(result, expected)

        # Test with @last conditional
        template_str = """{{#each items}}{{this}}{{#unless @last}}, {{/unless}}{{/each}}"""
        template.register_template('each-last', template_str)

        result = template.render('each-last', data)
        expected = 'apple, banana, cherry'
        self.assertEqual(result, expected)

    def test_with_null_data(self) -> None:
        """Test rendering with null data values."""
        template = Template()

        # Register a template that handles null values
        template_str = """{{#if value}}Value: {{value}}{{else}}No value{{/if}}"""
        template.register_template('null-test', template_str)

        # Test with null value
        data_null = {'value': None}
        result_null = template.render('null-test', data_null)
        self.assertEqual(result_null, 'No value')

        # Test with actual value
        data_value = {'value': 'test'}
        result_value = template.render('null-test', data_value)
        self.assertEqual(result_value, 'Value: test')

    def test_register_multiple_templates(self) -> None:
        """Test registering and rendering multiple templates."""
        template = Template()

        # Register multiple templates
        template.register_template('t1', 'Template One: {{value}}')
        template.register_template('t2', 'Template Two: {{value}}')

        # Verify both templates exist
        self.assertTrue(template.has_template('t1'))
        self.assertTrue(template.has_template('t2'))

        # Render both templates
        data = {'value': 'Hello'}
        self.assertEqual(template.render('t1', data), 'Template One: Hello')
        self.assertEqual(template.render('t2', data), 'Template Two: Hello')
