# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

JSONSchema = dict[str, Any]
SchemaResolver = Callable[[str], JSONSchema | None]

JSON_SCHEMA_SCALAR_TYPES = [
    'string',
    'boolean',
    'null',
    'number',
    'integer',
    'any',
]

WILDCARD_PROPERTY_NAME = '(*)'


@dataclass
class PicoschemaOptions:
    schema_resolver: SchemaResolver | None = None


async def picoschema(
    schema: Any, options: PicoschemaOptions | None = None
) -> JSONSchema | None:
    return await PicoschemaParser(options).parse(schema)


class PicoschemaParser:
    def __init__(self, options: PicoschemaOptions | None = None):
        self.schema_resolver = options.schema_resolver if options else None

    async def must_resolve_schema(self, schema_name: str) -> JSONSchema:
        if not self.schema_resolver:
            raise ValueError(
                f"Picoschema: unsupported scalar type '{schema_name}'."
            )

        val = await self.schema_resolver(schema_name)
        if not val:
            raise ValueError(
                f"Picoschema: could not find schema with name '{schema_name}'"
            )
        return val

    async def parse(self, schema: Any) -> JSONSchema | None:
        if not schema:
            return None

        # Allow for top-level named schemas
        if isinstance(schema, str):
            type_, description = extract_description(schema)
            if type_ in JSON_SCHEMA_SCALAR_TYPES:
                out: JSONSchema = {'type': type_}
                if description:
                    out['description'] = description
                return out
            resolved_schema = await self.must_resolve_schema(type_)
            return (
                {**resolved_schema, 'description': description}
                if description
                else resolved_schema
            )

        # If there's a JSON schema-ish type at the top level, treat as JSON
        # schema.
        if isinstance(schema, dict) and schema.get('type') in [
            *JSON_SCHEMA_SCALAR_TYPES,
            'object',
            'array',
        ]:
            return schema

        if isinstance(schema, dict) and isinstance(
            schema.get('properties'), dict
        ):
            return {**schema, 'type': 'object'}

        return await self.parse_pico(schema)

    async def parse_pico(
        self, obj: Any, path: list[str] | None = None
    ) -> JSONSchema:
        if path is None:
            path = []

        if isinstance(obj, str):
            type_, description = extract_description(obj)
            if type_ not in JSON_SCHEMA_SCALAR_TYPES:
                resolved_schema = await self.must_resolve_schema(type_)
                if description:
                    resolved_schema = {
                        **resolved_schema,
                        'description': description,
                    }
                return resolved_schema

            if type_ == 'any':
                return {'description': description} if description else {}

            return (
                {'type': type_, 'description': description}
                if description
                else {'type': type_}
            )
        elif not isinstance(obj, dict):
            raise ValueError(
                f'Picoschema: only consists of objects and strings. Got: {obj}'
            )

        schema: JSONSchema = {
            'type': 'object',
            'properties': {},
            'required': [],
            'additionalProperties': False,
        }

        for key, value in obj.items():
            # wildcard property
            if key == WILDCARD_PROPERTY_NAME:
                schema['additionalProperties'] = await self.parse_pico(
                    value, [*path, key]
                )
                continue

            name_parts = key.split('(', 1)
            name = name_parts[0]
            type_info = name_parts[1][:-1] if len(name_parts) > 1 else None
            is_optional = name.endswith('?')
            property_name = name[:-1] if is_optional else name

            if not is_optional:
                schema['required'].append(property_name)

            if not type_info:
                prop = await self.parse_pico(value, [*path, key])
                # make all optional fields also nullable
                if is_optional and isinstance(prop.get('type'), str):
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
                continue

            type_, description = extract_description(type_info)
            if type_ == 'array':
                schema['properties'][property_name] = {
                    'type': ['array', 'null'] if is_optional else 'array',
                    'items': await self.parse_pico(value, [*path, key]),
                }
            elif type_ == 'object':
                prop = await self.parse_pico(value, [*path, key])
                if is_optional:
                    prop['type'] = [prop['type'], 'null']
                schema['properties'][property_name] = prop
            elif type_ == 'enum':
                prop = {'enum': value}
                if is_optional and None not in prop['enum']:
                    prop['enum'].append(None)
                schema['properties'][property_name] = prop
            else:
                raise ValueError(
                    'Picoschema: parenthetical types must be '
                    f"'object' or 'array', got: {type_}"
                )

            if description:
                schema['properties'][property_name]['description'] = description

        if not schema['required']:
            del schema['required']
        return schema


def extract_description(input_str: str) -> tuple[str, str | None]:
    if ',' not in input_str:
        return input_str, None

    parts = input_str.split(',', 1)
    return parts[0].strip(), parts[1].strip()
