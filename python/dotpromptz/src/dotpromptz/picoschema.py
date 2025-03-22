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

"""Picoschema parser and related helpers."""

import re
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

from dotpromptz.typing import JsonSchema, SchemaResolver

JSON_SCHEMA_SCALAR_TYPES = [
    'string',
    'boolean',
    'null',
    'number',
    'integer',
    'any',
]

WILDCARD_PROPERTY_NAME = '(*)'


class PicoschemaOptions(BaseModel):
    """
    Picoschema options.

    Attributes:
        schema_resolver: Schema resolver.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    schema_resolver: SchemaResolver | None = Field(default=None)


def picoschema(
    schema: Any, options: PicoschemaOptions | None = None
) -> JsonSchema | None:
    return PicoschemaParser(options).parse(schema)


class PicoschemaParser:
    def __init__(self, options: PicoschemaOptions | None = None):
        self.schema_resolver = options.schema_resolver if options else None

    def must_resolve_schema(self, schema_name: str) -> JsonSchema:
        if not self.schema_resolver:
            raise ValueError(
                f"Picoschema: unsupported scalar type '{schema_name}'."
            )

        val = self.schema_resolver(schema_name)
        if not val:
            raise ValueError(
                f"Picoschema: could not find schema with name '{schema_name}'"
            )
        return val

    def parse(self, schema: Any) -> JsonSchema | None:
        if not schema:
            return None

        if isinstance(schema, str):
            type_name, description = extract_description(schema)
            if type_name in JSON_SCHEMA_SCALAR_TYPES:
                out: JsonSchema = {'type': type_name}
                if description:
                    out['description'] = description
                return out
            resolved_schema = self.must_resolve_schema(type_name)
            return (
                {**resolved_schema, 'description': description}
                if description
                else resolved_schema
            )

        if isinstance(schema, dict):
            maybe_type_name = schema.get('type')
            if (
                maybe_type_name
                and isinstance(maybe_type_name, str)
                and (
                    maybe_type_name in JSON_SCHEMA_SCALAR_TYPES
                    or maybe_type_name in ['object', 'array']
                )
            ):
                return cast(JsonSchema, schema)

        if isinstance(schema, dict) and isinstance(
            schema.get('properties'), dict
        ):
            return {**cast(JsonSchema, schema), 'type': 'object'}

        return self.parse_pico(schema)

    def parse_pico(self, obj: Any, path: list[str] | None = None) -> JsonSchema:
        if path is None:
            path = []

        if isinstance(obj, str):
            type_name, description = extract_description(obj)
            if type_name not in JSON_SCHEMA_SCALAR_TYPES:
                resolved_schema = self.must_resolve_schema(type_name)
                return (
                    {**resolved_schema, 'description': description}
                    if description
                    else resolved_schema
                )

            if type_name == 'any':
                return {'description': description} if description else {}

            return (
                {'type': type_name, 'description': description}
                if description
                else {'type': type_name}
            )
        elif not isinstance(obj, dict):
            raise ValueError(
                f'Picoschema: only consists of objects and strings. Got: {obj}'
            )

        schema: JsonSchema = {
            'type': 'object',
            'properties': {},
            'required': [],
            'additionalProperties': False,
        }

        for key, value in obj.items():
            if key == WILDCARD_PROPERTY_NAME:
                schema['additionalProperties'] = self.parse_pico(
                    value, [*path, key]
                )
                continue

            parts = key.split('(')
            name = parts[0]
            type_info = parts[1][:-1] if len(parts) > 1 else None
            is_optional = name.endswith('?')
            property_name = name[:-1] if is_optional else name

            if not is_optional:
                schema['required'].append(property_name)

            if not type_info:
                prop = self.parse_pico(value, [*path, key])
                if is_optional and isinstance(prop.get('type'), str):
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
                continue

            type_name, description = extract_description(type_info)
            if type_name == 'array':
                prop = self.parse_pico(value, [*path, key])
                schema['properties'][property_name] = {
                    'type': ['array', 'null'] if is_optional else 'array',
                    'items': prop,
                }
            elif type_name == 'object':
                prop = self.parse_pico(value, [*path, key])
                if is_optional:
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
            elif type_name == 'enum':
                prop = {'enum': value}
                if is_optional and None not in prop['enum']:
                    prop['enum'].append(None)
                schema['properties'][property_name] = prop
            else:
                raise ValueError(
                    "Picoschema: parenthetical types must be 'object' or "
                    f"'array', got: {type_name}"
                )

            if description:
                schema['properties'][property_name]['description'] = description

        if not schema['required']:
            del schema['required']
        return schema


def extract_description(input_str: str) -> tuple[str, str | None]:
    if ',' not in input_str:
        return input_str, None

    match = re.match(r'(.*?), *(.*)$', input_str)
    if match:
        return match.group(1), match.group(2)
    else:
        return input_str, None
