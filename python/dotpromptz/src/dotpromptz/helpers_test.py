import json
import unittest
from typing import Any, Callable, Optional

from handlebars import Handlebars  # type: ignore

from dotpromptz.helpers import (
    history_helper,
    if_equals_helper,
    json_helper,
    media_helper,
    register_helpers,
    role_helper,
    section_helper,
    unless_equals_helper,
)

RenderCallable = Callable[[str], str]


class TestHelpers(unittest.TestCase):
    def setUp(self) -> None:
        # Use the Handlebars object directly without calling it.
        hb = Handlebars
        register_helpers(hb)
        self.hb = hb

    def test_json_helper(self) -> None:
        data = {"name": "test", "value": 42}
        json_str = json.dumps(data)
        template = self.hb.compile("{{json value}}")
        result = template({"value": json_str})
        self.assertEqual(result, json.dumps(data))

    def test_history_helper(self) -> None:
        template = self.hb.compile("{{history 'test'}}")
        result = template({})
        self.assertEqual(result, "<<history>>test<</history>>")

    def test_section_helper(self) -> None:
        template = self.hb.compile("{{section 'test'}}")
        result = template({})
        self.assertEqual(result, "<<section test>>")

    def test_role_helper(self) -> None:
        template = self.hb.compile("{{role 'user'}}")
        result = template({})
        self.assertEqual(result, "<<user>>")

    def test_media_helper(self) -> None:
        template = self.hb.compile("{{media 'test.png image/png'}}")
        result = template({})
        self.assertEqual(result, "<>")

    def test_if_equals_helper(self) -> None:
        options = {"fn": lambda: "equal", "inverse": lambda: "not equal"}
        result = if_equals_helper("test", "test", options)
        self.assertEqual(result, "equal")

    def test_unless_equals_helper(self) -> None:
        template = self.hb.compile(
            "{{#unlessEquals arg1 arg2}}not equal{{else}}equal{{/unlessEquals}}"
        )
        # When arg1 and arg2 are equal, the inverse block should render.
        result = template({"arg1": "test", "arg2": "test"})
        self.assertEqual(result, "equal")
        # When arguments differ, the main block should render.
        result = template({"arg1": "test", "arg2": "other"})
        self.assertEqual(result, "not equal")

    def test_template_rendering(self) -> None:
        template = self.hb.compile(
            """
            {{json value}}
            {{role 'user'}}
            {{history 'test'}}
            {{section 'test'}}
            {{media 'test.png image/png'}}
            {{#ifEquals arg1 arg1}}equal{{else}}not equal{{/ifEquals}}
            {{#unlessEquals arg1 arg2}}not equal{{else}}equal{{/unlessEquals}}
        """
        )
        data = {"value": '{"test": "value"}', "arg1": "a", "arg2": "b"}
        result = template(data)
        expected_json = json.dumps({"test": "value"})
        self.assertIn(expected_json, result)
        self.assertIn("<<user>>", result)
        self.assertIn("<<history>>test<</history>>", result)
        self.assertIn("<<section test>>", result)
        self.assertIn("<>", result)
        self.assertIn("equal", result)
        self.assertIn("not equal", result)


if __name__ == "__main__":
    unittest.main()
