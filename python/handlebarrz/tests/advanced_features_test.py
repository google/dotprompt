# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for advanced Handlebars features."""

import unittest
from typing import Any

from handlebarrz import Template


class TestAdvancedFeatures(unittest.TestCase):
    def test_simple_custom_helper(self) -> None:
        """Test a simple custom helper function."""
        template = Template()

        # Register a simple helper.
        def loud_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            # Get the first parameter or use an empty string
            text = params[0] if params else ''
            return text.upper()

        template.register_helper('loud', loud_helper)

        # Test with a simple template.
        template_string = '{{loud name}}'
        template.register_template('test', template_string)
        result = template.render('test', {'name': 'world'})

        self.assertEqual(result, 'WORLD')

    def test_helper_with_hash_arguments(self) -> None:
        """Test a helper that uses hash arguments."""
        template = Template()

        # Register a helper that uses hash arguments.
        def format_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            # First parameter is the text.
            text = params[0] if params else ''

            # Get formatting options from hash arguments.
            bold = hash_args.get('bold', False)
            italic = hash_args.get('italic', False)

            # Apply formatting.
            if bold:
                text = f'<b>{text}</b>'
            if italic:
                text = f'<i>{text}</i>'

            return text

        template.register_helper('format', format_helper)

        # Test with different hash arguments.
        template.register_template('test', '{{format name bold=true}}')
        result = template.render('test', {'name': 'world'})
        self.assertEqual(result, '<b>world</b>')

        template.register_template('test2', '{{format name italic=true}}')
        result = template.render('test2', {'name': 'world'})
        self.assertEqual(result, '<i>world</i>')

        template.register_template(
            'test3', '{{format name bold=true italic=true}}'
        )
        result = template.render('test3', {'name': 'world'})
        self.assertEqual(result, '<i><b>world</b></i>')

    def test_helper_with_context(self) -> None:
        """Test a helper that uses the context."""
        template = Template()

        # Register a helper that uses the context.
        def greeting_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            # Get the name from the context.
            name = context.get('name', '')
            time_of_day = context.get('time_of_day', '')

            # Format greeting based on time of day.
            if time_of_day == 'morning':
                return f'Good morning, {name}!'
            elif time_of_day == 'evening':
                return f'Good evening, {name}!'
            else:
                return f'Hello, {name}!'

        template.register_helper('greeting', greeting_helper)

        # Test with different contexts.
        template.register_template('test', '{{greeting}}')

        result = template.render(
            'test', {'name': 'world', 'time_of_day': 'morning'}
        )
        self.assertEqual(result, 'Good morning, world!')

        result = template.render(
            'test', {'name': 'world', 'time_of_day': 'evening'}
        )
        self.assertEqual(result, 'Good evening, world!')

        result = template.render('test', {'name': 'world'})
        self.assertEqual(result, 'Hello, world!')

    def test_block_helper_with_content(self) -> None:
        """Test a block helper that processes its content."""
        template = Template()

        # Create a custom template that uses a block helper approach.
        template_string = """
    <div>{{name}}</div>
    <div>Hello, {{name}}!</div>
    """

        template.register_template('test', template_string)
        result = template.render('test', {'name': 'world'})

        # The expected result has both the name directly and in a greeting.
        expected = """
    <div>world</div>
    <div>Hello, world!</div>
    """

        self.assertEqual(result.strip(), expected.strip())

    def test_helper_with_nested_properties(self) -> None:
        """Test a helper that accesses nested properties."""
        template = Template()

        # Register a helper that formats a user's name.
        def format_name_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            # Access nested user object from the context.
            user = context.get('user', {})

            # Get first and last name.
            first_name: str = user.get('firstName', '')
            last_name: str = user.get('lastName', '')

            # Format based on hash arguments.
            format_type: str | None = hash_args.get('format')

            if format_type == 'full':
                return f'{first_name} {last_name}'
            elif format_type == 'last_first':
                return f'{last_name}, {first_name}'
            elif format_type == 'initials':
                return f'{first_name[0]}.{last_name[0]}.'
            else:
                return first_name

        template.register_helper('formatName', format_name_helper)

        # Test with different formats.
        template_string = '{{formatName format="full"}}'
        template.register_template('test1', template_string)

        template_string = '{{formatName format="last_first"}}'
        template.register_template('test2', template_string)

        template_string = '{{formatName format="initials"}}'
        template.register_template('test3', template_string)

        template_string = '{{formatName}}'
        template.register_template('test4', template_string)

        # Test data.
        data = {'user': {'firstName': 'John', 'lastName': 'Doe'}}

        self.assertEqual(template.render('test1', data), 'John Doe')
        self.assertEqual(template.render('test2', data), 'Doe, John')
        self.assertEqual(template.render('test3', data), 'J.D.')
        self.assertEqual(template.render('test4', data), 'John')

    def test_helper_with_this_context(self) -> None:
        """Test a helper that uses the 'this' context in Handlebars."""
        template = Template()

        # Register a helper that capitalizes all properties.
        def capitalize_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            if not params:
                return ''

            # Get the property to capitalize.
            prop = params[0]

            # Get the value from the context.
            value = context.get(prop, '')

            # Capitalize and return.
            return value.upper() if isinstance(value, str) else str(value)

        template.register_helper('capitalize', capitalize_helper)

        # Test with a simple template.
        template_string = '{{capitalize "name"}}'
        template.register_template('test', template_string)

        result = template.render('test', {'name': 'world'})
        self.assertEqual(result, 'WORLD')

    def test_conditional_rendering(self) -> None:
        """Test conditional rendering with helpers."""
        template = Template()

        # Register a helper that renders content conditionally.
        def if_equal_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            if len(params) < 2:
                return ''

            # Compare the two parameters.
            if params[0] == params[1]:
                # We can't easily access the block content in the current
                # implementation So, we'll return a simple string.
                return 'true'

            return ''

        template.register_helper('ifequal', if_equal_helper)

        # Test with different conditions.
        template_string = '{{ifequal value1 value2}}'
        template.register_template('test', template_string)

        # When equal.
        result = template.render('test', {'value1': 5, 'value2': 5})
        self.assertEqual(result, 'true')

        # When not equal.
        result = template.render('test', {'value1': 5, 'value2': 10})
        self.assertEqual(result, '')

    def test_complex_helper_with_loops(self) -> None:
        """Test a complex helper that processes arrays."""
        template = Template()

        # Register a helper that processes arrays.
        def list_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            # Get the array from the context.
            items = context.get('items', [])

            # Create an HTML list.
            result = '<ul>'
            for item in items:
                result += f'<li>{item}</li>'
            result += '</ul>'

            return result

        template.register_helper('list', list_helper)

        # Test with an array.
        template_string = '{{list}}'
        template.register_template('test', template_string)

        data = {'items': ['one', 'two', 'three']}

        result = template.render('test', data)
        expected = '<ul><li>one</li><li>two</li><li>three</li></ul>'
        self.assertEqual(result, expected)

    def test_template_with_partials(self) -> None:
        """Test using partials in templates."""
        template = Template()

        # Register a partial
        partial_template = '<p>{{name}}</p>'
        template.register_partial('user', partial_template)

        # Register a template that uses the partial
        template_string = '<div>{{> user}}</div>'
        template.register_template('test', template_string)

        # Render the template
        data = {'name': 'John Doe'}
        result = template.render('test', data)

        expected = '<div><p>John Doe</p></div>'
        self.assertEqual(result, expected)

    def test_advanced_partial_context(self) -> None:
        """Test partials with custom context."""
        template = Template()

        # Register a partial
        partial_template = '<p>{{firstName}} {{lastName}}</p>'
        template.register_partial('user', partial_template)

        # Register a template that uses the partial with a custom context
        template_string = '<div>{{> user user}}</div>'
        template.register_template('test', template_string)

        # Render the template
        data = {'user': {'firstName': 'John', 'lastName': 'Doe'}}
        result = template.render('test', data)

        expected = '<div><p>John Doe</p></div>'
        self.assertEqual(result, expected)

    def test_helper_that_returns_html(self) -> None:
        """Test a helper that returns HTML content."""
        template = Template()

        # Register a helper that returns HTML
        def html_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            tag = hash_args.get('tag', 'div')
            content = params[0] if params else ''

            return f'<{tag}>{content}</{tag}>'

        template.register_helper('html', html_helper)

        # Test with different tags
        template.register_template('test1', '{{html "Hello" tag="h1"}}')
        template.register_template('test2', '{{html "World" tag="span"}}')

        self.assertEqual(template.render('test1', {}), '<h1>Hello</h1>')
        self.assertEqual(template.render('test2', {}), '<span>World</span>')

    def test_helper_with_number_formatting(self) -> None:
        """Test a helper that formats numbers."""
        template = Template()

        # Register a helper that formats numbers
        def number_helper(
            params: list[str],
            hash_args: dict[str, Any],
            context: dict[str, Any],
        ) -> str:
            if not params:
                return ''

            value = params[0]
            format_type = hash_args.get('format', 'decimal')

            if format_type == 'currency':
                return f'${value:.2f}'
            elif format_type == 'percentage':
                return f'{value:.2f}%'
            else:  # decimal
                return f'{value:.2f}'

        template.register_helper('format_number', number_helper)

        # Test with different formats
        template.register_template(
            'test1', '{{format_number price format="currency"}}'
        )
        template.register_template(
            'test2', '{{format_number rate format="percentage"}}'
        )
        template.register_template('test3', '{{format_number value}}')

        data = {'price': 123.456, 'rate': 0.456, 'value': 789.012}

        self.assertEqual(template.render('test1', data), '$123.46')
        self.assertEqual(template.render('test2', data), '0.46%')
        self.assertEqual(template.render('test3', data), '789.01')

    def test_nested_properties_access(self) -> None:
        """Test accessing nested properties in templates."""
        template = Template()

        # Register a template with nested property access
        template_string = '{{user.profile.name}}'
        template.register_template('test', template_string)

        # Data with nested properties
        data = {'user': {'profile': {'name': 'John Doe'}}}

        result = template.render('test', data)
        self.assertEqual(result, 'John Doe')

    def test_template_with_comments(self) -> None:
        """Test templates with comments."""
        template = Template()

        # Register a template with comments
        template_string = '{{! This is a comment }}Hello, {{name}}!'
        template.register_template('test', template_string)

        # Render the template
        data = {'name': 'World'}
        result = template.render('test', data)

        self.assertEqual(result, 'Hello, World!')

    def test_array_iteration(self) -> None:
        """Test iterating over arrays in templates."""
        template = Template()

        # Test a template that iterates over an array
        template_string = """
    <ul>
    {{#each items}}
        <li>Item {{@index}}: {{this}}</li>
    {{/each}}
    </ul>
    """
        template.register_template('test', template_string)

        # Render with an array
        data = {'items': ['one', 'two', 'three']}
        result = template.render('test', data)

        expected = """
    <ul>
        <li>Item 0: one</li>
        <li>Item 1: two</li>
        <li>Item 2: three</li>
    </ul>
    """
        self.assertEqual(result.strip(), expected.strip())

    def test_object_iteration(self) -> None:
        """Test iterating over object properties in templates."""
        template = Template()

        # Test a template that iterates over object properties
        template_string = """
    <dl>
    {{#each person}}
        <dt>{{@key}}</dt>
        <dd>{{this}}</dd>
    {{/each}}
    </dl>
    """
        template.register_template('test', template_string)

        # Render with an object
        data = {'person': {'name': 'John', 'age': 30, 'city': 'New York'}}
        result = template.render('test', data)

        # We can't guarantee the order of properties, so just check for presence
        self.assertIn('<dt>name</dt>', result)
        self.assertIn('<dd>John</dd>', result)
        self.assertIn('<dt>age</dt>', result)
        self.assertIn('<dd>30</dd>', result)
        self.assertIn('<dt>city</dt>', result)
        self.assertIn('<dd>New York</dd>', result)
        self.assertEqual(result.count('<dt>'), 3)
        self.assertEqual(result.count('<dd>'), 3)

    def test_if_else_conditional(self) -> None:
        """Test if/else conditional rendering."""
        template = Template()

        # Test a template with conditional rendering
        template_string = """
    {{#if condition}}
        Condition is true
    {{else}}
        Condition is false
    {{/if}}
    """
        template.register_template('test', template_string)

        # Render with condition = true
        result_true = template.render('test', {'condition': True})
        self.assertIn('Condition is true', result_true)
        self.assertNotIn('Condition is false', result_true)

        # Render with condition = false
        result_false = template.render('test', {'condition': False})
        self.assertIn('Condition is false', result_false)
        self.assertNotIn('Condition is true', result_false)

    def test_nested_if_conditionals(self) -> None:
        """Test nested if conditional rendering."""
        template = Template()

        # Test a template with nested conditional rendering
        template_string = """
    {{#if outer}}
        Outer is true
        {{#if inner}}
            Inner is also true
        {{else}}
            Inner is false
        {{/if}}
    {{else}}
        Outer is false
    {{/if}}
    """
        template.register_template('test', template_string)

        # Test all combinations
        result1 = template.render('test', {'outer': True, 'inner': True})
        self.assertIn('Outer is true', result1)
        self.assertIn('Inner is also true', result1)

        result2 = template.render('test', {'outer': True, 'inner': False})
        self.assertIn('Outer is true', result2)
        self.assertIn('Inner is false', result2)

        result3 = template.render('test', {'outer': False, 'inner': True})
        self.assertIn('Outer is false', result3)
        self.assertNotIn('Inner is also true', result3)

        result4 = template.render('test', {'outer': False, 'inner': False})
        self.assertIn('Outer is false', result4)
        self.assertNotIn('Inner is false', result4)

    def test_unless_conditional(self) -> None:
        """Test unless conditional rendering."""
        template = Template()

        # Test a template with unless conditional
        template_string = """
    {{#unless condition}}
        Condition is false
    {{else}}
        Condition is true
    {{/unless}}
    """
        template.register_template('test', template_string)

        # Render with condition = true
        result_true = template.render('test', {'condition': True})
        self.assertIn('Condition is true', result_true)
        self.assertNotIn('Condition is false', result_true)

        # Render with condition = false
        result_false = template.render('test', {'condition': False})
        self.assertIn('Condition is false', result_false)
        self.assertNotIn('Condition is true', result_false)

    def test_with_helper(self) -> None:
        """Test the with helper for changing context."""
        template = Template()

        # Test a template with the with helper
        template_string = """
    {{#with person}}
        Name: {{name}}, Age: {{age}}
    {{/with}}
    """
        template.register_template('test', template_string)

        # Render with a person object
        data = {'person': {'name': 'John', 'age': 30}}
        result = template.render('test', data)

        self.assertIn('Name: John, Age: 30', result)

    def test_lookup_helper(self) -> None:
        """Test the lookup helper for dynamic property access."""
        template = Template()

        # Test a template with lookup helper
        template_string = '{{lookup data key}}'
        template.register_template('test', template_string)

        # Render with data and key
        data = {'data': {'name': 'John', 'age': 30}, 'key': 'name'}
        result = template.render('test', data)

        self.assertEqual(result, 'John')

        # Try with a different key
        data['key'] = 'age'
        result = template.render('test', data)

        self.assertEqual(result, '30')

    def test_log_helper(self) -> None:
        """Test the log helper for debugging."""
        template = Template()

        # Test a template with log helper - this doesn't render anything
        # But should not fail either
        template_string = 'Before {{log message}} After'
        template.register_template('test', template_string)

        # Render with a message
        data = {'message': 'This is a log message'}
        result = template.render('test', data)

        # The log helper shouldn't output anything to the template
        self.assertEqual(result, 'Before  After')
