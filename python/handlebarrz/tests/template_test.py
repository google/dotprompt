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

"""Unit tests for handlebarrz Template class."""

import unittest
from collections.abc import Callable
from typing import Any

import pytest

from handlebarrz import (
    CompiledRenderer,
    EscapeFunction,
    Handlebars,
    HelperOptions,
    Template,
    html_escape,
    no_escape,
)


class TestTemplate(unittest.TestCase):
    """Test the Template class."""

    def test_basic_template_rendering(self) -> None:
        """Test that a basic template renders correctly."""
        template = Template()
        template.register_template('hello', 'Hello {{name}}!')

        result = template.render('hello', {'name': 'World'})

        self.assertEqual(result, 'Hello World!')

    def test_template_with_helpers(self) -> None:
        """Test that a template with built-in helpers renders correctly."""
        template = Template()
        template.register_template('conditional', '{{#if condition}}Yes{{else}}No{{/if}}')

        result_true = template.render('conditional', {'condition': True})
        result_false = template.render('conditional', {'condition': False})

        self.assertEqual(result_true, 'Yes')
        self.assertEqual(result_false, 'No')

    def test_template_with_nested_context(self) -> None:
        """Test that a template with nested context renders correctly."""
        template = Template()
        template.register_template('nested', '{{person.name}} is {{person.age}} years old')

        result = template.render('nested', {'person': {'name': 'Alice', 'age': 30}})

        self.assertEqual(result, 'Alice is 30 years old')

    def test_template_with_each_helper(self) -> None:
        """Test that the each helper works correctly."""
        template = Template()
        template.register_template(
            'list',
            '{{#each items}}{{this}}{{#unless @last}}, {{/unless}}{{/each}}',
        )

        result = template.render('list', {'items': ['apple', 'banana', 'cherry']})

        self.assertEqual(result, 'apple, banana, cherry')

    def test_template_with_partials(self) -> None:
        """Test that partials work correctly."""
        template = Template()
        template.register_partial('person_details', '{{name}} ({{age}})')
        template.register_template('partial_example', 'Person: {{> person_details}}')

        result = template.render('partial_example', {'name': 'Bob', 'age': 25})

        self.assertEqual(result, 'Person: Bob (25)')

    def test_unregister_template(self) -> None:
        """Test that templates can be unregistered."""
        template = Template()
        template.register_template('temp', 'test')

        self.assertTrue(template.has_template('temp'))

        template.unregister_template('temp')

        self.assertFalse(template.has_template('temp'))

        # Rendering a non-existent template should raise ValueError
        with pytest.raises(ValueError):
            template.render('temp', {})

    def test_set_escape_function(self) -> None:
        """Test setting different escape functions."""
        template = Template()
        template.register_template('escape', '{{value}}')

        # Default is HTML escape
        result_html = template.render('escape', {'value': '<script>'})
        self.assertEqual(result_html, '&lt;script&gt;')

        # Set to no escape
        template.set_escape_function(EscapeFunction.NO_ESCAPE)
        result_no_escape = template.render('escape', {'value': '<script>'})
        self.assertEqual(result_no_escape, '<script>')

        # Invalid escape function should raise ValueError
        with pytest.raises(ValueError):
            template.set_escape_function(EscapeFunction('invalid_function'))

    def test_strict_mode(self) -> None:
        """Test that strict mode raises error for missing fields."""
        template = Template()
        template.register_template('strict_test', '{{missing_field}}')

        # Default (non-strict) mode returns empty string for missing fields
        self.assertEqual(template.render('strict_test', {}), '')

        # Enable strict mode
        template.strict_mode = True

        # Now missing fields should raise ValueError
        with pytest.raises(ValueError):
            template.render('strict_test', {})

    def test_custom_helper(self) -> None:
        """Test registering and using a custom helper function."""

        def create_helper(
            func: Callable[[list[Any], HelperOptions], str],
        ) -> Callable[[list[Any], HelperOptions], str]:
            """Test helper builder."""

            def helper_wrapper(
                params: list[Any],
                options: HelperOptions,
            ) -> str:
                return func(params, options)

            return helper_wrapper

        def format_list(params: list[Any], options: HelperOptions) -> str:
            """Format a list with custom separator."""
            # Access the items from the context instead of params.
            items: list[Any] = options.context().get('items', [])
            separator: str = options.hash_value('separator') or ', '

            # Make sure items is a list before joining.
            if not isinstance(items, list):
                return ''

            return separator.join(items)

        template = Template()
        template.register_helper('formatList', create_helper(format_list))
        template.register_template('custom_helper', "Items: {{formatList separator=' | '}}")

        result = template.render('custom_helper', {'items': ['one', 'two', 'three']})

        self.assertEqual(result, 'Items: one | two | three')

    def test_render_template_string(self) -> None:
        """Test rendering a template string without registering it."""
        template = Template()

        result = template.render_template('Hello {{name}}!', {'name': 'World'})

        self.assertEqual(result, 'Hello World!')

    def test_invalid_template_syntax(self) -> None:
        """Test registering a template with invalid syntax raises ValueError."""
        template = Template()
        with pytest.raises(ValueError):
            template.register_template(
                'invalid',
                'Hello {{name}!',  # Missing closing brace
            )

    def test_escape_functions(self) -> None:
        """Test the standalone escape functions."""
        self.assertEqual(html_escape('<script>'), '&lt;script&gt;')
        self.assertEqual(no_escape('<script>'), '<script>')

    def test_template_with_file(self) -> None:
        """Test registering a template from a file."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            template_content = 'Hello {{name}} from file!'
            temp_file.write(template_content)
            temp_path = temp_file.name

        try:
            template = Template()
            template.register_template_file('file_template', temp_path)

            result = template.render('file_template', {'name': 'World'})
            self.assertEqual(result, 'Hello World from file!')
        finally:
            os.unlink(temp_path)

    def test_compile_basic(self) -> None:
        """Test basic template compilation and execution."""
        template = Template()
        compiled_func: CompiledRenderer = template.compile('Hello {{name}}!')
        result = compiled_func({'name': 'Compiled World'}, None)
        self.assertEqual(result, 'Hello Compiled World!')

    def test_compile_with_data_changes(self) -> None:
        """Test that the compiled function works with different data."""
        template = Template()
        compiled_func: CompiledRenderer = template.compile('Value: {{val}}')
        result1 = compiled_func({'val': 10}, None)
        result2 = compiled_func({'val': 'abc'}, None)
        self.assertEqual(result1, 'Value: 10')
        self.assertEqual(result2, 'Value: abc')

    def test_compile_uses_current_template_state(self) -> None:
        """Test that compiled function uses the template state at call time."""
        template = Template()
        compiled_func: CompiledRenderer = template.compile('Helper: {{my_helper val}}')

        # Register the helper AFTER compiling.
        def simple_upper(params: list[Any], options: HelperOptions) -> str:
            """Test helper."""
            return str(params[0]).upper()

        template.register_helper('my_helper', simple_upper)

        # Call again AFTER helper is registered.
        result_after = compiled_func({'val': 'test'}, None)
        self.assertEqual(result_after, 'Helper: TEST')

        # Change strict mode AFTER compiling.
        template.strict_mode = True
        compiled_strict: CompiledRenderer = template.compile('{{missing}}')
        with pytest.raises(ValueError, match=r'Failed to access variable.*missing.*'):
            compiled_strict({}, None)

    def test_compile_invalid_syntax(self) -> None:
        """Test that compiling invalid syntax raises ValueError when called."""
        template = Template()

        # Compile should succeed, but the returned function should fail.
        compiled_func: CompiledRenderer = template.compile('Hello {{name!')

        # Expect ValueError when the compiled function is executed.
        with pytest.raises(ValueError, match=r'Failed to parse template.*'):
            compiled_func({}, None)


class TestTemplateEdgeCases(unittest.TestCase):
    """Test edge cases and error handling for Template class."""

    def test_empty_template(self) -> None:
        """Test that an empty template renders to empty string."""
        template = Template()
        template.register_template('empty', '')
        result = template.render('empty', {'name': 'World'})
        self.assertEqual(result, '')

    def test_template_with_only_whitespace(self) -> None:
        """Test that a whitespace-only template preserves whitespace."""
        template = Template()
        template.register_template('whitespace', '   \n\t  ')
        result = template.render('whitespace', {})
        self.assertEqual(result, '   \n\t  ')

    def test_template_with_unicode(self) -> None:
        """Test that templates handle unicode characters correctly."""
        template = Template()
        template.register_template('unicode', 'Hello {{name}}! 你好 🎉')
        result = template.render('unicode', {'name': '世界'})
        self.assertEqual(result, 'Hello 世界! 你好 🎉')

    def test_template_with_special_characters_in_data(self) -> None:
        """Test that special characters in data are handled correctly."""
        template = Template()
        template.register_template('special', 'Value: {{{value}}}')  # Triple braces = no escape
        result = template.render('special', {'value': '<div class="test">&amp;</div>'})
        self.assertEqual(result, 'Value: <div class="test">&amp;</div>')

    def test_deeply_nested_context(self) -> None:
        """Test that deeply nested context paths work correctly."""
        template = Template()
        template.register_template('deep', '{{a.b.c.d.e}}')
        data = {'a': {'b': {'c': {'d': {'e': 'deep_value'}}}}}
        result = template.render('deep', data)
        self.assertEqual(result, 'deep_value')

    def test_array_index_access(self) -> None:
        """Test accessing array elements by index."""
        template = Template()
        template.register_template('array', '{{items.[0]}} and {{items.[2]}}')
        result = template.render('array', {'items': ['first', 'second', 'third']})
        self.assertEqual(result, 'first and third')

    def test_multiple_templates(self) -> None:
        """Test registering and rendering multiple templates."""
        template = Template()
        template.register_template('greeting', 'Hello {{name}}!')
        template.register_template('farewell', 'Goodbye {{name}}!')
        template.register_template('question', 'How are you, {{name}}?')

        self.assertEqual(template.render('greeting', {'name': 'Alice'}), 'Hello Alice!')
        self.assertEqual(template.render('farewell', {'name': 'Bob'}), 'Goodbye Bob!')
        self.assertEqual(template.render('question', {'name': 'Charlie'}), 'How are you, Charlie?')

    def test_reregister_template(self) -> None:
        """Test that re-registering a template overwrites the previous one."""
        template = Template()
        template.register_template('test', 'Version 1: {{value}}')
        result1 = template.render('test', {'value': 'data'})
        self.assertEqual(result1, 'Version 1: data')

        template.register_template('test', 'Version 2: {{value}}')
        result2 = template.render('test', {'value': 'data'})
        self.assertEqual(result2, 'Version 2: data')


class TestUnicodeAndInternationalization(unittest.TestCase):
    """Test Unicode and internationalization support."""

    def test_hindi_devanagari_script(self) -> None:
        """Test Hindi text in Devanagari script."""
        template = Template()
        template.register_template('hindi', 'नमस्ते {{name}}!')
        result = template.render('hindi', {'name': 'दुनिया'})
        self.assertEqual(result, 'नमस्ते दुनिया!')

    def test_arabic_rtl_text(self) -> None:
        """Test Arabic right-to-left text."""
        template = Template()
        template.register_template('arabic', 'مرحبا {{name}}!')
        result = template.render('arabic', {'name': 'العالم'})
        self.assertEqual(result, 'مرحبا العالم!')

    def test_japanese_mixed_scripts(self) -> None:
        """Test Japanese with hiragana, katakana, and kanji."""
        template = Template()
        template.register_template('japanese', 'こんにちは {{name}}さん!')
        result = template.render('japanese', {'name': '田中'})
        self.assertEqual(result, 'こんにちは 田中さん!')

    def test_korean_hangul(self) -> None:
        """Test Korean Hangul script."""
        template = Template()
        template.register_template('korean', '안녕하세요 {{name}}님!')
        result = template.render('korean', {'name': '세계'})
        self.assertEqual(result, '안녕하세요 세계님!')

    def test_chinese_simplified(self) -> None:
        """Test Simplified Chinese characters."""
        template = Template()
        template.register_template('chinese', '你好 {{name}}!')
        result = template.render('chinese', {'name': '世界'})
        self.assertEqual(result, '你好 世界!')

    def test_tamil_script(self) -> None:
        """Test Tamil script."""
        template = Template()
        template.register_template('tamil', 'வணக்கம் {{name}}!')
        result = template.render('tamil', {'name': 'உலகம்'})
        self.assertEqual(result, 'வணக்கம் உலகம்!')

    def test_emoji_in_template(self) -> None:
        """Test emoji characters in templates."""
        template = Template()
        template.register_template('emoji', '{{greeting}} 🎉🎊 {{name}} 🌍🌎🌏')
        result = template.render('emoji', {'greeting': 'Hello', 'name': 'World'})
        self.assertEqual(result, 'Hello 🎉🎊 World 🌍🌎🌏')

    def test_mixed_scripts_in_single_template(self) -> None:
        """Test multiple scripts in a single template."""
        template = Template()
        template.register_template(
            'mixed',
            'English: {{en}}, 中文: {{zh}}, हिंदी: {{hi}}, العربية: {{ar}}',
        )
        result = template.render(
            'mixed',
            {'en': 'Hello', 'zh': '你好', 'hi': 'नमस्ते', 'ar': 'مرحبا'},
        )
        self.assertEqual(result, 'English: Hello, 中文: 你好, हिंदी: नमस्ते, العربية: مرحبا')

    def test_combining_diacritical_marks(self) -> None:
        """Test characters with combining diacritical marks."""
        template = Template()
        # é can be represented as e + combining acute accent
        template.register_template('diacritics', 'Café: {{name}}')
        result = template.render('diacritics', {'name': 'résumé'})
        self.assertEqual(result, 'Café: résumé')

    def test_zero_width_characters(self) -> None:
        """Test handling of zero-width characters."""
        template = Template()
        # Zero-width joiner (U+200D) is used in some scripts
        template.register_template('zwj', 'Family: {{emoji}}')
        result = template.render('zwj', {'emoji': '👨‍👩‍👧‍👦'})  # Family emoji with ZWJ
        self.assertEqual(result, 'Family: 👨‍👩‍👧‍👦')


class TestHandlebarsAlias(unittest.TestCase):
    """Test that the Handlebars alias works like Template."""

    def test_handlebars_alias(self) -> None:
        """Test that the Handlebars alias works like Template."""
        # Test that Handlebars is same type as Template
        self.assertEqual(Handlebars, Template)

    def test_handlebars_alias_features(self) -> None:
        """Test that the Handlebars alias works like Template."""
        # Test that Handlebars instances work the same as Template instances
        handlebars = Handlebars()
        handlebars.register_template('hello', 'Hello {{name}}!')
        result = handlebars.render('hello', {'name': 'World'})
        self.assertEqual(result, 'Hello World!')

    def test_handlebars_features_work_with_alias(self) -> None:
        """Test that all features work with the Handlebars alias."""
        handlebars = Handlebars()
        handlebars.register_partial('name_partial', '{{name}}')
        handlebars.register_template('with_partial', 'Hello {{> name_partial}}!')
        result = handlebars.render('with_partial', {'name': 'Universe'})
        self.assertEqual(result, 'Hello Universe!')

    def test_handlebars_alias_custom_helper(self) -> None:
        """Test that custom helpers work with the Handlebars alias."""
        handlebars = Handlebars()

        def upper_helper(params: list[Any], options: HelperOptions) -> str:
            """Test helper."""
            return str(params[0]).upper()

        handlebars.register_helper('upper', upper_helper)
        handlebars.register_template('with_helper', 'Hello {{upper name}}!')
        result = handlebars.render('with_helper', {'name': 'world'})
        self.assertEqual(result, 'Hello WORLD!')
