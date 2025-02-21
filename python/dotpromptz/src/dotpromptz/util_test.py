# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for utility functions."""

import unittest

from dotpromptz.util import remove_undefined_fields


class TestRemoveUndefinedFields(unittest.TestCase):
    def test_remove_undefined_fields_none(self) -> None:
        """Test removing undefined fields from None."""
        assert remove_undefined_fields(None) is None

    def test_remove_undefined_fields_primitive(self) -> None:
        """Test removing undefined fields from primitive types."""
        assert remove_undefined_fields(42) == 42
        assert remove_undefined_fields('test') == 'test'
        assert remove_undefined_fields(True) is True

    def test_remove_undefined_fields_list(self) -> None:
        """Test removing undefined fields from lists."""
        input_list = [1, None, {'a': 2, 'b': None}, [3, None, 4]]
        expected = [1, {'a': 2}, [3, 4]]
        result = remove_undefined_fields(input_list)
        assert result == expected, f'Expected {expected}, but got {result}'

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
        assert result == expected, f'Expected {expected}, but got {result}'

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
        assert result == expected, f'Expected {expected}, but got {result}'

    def test_remove_undefined_fields_empty(self) -> None:
        """Test removing undefined fields from empty structures."""
        assert remove_undefined_fields({}) == {}
        assert remove_undefined_fields([]) == []
        assert remove_undefined_fields({'a': {}}) == {'a': {}}
        assert remove_undefined_fields({'a': []}) == {'a': []}


if __name__ == '__main__':
    unittest.main()
