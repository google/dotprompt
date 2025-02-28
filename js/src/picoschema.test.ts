// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from 'vitest';
import {
  PicoschemaParser,
  extractDescription,
  isJSONSchema,
  mustResolveSchema,
  picoschema,
} from './picoschema';
import type { JSONSchema, SchemaResolver } from './types.js';

describe('extractDescription', () => {
  // Now we can test the function directly since it's exported
  it('should extract description from a string with a comma', () => {
    const [type, description] = extractDescription('string, A text string');
    expect(type).toBe('string');
    expect(description).toBe('A text string');
  });

  it('should not extract description when there is no comma', () => {
    const [type, description] = extractDescription('string');
    expect(type).toBe('string');
    expect(description).toBeNull();
  });

  it('should handle descriptions with commas', () => {
    const [type, description] = extractDescription(
      'string, A description, with multiple, commas'
    );
    expect(type).toBe('string');
    expect(description).toBe('A description, with multiple, commas');
  });

  it('should not trim whitespace in descriptions', () => {
    const [type, description] = extractDescription(
      'string,    A text string with extra whitespace    '
    );
    expect(type).toBe('string');
    // The regex in extractDescription will match "   " after the comma but preserve trailing spaces
    // The regex pattern " *" in extractDescription will match and skip the spaces after the comma
    expect(description).toBe('A text string with extra whitespace    ');
  });
});

describe('picoschema', () => {
  it('should handle null schema', async () => {
    const result = await picoschema(null);
    expect(result).toBeNull();
  });

  it('should handle undefined schema', async () => {
    const result = await picoschema(undefined);
    expect(result).toBeNull();
  });

  it('should handle basic scalar types', async () => {
    const scalarTypes = ['string', 'number', 'integer', 'boolean', 'null'];

    for (const type of scalarTypes) {
      const result = await picoschema(type);
      expect(result).toEqual({ type });
    }
  });

  it('should handle any type as a scalar type with type "any"', async () => {
    const result = await picoschema('any');

    // TODO: verify whether it should return this?
    // expect(result).toEqual({type: 'any'});
    expect(result).toEqual({});
  });

  it('should handle scalar types with descriptions', async () => {
    const result = await picoschema('number, A numeric value');
    expect(result).toEqual({ type: 'number', description: 'A numeric value' });
  });

  it('should handle JSON Schema with a type field', async () => {
    const schema = { type: 'string', format: 'email' };
    const result = await picoschema(schema);
    expect(result).toEqual(schema);
  });

  it('should handle objects with properties without type', async () => {
    const schema = { properties: { foo: { type: 'string' } } };
    const result = await picoschema(schema);
    expect(result).toEqual({ ...schema, type: 'object' });
  });
});

