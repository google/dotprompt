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

import * as Handlebars from 'handlebars';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Dotprompt } from './dotprompt';
import * as parse from './parse';
import type { JSONSchema, PromptMetadata, ToolDefinition } from './types';

describe('Dotprompt', () => {
  describe('constructor', () => {
    it('should initialize with default options', () => {
      const dp = new Dotprompt();
      expect(dp).toBeInstanceOf(Dotprompt);
    });

    it('should initialize with custom model configs', () => {
      const modelConfigs = {
        'gemini-1.5-pro': { temperature: 0.7 },
        'gemini-2.0-flash': { top_p: 0.9 },
      };
      const dp = new Dotprompt({ modelConfigs });
      expect(dp).toBeInstanceOf(Dotprompt);
    });

    it('should initialize with default model', () => {
      const defaultModel = 'gemini-1.5-pro';
      const dp = new Dotprompt({ defaultModel });
      expect(dp).toBeInstanceOf(Dotprompt);
    });

    it('should initialize with custom helpers', () => {
      const customHelper = (context: unknown) => `HELPER: ${context}`;
      const dp = new Dotprompt({
        helpers: {
          customHelper,
        },
      });

      const template = '{{customHelper "test"}}';
      const compiled = Handlebars.compile(template, { noEscape: true });
      const result = compiled({ customHelper });

      expect(result).toBe('HELPER: test');
    });

    it('should initialize with custom partials', () => {
      const registerPartialSpy = vi.spyOn(Handlebars, 'registerPartial');

      const partials = {
        header: 'This is a header',
        footer: 'This is a footer',
      };

      new Dotprompt({ partials });

      expect(registerPartialSpy).toHaveBeenCalledWith(
        'header',
        'This is a header'
      );
      expect(registerPartialSpy).toHaveBeenCalledWith(
        'footer',
        'This is a footer'
      );
    });
  });

  describe('defineHelper', () => {
    it('should register a helper function', () => {
      const dp = new Dotprompt();
      const helperFn = (context: unknown) => `Helper: ${context}`;

      const registerHelperSpy = vi.spyOn(Handlebars, 'registerHelper');

      dp.defineHelper('testHelper', helperFn);

      expect(registerHelperSpy).toHaveBeenCalledWith('testHelper', helperFn);
    });

    it('should return the Dotprompt instance for chaining', () => {
      const dp = new Dotprompt();
      const helperFn = (context: unknown) => `Helper: ${context}`;

      const result = dp.defineHelper('testHelper', helperFn);

      expect(result).toBe(dp);
    });
  });

  describe('definePartial', () => {
    it('should register a partial template', () => {
      const dp = new Dotprompt();
      const registerPartialSpy = vi.spyOn(Handlebars, 'registerPartial');

      dp.definePartial('testPartial', '<div>Partial content</div>');

      expect(registerPartialSpy).toHaveBeenCalledWith(
        'testPartial',
        '<div>Partial content</div>'
      );
    });

    it('should return the Dotprompt instance for chaining', () => {
      const dp = new Dotprompt();

      const result = dp.definePartial(
        'testPartial',
        '<div>Partial content</div>'
      );

      expect(result).toBe(dp);
    });
  });

  describe('defineTool', () => {
    it('should register a tool definition', () => {
      const dp = new Dotprompt();
      const toolDef: ToolDefinition = {
        name: 'testTool',
        description: 'A test tool',
        inputSchema: {
          type: 'object',
          properties: {
            param1: { type: 'string' },
          },
        },
      };

      dp.defineTool(toolDef);

      expect(dp).toBeInstanceOf(Dotprompt);
    });

    it('should return the Dotprompt instance for chaining', () => {
      const dp = new Dotprompt();
      const toolDef: ToolDefinition = {
        name: 'testTool',
        description: 'A test tool',
        inputSchema: {
          type: 'object',
          properties: {
            param1: { type: 'string' },
          },
        },
      };

      const result = dp.defineTool(toolDef);

      expect(result).toBe(dp);
    });
  });

  describe('parse', () => {
    it('should call parseDocument with the source string', () => {
      const parseDocumentMock = vi.spyOn(parse, 'parseDocument');
      parseDocumentMock.mockReturnValue({
        template: 'Template content',
        model: 'gemini-1.5-pro',
      });

      const dp = new Dotprompt();
      const result = dp.parse('Source template');

      expect(parseDocumentMock).toHaveBeenCalledWith('Source template');
      expect(result).toEqual({
        template: 'Template content',
        model: 'gemini-1.5-pro',
      });
    });
  });

  describe('compile and render', () => {
    let dp: Dotprompt;

    beforeEach(() => {
      dp = new Dotprompt();
    });

    it('should compile a template string into a render function', async () => {
      const templateSource = 'Hello {{input.name}}!';
      const parseDocumentMock = vi.spyOn(parse, 'parseDocument');
      parseDocumentMock.mockReturnValue({
        template: templateSource,
      });

      const handlebarsCompileMock = vi.spyOn(Handlebars, 'compile');
      const mockCompiledTemplate = vi.fn().mockReturnValue('Hello World!');
      handlebarsCompileMock.mockReturnValue(mockCompiledTemplate);

      const renderer = await dp.compile(templateSource);

      expect(parseDocumentMock).toHaveBeenCalledWith(templateSource);
      expect(handlebarsCompileMock).toHaveBeenCalledWith(
        templateSource,
        expect.anything()
      );

      // Test the rendered function.
      const toMessagesMock = vi.spyOn(parse, 'toMessages');
      toMessagesMock.mockReturnValue([
        { role: 'user', content: [{ text: 'Hello World!' }] },
      ]);

      const result = await renderer({ input: { name: 'World' } });

      expect(mockCompiledTemplate).toHaveBeenCalled();
      expect(toMessagesMock).toHaveBeenCalledWith(
        'Hello World!',
        expect.anything()
      );
      expect(result.messages).toEqual([
        { role: 'user', content: [{ text: 'Hello World!' }] },
      ]);
    });

    it('should render a template with provided data', async () => {
      const templateSource = 'Hello {{input.name}}!';

      const toMessagesMock = vi.spyOn(parse, 'toMessages');
      toMessagesMock.mockReturnValue([
        { role: 'user', content: [{ text: 'Hello World!' }] },
      ]);

      const parseDocumentMock = vi.spyOn(parse, 'parseDocument');
      parseDocumentMock.mockReturnValue({
        template: templateSource,
      });

      const handlebarsCompileMock = vi.spyOn(Handlebars, 'compile');
      const mockCompiledTemplate = vi.fn().mockReturnValue('Hello World!');
      handlebarsCompileMock.mockReturnValue(mockCompiledTemplate);

      const result = await dp.render(templateSource, {
        input: { name: 'World' },
      });

      expect(parseDocumentMock).toHaveBeenCalledWith(templateSource);
      expect(handlebarsCompileMock).toHaveBeenCalledWith(
        templateSource,
        expect.anything()
      );
      expect(mockCompiledTemplate).toHaveBeenCalled();
      expect(toMessagesMock).toHaveBeenCalledWith(
        'Hello World!',
        expect.anything()
      );
      expect(result.messages).toEqual([
        { role: 'user', content: [{ text: 'Hello World!' }] },
      ]);
    });
  });

  describe('identifyPartials', () => {
    it('should identify partial references in a template', () => {
      const dp = new Dotprompt();
      const template =
        'Start {{> header}} Middle {{> sidebar}} End {{> footer}}';

      const ast = Handlebars.parse(template);
      const partialSet = new Set<string>();
      const originalHandlebarsVisitor = Handlebars.Visitor;

      class MockVisitor extends originalHandlebarsVisitor {
        PartialStatement(partial: unknown): void {
          if (
            partial &&
            typeof partial === 'object' &&
            'name' in partial &&
            partial.name &&
            typeof partial.name === 'object' &&
            'original' in partial.name &&
            typeof partial.name.original === 'string'
          ) {
            partialSet.add(partial.name.original);
          }
        }
      }

      // @ts-ignore Temporarily modify Handlebars.Visitor
      Handlebars.Visitor = MockVisitor;

      const visitor = new Handlebars.Visitor();
      visitor.accept(ast);

      // @ts-ignore Restore Handlebars.Visitor
      Handlebars.Visitor = originalHandlebarsVisitor;

      expect(partialSet.has('header')).toBe(true);
      expect(partialSet.has('sidebar')).toBe(true);
      expect(partialSet.has('footer')).toBe(true);
      expect(partialSet.size).toBe(3);
    });

    it('should return an empty set for a template with no partials', () => {
      const dp = new Dotprompt();
      const template = 'Template with {{variable}} but no partials';

      const ast = Handlebars.parse(template);
      const partialSet = new Set<string>();
      const originalHandlebarsVisitor = Handlebars.Visitor;

      class MockVisitor extends originalHandlebarsVisitor {
        PartialStatement(partial: unknown): void {
          if (
            partial &&
            typeof partial === 'object' &&
            'name' in partial &&
            partial.name &&
            typeof partial.name === 'object' &&
            'original' in partial.name &&
            typeof partial.name.original === 'string'
          ) {
            partialSet.add(partial.name.original);
          }
        }
      }

      // @ts-ignore Temporarily modify Handlebars.Visitor.
      Handlebars.Visitor = MockVisitor;
      const visitor = new Handlebars.Visitor();

      visitor.accept(ast);

      // @ts-ignore Restore Handlebars.Visitor.
      Handlebars.Visitor = originalHandlebarsVisitor;

      expect(partialSet.size).toBe(0);
    });
  });

  describe('resolveTools', () => {
    it('should resolve registered tools', async () => {
      const dp = new Dotprompt();
      const toolDef: ToolDefinition = {
        name: 'testTool',
        description: 'A test tool',
        inputSchema: {
          type: 'object',
          properties: {
            param1: { type: 'string' },
          },
        },
      };

      dp.defineTool(toolDef);

      const metadata: PromptMetadata = {
        tools: ['testTool', 'unknownTool'],
      };

      // @ts-ignore Accessing private method for testing
      const result = await dp.resolveTools(metadata);

      expect(result.toolDefs).toHaveLength(1);
      expect(result.toolDefs?.[0]).toEqual(toolDef);
      expect(result.tools).toEqual(['unknownTool']);
    });

    it('should use the tool resolver for unregistered tools', async () => {
      const toolDef: ToolDefinition = {
        name: 'resolvedTool',
        description: 'A resolved tool',
        inputSchema: {
          type: 'object',
          properties: {
            param1: { type: 'string' },
          },
        },
      };

      const toolResolver = vi.fn().mockResolvedValue(toolDef);

      const dp = new Dotprompt({
        toolResolver,
      });

      const metadata: PromptMetadata = {
        tools: ['resolvedTool'],
      };

      // @ts-ignore Accessing private method for testing
      const result = await dp.resolveTools(metadata);

      expect(toolResolver).toHaveBeenCalledWith('resolvedTool');
      expect(result.toolDefs).toHaveLength(1);
      expect(result.toolDefs?.[0]).toEqual(toolDef);
      expect(result.tools).toEqual([]);
    });

    it('should throw an error when the tool resolver returns null', async () => {
      const toolResolver = vi.fn().mockResolvedValue(null);

      const dp = new Dotprompt({
        toolResolver,
      });

      const metadata: PromptMetadata = {
        tools: ['nonExistentTool'],
      };

      // @ts-ignore Accessing private method for testing
      await expect(dp.resolveTools(metadata)).rejects.toThrow(
        "Dotprompt: Unable to resolve tool 'nonExistentTool' to a recognized tool definition."
      );
    });
  });

  describe('renderPicoschema', () => {
    it('should process picoschema definitions', async () => {
      const dp = new Dotprompt();

      vi.mock('./picoschema', () => ({
        picoschema: vi.fn().mockImplementation((schema) => {
          return Promise.resolve({
            type: 'object',
            properties: { expanded: true },
          });
        }),
      }));

      const metadata: PromptMetadata = {
        input: {
          schema: { type: 'string' },
        },
        output: {
          schema: { type: 'number' },
        },
      };

      // @ts-ignore Accessing private method for testing.
      const result = await dp.renderPicoschema(metadata);

      expect(result.input?.schema).toEqual({
        type: 'object',
        properties: { expanded: true },
      });
      expect(result.output?.schema).toEqual({
        type: 'object',
        properties: { expanded: true },
      });
    });

    it('should return the original metadata if no schemas are present', async () => {
      const dp = new Dotprompt();

      const metadata: PromptMetadata = {
        model: 'gemini-1.5-pro',
      };

      // @ts-ignore Accessing private method for testing.
      const result = await dp.renderPicoschema(metadata);

      expect(result).toEqual(metadata);
    });
  });

  describe('wrappedSchemaResolver', () => {
    it('should resolve schemas from the registered schemas', async () => {
      const schemas: Record<string, JSONSchema> = {
        'test-schema': {
          type: 'object',
          properties: {
            name: { type: 'string' },
          },
        },
      };

      const dp = new Dotprompt({ schemas });

      // @ts-ignore Accessing private method for testing.
      const result = await dp.wrappedSchemaResolver('test-schema');

      expect(result).toEqual(schemas['test-schema']);
    });

    it('should use the schema resolver for unregistered schemas', async () => {
      const schemaResolver = vi.fn().mockResolvedValue({
        type: 'object',
        properties: {
          resolved: { type: 'boolean' },
        },
      });

      const dp = new Dotprompt({ schemaResolver });

      // @ts-ignore Accessing private method for testing.
      const result = await dp.wrappedSchemaResolver('external-schema');

      expect(schemaResolver).toHaveBeenCalledWith('external-schema');
      expect(result).toEqual({
        type: 'object',
        properties: {
          resolved: { type: 'boolean' },
        },
      });
    });

    it('should return null if schema not found and no resolver', async () => {
      const dp = new Dotprompt();

      // @ts-ignore Accessing private method for testing.
      const result = await dp.wrappedSchemaResolver('non-existent-schema');

      expect(result).toBeNull();
    });
  });

  describe('resolveMetadata', () => {
    it('should merge multiple metadata objects', async () => {
      const dp = new Dotprompt();

      const base: PromptMetadata = {
        model: 'gemini-1.5-pro',
        config: {
          temperature: 0.7,
        },
      };

      const merge1: PromptMetadata = {
        config: {
          top_p: 0.9,
        },
        tools: ['tool1'],
      };

      const merge2: PromptMetadata = {
        model: 'gemini-2.0-flash',
        config: {
          max_tokens: 2000,
        },
      };

      // @ts-ignore Mocking private method.
      dp.resolveTools = vi
        .fn()
        .mockImplementation((metadata) => Promise.resolve(metadata));

      // @ts-ignore Mocking private method.
      dp.renderPicoschema = vi
        .fn()
        .mockImplementation((metadata) => Promise.resolve(metadata));

      // @ts-ignore Accessing private method for testing.
      const result = await dp.resolveMetadata(base, merge1, merge2);

      expect(result.model).toBe('gemini-2.0-flash');
      expect(result.config).toEqual({
        temperature: 0.7,
        top_p: 0.9,
        max_tokens: 2000,
      });
      expect(result.tools).toEqual(['tool1']);

      // @ts-ignore
      expect(dp.resolveTools).toHaveBeenCalled();
      // @ts-ignore
      expect(dp.renderPicoschema).toHaveBeenCalled();
    });

    it('should handle undefined merges', async () => {
      const dp = new Dotprompt();

      const base: PromptMetadata = {
        model: 'gemini-1.5-pro',
        config: {
          temperature: 0.7,
        },
      };

      // @ts-ignore Mocking private method.
      dp.resolveTools = vi
        .fn()
        .mockImplementation((metadata) => Promise.resolve(metadata));

      // @ts-ignore Mocking private method.
      dp.renderPicoschema = vi
        .fn()
        .mockImplementation((metadata) => Promise.resolve(metadata));

      // @ts-ignore Accessing private method for testing.
      const result = await dp.resolveMetadata(base, undefined);

      expect(result.model).toBe('gemini-1.5-pro');
      expect(result.config).toEqual({
        temperature: 0.7,
      });
    });
  });

  describe('resolvePartials', () => {
    it('should resolve and register partials from a template', async () => {
      const partialResolver = vi.fn();
      partialResolver.mockImplementation((name: string) => {
        if (name === 'header') return 'Header content';
        if (name === 'footer') return 'Footer content';
        return null;
      });

      const dp = new Dotprompt({ partialResolver });

      // @ts-ignore Creating a partials mock.
      Handlebars.partials = {};

      const identifyPartialsMock = vi
        .fn()
        .mockReturnValue(new Set(['header', 'footer']));
      // @ts-ignore Setting private method for testing.
      dp.identifyPartials = identifyPartialsMock;

      const definePartialSpy = vi.spyOn(dp, 'definePartial');

      const template = '{{> header}} Main content {{> footer}}';

      // @ts-ignore Calling private method for testing.
      await dp.resolvePartials(template);

      expect(identifyPartialsMock).toHaveBeenCalledWith(template);
      expect(partialResolver).toHaveBeenCalledWith('header');
      expect(partialResolver).toHaveBeenCalledWith('footer');
      expect(definePartialSpy).toHaveBeenCalledWith('header', 'Header content');
      expect(definePartialSpy).toHaveBeenCalledWith('footer', 'Footer content');
    });

    it('should not try to resolve partials when no resolver or store is provided', async () => {
      const dp = new Dotprompt();

      const template = '{{> header}} Main content {{> footer}}';

      const identifyPartialsMock = vi.fn();
      // @ts-ignore Mocking private method.
      dp.identifyPartials = identifyPartialsMock;

      // @ts-ignore Accessing private method for testing.
      await dp.resolvePartials(template);

      expect(identifyPartialsMock).not.toHaveBeenCalled();
    });

    it('should use the store as fallback if partial resolver returns null', async () => {
      const partialResolver = vi.fn().mockResolvedValue(null);

      const store = {
        loadPartial: vi.fn().mockResolvedValue({
          source: 'Partial from store',
        }),
      };

      const dp = new Dotprompt({ partialResolver });
      // @ts-ignore Setting private property for testing.
      dp.store = store;

      // @ts-ignore Creating a partials mock.
      Handlebars.partials = {};

      const template = '{{> partial}}';

      const identifyPartialsMock = vi
        .fn()
        .mockReturnValue(new Set(['partial']));

      // @ts-ignore Mocking private method.
      dp.identifyPartials = identifyPartialsMock;

      const definePartialSpy = vi.spyOn(dp, 'definePartial');

      // @ts-ignore Accessing private method for testing
      await dp.resolvePartials(template);

      expect(partialResolver).toHaveBeenCalledWith('partial');
      expect(store.loadPartial).toHaveBeenCalledWith('partial');
      expect(definePartialSpy).toHaveBeenCalledWith(
        'partial',
        'Partial from store'
      );
    });
  });

  describe('renderMetadata', () => {
    it('should process parsed source metadata', async () => {
      const dp = new Dotprompt();

      const parsedSource = {
        template: 'Template content',
        model: 'gemini-1.5-pro',
      };

      const resolveMetadataMock = vi.fn().mockResolvedValue({
        model: 'gemini-1.5-pro',
        processed: true,
      });

      // @ts-ignore Mocking private method
      dp.resolveMetadata = resolveMetadataMock;

      const result = await dp.renderMetadata(parsedSource);

      expect(resolveMetadataMock).toHaveBeenCalledWith(
        {},
        parsedSource,
        undefined
      );

      expect(result).toEqual({
        model: 'gemini-1.5-pro',
        processed: true,
      });
    });

    it('should use the default model when no model is specified', async () => {
      const dp = new Dotprompt({ defaultModel: 'default-model' });

      const parsedSource = {
        template: 'Template content',
      };

      const resolveMetadataMock = vi.fn().mockResolvedValue({
        model: 'default-model',
        processed: true,
      });

      // @ts-ignore Mocking private method
      dp.resolveMetadata = resolveMetadataMock;

      const result = await dp.renderMetadata(parsedSource);

      expect(resolveMetadataMock).toHaveBeenCalled();

      expect(result).toEqual({
        model: 'default-model',
        processed: true,
      });
    });

    it('should use model configs when available', async () => {
      const modelConfigs = {
        'gemini-1.5-pro': { temperature: 0.7 },
      };

      const dp = new Dotprompt({ modelConfigs });

      const parsedSource = {
        template: 'Template content',
        model: 'gemini-1.5-pro',
      };

      const resolveMetadataMock = vi
        .fn()
        .mockImplementation((base, ...args) => {
          return Promise.resolve({
            ...args[0],
            config: { ...base.config },
          });
        });
      // @ts-ignore Mocking private method
      dp.resolveMetadata = resolveMetadataMock;

      const result = await dp.renderMetadata(parsedSource);

      expect(resolveMetadataMock).toHaveBeenCalledWith(
        { config: { temperature: 0.7 } },
        parsedSource,
        undefined
      );

      expect(result.config).toEqual({ temperature: 0.7 });
    });
  });
});
