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
    json_helper,
    media_helper,
    role_helper,
    section_helper,
)
from handlebarrz import Handlebars


class TestJsonHelper(unittest.TestCase):
    """Tests for the JSON helper function."""

    def test_json_helper_direct(self) -> None:
        """Test the JSON helper function directly."""
        # Basic object
        data = {'a': 1, 'b': 2}
        result = json_helper([data], {}, {})
        self.assertEqual(json.loads(result), data)

        # With indent
        result = json_helper([data], {'indent': 2}, {})
        self.assertEqual(json.loads(result), data)

        # Empty params
        result = json_helper([], {}, {})
        self.assertEqual(result, '')

        # Non-serializable object
        class TestObj:
            pass

        result = json_helper([TestObj()], {}, {})
        self.assertEqual(result, '{}')

    def test_json_helper_in_template(self) -> None:
        """Test the JSON helper function in a template."""
        handlebars = Handlebars()
        handlebars.register_helper('json', json_helper)

        # Basic usage
        handlebars.register_template('test1', '{{json data}}')
        result = handlebars.render('test1', {'data': {'name': 'John', 'age': 30}})
        expected = {'name': 'John', 'age': 30}
        self.assertEqual(json.loads(result), expected)

        # With indent
        handlebars.register_template('test2', '{{json data indent=2}}')
        result = handlebars.render('test2', {'data': {'name': 'John', 'age': 30}})
        self.assertEqual(json.loads(result), expected)

        # With string indent (should convert to int)
        handlebars.register_template('test3', '{{json data indent="4"}}')
        result = handlebars.render('test3', {'data': {'name': 'John', 'age': 30}})
        self.assertEqual(json.loads(result), expected)

        # Array.
        handlebars.register_template('test4', '{{json data}}')
        result = handlebars.render('test4', {'data': [1, 2, 3]})
        self.assertEqual(json.loads(result), [1, 2, 3])


class TestRoleHelper(unittest.TestCase):
    """Tests for the role helper function."""

    def test_role_helper_direct(self) -> None:
        """Test role helper function directly."""
        result = role_helper(['system'], {}, {})
        self.assertEqual(result, '<<<dotprompt:role:system>>>')

        result = role_helper(['user'], {}, {})
        self.assertEqual(result, '<<<dotprompt:role:user>>>')

        # Empty params.
        result = role_helper([], {}, {})
        self.assertEqual(result, '')


class TestHistoryHelper(unittest.TestCase):
    """Tests for the history helper function."""

    def test_history_helper_direct(self) -> None:
        """Test history helper function directly."""
        result = history_helper([], {}, {})
        self.assertEqual(result, '<<<dotprompt:history>>>')


class TestSectionHelper(unittest.TestCase):
    """Tests for the section helper function."""

    def test_section_helper_direct(self) -> None:
        """Test section helper function directly."""
        result = section_helper(['test'], {}, {})
        self.assertEqual(result, '<<<dotprompt:section test>>>')

        # Empty params.
        result = section_helper([], {}, {})

        self.assertEqual(result, '')


class TestMediaHelper(unittest.TestCase):
    """Tests for the media helper function."""

    def test_media_helper_direct(self) -> None:
        """Test media helper function directly."""
        # With URL only.
        result = media_helper([], {'url': 'https://example.com/image.png'}, {})
        self.assertEqual(result, '<<<dotprompt:media:url https://example.com/image.png>>>')

        # With URL and content type.
        result = media_helper(
            [],
            {
                'url': 'https://example.com/image.png',
                'contentType': 'image/png',
            },
            {},
        )
        expected = '<<<dotprompt:media:url https://example.com/image.png image/png>>>'
        self.assertEqual(result, expected)

        # Missing URL.
        result = media_helper([], {}, {})
        self.assertEqual(result, '')


class TestDotpromptHelpers(unittest.TestCase):
    """Tests for the dotprompt helpers."""

    def test_dotprompt_helpers_in_template(self) -> None:
        """Test dotprompt helpers in templates."""
        handlebars = Handlebars()
        handlebars.register_helper('role', role_helper)
        handlebars.register_helper('history', history_helper)
        handlebars.register_helper('section', section_helper)
        handlebars.register_helper('media', media_helper)

        # Role helper.
        handlebars.register_template('role_test', '{{role "system"}}')
        result = handlebars.render('role_test', {})
        self.assertEqual(result, '<<<dotprompt:role:system>>>')

        # History helper.
        handlebars.register_template('history_test', '{{history}}')
        result = handlebars.render('history_test', {})
        self.assertEqual(result, '<<<dotprompt:history>>>')

        # Section helper.
        handlebars.register_template('section_test', '{{section "example"}}')
        result = handlebars.render('section_test', {})
        self.assertEqual(result, '<<<dotprompt:section example>>>')

        # Media helper.
        template = '{{media url="https://example.com/img.png"}}'
        handlebars.register_template('media_test1', template)
        result = handlebars.render('media_test1', {})
        self.assertEqual(result, '<<<dotprompt:media:url https://example.com/img.png>>>')

        # Media helper with content type.
        template = '{{media url="https://example.com/img.png" contentType="image/png"}}'
        handlebars.register_template('media_test2', template)
        result = handlebars.render('media_test2', {})
        expected = '<<<dotprompt:media:url https://example.com/img.png image/png>>>'
        self.assertEqual(result, expected)


class TestIfEqualsHelper(unittest.TestCase):
    """Tests for the ifEquals helper function."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self.handlebars = Handlebars()
        self.handlebars.register_extra_helpers()

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


class TestUnlessEqualsHelper(unittest.TestCase):
    """Tests for the unlessEquals helper function."""

    def setUp(self) -> None:
        """Set up the test environment."""
        self.handlebars = Handlebars()
        self.handlebars.register_extra_helpers()

    def test_unless_equals_helper_unequal_values(self) -> None:
        """Test unlessEquals helper with unequal integer values."""
        self.handlebars.register_template(
            'unless_equals_test',
            '{{#unlessEquals arg1 arg2}}yes{{else}}no{{/unlessEquals}}',
        )
        result = self.handlebars.render('unless_equals_test', {'arg1': 1, 'arg2': 2})
        self.assertEqual(result, 'yes')

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
