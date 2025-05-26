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

"""Tests for Handlebars helpers."""

import json
import unittest

from dotpromptz.helpers import (
    history_helper,
    if_equals_helper,
    json_helper,
    media_helper,
    role_helper,
    section_helper,
    unless_equals_helper,
)
from handlebarrz import Handlebars


class TestDotpromptHelpers(unittest.TestCase):
    """Tests for the dotprompt helpers."""

    def setUp(self) -> None:
        self.handlebars = Handlebars()
        self.handlebars.register_helper('json', json_helper)
        self.handlebars.register_helper('role', role_helper)
        self.handlebars.register_helper('history', history_helper)
        self.handlebars.register_helper('section', section_helper)
        self.handlebars.register_helper('media', media_helper)
        self.handlebars.register_helper('ifEquals', if_equals_helper)
        self.handlebars.register_helper('unlessEquals', unless_equals_helper)

    def test_json_helper_basic_object(self) -> None:
        self.handlebars.register_template('test1', '{{json data}}')
        result = self.handlebars.render('test1', {'data': {'name': 'John', 'age': 30}})
        expected = {'name': 'John', 'age': 30}
        self.assertEqual(json.loads(result), expected)

    def test_json_helper_with_indent(self) -> None:
        self.handlebars.register_template('test2', '{{json data indent=2}}')
        result = self.handlebars.render('test2', {'data': {'name': 'John', 'age': 30}})
        expected = {'name': 'John', 'age': 30}
        self.assertEqual(json.loads(result), expected)

    def test_json_helper_with_str_indent(self) -> None:
        self.handlebars.register_template('test3', '{{json data indent="4"}}')
        result = self.handlebars.render('test3', {'data': {'name': 'John', 'age': 30}})
        expected = {'name': 'John', 'age': 30}
        self.assertEqual(json.loads(result), expected)

    def test_json_helper_with_array(self) -> None:
        self.handlebars.register_template('test4', '{{json data}}')
        result = self.handlebars.render('test4', {'data': [1, 2, 3]})
        self.assertEqual(json.loads(result), [1, 2, 3])

    def test_role_helper_system(self) -> None:
        self.handlebars.register_template('role_test', '{{role "system"}}')
        result = self.handlebars.render('role_test', {})
        self.assertEqual(result, '<<<dotprompt:role:system>>>')

    def test_role_helper_user(self) -> None:
        self.handlebars.register_template('role_test', '{{role "user"}}')
        result = self.handlebars.render('role_test', {})
        self.assertEqual(result, '<<<dotprompt:role:user>>>')

    def test_history_helper(self) -> None:
        self.handlebars.register_template('history_test', '{{history}}')
        result = self.handlebars.render('history_test', {})
        self.assertEqual(result, '<<<dotprompt:history>>>')

    def test_section_helper(self) -> None:
        self.handlebars.register_template('section_test', '{{section "example"}}')
        result = self.handlebars.render('section_test', {})
        self.assertEqual(result, '<<<dotprompt:section example>>>')

    def test_media_helper_with_url(self) -> None:
        template = '{{media url="https://example.com/img.png"}}'
        self.handlebars.register_template('media_test1', template)
        result = self.handlebars.render('media_test1', {})
        self.assertEqual(result, '<<<dotprompt:media:url https://example.com/img.png>>>')

    def test_media_helper_with_url_and_content_type(self) -> None:
        template = '{{media url="https://example.com/img.png" contentType="image/png"}}'
        self.handlebars.register_template('media_test2', template)
        result = self.handlebars.render('media_test2', {})
        expected = '<<<dotprompt:media:url https://example.com/img.png image/png>>>'
        self.assertEqual(result, expected)

    def test_unless_equals_helper_unequal_values(self) -> None:
        """Test unlessEquals helper with unequal integer values."""
        self.handlebars.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.handlebars.render('unless_equals_test', {'arg1': 1, 'arg2': 2})
        self.assertEqual(result, 'yes')

    def test_if_equals_helper_equal_values(self) -> None:
        """Test ifEquals helper with equal integer values."""
        self.handlebars.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.handlebars.render('if_equals_test', {'arg1': 1, 'arg2': 1})
        self.assertEqual(result, 'yes')

    def test_if_equals_helper_unequal_values(self) -> None:
        """Test ifEquals helper with unequal integer values."""
        self.handlebars.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.handlebars.render('if_equals_test', {'arg1': 1, 'arg2': 2})
        self.assertEqual(result, 'no')

    def test_if_equals_helper_string_equal_values(self) -> None:
        """Test ifEquals helper with equal string values."""
        self.handlebars.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.handlebars.render('if_equals_test', {'arg1': 'test', 'arg2': 'test'})
        self.assertEqual(result, 'yes')

    def test_if_equals_helper_string_unequal_values(self) -> None:
        """Test ifEquals helper with unequal string values."""
        self.handlebars.register_template(
            'if_equals_test',
            '{{#ifEquals arg1 arg2}}yes{{else}}no{{/ifEquals}}',
        )
        result = self.handlebars.render('if_equals_test', {'arg1': 'test', 'arg2': 'diff'})
        self.assertEqual(result, 'no')

    def test_unless_equals_helper_equal_values(self) -> None:
        """Test unlessEquals helper with equal integer values."""
        self.handlebars.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.handlebars.render('unless_equals_test', {'arg1': 1, 'arg2': 1})
        self.assertEqual(result, 'no')

    def test_unless_equals_helper_string_unequal_values(self) -> None:
        """Test unlessEquals helper with unequal string values."""
        self.handlebars.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.handlebars.render('unless_equals_test', {'arg1': 'test', 'arg2': 'diff'})
        self.assertEqual(result, 'yes')

    def test_unless_equals_helper_string_equal_values(self) -> None:
        """Test unlessEquals helper with equal string values."""
        self.handlebars.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.handlebars.render('unless_equals_test', {'arg1': 'test', 'arg2': 'test'})
        self.assertEqual(result, 'no')


if __name__ == '__main__':
    unittest.main()