describe('PicoschemaParser', () => {
  describe('constructor', () => {
    it('should create a parser with the provided schema resolver', () => {
      const schemaResolver: SchemaResolver = async () => ({ type: 'string' });
      const parser = new PicoschemaParser({ schemaResolver });
      expect(parser['schemaResolver']).toBe(schemaResolver);
    });

    it('should create a parser without a schema resolver', () => {
      const parser = new PicoschemaParser();
      expect(parser['schemaResolver']).toBeUndefined();
    });
  });

  describe('parse', () => {
    it('should parse basic object schema', async () => {
      const picoSchema = {
        field1: 'boolean',
        field2: 'string',
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          field1: { type: 'boolean' },
          field2: { type: 'string' },
        },
        required: ['field1', 'field2'],
        additionalProperties: false,
      });
    });

    it('should parse object with optional properties', async () => {
      const picoSchema = {
        req: 'string, required field',
        'nonreq?': 'boolean, optional field',
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          req: { type: 'string', description: 'required field' },
          nonreq: { type: ['boolean', 'null'], description: 'optional field' },
        },
        required: ['req'],
        additionalProperties: false,
      });
    });

    it('should parse nested objects', async () => {
      const picoSchema = {
        user: {
          name: 'string',
          contact: {
            email: 'string',
            'phone?': 'string',
          },
        },
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          user: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              contact: {
                type: 'object',
                properties: {
                  email: { type: 'string' },
                  phone: { type: ['string', 'null'] },
                },
                required: ['email'],
                additionalProperties: false,
              },
            },
            required: ['name', 'contact'],
            additionalProperties: false,
          },
        },
        required: ['user'],
        additionalProperties: false,
      });
    });

    it('should parse array types', async () => {
      const picoSchema = {
        'tags(array, list of tags)': 'string, the tag',
        'vector(array)': 'number',
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          tags: {
            type: 'array',
            description: 'list of tags',
            items: { type: 'string', description: 'the tag' },
          },
          vector: {
            type: 'array',
            items: { type: 'number' },
          },
        },
        required: ['tags', 'vector'],
        additionalProperties: false,
      });
    });

    it('should parse complex nested structures with objects and arrays', async () => {
      const picoSchema = {
        'obj?(object, a nested object)': {
          'nest1?': 'string',
        },
        'arr(array, array of objects)': {
          'nest2?': 'boolean',
        },
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          obj: {
            type: ['object', 'null'],
            description: 'a nested object',
            properties: {
              nest1: { type: ['string', 'null'] },
            },
            additionalProperties: false,
          },
          arr: {
            type: 'array',
            description: 'array of objects',
            items: {
              type: 'object',
              properties: {
                nest2: { type: ['boolean', 'null'] },
              },
              additionalProperties: false,
            },
          },
        },
        required: ['arr'],
        additionalProperties: false,
      });
    });

    it('should parse enum types', async () => {
      const picoSchema = {
        'color?(enum, the enum)': ['RED', 'BLUE', 'GREEN'],
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          color: {
            description: 'the enum',
            enum: ['RED', 'BLUE', 'GREEN', null],
          },
        },
        additionalProperties: false,
      });
    });

    it('should handle any type', async () => {
      const picoSchema = {
        first: 'any',
        'second?': 'any, could be anything',
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          first: {},
          second: { description: 'could be anything' },
        },
        required: ['first'],
        additionalProperties: false,
      });
    });

    it('should handle wildcard properties with other fields', async () => {
      const picoSchema = {
        otherField: 'string, another string',
        '(*)': 'any, whatever you want',
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {
          otherField: { type: 'string', description: 'another string' },
        },
        required: ['otherField'],
        additionalProperties: { description: 'whatever you want' },
      });
    });

    it('should handle wildcard properties without other fields', async () => {
      const picoSchema = {
        '(*)': 'number, lucky number',
      };

      const result = await new PicoschemaParser().parse(picoSchema);

      expect(result).toEqual({
        type: 'object',
        properties: {},
        additionalProperties: { type: 'number', description: 'lucky number' },
      });
    });
  });

  describe('Error handling', () => {
    it('should throw an error for invalid schema types', async () => {
      await expect(async () => {
        await picoschema(123);
      }).rejects.toThrow('Picoschema: only consists of objects and strings');
    });

    it('should throw an error for invalid parenthetical types', async () => {
      const picoSchema = {
        'name(invalid)': 'value',
      };

      await expect(async () => {
        await picoschema(picoSchema);
      }).rejects.toThrow(
        "Picoschema: parenthetical types must be 'object' or 'array'"
      );
    });
  });
});

describe('testMustResolveSchema', () => {
  it('should throw an error if no schema resolver is provided', async () => {
    await expect(async () => {
      await mustResolveSchema('CustomType', undefined);
    }).rejects.toThrow("Picoschema: unknown schema resolver for 'CustomType'");
  });

  it('should throw an error if schema resolver returns null', async () => {
    const schemaResolver: SchemaResolver = async () => null;
    await expect(async () => {
      await mustResolveSchema('CustomType', schemaResolver);
    }).rejects.toThrow(
      "Picoschema: could not find schema with name 'CustomType'"
    );
  });

  it('should return the resolved schema', async () => {
    const customSchema: JSONSchema = {
      type: 'string',
      description: 'a custom type',
    };

    const schemaResolver: SchemaResolver = async (name) => {
      if (name === 'CustomType') {
        return customSchema;
      }
      return null;
    };

    const result = await mustResolveSchema('CustomType', schemaResolver);

    expect(result).toEqual(customSchema);
  });
});

