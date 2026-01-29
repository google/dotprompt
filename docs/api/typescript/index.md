# TypeScript/JavaScript API

The `dotprompt` package is the canonical TypeScript/JavaScript implementation
of the Dotprompt file format.

## Installation

\=== "npm"
`bash
    npm install dotprompt
    `

\=== "pnpm"
`bash
    pnpm add dotprompt
    `

\=== "yarn"
`bash
    yarn add dotprompt
    `

## Quick Start

```typescript
import { Dotprompt } from 'dotprompt';

// Create a Dotprompt instance
const dotprompt = new Dotprompt();

// Parse and render a prompt
const source = `
---
model: gemini-pro
input:
  schema:
    name: string
---
Hello, {{name}}!
`;

const rendered = await dotprompt.render(source, {
  input: { name: 'World' }
});

console.log(rendered.messages);
```

## Core Classes

### Dotprompt

The main entry point for working with Dotprompt templates.

```typescript
import { Dotprompt } from 'dotprompt';

const dp = new Dotprompt({
  defaultModel: 'gemini-pro',
  helpers: {
    uppercase: (params) => String(params[0]).toUpperCase(),
  },
  partials: {
    header: 'Welcome to {{appName}}!',
  },
});
```

#### Constructor Options

| Option | Type | Description |
|--------|------|-------------|
| `defaultModel` | `string` | Default model to use when not specified in template |
| `modelConfigs` | `Record<string, ModelConfig>` | Model-specific configurations |
| `helpers` | `Record<string, HelperFn>` | Custom Handlebars helpers |
| `partials` | `Record<string, string>` | Partial templates |
| `tools` | `Record<string, ToolDefinition>` | Static tool definitions |
| `toolResolver` | `ToolResolver` | Dynamic tool resolution function |
| `schemas` | `Record<string, JsonSchema>` | Static schema definitions |
| `schemaResolver` | `SchemaResolver` | Dynamic schema resolution function |
| `partialResolver` | `PartialResolver` | Dynamic partial resolution function |

#### Methods

##### `parse(source: string): ParsedPrompt`

Parse a Dotprompt template string into a structured object.

```typescript
const parsed = dp.parse(source);
console.log(parsed.template);  // The Handlebars template
console.log(parsed.model);     // The model name
console.log(parsed.input);     // Input schema configuration
```

##### `compile(source: string): Promise<PromptFunction>`

Compile a template into a reusable render function.

```typescript
const renderFn = await dp.compile(source);
const result = await renderFn({ input: { name: 'World' } });
```

##### `render(source: string, data: DataArgument): Promise<RenderedPrompt>`

Parse, compile, and render a template in one step.

```typescript
const rendered = await dp.render(source, {
  input: { name: 'World' },
  messages: previousMessages,  // Optional history
});
```

##### `defineHelper(name: string, fn: HelperFn): Dotprompt`

Register a custom Handlebars helper.

```typescript
dp.defineHelper('shout', (params) => {
  return String(params[0]).toUpperCase() + '!';
});
```

##### `definePartial(name: string, source: string): Dotprompt`

Register a partial template.

```typescript
dp.definePartial('signature', 'Best regards,\n{{author}}');
```

##### `defineTool(definition: ToolDefinition): Dotprompt`

Register a tool definition.

```typescript
dp.defineTool({
  name: 'calculator',
  description: 'Perform calculations',
  inputSchema: { type: 'object', properties: { expression: { type: 'string' } } },
});
```

## Types

### ParsedPrompt

Result of parsing a Dotprompt template.

```typescript
interface ParsedPrompt<T = any> {
  template: string;
  name?: string;
  description?: string;
  variant?: string;
  version?: string;
  model?: string;
  config?: T;
  input?: PromptInputConfig;
  output?: PromptOutputConfig;
  tools?: string[];
  toolDefs?: ToolDefinition[];
  ext?: Record<string, Record<string, any>>;
  raw?: Record<string, any>;
}
```

### RenderedPrompt

Result of rendering a Dotprompt template.

```typescript
interface RenderedPrompt<T = any> extends PromptMetadata<T> {
  messages: Message[];
}
```

### Message

A single message in a conversation.

```typescript
interface Message {
  role: 'user' | 'model' | 'tool' | 'system';
  content: Part[];
  metadata?: Record<string, any>;
}
```

### Part

Content within a message.

```typescript
type Part = TextPart | MediaPart | DataPart | ToolRequestPart | ToolResponsePart | PendingPart;

interface TextPart {
  text: string;
  metadata?: Record<string, any>;
}

interface MediaPart {
  media: {
    url: string;
    contentType?: string;
  };
  metadata?: Record<string, any>;
}
```

### DataArgument

Runtime data for rendering a template.

```typescript
interface DataArgument<T = Record<string, any>> {
  input?: T;
  docs?: Document[];
  messages?: Message[];
  context?: Record<string, any>;
}
```

## Built-in Helpers

| Helper | Description | Example |
|--------|-------------|---------|
| `role` | Set message role | `{{role "system"}}` |
| `media` | Insert media content | `{{media url="..." contentType="image/png"}}` |
| `history` | Insert message history | `{{history}}` |
| `section` | Create a content section | `{{section "code"}}` |
| `json` | Serialize to JSON | `{{json data indent=2}}` |
| `ifEquals` | Conditional equality | `{{#ifEquals a b}}...{{/ifEquals}}` |
| `unlessEquals` | Conditional inequality | `{{#unlessEquals a b}}...{{/unlessEquals}}` |

## Stores

### DirStore

Load prompts from a directory.

```typescript
import { DirStore } from 'dotprompt/stores';

const store = new DirStore({ directory: './prompts' });
const prompt = await store.load('greeting');
```

## External Documentation

* [npm package](https://www.npmjs.com/package/dotprompt)
* [GitHub source](https://github.com/google/dotprompt/tree/main/js)
