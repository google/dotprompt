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

"""Tests for picoschema functionality."""

import unittest

from dotpromptz import picoschema
from dotpromptz.typing import JsonSchema


class TestPicoschemaParser(unittest.TestCase):
    """Picoshema parser functionality tests."""

    def setUp(self) -> None:
        self.parser = picoschema.PicoschemaParser(picoschema.PicoschemaOptions())

    def test_must_resolve_schema_success(self) -> None:
        def mock_resolver(name: str) -> JsonSchema | None:
            if name == 'MySchema':
                return {'type': 'object'}
            return None

        parser = picoschema.PicoschemaParser(picoschema.PicoschemaOptions(schema_resolver=mock_resolver))
        result = parser.must_resolve_schema('MySchema')
        self.assertEqual(result, {'type': 'object'})

    def test_must_resolve_schema_not_found(self) -> None:
        def mock_resolver(name: str) -> JsonSchema | None:
            return None

        parser = picoschema.PicoschemaParser(picoschema.PicoschemaOptions(schema_resolver=mock_resolver))
        with self.assertRaises(ValueError) as context:
            parser.must_resolve_schema('NonExistentSchema')
        self.assertEqual(
            str(context.exception),
            "Picoschema: could not find schema with name 'NonExistentSchema'",
        )

    def test_must_resolve_schema_no_resolver(self) -> None:
        with self.assertRaises(ValueError) as context:
            self.parser.must_resolve_schema('AnySchema')
        self.assertEqual(
            str(context.exception),
            "Picoschema: unsupported scalar type 'AnySchema'.",
        )

    def test_parse_no_schema(self) -> None:
        result = self.parser.parse(None)
        self.assertIsNone(result)

    def test_parse_scalar_type_schema(self) -> None:
        result = self.parser.parse('string')
        self.assertEqual(result, {'type': 'string'})

    def test_parse_object_schema(self) -> None:
        schema = {'type': 'object', 'properties': {'name': {'type': 'string'}}}
        expected_schema = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
        }
        result = self.parser.parse(schema)
        self.assertEqual(result, expected_schema)

    def test_parse_invalid_schema_type(self) -> None:
        with self.assertRaises(ValueError):
            self.parser.parse(123)

    def test_parse_named_schema(self) -> None:
        def mock_resolver(name: str) -> JsonSchema | None:
            if name == 'MySchema':
                return {
                    'type': 'object',
                    'properties': {'name': {'type': 'string'}},
                }
            return None

        parser = picoschema.PicoschemaParser(picoschema.PicoschemaOptions(schema_resolver=mock_resolver))
        result = parser.parse('MySchema')
        self.assertEqual(
            result,
            {'type': 'object', 'properties': {'name': {'type': 'string'}}},
        )

    def test_parse_named_schema_with_description(self) -> None:
        def mock_resolver(name: str) -> JsonSchema | None:
            if name == 'MySchema':
                return {
                    'type': 'object',
                    'properties': {'name': {'type': 'string'}},
                }
            return None

        parser = picoschema.PicoschemaParser(picoschema.PicoschemaOptions(schema_resolver=mock_resolver))
        result = parser.parse('MySchema, a schema')
        self.assertEqual(
            result,
            {
                'type': 'object',
                'properties': {'name': {'type': 'string'}},
                'description': 'a schema',
            },
        )

    def test_parse_scalar_type_schema_with_description(self) -> None:
        result = self.parser.parse('string, a string')
        self.assertEqual(result, {'type': 'string', 'description': 'a string'})

    def test_parse_properties_object_shorthand(self) -> None:
        schema = {'name': 'string'}
        expected = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
            'required': ['name'],
            'additionalProperties': False,
        }
        result = self.parser.parse(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_scalar_type(self) -> None:
        result = self.parser.parse_pico('string')
        self.assertEqual(result, {'type': 'string'})

    def test_parse_pico_object_type(self) -> None:
        schema = {'name': 'string'}
        expected = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
            'required': ['name'],
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_array_type(self) -> None:
        schema = {'names(array)': 'string'}
        expected = {
            'type': 'object',
            'properties': {'names': {'type': 'array', 'items': {'type': 'string'}}},
            'required': ['names'],
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_enum_type(self) -> None:
        schema = {'status(enum)': ['active', 'inactive']}
        expected = {
            'type': 'object',
            'properties': {'status': {'enum': ['active', 'inactive']}},
            'required': ['status'],
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_optional_property(self) -> None:
        schema = {'name?': 'string'}
        expected = {
            'type': 'object',
            'properties': {'name': {'type': ['string', 'null']}},
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_wildcard_property(self) -> None:
        schema = {'(*)': 'string'}
        expected = {
            'type': 'object',
            'properties': {},
            'additionalProperties': {'type': 'string'},
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_nested_object(self) -> None:
        schema = {'address(object)': {'street': 'string'}}
        expected = {
            'type': 'object',
            'properties': {
                'address': {
                    'type': 'object',
                    'properties': {'street': {'type': 'string'}},
                    'required': ['street'],
                    'additionalProperties': False,
                }
            },
            'required': ['address'],
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_nested_array(self) -> None:
        schema = {'items(array)': {'props(array)': 'string'}}
        expected = {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'props': {
                                'type': 'array',
                                'items': {
                                    'type': 'string',
                                },
                            }
                        },
                        'required': ['props'],
                        'additionalProperties': False,
                    },
                }
            },
            'required': ['items'],
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_enum_with_optional_and_null(self) -> None:
        schema = {'status?(enum)': ['active', 'inactive']}
        expected = {
            'type': 'object',
            'properties': {'status': {'enum': ['active', 'inactive', None]}},
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_description_on_type(self) -> None:
        schema = {'name': 'string, a name'}
        expected = {
            'type': 'object',
            'properties': {'name': {'type': 'string', 'description': 'a name'}},
            'required': ['name'],
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_description_on_optional_array(self) -> None:
        schema = {'items?(array, list of items)': 'string'}
        expected = {
            'type': 'object',
            'properties': {
                'items': {
                    'type': ['array', 'null'],
                    'items': {'type': 'string'},
                    'description': 'list of items',
                }
            },
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_escription_on_enum(self) -> None:
        schema = {'status(enum, the status)': ['active', 'inactive']}
        expected = {
            'type': 'object',
            'properties': {
                'status': {
                    'enum': ['active', 'inactive'],
                    'description': 'the status',
                }
            },
            'required': ['status'],
            'additionalProperties': False,
        }
        result = self.parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_parse_pico_description_on_custom_schema(self) -> None:
        def mock_resolver(name: str) -> JsonSchema | None:
            if name == 'CustomType':
                return {'type': 'string'}
            return None

        parser = picoschema.PicoschemaParser(picoschema.PicoschemaOptions(schema_resolver=mock_resolver))
        schema = {'field': 'CustomType, a custom type'}
        expected = {
            'type': 'object',
            'properties': {'field': {'type': 'string', 'description': 'a custom type'}},
            'required': ['field'],
            'additionalProperties': False,
        }
        result = parser.parse_pico(schema)
        self.assertEqual(result, expected)

    def test_invalid_input_type(self) -> None:
        with self.assertRaises(ValueError):
            self.parser.parse_pico(123)


class TestExtractDescription(unittest.TestCase):
    """Extract description tests."""

    def test_extract(self) -> None:
        input_str = 'string, a simple string'
        expected = ('string', 'a simple string')
        result = picoschema.extract_description(input_str)
        self.assertEqual(result, expected)

    def test_extract_no_description(self) -> None:
        input_str = 'string'
        expected = ('string', None)
        result = picoschema.extract_description(input_str)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
