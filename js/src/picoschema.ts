/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JSONSchema, SchemaResolver } from './types.js';

/**
 * Regex pattern for extracting a description following a comma in a string
 */
const DESCRIPTION_PATTERN = /(.*?), *(.*)$/;

/**
 * Scalar types for JSON schema.
 */
const JSON_SCHEMA_SCALAR_TYPES = [
  // NOTE: Keep sorted.
  'any',
  'boolean',
  'integer',
  'null',
  'number',
  'string',
];

/**
 * A special property name for wildcard properties.
 */
const WILDCARD_PROPERTY_NAME = '(*)';

/**
 * Extracts a description following a comma in a string
 *
 * @param text The string to extract from
 * @return The extracted type and description
 */
export function extractDescription(text: string): [string, string | null] {
  if (!text.includes(',')) {
    return [text, null];
  }

  const match = text.match(DESCRIPTION_PATTERN);
  if (!match || match.length < 3) {
    // If the match fails for any reason, return the text as is
    return [text, null];
  }

  return [match[1], match[2]];
}

/**
 * Checks if the provided object appears to be a JSON Schema
 *
 * @param obj The object to check
 * @return Whether it appears to be a JSON Schema
 */
export function isJSONSchema(obj: any): boolean {
  return [...JSON_SCHEMA_SCALAR_TYPES, 'object', 'array'].includes(obj?.type);
}

/**
 * Creates a schema for a scalar type
 *
 * @param typeName The scalar type
 * @param description Optional description
 * @return A JSON Schema for the scalar type
 */
export function createScalarTypeSchema(
  typeName: string,
  description: string | null
): JSONSchema {
  switch (typeName) {
    case 'any':
      return description ? { description } : {};
    default:
      return description ? { type: typeName, description } : { type: typeName };
  }
}

/**
 * Resolves a schema name to a JSON schema.
 *
 * @param schemaName The name of the schema to resolve.
 * @param schemaResolver The function to use to resolve the schema.
 * @return The resolved JSON schema, or null if the schema is null.
 */
export async function mustResolveSchema(
  schemaName: string,
  schemaResolver: SchemaResolver | undefined
): Promise<JSONSchema> {
  if (!schemaResolver) {
    throw new Error(`Picoschema: unknown schema resolver for '${schemaName}'.`);
  }

  const val = await schemaResolver(schemaName);
  if (!val) {
    throw new Error(
      `Picoschema: could not find schema with name '${schemaName}'`
    );
  }
  return val;
}

/**
 * Options for the PicoschemaParser constructor.
 */
export interface PicoschemaOptions {
  schemaResolver?: SchemaResolver;
}

/**
 * Parses a Picoschema into a JSON Schema.
 *
 * @param schema The Picoschema to parse.
 * @param options Options for the parser.
 * @return The parsed JSON Schema.
 */
export async function picoschema(
  schema: unknown,
  options?: PicoschemaOptions
): Promise<JSONSchema> {
  return new PicoschemaParser(options).parse(schema);
}

/**
 * Parses a Picoschema into a JSON Schema.
 */
export class PicoschemaParser {
  private schemaResolver?: SchemaResolver;

  constructor(options?: PicoschemaOptions) {
    this.schemaResolver = options?.schemaResolver;
  }

  /**
   * Parses a schema into JSON schema.
   *
   * @param schema The schema to parse.
   * @return The parsed JSON schema, or null if the schema is null.
   */
  async parse(schema: unknown): Promise<JSONSchema | null> {
    if (!schema) {
      return null;
    }

    // Allow for top-level named schemas
    if (typeof schema === 'string') {
      return this.parseStringSchema(schema);
    }

    // If there's a JSON schema-ish type at the top level, treat as JSON schema
    if (isJSONSchema(schema as any)) {
      return schema as JSONSchema;
    }

    if (typeof (schema as any)?.properties === 'object') {
      return { ...schema, type: 'object' } as JSONSchema;
    }

    return this.parsePico(schema);
  }