describe('testParsePico', () => {
  it('should parse string scalar types', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico('string');

    expect(result).toEqual({ type: 'string' });
  });

  it('should parse string scalar types with descriptions', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico('string, description');

    expect(result).toEqual({ type: 'string', description: 'description' });
  });

  it('should handle any type', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico('any');

    expect(result).toEqual({});
  });

  it('should handle any type with description', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico('any, anything goes');

    expect(result).toEqual({ description: 'anything goes' });
  });

  it('should parse object with properties', async () => {
    const parser = new PicoschemaParser();
    const schema = {
      name: 'string',
      age: 'number',
    };

    const result = await parser.testParsePico(schema);

    expect(result).toEqual({
      type: 'object',
      properties: {
        name: { type: 'string' },
        age: { type: 'number' },
      },
      required: ['name', 'age'],
      additionalProperties: false,
    });
  });

  it('should parse object with optional properties', async () => {
    const parser = new PicoschemaParser();
    const schema = {
      'name?': 'string',
      age: 'number',
    };

    const result = await parser.testParsePico(schema);

    expect(result).toEqual({
      type: 'object',
      properties: {
        name: { type: ['string', 'null'] },
        age: { type: 'number' },
      },
      required: ['age'],
      additionalProperties: false,
    });
  });

  it('should parse array types', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico({
      'items(array)': 'string',
    });

    expect(result).toEqual({
      type: 'object',
      properties: {
        items: {
          type: 'array',
          items: { type: 'string' },
        },
      },
      required: ['items'],
      additionalProperties: false,
    });
  });

  it('should parse array types with description', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico({
      'items(array, list of strings)': 'string, a string item',
    });

    expect(result).toEqual({
      type: 'object',
      properties: {
        items: {
          type: 'array',
          description: 'list of strings',
          items: { type: 'string', description: 'a string item' },
        },
      },
      required: ['items'],
      additionalProperties: false,
    });
  });

  it('should parse enum types', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico({
      'status(enum)': ['ACTIVE', 'INACTIVE'],
    });

    expect(result).toEqual({
      type: 'object',
      properties: {
        status: {
          enum: ['ACTIVE', 'INACTIVE'],
        },
      },
      required: ['status'],
      additionalProperties: false,
    });
  });

  it('should parse optional enum types', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico({
      'status?(enum)': ['ACTIVE', 'INACTIVE'],
    });

    expect(result).toEqual({
      type: 'object',
      properties: {
        status: {
          enum: ['ACTIVE', 'INACTIVE', null],
        },
      },
      additionalProperties: false,
    });
  });

  it('should parse wildcard properties', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico({
      '(*)': 'string, any string key',
    });

    expect(result).toEqual({
      type: 'object',
      properties: {},
      additionalProperties: { type: 'string', description: 'any string key' },
    });
  });

  it('should parse nested objects', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParsePico({
      user: {
        name: 'string',
        address: {
          street: 'string',
          'city?': 'string',
        },
      },
    });

    expect(result).toEqual({
      type: 'object',
      properties: {
        user: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            address: {
              type: 'object',
              properties: {
                street: { type: 'string' },
                city: { type: ['string', 'null'] },
              },
              required: ['street'],
              additionalProperties: false,
            },
          },
          required: ['name', 'address'],
          additionalProperties: false,
        },
      },
      required: ['user'],
      additionalProperties: false,
    });
  });

  it('should handle non-object/string input', async () => {
    const parser = new PicoschemaParser();

    await expect(async () => {
      await parser.testParsePico(123);
    }).rejects.toThrow('Picoschema: only consists of objects and strings');
  });

  it('should handle invalid parenthetical types', async () => {
    const parser = new PicoschemaParser();

    await expect(async () => {
      await parser.testParsePico({
        'field(invalid)': 'value',
      });
    }).rejects.toThrow(
      "Picoschema: parenthetical types must be 'object' or 'array'"
    );
  });
});

