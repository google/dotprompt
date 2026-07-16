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

"""Picoschema parser and JSON Schema compiler.

Picoschema is a compact, YAML-optimized schema definition format designed for
describing structured data in generative AI prompts. It compiles to JSON Schema.

Key Features:
    - Basic types: string, number, integer, boolean, null, any
    - Optional fields with `?` suffix (e.g., `name?: string`)
    - Inline descriptions with comma separator (e.g., `age: integer, User's age`)
    - Arrays: `tags(array): string`
    - Nested objects: `address(object): ...`
    - Enums: `status(enum): [PENDING, APPROVED, REJECTED]`
    - Wildcards: `(*): any` for additional properties

Example:
    ```yaml
    product:
      id: string, Unique identifier
      price: number, Current price
      tags(array): string
      category(enum): [ELECTRONICS, CLOTHING]
    ```

See Also:
    Full Picoschema reference: https://google.github.io/dotprompt/extending/picoschema/
"""

import re
from typing import Any, cast

from dotpromptz.resolvers import resolve_json_schema
from dotpromptz.typing import JsonSchema, SchemaResolver

JSON_SCHEMA_SCALAR_TYPES = [
    'any',
    'boolean',
    'integer',
    'null',
    'number',
    'string',
]

WILDCARD_PROPERTY_NAME = '(*)'


def _is_json_schema(schema: dict[str, Any]) -> bool:
    """Checks if a schema is already in JSON Schema format.

    Args:
        schema: The schema to check.

    Returns:
        True if the schema is already in JSON Schema format, False otherwise.
    """
    types = JSON_SCHEMA_SCALAR_TYPES + ['object', 'array']
    return (
        isinstance(schema, dict)  # force format
        and isinstance(schema.get('type'), str)  # force format
        and schema['type'] in types  # force format
    )


async def picoschema_to_json_schema(schema: Any, schema_resolver: SchemaResolver | None = None) -> JsonSchema | None:
    """Parses a Picoschema definition into a JSON Schema.

    Args:
        schema: The Picoschema definition (can be a dict or string).
        schema_resolver: Optional callable to resolve named schema references.

    Returns:
        The equivalent JSON Schema, or None if the input schema is None.
    """
    return await PicoschemaParser(schema_resolver).parse(schema)


def picoschema_to_json_schema_sync(schema: Any) -> JsonSchema | None:
    """Parses a Picoschema definition into a JSON Schema (synchronous).

    This sync version works for schemas using only built-in scalar types
    (string, number, integer, boolean, null, any). Use the async version
    if you need to resolve named schema references.

    Args:
        schema: The Picoschema definition (can be a dict or string).

    Returns:
        The equivalent JSON Schema, or None if the input schema is None.

    Raises:
        ValueError: If the schema references a named type that requires resolution.
    """
    return PicoschemaParser(schema_resolver=None).parse_sync(schema)


