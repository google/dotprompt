/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export type Schema = Record<string, any>;

export interface ToolDefinition {
  name: string;
  description?: string;
  inputSchema: Schema;
  outputSchema?: Schema;
}

export type ToolArgument = string | ToolDefinition;

interface HasMetadata {
  /** Arbitrary metadata to be used by tooling or for informational purposes. */
  metadata?: Record<string, any>;
}

export interface PromptRef {
  name: string;
  variant?: string;
  version?: string;
}

export interface PromptData extends PromptRef {
  source: string;
}

export interface PromptMetadata<ModelConfig = Record<string, any>>
  extends HasMetadata {
  /** The name of the prompt. */
  name?: string;
  /** The variant name for the prompt. */
  variant?: string;
  /** The version of the prompt. */
  version?: string;
  /** A description of the prompt. */
  description?: string;
  /** The name of the model to use for this prompt, e.g. `vertexai/gemini-1.0-pro` */
  model?: string;
  /** Names of tools (registered separately) to allow use of in this prompt. */
  tools?: string[];
  /** Definitions of tools to allow use of in this prompt. */
  toolDefs?: ToolDefinition[];
  /** Model configuration. Not all models support all options. */
  config?: ModelConfig;
  /** Configuration for input variables. */
  input?: {
    /** Defines the default input variable values to use if none are provided. */
    default?: Record<string, any>;
    /** Schema definition for input variables. */
    schema?: Schema;
  };

  /** Defines the expected model output format. */
  output?: {
    /** Desired output format for this prompt. */
    format?: string | 'json' | 'text';
    /** Schema defining the output structure. */
    schema?: Schema;
  };
  /**
   * This field will contain the raw frontmatter as parsed with no additional processing
   * or substitutions. If your implementation requires custom fields they will be available
   * here.
   **/
  raw?: Record<string, any>;
  /**
   * Fields that contain a period will be considered "extension fields" in the frontmatter
   * and will be gathered by namespace. For example, `myext.foo: 123` would be available
   * at `parsedPrompt.ext.myext.foo`. Nested namespaces will be flattened, so `myext.foo.bar: 123`
   * would be available at `parsedPrompt.ext["myext.foo"].bar`.
   */
  ext?: Record<string, Record<string, any>>;
}

export interface ParsedPrompt<ModelConfig = Record<string, any>>
  extends PromptMetadata<ModelConfig> {
  /** The source of the template with metadata / frontmatter already removed. */
  template: string;
}

interface EmptyPart extends HasMetadata {
  text?: never;
  data?: never;
  media?: never;
  toolRequest?: never;
  toolResponse?: never;
}

export type TextPart = Omit<EmptyPart, 'text'> & { text: string };
export type DataPart = Omit<EmptyPart, 'data'> & { data: Record<string, any> };
export type MediaPart = Omit<EmptyPart, 'media'> & {
  media: { url: string; contentType?: string };
};
export type ToolRequestPart<Input = any> = Omit<EmptyPart, 'toolRequest'> & {
  toolRequest: { name: string; input?: Input; ref?: string };
};
export type ToolResponsePart<Output = any> = Omit<EmptyPart, 'toolResponse'> & {
  toolResponse: { name: string; output?: Output; ref?: string };
};
export type PendingPart = EmptyPart & {
  metadata: { pending: true; [key: string]: any };
};
export type Part =
  | TextPart
  | DataPart
  | MediaPart
  | ToolRequestPart
  | ToolResponsePart
  | PendingPart;

export interface Message extends HasMetadata {
  role: 'user' | 'model' | 'tool' | 'system';
  content: Part[];
}

export interface Document extends HasMetadata {
  content: Part[];
}

/**
 * DataArgument provides all of the information necessary to render a
 * template at runtime.
 **/
export interface DataArgument<Variables = any, State = any> {
  /** Input variables for the prompt template. */
  input?: Variables;
  /** Relevant documents. */
  docs?: Document[];
  /** Previous messages in the history of a multi-turn conversation. */
  messages?: Message[];
  /**
   * Items in the context argument are exposed as `@` variables, e.g.
   * `context: {state: {...}}` is exposed as `@state`.
   **/
  context?: Record<string, any>;
}

export type JSONSchema = any;

/**
 * SchemaResolver is a function that can resolve a provided schema name to
 * an underlying JSON schema, utilized for shorthand to a schema library
 * provided by an external tool.
 **/
export type SchemaResolver = (
  schemaName: string
) => JSONSchema | null | Promise<JSONSchema | null>;

/**
 * SchemaResolver is a function that can resolve a provided tool name to
 * an underlying ToolDefinition, utilized for shorthand to a tool registry
 * provided by an external library.
 **/
export type ToolResolver = (
  toolName: string
) => ToolDefinition | null | Promise<ToolDefinition | null>;

/**
 * RenderedPrompt is the final result of rendering a Dotprompt template.
 * It includes all of the prompt metadata as well as a set of `messages` to
 * be sent to the  model.
 */
export interface RenderedPrompt<ModelConfig = Record<string, any>>
  extends PromptMetadata<ModelConfig> {
  /** The rendered messages of the prompt. */
  messages: Message[];
}

/**
 * PromptFunction is a function that takes runtime data / context and returns
 * a rendered prompt result.
 */
export interface PromptFunction<ModelConfig = Record<string, any>> {
  (
    data: DataArgument,
    options?: PromptMetadata<ModelConfig>
  ): Promise<RenderedPrompt<ModelConfig>>;
  prompt: ParsedPrompt<ModelConfig>;
}

/**
 * PromptRefFunction is a function that takes runtime data / context and returns
 * a rendered prompt result after loading a prompt via reference.
 */
export interface PromptRefFunction<ModelConfig = Record<string, any>> {
  (
    data: DataArgument,
    options?: PromptMetadata<ModelConfig>
  ): Promise<RenderedPrompt<ModelConfig>>;
  promptRef: PromptRef;
}

export interface PaginatedResponse {
  cursor?: string;
}

export interface PartialRef {
  name: string;
  variant?: string;
  version?: string;
}

export interface PartialData extends PartialRef {
  source: string;
}

/**
 * PromptStore is a common interface that provides for
 */
export interface PromptStore {
  /** Return a list of all prompts in the store (optionally paginated). Some store providers may return limited metadata. */
  list(options?: {
    cursor?: string;
    limit?: number;
  }): Promise<{ prompts: Array<PromptRef>; cursor?: string }>;
  /** Return a list of partial names available in this store. */
  listPartials(options?: { cursor?: string; limit?: number }): Promise<{
    partials: Array<PartialRef>;
    cursor?: string;
  }>;
  /** Retrieve a prompt from the store.  */
  load(
    name: string,
    options?: { variant?: string; version?: string }
  ): Promise<PromptData>;
  /** Retrieve a partial from the store. */
  loadPartial(
    name: string,
    options?: { variant?: string; version?: string }
  ): Promise<PromptData>;
}

/**
 * PromptStoreWritable is a PromptStore that also has built-in methods for writing prompts in addition to reading them.
 */
export interface PromptStoreWritable extends PromptStore {
  /** Save a prompt in the store. May be destructive for prompt stores without versioning. */
  save(prompt: PromptData): Promise<void>;
  /** Delete a prompt from the store. */
  delete(name: string, options?: { variant?: string }): Promise<void>;
}

export interface PromptBundle {
  partials: PartialData[];
  prompts: PromptData[];
}
