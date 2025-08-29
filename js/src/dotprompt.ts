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

import Handlebars from 'handlebars/dist/cjs/handlebars.js';
import * as builtinHelpers from './helpers';
import { parseDocument, toMessages } from './parse';
import { picoschema } from './picoschema';
import type {
  DataArgument,
  JSONSchema,
  ParsedPrompt,
  PromptFunction,
  PromptMetadata,
  PromptStore,
  RenderedPrompt,
  Schema,
  SchemaResolver,
  ToolDefinition,
  ToolResolver,
} from './types';
import { removeUndefinedFields } from './util';

/** Function to resolve partial names to their content */
export type PartialResolver = (
  partialName: string
) => string | null | Promise<string | null>;

/** Options for the Dotprompt class. */
export interface DotpromptOptions {
  /** A default model to use if none is supplied. */
  defaultModel?: string;
  /** Assign a set of default configuration options to be used with a particular model. */
  modelConfigs?: Record<string, object>;
  /** Helpers to pre-register. */
  helpers?: Record<string, Handlebars.HelperDelegate>;
  /** Partials to pre-register. */
  partials?: Record<string, string>;
  /** Provide a static mapping of tool definitions that should be used when resolving tool names. */
  tools?: Record<string, ToolDefinition>;
  /** Provide a lookup implementation to resolve tool names to definitions. */
  toolResolver?: ToolResolver;
  /** Provide a static mapping of schema names to their JSON Schema definitions. */
  schemas?: Record<string, JSONSchema>;
  /** Provide a lookup implementation to resolve schema names to JSON schema definitions. */
  schemaResolver?: SchemaResolver;
  /** Provide a lookup implementation to resolve partial names to their content. */
  partialResolver?: PartialResolver;
}

/**
 * The main class for the Dotprompt library.
 */
export class Dotprompt {
  private handlebars: typeof Handlebars;
  private knownHelpers: Record<string, true> = {};
  private defaultModel?: string;
  private modelConfigs: Record<string, object> = {};
  private tools: Record<string, ToolDefinition> = {};
  private toolResolver?: ToolResolver;
  private schemas: Record<string, JSONSchema> = {};
  private schemaResolver?: SchemaResolver;
  private partialResolver?: PartialResolver;
  private store?: PromptStore;

  constructor(options?: DotpromptOptions) {
    this.handlebars = Handlebars.noConflict();
    this.modelConfigs = options?.modelConfigs || this.modelConfigs;
    this.defaultModel = options?.defaultModel;
    this.tools = options?.tools || {};
    this.toolResolver = options?.toolResolver;
    this.schemas = options?.schemas || {};
    this.schemaResolver = options?.schemaResolver;
    this.partialResolver = options?.partialResolver;

    this.registerInitialHelpers(builtinHelpers, options?.helpers);
    this.registerInitialPartials(options?.partials);
  }


  /**
   * Registers a helper function for use in templates.
   *
   * @param name The name of the helper function to register
   * @param fn The helper function implementation
   * @return This instance for method chaining
   */
  defineHelper(name: string, fn: Handlebars.HelperDelegate): this {
    this.handlebars.registerHelper(name, fn);
    this.knownHelpers[name] = true;
    return this;
  }

  /**
   * Registers a partial template for use in other templates.
   *
   * @param name The name of the partial to register
   * @param source The template source for the partial
   * @return This instance for method chaining
   */
  definePartial(name: string, source: string): this {
    this.handlebars.registerPartial(name, source);
    return this;
  }

  /**
   * Registers a tool definition for use in prompts.
   *
   * @param def The tool definition to register
   * @return This instance for method chaining
   */
  defineTool(def: ToolDefinition): this {
    this.tools[def.name] = def;
    return this;
  }

  /**
   * Parses a prompt template string into a structured ParsedPrompt object.
   *
   * @param source The template source string to parse
   * @return A parsed prompt object with extracted metadata and template
   */
  parse<ModelConfig = Record<string, unknown>>(
    source: string
  ): ParsedPrompt<ModelConfig> {
    return parseDocument<ModelConfig>(source);
  }

  /**
   * Renders a prompt template with the provided data.
   *
   * @param source The template source string to render
   * @param data The data to use when rendering the template
   * @param options Additional metadata and options for rendering
   * @return A promise resolving to the rendered prompt
   */
  async render<
    Variables = Record<string, unknown>,
    ModelConfig = Record<string, unknown>,
  >(
    source: string,
    data: DataArgument<Variables> = {},
    options?: PromptMetadata<ModelConfig>
  ): Promise<RenderedPrompt<ModelConfig>> {
    const renderer = await this.compile<Variables, ModelConfig>(source);
    return renderer(data, options);
  }

