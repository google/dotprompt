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

"""Tests for utility functions."""

import unittest

from dotpromptz.util import (
    remove_undefined_fields,
    unquote,
    validate_prompt_name,
)


class TestRemoveUndefinedFields(unittest.TestCase):
    """Tests for remove_undefined_fields."""

    def test_remove_undefined_fields_recursively(self) -> None:
        """Test removing undefined fields from dictionaries."""
        input_dict = {
            'a': 1,
            'b': None,
            'c': {'d': 2, 'e': None},
            'f': [3, None, {'g': 4, 'h': None}],
        }
        expected = {
            'a': 1,
            'c': {'d': 2},
            'f': [3, {'g': 4}],
        }
        result = remove_undefined_fields(input_dict)
        self.assertEqual(result, expected)

    def test_remove_undefined_fields_none(self) -> None:
        """Test removing undefined fields from None."""
        self.assertIsNone(remove_undefined_fields(None))

    def test_remove_undefined_fields_primitive(self) -> None:
        """Test removing undefined fields from primitive types."""
        self.assertEqual(remove_undefined_fields(42), 42)
        self.assertEqual(remove_undefined_fields('test'), 'test')
        self.assertEqual(remove_undefined_fields(True), True)

    def test_remove_undefined_fields_list(self) -> None:
        """Test removing undefined fields from lists."""
        input_list = [1, None, {'a': 2, 'b': None}, [3, None, 4]]
        expected = [1, {'a': 2}, [3, 4]]
        result = remove_undefined_fields(input_list)
        self.assertEqual(result, expected)

    def test_remove_undefined_fields_dict(self) -> None:
        """Test removing undefined fields from dictionaries."""
        input_dict = {
            'a': 1,
            'b': None,
            'c': {'d': 2, 'e': None},
            'f': [3, None, {'g': 4, 'h': None}],
        }
        expected = {
            'a': 1,
            'c': {'d': 2},
            'f': [3, {'g': 4}],
        }
        result = remove_undefined_fields(input_dict)
        self.assertEqual(result, expected)

    def test_remove_undefined_fields_nested(self) -> None:
        """Test removing undefined fields from nested structures."""
        input_data = {
            'a': {
                'b': [
                    {'c': 1, 'd': None},
                    None,
                    {'e': {'f': 2, 'g': None}},
                ],
                'h': None,
            },
            'i': None,
        }
        expected = {
            'a': {
                'b': [
                    {'c': 1},
                    {'e': {'f': 2}},
                ],
            },
        }
        result = remove_undefined_fields(input_data)
        self.assertEqual(result, expected)

    def test_remove_undefined_fields_empty(self) -> None:
        """Test removing undefined fields from empty structures."""
        self.assertEqual(remove_undefined_fields({}), {})
        self.assertEqual(remove_undefined_fields([]), [])
        self.assertEqual(remove_undefined_fields({'a': {}}), {'a': {}})
        self.assertEqual(remove_undefined_fields({'a': []}), {'a': []})


class TestUnquote(unittest.TestCase):
    """Tests for unquote."""

    def test_unquote(self) -> None:
        """Test removing quotes from a string."""
        self.assertEqual(unquote('"test"'), 'test')
        self.assertEqual(unquote("'test'"), 'test')

    def test_unquote_leaves_alone_unpaired(self) -> None:
        """Test that unquote leaves alone strings that are not paired."""
        self.assertEqual(unquote('test'), 'test')
        self.assertEqual(unquote("'test"), "'test")
        self.assertEqual(unquote('"test'), '"test')
        self.assertEqual(unquote("test'"), "test'")
        self.assertEqual(unquote('test"'), 'test"')
        self.assertEqual(unquote('"test\''), '"test\'')
        self.assertEqual(unquote('\'test"'), '\'test"')

    def test_unquote_leaves_along_internal_quotes(self) -> None:
        """Test that unquote leaves alone strings with internal quotes."""
        self.assertEqual(unquote('"test\'test"'), "test'test")
        self.assertEqual(unquote('\'test"'), '\'test"')
        self.assertEqual(unquote('"test\'test""'), 'test\'test"')
        self.assertEqual(unquote("'test\"test''"), 'test"test\'')

    def test_unquote_only_unquotes_one_level(self) -> None:
        """Test that unquote only removes one level of quotes."""
        self.assertEqual(unquote('""test\'test""'), '"test\'test"')
        self.assertEqual(unquote("''test\"test''"), "'test\"test'")


