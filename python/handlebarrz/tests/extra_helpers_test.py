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

import json
import unittest
from typing import Any

from handlebarrz import Template


class TestIfEqualsHelper(unittest.TestCase):
    def setUp(self) -> None:
        self.template = Template()
        self.template.register_extra_helpers()

    def test_if_equals_helper_equal_values(self) -> None:
        """Test ifEquals helper with equal integer values."""
        self.template.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.template.render('if_equals_test', {'arg1': 1, 'arg2': 1})
        self.assertEqual(result, 'yes')

    def test_if_equals_helper_unequal_values(self) -> None:
        """Test ifEquals helper with unequal integer values."""
        self.template.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.template.render('if_equals_test', {'arg1': 1, 'arg2': 2})
        self.assertEqual(result, 'no')

    def test_if_equals_helper_string_equal_values(self) -> None:
        """Test ifEquals helper with equal string values."""
        self.template.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.template.render(
            'if_equals_test', {'arg1': 'test', 'arg2': 'test'}
        )
        self.assertEqual(result, 'yes')

    def test_if_equals_helper_string_unequal_values(self) -> None:
        """Test ifEquals helper with unequal string values."""
        self.template.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.template.render(
            'if_equals_test', {'arg1': 'test', 'arg2': 'diff'}
        )
        self.assertEqual(result, 'no')


class TestUnlessEqualsHelper(unittest.TestCase):
    def setUp(self) -> None:
        self.template = Template()
        self.template.register_extra_helpers()

    def test_unless_equals_helper_unequal_values(self) -> None:
        """Test unlessEquals helper with unequal integer values."""
        self.template.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.template.render(
            'unless_equals_test', {'arg1': 1, 'arg2': 2}
        )
        self.assertEqual(result, 'yes')

    def test_unless_equals_helper_equal_values(self) -> None:
        """Test unlessEquals helper with equal integer values."""
        self.template.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.template.render(
            'unless_equals_test', {'arg1': 1, 'arg2': 1}
        )
        self.assertEqual(result, 'no')

    def test_unless_equals_helper_string_unequal_values(self) -> None:
        """Test unlessEquals helper with unequal string values."""
        self.template.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.template.render(
            'unless_equals_test', {'arg1': 'test', 'arg2': 'diff'}
        )
        self.assertEqual(result, 'yes')

    def test_unless_equals_helper_string_equal_values(self) -> None:
        """Test unlessEquals helper with equal string values."""
        self.template.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.template.render(
            'unless_equals_test', {'arg1': 'test', 'arg2': 'test'}
        )
        self.assertEqual(result, 'no')


class TestJsonHelper(unittest.TestCase):
    def setUp(self) -> None:
        self.template = Template()
        self.template.register_extra_helpers()

    def test_json_helper_basic_object(self) -> None:
        """Test the JSON helper with a basic object."""
        self.template.register_template('json_basic', '{{json data}}')
        data = {'a': 1, 'b': 2}
        result = self.template.render('json_basic', {'data': data})
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, data)

    def test_json_helper_with_indent(self) -> None:
        """Test the JSON helper with explicit indent."""
        self.template.register_template('json_indent', '{{json data indent=2}}')
        data = {'a': 1, 'b': 2}
        result = self.template.render('json_indent', {'data': data})
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, data)
        self.assertIn('\n', result)

    def test_json_helper_empty_params_renders_empty_string(self) -> None:
        """Test the JSON helper with empty params."""
        self.template.register_template('json_empty', '{{json}}')
        result = self.template.render('json_empty', {})
        self.assertEqual(result, '')

    def test_json_helper_with_array(self) -> None:
        """Test the JSON helper with an array."""
        self.template.register_template('json_basic', '{{json data}}')
        array_data = [1, 2, 3]
        result = self.template.render('json_basic', {'data': array_data})
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, array_data)

    def test_json_helper_with_indent_on_array(self) -> None:
        """Test the JSON helper with indent on array."""
        self.template.register_template('json_indent', '{{json data indent=2}}')
        array_data = [1, 2, 3]
        result = self.template.render('json_indent', {'data': array_data})
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, array_data)
        self.assertIn('\n', result)

    def test_json_helper_empty_object(self) -> None:
        """Test the JSON helper with an empty object."""
        self.template.register_template('json_basic', '{{json data}}')
        empty_data: dict[str, Any] = {}
        result = self.template.render('json_basic', {'data': empty_data})
        self.assertEqual(result, '{}')


if __name__ == '__main__':
    unittest.main()
