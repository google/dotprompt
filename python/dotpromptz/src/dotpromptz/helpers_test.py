# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for dotprompt helpers."""

import json
import unittest
from typing import Any

from dotpromptz.helpers import (
    register_helpers,
    render,
)


class TestHelpers(unittest.TestCase):
    def setUp(self) -> None:
        """Set up the test environment."""
        register_helpers()

    def assert_renders(
        self, template: str, data: dict[str, Any], expected_result: str
    ) -> None:
        """Assert that the template renders the expected result.

        Args:
            template: The template to render.
            data: The data to render the template with.
            expected_result: The expected result of the template.


        Raises:
            AssertionError: If the template does not render the expected result.

        Returns:
            None
        """
        actual = render(template, data)
        self.assertEqual(
            actual,
            expected_result,
            f'Expected to render `{expected_result}`, got `{actual}`',
        )

    def test_json_helper(self) -> None:
        data = {'name': 'test', 'value': 42}
        json_str = json.dumps(data)
        self.assert_renders('{{json this.value}}', {'value': data}, json_str)

    def test_json_helper_indented(self) -> None:
        data = {'name': 'test', 'value': 42}
        json_str = json.dumps(data, indent=4)
        self.assert_renders(
            '{{json this.value hash={"indent": 4}}}', {'value': data}, json_str
        )

    def test_history_helper(self) -> None:
        self.assert_renders(
            '{{history}}',
            {},
            '<<<dotprompt:history>>>',
        )

    def test_section_helper(self) -> None:
        self.assert_renders(
            '{{section "test"}}', {}, '<<<dotprompt:section test>>>'
        )

    def test_role_helper(self) -> None:
        self.assert_renders('{{role "user"}}', {}, '<<<dotprompt:role:user>>>')
        self.assert_renders(
            '{{role "system"}}', {}, '<<<dotprompt:role:system>>>'
        )
        self.assert_renders(
            '{{role "model"}}', {}, '<<<dotprompt:role:model>>>'
        )

    def test_media_helper(self) -> None:
        self.assert_renders(
            '{{media hash="{"url": "test.png", "contentType": "image/png"}"}}',
            {},
            '<<<dotprompt:media:url test.png image/png>>>',
        )

    def test_if_equals_helper_when_equal(self) -> None:
        self.assert_renders(
            '{{#ifEquals a b}}equal{{else}}not equal{{/ifEquals}}',
            {'a': 'a', 'b': 'a'},
            'equal',
        )

    def test_if_equals_helper_when_unequal(self) -> None:
        self.assert_renders(
            '{{#ifEquals a b}}equal{{else}}not equal{{/ifEquals}}',
            {'a': 'a', 'b': 'b'},
            'not equal',
        )

    def test_unless_equals_helper_when_equal(self) -> None:
        self.assert_renders(
            '{{#unlessEquals a b}}not equal{{else}}equal{{/unlessEquals}}',
            {'a': 'test', 'b': 'test'},
            'equal',
        )

    def test_unless_equals_helper_when_unequal(self) -> None:
        self.assert_renders(
            '{{#unlessEquals a b}}not equal{{else}}equal{{/unlessEquals}}',
            {'a': 'test', 'b': 'other'},
            'not equal',
        )

    def test_template_rendering(self) -> None:
        data = {'value': '{"test": "value"}', 'arg1': 'a', 'arg2': 'b'}
        result = render(
            """
            {{json this.value}}
            {{role 'user'}}
            {{history}}
            {{section 'test'}}
            {{media hash="{\"url\": \"test.png\", \"contentType\": \"image/png\"}" }}
            {{#ifEquals arg1 arg1}}equal{{else}}not equal{{/ifEquals}}
            {{#unlessEquals arg1 arg2}}not equal{{else}}equal{{/unlessEquals}}
        """,
            data,
        )
        expected_json = json.dumps({'test': 'value'})
        self.assertIn(expected_json, result)
        self.assertIn('<<<dotprompt:role:user>>>', result)
        self.assertIn('<<<dotprompt:history>>>', result)
        self.assertIn('<<<dotprompt:section test>>>', result)
        self.assertIn('<<<dotprompt:media:url test.png image/png>>>', result)
        self.assertIn('equal', result)
        self.assertIn('not equal', result)


if __name__ == '__main__':
    unittest.main()
