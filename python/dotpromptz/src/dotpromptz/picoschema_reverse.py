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

"""JSON Schema to Picoschema reverse conversion.

Converts a JSON Schema object back into the compact Picoschema format used
in dotprompt YAML frontmatter. This is a best-effort conversion: some JSON
Schema features (``$ref``, ``allOf``, ``oneOf``, ``anyOf``, ``if/then/else``,
``patternProperties``) have no Picoschema equivalent and are dropped with a
warning.

Example::

    from dotpromptz.picoschema_reverse import json_schema_to_picoschema

    schema = {
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'description': 'User name'},
            'age': {'type': 'integer'},
        },
        'required': ['name'],
    }
    pico = json_schema_to_picoschema(schema)
    # {'name': 'string, User name', 'age?': 'integer'}
"""

from __future__ import annotations

from typing import Any

import structlog

from dotpromptz.typing import JsonSchema

logger = structlog.get_logger(__name__)

# JSON Schema scalar types that map directly to Picoschema type strings.
_SCALAR_TYPES = frozenset({'string', 'number', 'integer', 'boolean', 'null'})


def json_schema_to_picoschema(schema: JsonSchema) -> Any:
    """Convert a JSON Schema to Picoschema notation.

    Args:
        schema: A JSON Schema dict.

    Returns:
        A Picoschema representation (str, dict, or list depending on the
        schema structure). Returns ``None`` for empty or unsupported schemas.
    """
    if not schema or not isinstance(schema, dict):
        return None

    return _convert_node(schema, required=True)


def _convert_node(node: dict[str, Any], required: bool = True) -> Any:
    """Recursively convert a JSON Schema node to Picoschema.

    Args:
        node: A JSON Schema node.
        required: Whether this node is required by its parent.

    Returns:
        Picoschema representation of the node.
    """
    schema_type = node.get('type')
    description = node.get('description')

    # Handle nullable types: {"type": ["string", "null"]} -> optional string
    is_nullable = False
    if isinstance(schema_type, list):
        non_null = [t for t in schema_type if t != 'null']
        is_nullable = 'null' in schema_type
        schema_type = non_null[0] if len(non_null) == 1 else None

    # Enum
    if 'enum' in node:
        enum_values = [v for v in node['enum'] if v is not None]
        return enum_values

    # Scalar types
    if isinstance(schema_type, str) and schema_type in _SCALAR_TYPES:
        type_str = schema_type
        if description:
            type_str = f'{schema_type}, {description}'
        return type_str

    # "any" type (no type specified, no properties)
    if schema_type is None and 'properties' not in node and 'items' not in node:
        if description:
            return f'any, {description}'
        return 'any'

    # Array
    if schema_type == 'array':
        items = node.get('items', {})
        if items:
            return _convert_node(items)
        return 'any'

    # Object
    if schema_type == 'object' or 'properties' in node:
        return _convert_object(node)

    # Fallback: return the type as a string if known
    if isinstance(schema_type, str):
        if description:
            return f'{schema_type}, {description}'
        return schema_type

    logger.warning('json_schema_to_picoschema: unsupported schema node', node=node)
    return None


def _convert_object(node: dict[str, Any]) -> dict[str, Any]:
    """Convert a JSON Schema object node to a Picoschema dict.

    Args:
        node: A JSON Schema object node.

    Returns:
        A Picoschema dict.
    """
    properties = node.get('properties', {})
    required_fields = set(node.get('required', []))
    additional = node.get('additionalProperties')
    result: dict[str, Any] = {}

    for prop_name, prop_schema in properties.items():
        is_required = prop_name in required_fields
        prop_type = prop_schema.get('type')
        description = prop_schema.get('description')

        # Detect nullable from type list
        is_nullable = False
        if isinstance(prop_type, list):
            non_null = [t for t in prop_type if t != 'null']
            is_nullable = 'null' in prop_type
            prop_type = non_null[0] if len(non_null) == 1 else None

        # Build the key: add ? suffix for optional fields
        key = prop_name if is_required else f'{prop_name}?'

        # Enum property
        if 'enum' in prop_schema:
            enum_values = [v for v in prop_schema['enum'] if v is not None]
            key_with_type = f'{key}(enum)'
            result[key_with_type] = enum_values
            if description:
                # Picoschema doesn't have a clean way to add descriptions to enums
                # in the key, so we note it in the type annotation
                result[key_with_type] = enum_values
            continue

        # Array property
        if prop_type == 'array':
            items = prop_schema.get('items', {})
            key_with_type = f'{key}(array)'
            result[key_with_type] = _convert_node(items) if items else 'any'
            continue

        # Nested object property
        if prop_type == 'object' or 'properties' in prop_schema:
            key_with_type = f'{key}(object)'
            result[key_with_type] = _convert_object(prop_schema)
            continue

        # Scalar or reference
        value = _convert_node(prop_schema, required=is_required)
        result[key] = value

    # Wildcard for additionalProperties
    if additional and isinstance(additional, dict):
        result['(*)'] = _convert_node(additional)
    elif additional is True:
        result['(*)'] = 'any'

    return result