  /**
   * Compiles a template into a reusable function for rendering prompts.
   *
   * @param source The template source or parsed prompt to compile
   * @param additionalMetadata Additional metadata to include in the compiled template
   * @return A promise resolving to a function for rendering the template
   */
  async compile<
    Variables = Record<string, unknown>,
    ModelConfig = Record<string, unknown>,
  >(
    source: string | ParsedPrompt<ModelConfig>,
    additionalMetadata?: PromptMetadata<ModelConfig>
  ): Promise<PromptFunction<ModelConfig>> {
    let parsedSource: ParsedPrompt<ModelConfig>;
    if (typeof source === 'string') {
      parsedSource = this.parse<ModelConfig>(source);
    } else {
      parsedSource = source;
    }

    if (additionalMetadata) {
      parsedSource = { ...parsedSource, ...additionalMetadata };
    }

    // Resolve all partials before compilation.
    await this.resolvePartials(parsedSource.template);

    const renderString = this.handlebars.compile<Variables>(
      parsedSource.template,
      {
        knownHelpers: this.knownHelpers,
        knownHelpersOnly: true,
        noEscape: true,
      }
    );

    // Create an instance of a PromptFunction.
    const renderFunc = async (
      data: DataArgument,
      options?: PromptMetadata<ModelConfig>
    ) => {
      // Discard the input schema as once rendered it doesn't make sense.
      const { input, ...mergedMetadata } =
        await this.renderMetadata(parsedSource);

      const renderedString = renderString(
        { ...(options?.input?.default || {}), ...data.input },
        {
          data: {
            metadata: {
              prompt: mergedMetadata,
              docs: data.docs,
              messages: data.messages,
            },
            ...(data.context || {}),
          },
        }
      );

      return {
        ...mergedMetadata,
        messages: toMessages<ModelConfig>(renderedString, data),
      };
    };

    // Add the parsed source to the prompt function as a property.
    (renderFunc as PromptFunction<ModelConfig>).prompt = parsedSource;

    return renderFunc as PromptFunction<ModelConfig>;
  }

  /**
   * Processes and resolves all metadata for a prompt template.
   *
   * @param source The template source or parsed prompt
   * @param additionalMetadata Additional metadata to include
   * @return A promise resolving to the fully processed metadata
   */
  async renderMetadata<ModelConfig>(
    source: string | ParsedPrompt<ModelConfig>,
    additionalMetadata?: PromptMetadata<ModelConfig>
  ): Promise<PromptMetadata<ModelConfig>> {
    let parsedSource: ParsedPrompt<ModelConfig>;
    if (typeof source === 'string') {
      parsedSource = this.parse<ModelConfig>(source);
    } else {
      parsedSource = source;
    }

    const model =
      additionalMetadata?.model || parsedSource.model || this.defaultModel;

    let modelConfig: ModelConfig | undefined;
    if (model && this.modelConfigs[model]) {
      modelConfig = this.modelConfigs[model] as ModelConfig;
    }

    return this.resolveMetadata<ModelConfig>(
      modelConfig ? { config: modelConfig } : {},
      parsedSource,
      additionalMetadata
    );
  }

  /**
   * Merges multiple metadata objects together, resolving tools and schemas.
   *
   * @param base The base metadata object
   * @param merges Additional metadata objects to merge into the base
   * @return A promise resolving to the merged and processed metadata
   */
  private async resolveMetadata<ModelConfig = Record<string, unknown>>(
    base: PromptMetadata<ModelConfig>,
    ...merges: (PromptMetadata<ModelConfig> | undefined)[]
  ): Promise<PromptMetadata<ModelConfig>> {
    let out = { ...base };

    for (let i = 0; i < merges.length; i++) {
      if (!merges[i]) {
        continue;
      }

      // Keep a reference to the original config.
      const originalConfig = out.config || ({} as ModelConfig);

      // Merge the new metadata.
      out = { ...out, ...merges[i] };

      // Merge the configs.
      out.config = { ...originalConfig, ...(merges[i]?.config || {}) };
    }

    // Remove the template attribute if it exists.
    const { template: _, ...outWithoutTemplate } =
      out as PromptMetadata<ModelConfig> & { template?: string };
    out = outWithoutTemplate as PromptMetadata<ModelConfig>;

    out = removeUndefinedFields(out);
    // TODO: Can this be done concurrently?
    out = await this.resolveTools(out);
    out = await this.renderPicoschema(out);

    return out;
  }

