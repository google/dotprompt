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

"""Picoschema parser and related helpers.

Picoschema is a compact, YAML-optimized schema definition format specifically
designed to aid in describing structured data for better understanding by
generative AI models. Whenever a schema is accepted by dotprompt in its
frontmatter, the Picoschema format is accepted.

Picoschema compiles to JSON Schema and is a subset of JSON Schema capabilities.

## Example:

```yaml
product:
  id: string, Unique identifier for the product
  description?: string, Optional detailed description of the product
  price: number, Current price of the product
  inStock: integer, Number of items in stock
  isActive: boolean, Whether the product is currently available
  category(enum, Main category of the product): [ELECTRONICS, CLOTHING, BOOKS, HOME]
  tags(array, List of tags associated with the product): string
  primaryImage:
    url: string, URL of the primary product image
    altText: string, Alternative text for the image
  attributes(object, Custom attributes of the product):
    (*): any, Allow any attribute name with any value
  variants?(array, List of product variant objects):
    id: string, Unique identifier for the variant
    name: string, Name of the variant
    price: number, Price of the variant
```

## Picoschema Reference

### Basic Types

Picoschema supports the following scalar types:

#### **string**
- **Syntax:** `fieldName: string[, optional description]`
- **Description:** Represents a string value.
- **Example:** `title: string`

#### **number**
- **Syntax:** `fieldName: number[, optional description]`
- **Description:** Represents a numeric value (integer or float).
- **Example:** `price: number`

#### **integer**
- **Syntax:** `fieldName: integer[, optional description]`
- **Description:** Represents an integer value.
- **Example:** `age: integer`

#### **boolean**
- **Syntax:** `fieldName: boolean[, optional description]`
- **Description:** Represents a boolean value.
- **Example:** `isActive: boolean`

#### **null**
- **Syntax:** `fieldName: null[, optional description]`
- **Description:** Represents a null value.
- **Example:** `emptyField: null`

#### **any**
- **Syntax:** `fieldName: any[, optional description]`
- **Description:** Represents a value of any type.
- **Example:** `data: any`

### Optional Fields

- **Syntax:** Add `?` after the field name.
- **Description:** Marks a field as optional. Optional fields are also automatically nullable.
- **Example:** `subtitle?: string`

### Field Descriptions

- **Syntax:** Add a comma followed by the description after the type.
- **Description:** Provides additional information about the field.
- **Example:** `date: string, the date of publication e.g. '2024-04-09'`

### Arrays

- **Syntax:** `fieldName(array[, optional description]): elementType`
- **Description:** Defines an array of a specific type.
- **Example:** `tags(array, string list of tags): string`

### Objects

- **Syntax:** `fieldName(object[, optional description]):`
- **Description:** Defines a nested object structure.
- **Example:**
  ```yaml
  address(object, the address of the recipient):
    address1: string, street address
    address2?: string, optional apartment/unit number etc.
    city: string
    state: string
  ```

### Enums

- **Syntax:** `fieldName(enum[, optional description]): [VALUE1, VALUE2, ...]`
- **Description:** Defines a field with a fixed set of possible values.
- **Example:** `status(enum): [PENDING, APPROVED, REJECTED]`

### Wildcard Fields

- **Syntax:** `(*): type[, optional description]`
- **Description:** Allows additional properties of a specified type in an object.
- **Example:** `(*): string`

### Additional Notes

1. By default, all fields are required unless marked as optional with `?`.
2. Objects defined using Picoschema do not allow additional properties unless a wildcard `(*)` is added.
3. Optional fields are automatically made nullable in the resulting JSON Schema.
4. The `any` type results in an empty schema `{}` in JSON Schema, allowing any value.

## Eject to JSON Schema

Picoschema automatically detects if a schema is already in JSON Schema format.
If the top-level schema contains a `type` property with values like "object",
"array", or any of the scalar types, it's treated as JSON Schema.

You can also explicitly use JSON Schema by defining `{"type": "object"}` at the
top level. For example:

```handlebars
---
output:
  schema:
    type: object # this is now JSON Schema
    properties:
      field1: {type: string, description: A sample field}
---
```

## Error Handling

Picoschema will throw errors in the following cases:

1. If an unsupported scalar type is used.
2. If the schema contains values that are neither objects nor strings.
3. If parenthetical types other than 'object' or 'array' are used (except for 'enum').

These error checks ensure that the Picoschema is well-formed and can be
correctly translated to JSON Schema.
"""

import re
from typing import Any, cast

from dotpromptz.resolvers import resolve_json_schema
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


async def picoschema_to_json_schema(schema: Any, schema_resolver: SchemaResolver | None = None) -> JsonSchema | None:
    """Parses a Picoschema definition into a JSON Schema.

    Args:
        schema: The Picoschema definition (can be a dict or string).
        schema_resolver: Optional callable to resolve named schema references.

    Returns:
        The equivalent JSON Schema, or None if the input schema is None.
    """
    return await PicoschemaParser(schema_resolver).parse(schema)


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

        if isinstance(schema, dict):
            maybe_type_name = schema.get('type')
            if (
                maybe_type_name
                and isinstance(maybe_type_name, str)
                and (maybe_type_name in JSON_SCHEMA_SCALAR_TYPES or maybe_type_name in ['object', 'array'])
            ):
                return cast(JsonSchema, schema)

        if isinstance(schema, dict) and isinstance(schema.get('properties'), dict):
            return {**cast(JsonSchema, schema), 'type': 'object'}

        return await self.parse_pico(schema)

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

        schema: JsonSchema = {
            'type': 'object',
            'properties': {},
            'required': [],
            'additionalProperties': False,
        }

        for key, value in obj.items():
            if key == WILDCARD_PROPERTY_NAME:
                schema['additionalProperties'] = self.parse_pico(value, [*path, key])
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