class PicoschemaParser:
    """Parses Picoschema definitions into JSON Schema.

    Handles basic types, optional fields, descriptions, arrays, objects,
    enums, wildcards, and named schema resolution.
    """

    def __init__(self, schema_resolver: SchemaResolver | None = None):
        """Initializes the PicoschemaParser.

        Args:
            schema_resolver: Optional callable to resolve named schema references.
        """
        self._schema_resolver = schema_resolver

    async def must_resolve_schema(self, schema_name: str) -> JsonSchema:
        """Resolves a named schema using the configured resolver.

        Args:
            schema_name: The name of the schema to resolve.

        Returns:
            The resolved JSON Schema.

        Raises:
            ValueError: If no schema resolver is configured or the schema
                        name is not found.
        """
        if not self._schema_resolver:
            raise ValueError(f"Picoschema: unsupported scalar type '{schema_name}'.")

        val = await resolve_json_schema(schema_name, self._schema_resolver)
        if not val:
            raise ValueError(f"Picoschema: could not find schema with name '{schema_name}'")
        return val

    async def parse(self, schema: Any) -> JsonSchema | None:
        """Parses a schema, detecting if it's Picoschema or JSON Schema.

        If the input looks like standard JSON Schema (contains top-level 'type'
        or 'properties'), it's returned directly. Otherwise, it's parsed as
        Picoschema.

        Args:
            schema: The schema definition to parse.

        Returns:
            The resulting JSON Schema, or None if the input is None.
        """
        if not schema:
            return None

        if isinstance(schema, str):
            type_name, description = extract_description(schema)
            if type_name in JSON_SCHEMA_SCALAR_TYPES:
                out: JsonSchema = {'type': type_name}
                if description:
                    out['description'] = description
                return out
            resolved_schema = await self.must_resolve_schema(type_name)
            return {**resolved_schema, 'description': description} if description else resolved_schema

        if isinstance(schema, dict) and _is_json_schema(schema):
            return cast(JsonSchema, schema)

        if isinstance(schema, dict) and isinstance(schema.get('properties'), dict):
            return {**cast(JsonSchema, schema), 'type': 'object'}

        # If the schema is not a JSON Schema, parse it as Picoschema.
        return await self.parse_pico(schema)

    def parse_sync(self, schema: Any) -> JsonSchema | None:
        """Parses a schema synchronously (no schema resolution support).

        Args:
            schema: The schema definition to parse.

        Returns:
            The resulting JSON Schema, or None if the input is None.

        Raises:
            ValueError: If the schema references a named type that requires resolution.
        """
        if not schema:
            return None

        if isinstance(schema, str):
            type_name, description = extract_description(schema)
            if type_name in JSON_SCHEMA_SCALAR_TYPES:
                out: JsonSchema = {'type': type_name}
                if description:
                    out['description'] = description
                return out
            raise ValueError(f"Picoschema: unsupported scalar type '{type_name}'. Use async version for schema resolution.")

        if isinstance(schema, dict) and _is_json_schema(schema):
            return cast(JsonSchema, schema)

        if isinstance(schema, dict) and isinstance(schema.get('properties'), dict):
            return {**cast(JsonSchema, schema), 'type': 'object'}

        return self.parse_pico_sync(schema)

    async def parse_pico(self, obj: Any, path: list[str] | None = None) -> JsonSchema:
        """Recursively parses a Picoschema object or string fragment.

        Args:
            obj: The Picoschema fragment (dict or string).
            path: The current path within the schema structure (for error reporting).

        Returns:
            The JSON Schema representation of the fragment.

        Raises:
            ValueError: If the schema structure is invalid.
        """
        if path is None:
            path = []

        if isinstance(obj, str):
            type_name, description = extract_description(obj)
            if type_name not in JSON_SCHEMA_SCALAR_TYPES:
                resolved_schema = await self.must_resolve_schema(type_name)
                return {**resolved_schema, 'description': description} if description else resolved_schema

            if type_name == 'any':
                return {'description': description} if description else {}

            return {'type': type_name, 'description': description} if description else {'type': type_name}
        elif not isinstance(obj, dict):
            raise ValueError(f'Picoschema: only consists of objects and strings. Got: {obj}')

        schema: dict[str, Any] = {
            'type': 'object',
            'properties': {},
            'required': [],
            'additionalProperties': False,
        }

        for key, value in obj.items():
            if key == WILDCARD_PROPERTY_NAME:
                schema['additionalProperties'] = await self.parse_pico(value, [*path, key])
                continue

            parts = key.split('(')
            name = parts[0]
            type_info = parts[1][:-1] if len(parts) > 1 else None
            is_optional = name.endswith('?')
            property_name = name[:-1] if is_optional else name

            if not is_optional:
                schema['required'].append(property_name)

            if not type_info:
                prop = await self.parse_pico(value, [*path, key])
                if is_optional and isinstance(prop.get('type'), str):
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
                continue

            type_name, description = extract_description(type_info)
            if type_name == 'array':
                prop = await self.parse_pico(value, [*path, key])
                schema['properties'][property_name] = {
                    'type': ['array', 'null'] if is_optional else 'array',
                    'items': prop,
                }
            elif type_name == 'object':
                prop = await self.parse_pico(value, [*path, key])
                if is_optional:
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
            elif type_name == 'enum':
                prop = {'enum': value}
                if is_optional and None not in prop['enum']:
                    prop['enum'].append(None)
                schema['properties'][property_name] = prop
            else:
                raise ValueError(f"Picoschema: parenthetical types must be 'object' or 'array', got: {type_name}")

            if description:
                schema['properties'][property_name]['description'] = description

        if not schema['required']:
            del schema['required']
        return schema

    def parse_pico_sync(self, obj: Any, path: list[str] | None = None) -> JsonSchema:
        """Recursively parses a Picoschema object synchronously.

        Args:
            obj: The Picoschema fragment (dict or string).
            path: The current path within the schema structure (for error reporting).

        Returns:
            The JSON Schema representation of the fragment.

        Raises:
            ValueError: If the schema references a named type or is invalid.
        """
        if path is None:
            path = []

        if isinstance(obj, str):
            type_name, description = extract_description(obj)
            if type_name not in JSON_SCHEMA_SCALAR_TYPES:
                raise ValueError(f"Picoschema: unsupported scalar type '{type_name}'. Use async version for schema resolution.")

            if type_name == 'any':
                return {'description': description} if description else {}

            return {'type': type_name, 'description': description} if description else {'type': type_name}
        elif not isinstance(obj, dict):
            raise ValueError(f'Picoschema: only consists of objects and strings. Got: {obj}')

        schema: dict[str, Any] = {
            'type': 'object',
            'properties': {},
            'required': [],
            'additionalProperties': False,
        }

        for key, value in obj.items():
            if key == WILDCARD_PROPERTY_NAME:
                schema['additionalProperties'] = self.parse_pico_sync(value, [*path, key])
                continue

            parts = key.split('(')
            name = parts[0]
            type_info = parts[1][:-1] if len(parts) > 1 else None
            is_optional = name.endswith('?')
            property_name = name[:-1] if is_optional else name

            if not is_optional:
                schema['required'].append(property_name)

            if not type_info:
                prop = self.parse_pico_sync(value, [*path, key])
                if is_optional and isinstance(prop.get('type'), str):
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
                continue

            type_name, description = extract_description(type_info)
            if type_name == 'array':
                prop = self.parse_pico_sync(value, [*path, key])
                schema['properties'][property_name] = {
                    'type': ['array', 'null'] if is_optional else 'array',
                    'items': prop,
                }
            elif type_name == 'object':
                prop = self.parse_pico_sync(value, [*path, key])
                if is_optional:
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
            elif type_name == 'enum':
                prop = {'enum': value}
                if is_optional and None not in prop['enum']:
                    prop['enum'].append(None)
                schema['properties'][property_name] = prop
            else:
                raise ValueError(f"Picoschema: parenthetical types must be 'object' or 'array', got: {type_name}")

            if description:
                schema['properties'][property_name]['description'] = description

        if not schema['required']:
            del schema['required']
        return schema


def extract_description(input_str: str) -> tuple[str, str | None]:
    """Extracts the type/name and optional description from a Picoschema string.

    Splits a string like "type, description" into ("type", "description").

    Args:
        input_str: The Picoschema string definition.

    Returns:
        A tuple containing the type/name and the description (or None).
    """
    if ',' not in input_str:
        return input_str, None

    match = re.match(r'(.*?), *(.*)$', input_str)
    if match:
        return match.group(1), match.group(2)
    else:
        return input_str, None