describe('parsePropertyKey', () => {
  it('should parse a simple property key', () => {
    const parser = new PicoschemaParser();
    const result = parser.testParsePropertyKey('name');

    expect(result).toEqual({
      propertyName: 'name',
      isOptional: false,
      type: null,
      description: null,
    });
  });

  it('should parse an optional property key', () => {
    const parser = new PicoschemaParser();
    const result = parser.testParsePropertyKey('name?');

    expect(result).toEqual({
      propertyName: 'name',
      isOptional: true,
      type: null,
      description: null,
    });
  });

  it('should parse a property key with type info', () => {
    const parser = new PicoschemaParser();
    const result = parser.testParsePropertyKey('items(array)');

    expect(result).toEqual({
      propertyName: 'items',
      isOptional: false,
      type: 'array',
      description: null,
    });
  });

  it('should parse a property key with type and description', () => {
    const parser = new PicoschemaParser();
    const result = parser.testParsePropertyKey('items(array, item list)');

    expect(result).toEqual({
      propertyName: 'items',
      isOptional: false,
      type: 'array',
      description: 'item list',
    });
  });

  it('should parse an optional property key with type and description', () => {
    const parser = new PicoschemaParser();
    const result = parser.testParsePropertyKey('items?(array, optional items)');

    expect(result).toEqual({
      propertyName: 'items',
      isOptional: true,
      type: 'array',
      description: 'optional items',
    });
  });
});

describe('createScalarTypeSchema', () => {
  it('should create a schema for string type', () => {
    const parser = new PicoschemaParser();
    const result = parser.testCreateScalarTypeSchema('string', null);

    expect(result).toEqual({ type: 'string' });
  });

  it('should create a schema for string type with description', () => {
    const parser = new PicoschemaParser();
    const result = parser.testCreateScalarTypeSchema('string', 'A text string');

    expect(result).toEqual({
      type: 'string',
      description: 'A text string',
    });
  });

  it('should create an empty schema for any type', () => {
    const parser = new PicoschemaParser();
    const result = parser.testCreateScalarTypeSchema('any', null);

    expect(result).toEqual({});
  });

  it('should create a schema with only description for any type', () => {
    const parser = new PicoschemaParser();
    const result = parser.testCreateScalarTypeSchema('any', 'Any value');

    expect(result).toEqual({ description: 'Any value' });
  });
});

describe('isJSONSchema', () => {
  it('should identify a schema with scalar type', () => {
    const result = isJSONSchema({ type: 'string' });

    expect(result).toBe(true);
  });

  it('should identify a schema with object type', () => {
    const result = isJSONSchema({ type: 'object' });

    expect(result).toBe(true);
  });

  it('should identify a schema with array type', () => {
    const result = isJSONSchema({ type: 'array' });

    expect(result).toBe(true);
  });

  it('should reject a non-schema object', () => {
    const result = isJSONSchema({
      foo: 'bar',
      baz: 123,
    });

    expect(result).toBe(false);
  });

  it('should reject null', () => {
    const result = isJSONSchema(null);

    expect(result).toBe(false);
  });
});

describe('parseStringSchema', () => {
  it('should parse a scalar type', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParseStringSchema('string');

    expect(result).toEqual({ type: 'string' });
  });

  it('should parse a scalar type with description', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParseStringSchema('string, A text string');

    expect(result).toEqual({
      type: 'string',
      description: 'A text string',
    });
  });

  it('should parse the any type', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testParseStringSchema('any');

    expect(result).toEqual({});
  });

  it('should resolve a custom type', async () => {
    const customSchema = { type: 'object', properties: {} };
    const schemaResolver: SchemaResolver = async (name) =>
      name === 'CustomType' ? customSchema : null;

    const parser = new PicoschemaParser({ schemaResolver });
    const result = await parser.testParseStringSchema('CustomType');

    expect(result).toEqual(customSchema);
  });

  it('should resolve a custom type and add description', async () => {
    const customSchema = { type: 'object', properties: {} };
    const schemaResolver: SchemaResolver = async (name) =>
      name === 'CustomType' ? customSchema : null;

    const parser = new PicoschemaParser({ schemaResolver });
    const result = await parser.testParseStringSchema(
      'CustomType, A custom type'
    );

    expect(result).toEqual({
      ...customSchema,
      description: 'A custom type',
    });
  });
});

