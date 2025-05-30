/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JSONSchema, SchemaResolver } from './types.js';

const JSON_SCHEMA_SCALAR_TYPES = [
  'any',
  'boolean',
  'integer',
  'null',
  'number',
  'string',
];

const WILDCARD_PROPERTY_NAME = '(*)';

/** Options for the Picoschema parser. */
export interface PicoschemaOptions {
  /** The schema resolver to use. */
  schemaResolver?: SchemaResolver;
}

/**
 * Parses Picoschema definitions into JSON Schema.
 *
 * Handles basic types, optional fields, descriptions, arrays, objects,
 * enums, wildcards, and named schema resolution.
 *
 * @param schema The schema definition to parse.
 * @param options The options for the parser.
 * @return The resulting JSON Schema, or null if the input is null.
 */
export async function picoschema(schema: unknown, options?: PicoschemaOptions) {
  return new PicoschemaParser(options).parse(schema);
}

/**
 * Parses Picoschema definitions into JSON Schema.
 *
 * Handles basic types, optional fields, descriptions, arrays, objects,
 * enums, wildcards, and named schema resolution.
 */
export class PicoschemaParser {
  schemaResolver?: SchemaResolver;

  /**
   * Constructs a new PicoschemaParser.
   *
   * @param options The options for the parser.
   */
  constructor(options?: PicoschemaOptions) {
    this.schemaResolver = options?.schemaResolver;
  }

  /**
   * Resolves a named schema using the configured resolver.
   *
   * @param schemaName The name of the schema to resolve.
   * @return The resolved JSON Schema.
   */
  private async mustResolveSchema(schemaName: string): Promise<JSONSchema> {
    if (!this.schemaResolver) {
      throw new Error(`Picoschema: unsupported scalar type '${schemaName}'.`);
    }

    const val = await this.schemaResolver(schemaName);
    if (!val) {
      throw new Error(
        `Picoschema: could not find schema with name '${schemaName}'`
      );
    }
    return val;
  }

  /**
   * Parses a schema, detecting if it's Picoschema or JSON Schema.
   *
   * @param schema The schema definition to parse.
   * @return The resulting JSON Schema, or null if the input is null.
   */
  async parse(schema: unknown): Promise<JSONSchema | null> {
    if (!schema) {
      return null;
    }

    // Allow for top-level named schemas
    if (typeof schema === 'string') {
      const [type, description] = extractDescription(schema);
      if (JSON_SCHEMA_SCALAR_TYPES.includes(type)) {
        let out: JSONSchema = { type };
        if (description) {
          out = { ...out, description };
        }
        return out;
      }
      const resolvedSchema = await this.mustResolveSchema(type);
      return description ? { ...resolvedSchema, description } : resolvedSchema;
    }

    // If there's a JSON schema-ish type at the top level, treat as JSON schema.
    if (
      [...JSON_SCHEMA_SCALAR_TYPES, 'object', 'array'].includes(
        (schema as any)?.type
      )
    ) {
      return schema;
    }

    if (typeof (schema as any)?.properties === 'object') {
      return { ...schema, type: 'object' };
    }

    return this.parsePico(schema);
  }

  /**
   * Parses a Picoschema object or string fragment.
   *
   * @param obj The object or string fragment to parse.
   * @param path The current path within the schema structure.
   * @return The parsed JSON Schema.
   */
  private async parsePico(obj: any, path: string[] = []): Promise<JSONSchema> {
    if (typeof obj === 'string') {
      const [type, description] = extractDescription(obj);
      if (!JSON_SCHEMA_SCALAR_TYPES.includes(type)) {
        let resolvedSchema = await this.mustResolveSchema(type);
        if (description) resolvedSchema = { ...resolvedSchema, description };
        return resolvedSchema;
      }

      if (type === 'any') {
        return description ? { description } : {};
      }

      return description ? { type, description } : { type };
    }
    if (typeof obj !== 'object') {
      throw new Error(
        `Picoschema: only consists of objects and strings. Got: ${JSON.stringify(obj)}`
      );
    }

    const schema: JSONSchema = {
      type: 'object',
      properties: {},
      required: [],
      additionalProperties: false,
    };

    for (const key in obj) {
      // wildcard property
      if (key === WILDCARD_PROPERTY_NAME) {
        schema.additionalProperties = await this.parsePico(obj[key], [
          ...path,
          key,
        ]);
        continue;
      }

      const [name, typeInfo] = key.split('(');
      const isOptional = name.endsWith('?');
      const propertyName = isOptional ? name.slice(0, -1) : name;

      if (!isOptional) {
        schema.required.push(propertyName);
      }

      if (!typeInfo) {
        const prop = { ...(await this.parsePico(obj[key], [...path, key])) };
        // make all optional fields also nullable
        if (isOptional && typeof prop.type === 'string') {
          prop.type = [prop.type, 'null'];
        }
        schema.properties[propertyName] = prop;
        continue;
      }

      const [type, description] = extractDescription(
        typeInfo.substring(0, typeInfo.length - 1)
      );
      if (type === 'array') {
        schema.properties[propertyName] = {
          type: isOptional ? ['array', 'null'] : 'array',
          items: await this.parsePico(obj[key], [...path, key]),
        };
      } else if (type === 'object') {
        const prop = await this.parsePico(obj[key], [...path, key]);
        if (isOptional) prop.type = [prop.type, 'null'];
        schema.properties[propertyName] = prop;
      } else if (type === 'enum') {
        const prop = { enum: obj[key] };
        if (isOptional && !prop.enum.includes(null)) prop.enum.push(null);
        schema.properties[propertyName] = prop;
      } else {
        throw new Error(
          `Picoschema: parenthetical types must be 'object' or 'array', got: ${type}`
        );
      }
      if (description) {
        schema.properties[propertyName].description = description;
      }
    }

    if (!schema.required.length) {
      schema.required = undefined;
    }
    return schema;
  }
}

/**
 * Extracts the type name and description from a string.
 *
 * @param input - The input string to extract from.
 * @return A tuple containing the type name and description.
 */
function extractDescription(input: string): [string, string | null] {
  if (!input.includes(',')) {
    return [input, null];
  }

  const match = input.match(/(.*?), *(.*)$/);
  if (!match) {
    return [input, null];
  }

  return [match[1], match[2]];
}
