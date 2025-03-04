# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for dotprompt helpers."""

import json
import unittest

import handlebars  # type: ignore

from dotpromptz.helpers import (
    HelperCallable,
    history_helper,
    if_equals_helper,
    json_helper,
    media_helper,
    register_helpers,
    role_helper,
    section_helper,
    unless_equals_helper,
)


class TestHelpers(unittest.TestCase):
    """Test cases for dotprompt helpers."""

    helpers: dict[str, HelperCallable] = {}

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.hb = handlebars.Handlebars()
        register_helpers(self.hb)

    def test_json_helper(self) -> None:
        """Test JSON serialization helper."""

        def render(text: str) -> str:
            return text

        data = {'name': 'test', 'value': 42}
        json_str = json.dumps(data)

        # Test without indentation
        result = json_helper(json_str, render, None)
        self.assertEqual(result, json.dumps(data))

        # Test with indentation
        result = json_helper(json_str, render, 2)
        self.assertEqual(result, json.dumps(data, indent=2))

        # Test error handling
        result = json_helper('invalid json', render, None)
        self.assertTrue(result.startswith('Error serializing JSON'))

    def test_role_helper(self) -> None:
        """Test role marker generation."""

        def render(text: str) -> str:
            return text

        result = role_helper('user', render)
        self.assertEqual(result, '<<>>')

    def test_history_helper(self) -> None:
        """Test history marker generation."""

        def render(text: str) -> str:
            return text

        result = history_helper('', render)
        self.assertEqual(result, '<<>>')

    def test_section_helper(self) -> None:
        """Test section marker generation."""

        def render(text: str) -> str:
            return text

        result = section_helper('test', render)
        self.assertEqual(result, '<<>>')

    def test_media_helper(self) -> None:
        """Test media marker generation."""

        def render(text: str) -> str:
            return text

        # Test with content type
        result = media_helper('test.png image/png', render)
        self.assertEqual(result, '<<>>')

        # Test without content type
        result = media_helper('test.png', render)
        self.assertEqual(result, '<<>>')

    def test_if_equals_helper(self) -> None:
        """Test ifEquals helper."""

        def render(text: str) -> str:
            return text

        # Test equal values
        result = if_equals_helper('test | test | equal', render)
        self.assertEqual(result, 'equal')

        # Test unequal values
        result = if_equals_helper('test | other | equal', render)
        self.assertEqual(result, '')

        # Test invalid format
        result = if_equals_helper('test | other', render)
        self.assertEqual(result, '')

    def test_unless_equals_helper(self) -> None:
        """Test unlessEquals helper."""

        def render(text: str) -> str:
            return text

        # Test equal values
        result = unless_equals_helper('test | test | not equal', render)
        self.assertEqual(result, '')

        # Test unequal values
        result = unless_equals_helper('test | other | not equal', render)
        self.assertEqual(result, 'not equal')

        # Test invalid format
        result = unless_equals_helper('test | other', render)
        self.assertEqual(result, '')

    # TODO: Re-enable this test once we have a way to render templates.
    @unittest.skip('Skipping template rendering test')
    def test_template_rendering(self) -> None:
        """Test helpers in actual template rendering."""
        template = """
        {{#json}}{"test": "value"}{{/json}}
        {{#role}}user{{/role}}
        {{#history}}{{/history}}
        {{#section}}test{{/section}}
        {{#media}}test.png image/png{{/media}}
        {{#ifEquals}}a | a | equal{{/ifEquals}}
        {{#unlessEquals}}a | b | not equal{{/unlessEquals}}
        """

        hbars = handlebars.Handlebars()  # Corrected import
        hbars.register_helper('json', json_helper)
        hbars.register_helper('role', role_helper)
        hbars.register_helper('history', history_helper)
        hbars.register_helper('section', section_helper)
        hbars.register_helper('media', media_helper)
        hbars.register_helper('ifEquals', if_equals_helper)
        hbars.register_helper('unlessEquals', unless_equals_helper)

        result = hbars.render(template, {'test': 'value'})

        expected_json = json.dumps({'test': 'value'})
        self.assertIn(expected_json, result)
        self.assertIn('<<>>', result)
        self.assertIn('<<>>', result)
        self.assertIn('<<>>', result)
        self.assertIn('<<>>', result)
        self.assertIn('equal', result)
        self.assertIn('not equal', result)


if __name__ == '__main__':
    unittest.main()