describe('createArraySchema', () => {
  it('should create an array schema with string items', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testCreateArraySchema('string', false, []);

    expect(result).toEqual({
      type: 'array',
      items: { type: 'string' },
    });
  });

  it('should create an optional array schema', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testCreateArraySchema('string', true, []);

    expect(result).toEqual({
      type: ['array', 'null'],
      items: { type: 'string' },
    });
  });

  it('should create an array schema with complex items', async () => {
    const parser = new PicoschemaParser();
    const result = await parser.testCreateArraySchema(
      {
        name: 'string',
        age: 'number',
      },
      false,
      []
    );

    expect(result).toEqual({
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          age: { type: 'number' },
        },
        required: ['name', 'age'],
        additionalProperties: false,
      },
    });
  });
});

describe('createEnumSchema', () => {
  it('should create an enum schema', () => {
    const parser = new PicoschemaParser();
    const result = parser.testCreateEnumSchema(['RED', 'GREEN', 'BLUE'], false);

    expect(result).toEqual({
      enum: ['RED', 'GREEN', 'BLUE'],
    });
  });

  it('should create an optional enum schema by adding null', () => {
    const parser = new PicoschemaParser();
    const result = parser.testCreateEnumSchema(['RED', 'GREEN', 'BLUE'], true);

    expect(result).toEqual({
      enum: ['RED', 'GREEN', 'BLUE', null],
    });
  });

  it('should not add null if already present', () => {
    const parser = new PicoschemaParser();
    const result = parser.testCreateEnumSchema(
      ['RED', 'GREEN', null, 'BLUE'],
      true
    );

    expect(result).toEqual({
      enum: ['RED', 'GREEN', null, 'BLUE'],
    });
  });
});