  /**
   * Processes schema definitions in picoschema format into standard JSON Schema.
   *
   * @param meta The prompt metadata containing schema definitions
   * @return A promise resolving to the processed metadata with expanded schemas
   */
  private async renderPicoschema<ModelConfig>(
    meta: PromptMetadata<ModelConfig>
  ): Promise<PromptMetadata<ModelConfig>> {
    if (!meta.output?.schema && !meta.input?.schema) {
      return meta;
    }

    const resolveSchema = (schema: Schema): Promise<Schema> => {
      return picoschema(schema, {
        schemaResolver: this.wrappedSchemaResolver.bind(this),
      });
    };

    const newMeta = { ...meta };
    let inputPromise: Promise<Schema | null> | null = null;
    let outputPromise: Promise<Schema | null> | null = null;

    // Collect all schemas to resolve.
    if (meta.input?.schema) {
      newMeta.input = { ...meta.input };
      inputPromise = resolveSchema(meta.input.schema);
    }
    if (meta.output?.schema) {
      newMeta.output = { ...meta.output };
      outputPromise = resolveSchema(meta.output.schema);
    }

    // Resolve schemas concurrently.
    const [inputSchema, outputSchema] = await Promise.all([
      inputPromise ?? Promise.resolve(null),
      outputPromise ?? Promise.resolve(null),
    ]);

    if (inputSchema && newMeta.input) {
      newMeta.input.schema = inputSchema;
    }
    if (outputSchema && newMeta.output) {
      newMeta.output.schema = outputSchema;
    }

    return newMeta;
  }

  /**
   * Resolves a schema name to its definition, using registered schemas or schema resolver.
   *
   * @param name The name of the schema to resolve
   * @return A promise resolving to the schema definition or null if not found
   */
  private async wrappedSchemaResolver(
    name: string
  ): Promise<JSONSchema | null> {
    if (this.schemas[name]) {
      return this.schemas[name];
    }
    if (this.schemaResolver) {
      return await this.schemaResolver(name);
    }
    return null;
  }

  /**
   * Resolves tool names to their definitions using registered tools or tool resolver.
   *
   * @param base The metadata containing tool references to resolve
   * @return A promise resolving to metadata with resolved tool definitions
   */
  private async resolveTools<ModelConfig>(
    base: PromptMetadata<ModelConfig>
  ): Promise<PromptMetadata<ModelConfig>> {
    const out = { ...base };
    if (!out.tools) {
      return out;
    }

    // Resolve tools that are already registered into toolDefs, leave
    // unregistered tools alone.
    const unregisteredNames: string[] = [];
    out.toolDefs = out.toolDefs || [];

    await Promise.all(
      out.tools.map(async (name: string) => {
        if (this.tools[name]) {
          // Found locally.
          if (out.toolDefs) {
            out.toolDefs.push(this.tools[name]);
          }
        } else if (this.toolResolver) {
          // Resolve from the tool resolver.
          const resolvedTool = await this.toolResolver(name);
          if (!resolvedTool) {
            throw new Error(
              `Dotprompt: Unable to resolve tool '${name}' to a recognized tool definition.`
            );
          }
          if (out.toolDefs) {
            out.toolDefs.push(resolvedTool);
          }
        } else {
          // Unregistered tool.
          unregisteredNames.push(name);
        }
      })
    );

    out.tools = unregisteredNames;
    return out;
  }

  /**
   * Identifies all partial references in a template.
   *
   * @param template The template to scan for partial references
   * @return A set of partial names referenced in the template
   */
  private identifyPartials(template: string): Set<string> {
    const ast = this.handlebars.parse(template);
    const partials = new Set<string>();

    // Create a visitor to collect partial names.
    const visitor = new (class extends this.handlebars.Visitor {
      // Visit partial statements and add their names to our set.
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
          partials.add(partial.name.original);
        }
      }
    })();

    visitor.accept(ast);
    return partials;
  }

  /**
   * Resolves and registers all partials referenced in a template.
   *
   * @param template The template containing partial references
   * @return A promise that resolves when all partials are registered
   */
  private async resolvePartials(template: string): Promise<void> {
    if (!this.partialResolver && !this.store) {
      return;
    }

    const names = this.identifyPartials(template);

    // Resolve and register each partial.
    await Promise.all(
      Array.from(names).map(async (name: string) => {
        if (!this.handlebars.partials[name]) {
          let content: string | null | undefined = null;

          if (this.partialResolver) {
            content = await this.partialResolver(name);
          }

          if (!content && this.store) {
            const partial = await this.store.loadPartial(name);
            content = partial?.source;
          }

          if (content) {
            this.definePartial(name, content);
            // Recursively resolve partials in the partial content.
            await this.resolvePartials(content);
          }
        }
      })
    );
  }

  /**
   * Registers initial helpers from built-in helpers and options.
   * @private
   */
  private registerInitialHelpers(
    builtinHelpers?: Record<string, Handlebars.HelperDelegate>,
    customHelpers?: Record<string, Handlebars.HelperDelegate>
  ): void {
    // Register built-in helpers
    if (builtinHelpers) {
      for (const key in builtinHelpers) {
        this.defineHelper(
          key,
          builtinHelpers[key as keyof typeof builtinHelpers]
        );
      }
    }

    // Register custom helpers from options
    if (customHelpers) {
      for (const key in customHelpers) {
        this.defineHelper(key, customHelpers[key]);
      }
    }
  }

  /**
   * Registers initial partials from the options.
   *
   * @param partials The partials to register
   * @private
   */
  private registerInitialPartials(partials?: Record<string, string>): void {
    if (partials) {
      for (const key in partials) {
        this.definePartial(key, partials[key]);
      }
    }
  }
}
