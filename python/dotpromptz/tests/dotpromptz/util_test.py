# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for utility functions."""

import unittest

from dotpromptz.util import (
    remove_undefined_fields,
    unquote,
)


class TestRemoveUndefinedFields(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