describe('PicoschemaParser refactored methods', () => {
  describe('parsePropertyKey', () => {
    it('should parse a simple property key', () => {
      const parser = new PicoschemaParser();
      const result = parser.testParsePropertyKey('name');

      expect(result).toEqual({
        propertyName: 'name',
        isOptional: false,
        type: null,
        description: null,
      });
    });

    it('should parse an optional property key', () => {
      const parser = new PicoschemaParser();
      const result = parser.testParsePropertyKey('name?');

      expect(result).toEqual({
        propertyName: 'name',
        isOptional: true,
        type: null,
        description: null,
      });
    });

    it('should parse a property key with type info', () => {
      const parser = new PicoschemaParser();
      const result = parser.testParsePropertyKey('items(array)');

      expect(result).toEqual({
        propertyName: 'items',
        isOptional: false,
        type: 'array',
        description: null,
      });
    });

    it('should parse a property key with type and description', () => {
      const parser = new PicoschemaParser();
      const result = parser.testParsePropertyKey('items(array, item list)');

      expect(result).toEqual({
        propertyName: 'items',
        isOptional: false,
        type: 'array',
        description: 'item list',
      });
    });

    it('should parse an optional property key with type and description', () => {
      const parser = new PicoschemaParser();
      const result = parser.testParsePropertyKey(
        'items?(array, optional items)'
      );

      expect(result).toEqual({
        propertyName: 'items',
        isOptional: true,
        type: 'array',
        description: 'optional items',
      });
    });
  });

  describe('createScalarTypeSchema', () => {
    it('should create a schema for string type', () => {
      const parser = new PicoschemaParser();
      const result = parser.testCreateScalarTypeSchema('string', null);

      expect(result).toEqual({ type: 'string' });
    });

    it('should create a schema for string type with description', () => {
      const parser = new PicoschemaParser();
      const result = parser.testCreateScalarTypeSchema(
        'string',
        'A text string'
      );

      expect(result).toEqual({
        type: 'string',
        description: 'A text string',
      });
    });

    it('should create an empty schema for any type', () => {
      const parser = new PicoschemaParser();
      const result = parser.testCreateScalarTypeSchema('any', null);

      expect(result).toEqual({});
    });

    it('should create a schema with only description for any type', () => {
      const parser = new PicoschemaParser();
      const result = parser.testCreateScalarTypeSchema('any', 'Any value');

      expect(result).toEqual({ description: 'Any value' });
    });
  });

  describe('parseStringSchema', () => {
    it('should parse a scalar type', async () => {
      const parser = new PicoschemaParser();
      const result = await parser.testParseStringSchema('string');

      expect(result).toEqual({ type: 'string' });
    });

    it('should parse a scalar type with description', async () => {
      const parser = new PicoschemaParser();
      const result = await parser.testParseStringSchema(
        'string, A text string'
      );

      expect(result).toEqual({
        type: 'string',
        description: 'A text string',
      });
    });

    it('should parse the any type', async () => {
      const parser = new PicoschemaParser();
      const result = await parser.testParseStringSchema('any');

      expect(result).toEqual({});
    });

    it('should resolve a custom type', async () => {
      const customSchema = { type: 'object', properties: {} };
      const schemaResolver: SchemaResolver = async (name) =>
        name === 'CustomType' ? customSchema : null;

      const parser = new PicoschemaParser({ schemaResolver });
      const result = await parser.testParseStringSchema('CustomType');

      expect(result).toEqual(customSchema);
    });

    it('should resolve a custom type and add description', async () => {
      const customSchema = { type: 'object', properties: {} };
      const schemaResolver: SchemaResolver = async (name) =>
        name === 'CustomType' ? customSchema : null;

      const parser = new PicoschemaParser({ schemaResolver });
      const result = await parser.testParseStringSchema(
        'CustomType, A custom type'
      );

      expect(result).toEqual({
        ...customSchema,
        description: 'A custom type',
      });
    });
  });

  describe('createArraySchema', () => {
    it('should create an array schema with string items', async () => {
      const parser = new PicoschemaParser();
      const result = await parser.testCreateArraySchema('string', false, []);

      expect(result).toEqual({
        type: 'array',
        items: { type: 'string' },
      });
    });

    it('should create an optional array schema', async () => {
      const parser = new PicoschemaParser();
      const result = await parser.testCreateArraySchema('string', true, []);

      expect(result).toEqual({
        type: ['array', 'null'],
        items: { type: 'string' },
      });
    });

    it('should create an array schema with complex items', async () => {
      const parser = new PicoschemaParser();
      const result = await parser.testCreateArraySchema(
        {
          name: 'string',
          age: 'number',
        },
        false,
        []
      );

      expect(result).toEqual({
        type: 'array',
        items: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            age: { type: 'number' },
          },
          required: ['name', 'age'],
          additionalProperties: false,
        },
      });
    });
  });

  describe('createEnumSchema', () => {
    it('should create an enum schema', () => {
      const parser = new PicoschemaParser();
      const result = parser.testCreateEnumSchema(
        ['RED', 'GREEN', 'BLUE'],
        false
      );

      expect(result).toEqual({
        enum: ['RED', 'GREEN', 'BLUE'],
      });
    });

    it('should create an optional enum schema by adding null', () => {
      const parser = new PicoschemaParser();
      const result = parser.testCreateEnumSchema(
        ['RED', 'GREEN', 'BLUE'],
        true
      );

      expect(result).toEqual({
        enum: ['RED', 'GREEN', 'BLUE', null],
      });
    });

    it('should not add null if already present', () => {
      const parser = new PicoschemaParser();
      const result = parser.testCreateEnumSchema(
        ['RED', 'GREEN', null, 'BLUE'],
        true
      );

      expect(result).toEqual({
        enum: ['RED', 'GREEN', null, 'BLUE'],
      });
    });
  });
});
