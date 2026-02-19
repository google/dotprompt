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

"""Tests for JSON Schema to Picoschema reverse conversion."""

from __future__ import annotations

import unittest

from dotpromptz.picoschema_reverse import json_schema_to_picoschema


class TestJsonSchemaToPicoschema(unittest.TestCase):
    """Tests for json_schema_to_picoschema."""

    def test_empty_schema(self) -> None:
        self.assertIsNone(json_schema_to_picoschema({}))

    def test_none_schema(self) -> None:
        self.assertIsNone(json_schema_to_picoschema(None))

    def test_scalar_string(self) -> None:
        self.assertEqual(json_schema_to_picoschema({'type': 'string'}), 'string')

    def test_scalar_integer(self) -> None:
        self.assertEqual(json_schema_to_picoschema({'type': 'integer'}), 'integer')

    def test_scalar_number(self) -> None:
        self.assertEqual(json_schema_to_picoschema({'type': 'number'}), 'number')

    def test_scalar_boolean(self) -> None:
        self.assertEqual(json_schema_to_picoschema({'type': 'boolean'}), 'boolean')

    def test_scalar_with_description(self) -> None:
        result = json_schema_to_picoschema({'type': 'string', 'description': 'A name'})
        self.assertEqual(result, 'string, A name')

    def test_simple_object(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'},
            },
            'required': ['name', 'age'],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'name': 'string', 'age': 'integer'})

    def test_optional_fields(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'nickname': {'type': 'string'},
            },
            'required': ['name'],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'name': 'string', 'nickname?': 'string'})

    def test_field_with_description(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string', 'description': 'User name'},
            },
            'required': ['name'],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'name': 'string, User name'})

    def test_array_property(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'tags': {'type': 'array', 'items': {'type': 'string'}},
            },
            'required': ['tags'],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'tags(array)': 'string'})

    def test_nested_object(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'address': {
                    'type': 'object',
                    'properties': {
                        'city': {'type': 'string'},
                        'zip': {'type': 'string'},
                    },
                    'required': ['city'],
                },
            },
            'required': ['address'],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'address(object)': {'city': 'string', 'zip?': 'string'}})

    def test_enum_property(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'status': {'enum': ['PENDING', 'APPROVED', 'REJECTED']},
            },
            'required': ['status'],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'status(enum)': ['PENDING', 'APPROVED', 'REJECTED']})

    def test_wildcard_additional_properties(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
            },
            'required': ['name'],
            'additionalProperties': {'type': 'string'},
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'name': 'string', '(*)': 'string'})

    def test_wildcard_additional_properties_true(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
            },
            'required': ['name'],
            'additionalProperties': True,
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'name': 'string', '(*)': 'any'})

    def test_nullable_type(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'value': {'type': ['string', 'null']},
            },
            'required': [],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'value?': 'string'})

    def test_enum_with_null(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'status': {'enum': ['PENDING', 'APPROVED', None]},
            },
            'required': ['status'],
        }
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, {'status(enum)': ['PENDING', 'APPROVED']})

    def test_top_level_array(self) -> None:
        schema = {'type': 'array', 'items': {'type': 'string'}}
        result = json_schema_to_picoschema(schema)
        self.assertEqual(result, 'string')

    def test_any_type(self) -> None:
        result = json_schema_to_picoschema({'description': 'Anything goes'})
        self.assertEqual(result, 'any, Anything goes')


class TestRoundTrip(unittest.IsolatedAsyncioTestCase):
    """Test round-trip: Picoschema -> JSON Schema -> Picoschema."""

    async def test_simple_roundtrip(self) -> None:
        from dotpromptz.picoschema import picoschema_to_json_schema

        pico_input = {
            'name': 'string, User name',
            'age': 'integer',
        }
        json_schema = await picoschema_to_json_schema(pico_input)
        self.assertIsNotNone(json_schema)
        pico_output = json_schema_to_picoschema(json_schema)
        self.assertEqual(pico_output, {'name': 'string, User name', 'age': 'integer'})

    async def test_array_roundtrip(self) -> None:
        from dotpromptz.picoschema import picoschema_to_json_schema

        pico_input = {
            'tags(array)': 'string',
        }
        json_schema = await picoschema_to_json_schema(pico_input)
        self.assertIsNotNone(json_schema)
        pico_output = json_schema_to_picoschema(json_schema)
        self.assertEqual(pico_output, {'tags(array)': 'string'})

    async def test_enum_roundtrip(self) -> None:
        from dotpromptz.picoschema import picoschema_to_json_schema

        pico_input = {
            'status(enum)': ['PENDING', 'APPROVED', 'REJECTED'],
        }
        json_schema = await picoschema_to_json_schema(pico_input)
        self.assertIsNotNone(json_schema)
        pico_output = json_schema_to_picoschema(json_schema)
        self.assertEqual(pico_output, {'status(enum)': ['PENDING', 'APPROVED', 'REJECTED']})


if __name__ == '__main__':
    unittest.main()
