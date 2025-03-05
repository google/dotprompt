# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0
"""Tests for dotprompt helpers."""

import json
import unittest
from collections.abc import Callable
from typing import Any

from handlebars import Handlebars  # type: ignore

from dotpromptz.helpers import (
    if_equals_helper,
    register_helpers,
)

RenderCallable = Callable[[str], str]
HelperCallable = Callable[[Any, RenderCallable, int | None], str]


class TestHelpers(unittest.TestCase):
    """Test cases for dotprompt helpers."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        hb = Handlebars()
        register_helpers(hb)
        self.hb = hb

    def test_json_helper(self) -> None:
        """Test JSON serialization helper."""
        data = {'name': 'test', 'value': 42}
        json_str = json.dumps(data)
        template = self.hb.compile('{{json value}}')
        result = template({'value': json_str})
        self.assertEqual(result, json.dumps(data))
        # Test error handling
        template = self.hb.compile("{{json 'invalid json'}}")
        result = template({})
        self.assertTrue(result.startswith('Error serializing JSON'))

    # Updated history helper test
    def test_history_helper(self) -> None:
        """Test history marker generation."""
        template = self.hb.compile("{{history 'test'}}")
        result = template({})
        self.assertEqual(result, '<<history>>test<</history>>')  # Fixed

    # Fixed section helper test
    def test_section_helper(self) -> None:
        """Test section marker generation."""
        template = self.hb.compile("{{section 'test'}}")
        result = template({})
        self.assertEqual(result, '<<section test>>')  # Fixed

    # Correct media helper tests
    # helpers_test.py
    def test_role_helper(self) -> None:
        """Test role marker generation."""
        template = self.hb.compile("{{role 'user'}}")
        result = template({})
        self.assertEqual(result, '<<user>>')  # Changed from <>

    def test_media_helper(self) -> None:
        """Test media marker generation."""
        template = self.hb.compile("{{media 'test.png image/png'}}")
        result = template({})
        self.assertEqual(result, '<<media url="test.png" type="image/png" >>')

    def test_if_equals_helper(self) -> None:
        """Test ifEquals helper."""

        def render(text: str) -> str:
            return text

        # Example test with explicit type annotations for options
        options = {
            'fn': lambda this=None: 'equal',
            'inverse': lambda this=None: 'not equal',
        }
        result = if_equals_helper('test', 'test', options)
        self.assertEqual(result, 'equal')

    def test_unless_equals_helper(self) -> None:
        """Test unlessEquals helper."""
        template = self.hb.compile(
            '{{#unlessEquals arg1 arg2}}not equal{{else}}equal{{/unlessEquals}}'
        )
        # Test equal values
        result = template({'arg1': 'test', 'arg2': 'test'})
        self.assertEqual(result, 'equal')
        # Test unequal values
        result = template({'arg1': 'test', 'arg2': 'other'})
        self.assertEqual(result, 'not equal')

    def test_template_rendering(self) -> None:
        """Test helpers in actual template rendering."""
        template = self.hb.compile("""
        {{json value}}
        {{role 'user'}}
        {{history 'test'}}
        {{section 'test'}}
        {{media 'test.png image/png'}}
        {{#ifEquals arg1 arg1}}equal{{else}}not equal{{/ifEquals}}
        {{#unlessEquals arg1 arg2}}not equal{{else}}equal{{/unlessEquals}}
        """)
        data = {'value': '{"test": "value"}', 'arg1': 'a', 'arg2': 'b'}
        result = template(data)
        expected_json = json.dumps({'test': 'value'})
        self.assertIn(expected_json, result)
        self.assertIn('<<user>>', result)
        self.assertIn('<>', result)
        self.assertIn('<>', result)
        self.assertIn('<>', result)
        self.assertIn('equal', result)
        self.assertIn('not equal', result)


# Test main block
if __name__ == '__main__':
    unittest.main()