  /**
   * Parses a string schema into a JSON Schema
   *
   * @param schema The string schema to parse
   * @return The parsed JSON Schema
   */
  private async parseStringSchema(schema: string): Promise<JSONSchema> {
    const [type, description] = extractDescription(schema);

    if (JSON_SCHEMA_SCALAR_TYPES.includes(type)) {
      return createScalarTypeSchema(type, description);
    }

    const resolvedSchema = await mustResolveSchema(type, this.schemaResolver);
    return description ? { ...resolvedSchema, description } : resolvedSchema;
  }

  /**
   * Parse picoschema into a JSON Schema.
   *
   * @param obj The picoschema to parse.
   * @param path The path to the current object in the picoschema.
   * @return The parsed JSON Schema.
   */
  private async parsePico(
    obj: unknown,
    path: string[] = []
  ): Promise<JSONSchema> {
    switch (typeof obj) {
      case 'string':
        return this.parseStringValueInPico(obj);
      case 'object':
        if (obj === null) {
          throw new Error(
            'Picoschema: only consists of objects and strings. Got: null'
          );
        }
        return this.parseObjectInPico(obj, path);
      default: {
        const sobj = JSON.stringify(obj);
        throw new Error(
          `Picoschema: only consists of objects and strings. Got: ${sobj}`
        );
      }
    }
  }

  /**
   * Parses a string value within a picoschema
   *
   * @param value The string value to parse
   * @return The parsed JSON Schema
   */
  private async parseStringValueInPico(value: string): Promise<JSONSchema> {
    const [type, description] = extractDescription(value);

    if (!JSON_SCHEMA_SCALAR_TYPES.includes(type)) {
      let resolvedSchema = await mustResolveSchema(type, this.schemaResolver);
      if (description) resolvedSchema = { ...resolvedSchema, description };
      return resolvedSchema;
    }

    return createScalarTypeSchema(type, description);
  }

  /**
   * Parses an object within a picoschema
   *
   * @param obj The object to parse
   * @param path The path to the current object
   * @return The parsed JSON Schema
   */
  private async parseObjectInPico(
    obj: unknown,
    path: string[]
  ): Promise<JSONSchema> {
    const schema: JSONSchema = {
      type: 'object',
      properties: {},
      required: [],
      additionalProperties: false,
    };

    const objAsRecord = obj as Record<string, unknown>;

    for (const key in objAsRecord) {
      if (key === WILDCARD_PROPERTY_NAME) {
        schema.additionalProperties = await this.parsePico(objAsRecord[key], [
          ...path,
          key,
        ]);
        continue;
      }

      await this.processProperty(schema, key, objAsRecord[key], path);
    }

    if (!schema.required.length) {
      delete schema.required;
    }
    return schema;
  }

  /**
   * Processes a single property in an object schema
   *
   * @param schema The schema being built
   * @param key The property key
   * @param value The property value
   * @param path The path to the current object
   */
  private async processProperty(
    schema: JSONSchema,
    key: string,
    value: unknown,
    path: string[]
  ): Promise<void> {
    const { propertyName, isOptional, type, description } =
      this.parsePropertyKey(key);

    if (!isOptional) {
      schema.required.push(propertyName);
    }

    if (!type) {
      // No type info in parentheses, parse the value
      schema.properties[propertyName] = await this.parsePropertyWithoutTypeInfo(
        value,
        isOptional,
        [...path, key]
      );
    } else {
      // Has type info in parentheses
      schema.properties[propertyName] = await this.parsePropertyWithTypeInfo(
        type,
        value,
        isOptional,
        [...path, key]
      );

      if (description) {
        schema.properties[propertyName].description = description;
      }
    }
  }

  /**
   * Parses a property key to extract name, optional flag, and type information
   *
   * @param key The property key
   * @return Parsed property information
   */
  private parsePropertyKey(key: string): {
    propertyName: string;
    isOptional: boolean;
    type: string | null;
    description: string | null;
  } {
    const [name, typeInfo] = key.split('(');
    const isOptional = name.endsWith('?');
    const propertyName = isOptional ? name.slice(0, -1) : name;

    if (!typeInfo) {
      return { propertyName, isOptional, type: null, description: null };
    }

    // Remove the trailing ')'
    const [type, description] = extractDescription(
      typeInfo.substring(0, typeInfo.length - 1)
    );

    return { propertyName, isOptional, type, description };
  }

