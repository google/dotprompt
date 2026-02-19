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

"""Tests for output schema validation."""

from __future__ import annotations

import unittest

from dotpromptz.validate import SchemaValidationError, validate_output


class TestValidateOutput(unittest.TestCase):
    """Tests for validate_output."""

    def test_valid_object(self) -> None:
        schema = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}},
            'required': ['name'],
        }
        validate_output({'name': 'Alice', 'age': 30}, schema)

    def test_valid_string(self) -> None:
        validate_output('hello', {'type': 'string'})

    def test_valid_number(self) -> None:
        validate_output(42, {'type': 'integer'})

    def test_valid_array(self) -> None:
        validate_output([1, 2, 3], {'type': 'array', 'items': {'type': 'integer'}})

    def test_valid_boolean(self) -> None:
        validate_output(True, {'type': 'boolean'})

    def test_valid_null(self) -> None:
        validate_output(None, {'type': 'null'})

    def test_invalid_type(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_output(123, {'type': 'string'})
        self.assertEqual(len(ctx.exception.errors), 1)
        self.assertIn('<root>', ctx.exception.errors[0])

    def test_missing_required_field(self) -> None:
        schema = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
            'required': ['name'],
        }
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_output({}, schema)
        self.assertIn('name', ctx.exception.errors[0])

    def test_wrong_nested_type(self) -> None:
        schema = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}, 'age': {'type': 'integer'}},
            'required': ['name', 'age'],
        }
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_output({'name': 'Alice', 'age': 'thirty'}, schema)
        self.assertEqual(len(ctx.exception.errors), 1)
        self.assertIn('age', ctx.exception.errors[0])

    def test_multiple_errors(self) -> None:
        schema = {
            'type': 'object',
            'properties': {'a': {'type': 'string'}, 'b': {'type': 'integer'}},
            'required': ['a', 'b'],
        }
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_output({'a': 123, 'b': 'wrong'}, schema)
        self.assertGreaterEqual(len(ctx.exception.errors), 2)

    def test_additional_properties_false(self) -> None:
        schema = {
            'type': 'object',
            'properties': {'name': {'type': 'string'}},
            'additionalProperties': False,
        }
        with self.assertRaises(SchemaValidationError):
            validate_output({'name': 'Alice', 'extra': 'field'}, schema)

    def test_enum_valid(self) -> None:
        validate_output('APPROVED', {'enum': ['PENDING', 'APPROVED', 'REJECTED']})

    def test_enum_invalid(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_output('UNKNOWN', {'enum': ['PENDING', 'APPROVED', 'REJECTED']})

    def test_nested_object_valid(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'address': {
                    'type': 'object',
                    'properties': {'city': {'type': 'string'}},
                    'required': ['city'],
                }
            },
            'required': ['address'],
        }
        validate_output({'address': {'city': 'NYC'}}, schema)

    def test_nested_object_invalid(self) -> None:
        schema = {
            'type': 'object',
            'properties': {
                'address': {
                    'type': 'object',
                    'properties': {'city': {'type': 'string'}},
                    'required': ['city'],
                }
            },
            'required': ['address'],
        }
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_output({'address': {}}, schema)
        self.assertIn('city', ctx.exception.errors[0])

    def test_array_items_invalid(self) -> None:
        schema = {'type': 'array', 'items': {'type': 'integer'}}
        with self.assertRaises(SchemaValidationError):
            validate_output([1, 'two', 3], schema)

    def test_error_message_contains_count(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_output(123, {'type': 'string'})
        self.assertIn('1 error(s)', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