class TestValidatePromptName(unittest.TestCase):
    """Tests for validate_prompt_name."""

    def test_rejects_double_dot_traversal(self) -> None:
        """Should reject names with '..' for path traversal."""
        with self.assertRaises(ValueError):
            validate_prompt_name('../../../etc/passwd')

    def test_rejects_double_dot_only(self) -> None:
        """Should reject '..' as a name."""
        with self.assertRaises(ValueError):
            validate_prompt_name('..')

    def test_rejects_absolute_paths(self) -> None:
        """Should reject absolute paths."""
        with self.assertRaises(ValueError):
            validate_prompt_name('/absolute/path.attack')

    def test_rejects_windows_absolute_paths(self) -> None:
        """Should reject Windows absolute paths."""
        with self.assertRaises(ValueError):
            validate_prompt_name('C:/Windows/System32')

    def test_rejects_embedded_traversal(self) -> None:
        """Should reject embedded traversal sequences."""
        with self.assertRaises(ValueError):
            validate_prompt_name('subdir/../../../escape')

    def test_rejects_windows_style_traversal(self) -> None:
        """Should reject Windows backslash traversal."""
        with self.assertRaises(ValueError):
            validate_prompt_name('..\\windows\\system32')

    def test_rejects_mixed_slash_traversal(self) -> None:
        """Should reject mixed forward/backslash traversal."""
        with self.assertRaises(ValueError):
            validate_prompt_name('..\\../etc/passwd')

    def test_rejects_empty_string(self) -> None:
        """Should reject empty string."""
        with self.assertRaises(ValueError):
            validate_prompt_name('')

    def test_rejects_whitespace_only(self) -> None:
        """Should reject whitespace-only names."""
        with self.assertRaises(ValueError):
            validate_prompt_name('   ')

    def test_rejects_trailing_slash(self) -> None:
        """Should reject trailing slash."""
        with self.assertRaises(ValueError):
            validate_prompt_name('prompt/')

    def test_rejects_leading_slash(self) -> None:
        """Should reject leading slash indicating absolute path."""
        with self.assertRaises(ValueError):
            validate_prompt_name('/subdir/prompt')

    def test_allows_simple_name(self) -> None:
        """Should allow simple alphanumeric names."""
        validate_prompt_name('simple')

    def test_allows_hyphenated_name(self) -> None:
        """Should allow hyphenated names."""
        validate_prompt_name('my-prompt')

    def test_allows_underscored_name(self) -> None:
        """Should allow underscored names."""
        validate_prompt_name('my_prompt')

    def test_allows_dots_in_middle_of_name(self) -> None:
        """Should allow dots within the name (not as traversal)."""
        validate_prompt_name('a..b')

    def test_allows_version_with_dots(self) -> None:
        """Should allow version-style naming with dots."""
        validate_prompt_name('version..2')

    def test_allows_subdirectory_paths(self) -> None:
        """Should allow legitimate subdirectory paths."""
        validate_prompt_name('subdir/nested')

    def test_allows_deep_nesting(self) -> None:
        """Should allow deeply nested legitimate paths."""
        validate_prompt_name('subdir/deeply/nested/prompt')

    def test_allows_multiple_dots_in_name(self) -> None:
        """Should allow multiple consecutive dots in name."""
        validate_prompt_name('a.b.c')


if __name__ == '__main__':
    unittest.main()
