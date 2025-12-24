/**
 * Copyright 2025 Google LLC
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

import { describe, expect, it } from 'vitest';
import { PicoschemaParser, picoschema } from './picoschema';
import type { JSONSchema, SchemaResolver } from './types';

describe('picoschema', () => {
  describe('parse null and basic types', () => {
    it('should return null for null input', async () => {
      const result = await picoschema(null);
      expect(result).toBeNull();
    });

    it('should parse scalar type string', async () => {
      const result = await picoschema('string');
      expect(result).toEqual({ type: 'string' });
    });

    it('should parse scalar type number', async () => {
      const result = await picoschema('number');
      expect(result).toEqual({ type: 'number' });
    });

    it('should parse scalar type integer', async () => {
      const result = await picoschema('integer');
      expect(result).toEqual({ type: 'integer' });
    });

    it('should parse scalar type boolean', async () => {
      const result = await picoschema('boolean');
      expect(result).toEqual({ type: 'boolean' });
    });

    it('should parse scalar type null', async () => {
      const result = await picoschema('null');
      expect(result).toEqual({ type: 'null' });
    });

    it('should parse any type', async () => {
      const result = await picoschema('any');
      expect(result).toEqual({ type: 'any' });
    });
  });

  describe('descriptions', () => {
    it('should parse scalar type with description', async () => {
      const result = await picoschema('string, a string');
      expect(result).toEqual({ type: 'string', description: 'a string' });
    });

    it('should parse any type with description', async () => {
      const result = await picoschema('any, can be any type');
      expect(result).toEqual({ type: 'any', description: 'can be any type' });
    });
  });

  describe('JSON Schema passthrough', () => {
    it('should pass through valid JSON Schema objects', async () => {
      const schema = {
        type: 'object',
        properties: { name: { type: 'string' } },
      };
      const result = await picoschema(schema);
      expect(result).toEqual(schema);
    });

    it('should add type: object when only properties is present', async () => {
      const schema = {
        properties: { name: { type: 'string' } },
      };
      const result = await picoschema(schema);
      expect(result).toEqual({
        type: 'object',
        properties: { name: { type: 'string' } },
      });
    });
  });

  describe('object shorthand', () => {
    it('should parse properties object shorthand', async () => {
      const result = await picoschema({ name: 'string' });
      expect(result).toEqual({
        type: 'object',
        properties: { name: { type: 'string' } },
        required: ['name'],
        additionalProperties: false,
      });
    });

    it('should parse multiple properties', async () => {
      const result = await picoschema({ name: 'string', age: 'integer' });
      expect(result).toHaveProperty('type', 'object');
      expect(result).toHaveProperty('properties.name');
      expect(result).toHaveProperty('properties.age');
    });
  });

  describe('array type', () => {
    it('should parse array type', async () => {
      const result = await picoschema({ 'names(array)': 'string' });
      expect(result).toEqual({
        type: 'object',
        properties: {
          names: { type: 'array', items: { type: 'string' } },
        },
        required: ['names'],
        additionalProperties: false,
      });
    });

    it('should parse array type with description', async () => {
      const result = await picoschema({
        'items(array, list of items)': 'string',
      });
      expect(result?.properties?.items).toEqual({
        type: 'array',
        items: { type: 'string' },
        description: 'list of items',
      });
    });

    it('should parse optional array with description', async () => {
      const result = await picoschema({
        'items?(array, list of items)': 'string',
      });
      expect(result?.properties?.items).toEqual({
        type: ['array', 'null'],
        items: { type: 'string' },
        description: 'list of items',
      });
      expect(result?.required).toBeUndefined();
    });

    it('should parse nested arrays', async () => {
      const result = await picoschema({
        'items(array)': { 'props(array)': 'string' },
      });
      expect(result?.properties?.items?.type).toBe('array');
      expect(result?.properties?.items?.items?.type).toBe('object');
      expect(result?.properties?.items?.items?.properties?.props?.type).toBe(
        'array'
      );
    });
  });

  describe('enum type', () => {
    it('should parse enum type', async () => {
      const result = await picoschema({
        'status(enum)': ['active', 'inactive'],
      });
      expect(result).toEqual({
        type: 'object',
        properties: { status: { enum: ['active', 'inactive'] } },
        required: ['status'],
        additionalProperties: false,
      });
    });

    it('should parse enum type with description', async () => {
      const result = await picoschema({
        'status(enum, the status)': ['active', 'inactive'],
      });
      expect(result?.properties?.status).toEqual({
        enum: ['active', 'inactive'],
        description: 'the status',
      });
    });

    it('should parse optional enum with null', async () => {
      const result = await picoschema({
        'status?(enum)': ['active', 'inactive'],
      });
      expect(result?.properties?.status?.enum).toContain(null);
      expect(result?.required).toBeUndefined();
    });
  });

  describe('optional properties', () => {
    it('should parse optional property', async () => {
      const result = await picoschema({ 'name?': 'string' });
      expect(result).toEqual({
        type: 'object',
        properties: { name: { type: ['string', 'null'] } },
        additionalProperties: false,
      });
    });
  });

  describe('wildcard properties', () => {
    it('should parse wildcard property', async () => {
      const result = await picoschema({ '(*)': 'string' });
      expect(result).toEqual({
        type: 'object',
        properties: {},
        additionalProperties: { type: 'string' },
      });
    });
  });

  describe('nested objects', () => {
    it('should parse nested object', async () => {
      const result = await picoschema({
        'address(object)': { street: 'string' },
      });
      expect(result).toEqual({
        type: 'object',
        properties: {
          address: {
            type: 'object',
            properties: { street: { type: 'string' } },
            required: ['street'],
            additionalProperties: false,
          },
        },
        required: ['address'],
        additionalProperties: false,
      });
    });

    it('should parse nested object with description', async () => {
      const result = await picoschema({
        'address(object, the address)': { street: 'string' },
      });
      expect(result?.properties?.address?.description).toBe('the address');
    });
  });

  describe('description on type', () => {
    it('should parse description on property type', async () => {
      const result = await picoschema({ name: 'string, a name' });
      expect(result).toEqual({
        type: 'object',
        properties: {
          name: { type: 'string', description: 'a name' },
        },
        required: ['name'],
        additionalProperties: false,
      });
    });
  });

  describe('invalid inputs', () => {
    it('should throw on invalid schema type', async () => {
      await expect(picoschema(123 as any)).rejects.toThrow();
    });

    it('should throw on unsupported scalar type without resolver', async () => {
      await expect(picoschema('UndefinedType')).rejects.toThrow(
        /unsupported scalar type/i
      );
    });
  });
});

describe('PicoschemaParser', () => {
  describe('schema resolution', () => {
    it('should resolve named schema', async () => {
      const resolver: SchemaResolver = (name) => {
        if (name === 'CustomType') return { type: 'integer' };
        return null;
      };

      const parser = new PicoschemaParser({ schemaResolver: resolver });
      const result = await parser.parse('CustomType');
      expect(result).toEqual({ type: 'integer' });
    });

    it('should resolve named schema with description', async () => {
      const resolver: SchemaResolver = (name) => {
        if (name === 'DescribedType') return { type: 'boolean' };
        return null;
      };

      const parser = new PicoschemaParser({ schemaResolver: resolver });
      const result = await parser.parse('DescribedType, this is a description');
      expect(result).toEqual({
        type: 'boolean',
        description: 'this is a description',
      });
    });

    it('should throw when named schema not found', async () => {
      const resolver: SchemaResolver = () => null;
      const parser = new PicoschemaParser({ schemaResolver: resolver });

      await expect(parser.parse('NonExistentSchema')).rejects.toThrow(
        /could not find schema/i
      );
    });

    it('should resolve async schema resolver', async () => {
      const resolver: SchemaResolver = async (name) => {
        // Simulate async operation
        await new Promise((resolve) => setTimeout(resolve, 10));
        if (name === 'AsyncType') return { type: 'number' };
        return null;
      };

      const parser = new PicoschemaParser({ schemaResolver: resolver });
      const result = await parser.parse('AsyncType');
      expect(result).toEqual({ type: 'number' });
    });

    it('should resolve custom schema in property with description', async () => {
      const resolver: SchemaResolver = (name) => {
        if (name === 'CustomSchema') return { type: 'string' };
        return null;
      };

      const parser = new PicoschemaParser({ schemaResolver: resolver });
      const result = await parser.parse({
        field1: 'CustomSchema, a custom field',
      });

      expect(result?.properties?.field1).toEqual({
        type: 'string',
        description: 'a custom field',
      });
    });
  });

  describe('mustResolveSchema', () => {
    it('should resolve successfully', async () => {
      const resolver: SchemaResolver = (name) => {
        if (name === 'MySchema')
          return { type: 'string', description: 'Resolved schema' };
        return null;
      };

      const parser = new PicoschemaParser({ schemaResolver: resolver });
      const result = await (parser as any).mustResolveSchema('MySchema');
      expect(result).toEqual({
        type: 'string',
        description: 'Resolved schema',
      });
    });

    it('should throw when schema not found', async () => {
      const resolver: SchemaResolver = () => null;
      const parser = new PicoschemaParser({ schemaResolver: resolver });

      await expect(
        (parser as any).mustResolveSchema('NonExistent')
      ).rejects.toThrow();
    });

    it('should throw when no resolver configured', async () => {
      const parser = new PicoschemaParser();

      await expect(
        (parser as any).mustResolveSchema('AnySchema')
      ).rejects.toThrow(/unsupported scalar type/i);
    });
  });
});
