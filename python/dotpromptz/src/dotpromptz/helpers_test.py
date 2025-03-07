import json
import unittest
from typing import Any, Dict

from django.utils.safestring import SafeString
from handlebars import Handlebars

from dotpromptz.helpers import hbs, render


class TestHelpers(unittest.TestCase):
    def assert_renders(self, template: str, data: Dict[str, Any], expected_result: str) -> None:
        actual = render(template, data).strip()
        self.assertEqual(actual, expected_result)

    def test_json_helper(self) -> None:
        data = {'name': 'test', 'value': 42}
        json_str = json.dumps(data)
        self.assert_renders('{{json this.value}}', {'value': data}, json_str)

    def test_history_helper(self) -> None:
        self.assert_renders('{{history}}', {}, '<<history>>')

    def test_section_helper(self) -> None:
        self.assert_renders('{{section "test"}}', {}, '<<section:test>>')

    def test_role_helper(self) -> None:
        self.assert_renders('{{role "user"}}', {}, '<<role:user>>')

    def test_media_helper(self) -> None:
        self.assert_renders(
            '{{media "image/png" "test.png"}}',
            {},
            '<<media:test.png image/png>>',
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

if __name__ == '__main__':
    unittest.main()