  /**
   * Parses a property value when no explicit type info is provided
   *
   * @param value The property value
   * @param isOptional Whether the property is optional
   * @param path The path to the property
   * @return The parsed JSON Schema
   */
  private async parsePropertyWithoutTypeInfo(
    value: unknown,
    isOptional: boolean,
    path: string[]
  ): Promise<JSONSchema> {
    const prop = { ...(await this.parsePico(value, path)) };

    // Make all optional fields also nullable
    if (isOptional && typeof prop.type === 'string') {
      prop.type = [prop.type, 'null'];
    }

    return prop;
  }

  /**
   * Parses a property value when explicit type info is provided
   *
   * @param typeName The explicit type name.
   * @param value The property value.
   * @param isOptional Whether the property is optional.
   * @param path The path to the property.
   * @return The parsed JSON Schema.
   */
  private async parsePropertyWithTypeInfo(
    typeName: string,
    value: unknown,
    isOptional: boolean,
    path: string[]
  ): Promise<JSONSchema> {
    switch (typeName) {
      case 'array':
        return this.createArraySchema(value, isOptional, path);

      case 'object':
        return this.createObjectSchema(value, isOptional, path);

      case 'enum':
        return this.createEnumSchema(value as unknown[], isOptional);

      default:
        throw new Error(
          `Picoschema: parenthetical types must be 'object' or 'array', got: ${typeName}`
        );
    }
  }

  /**
   * Creates an array schema
   *
   * @param items The array items schema
   * @param isOptional Whether the array is optional
   * @param path The path to the array
   * @return The array JSON Schema
   */
  private async createArraySchema(
    items: unknown,
    isOptional: boolean,
    path: string[]
  ): Promise<JSONSchema> {
    return {
      type: isOptional ? ['array', 'null'] : 'array',
      items: await this.parsePico(items, path),
    };
  }

  /**
   * Creates an object schema
   *
   * @param value The object schema
   * @param isOptional Whether the object is optional
   * @param path The path to the object
   * @return The object JSON Schema
   */
  private async createObjectSchema(
    value: unknown,
    isOptional: boolean,
    path: string[]
  ): Promise<JSONSchema> {
    const prop = await this.parsePico(value, path);
    if (isOptional) prop.type = [prop.type, 'null'];
    return prop;
  }

  /**
   * Creates an enum schema
   *
   * @param values The enum values
   * @param isOptional Whether the enum is optional
   * @return The enum JSON Schema
   */
  private createEnumSchema(values: unknown[], isOptional: boolean): JSONSchema {
    const prop = { enum: values };
    if (isOptional && !prop.enum.includes(null)) {
      prop.enum.push(null);
    }
    return prop;
  }

  // For testing only.
  async testParsePico(obj: unknown, path: string[] = []): Promise<JSONSchema> {
    return this.parsePico(obj, path);
  }

  // For testing only.
  async testParseStringSchema(schema: string): Promise<JSONSchema> {
    return this.parseStringSchema(schema);
  }

  // For testing only.
  async testParseObjectInPico(
    obj: unknown,
    path: string[] = []
  ): Promise<JSONSchema> {
    return this.parseObjectInPico(obj, path);
  }

  // For testing only.
  testParsePropertyKey(key: string): ReturnType<typeof this.parsePropertyKey> {
    return this.parsePropertyKey(key);
  }

  testCreateScalarTypeSchema(
    typeName: string,
    description: string | null
  ): JSONSchema {
    return createScalarTypeSchema(typeName, description);
  }

  async testCreateArraySchema(
    items: unknown,
    isOptional: boolean,
    path: string[]
  ): Promise<JSONSchema> {
    return this.createArraySchema(items, isOptional, path);
  }

  testCreateEnumSchema(values: unknown[], isOptional: boolean): JSONSchema {
    return this.createEnumSchema(values, isOptional);
  }
}
