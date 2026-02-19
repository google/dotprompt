# TypeScript Dotprompt (Reference Implementation)

Executable GenAI prompt templates in TypeScript/JavaScript.

## Overview

This is the reference implementation of the Dotprompt format -- a
language-neutral executable prompt template format for Generative AI. All
other language runtimes (Python, Go, Rust, Dart, Java) are tested against
the shared [spec suite](../spec/) to ensure cross-language compatibility.

## Features

- YAML frontmatter for prompt metadata (model, config, input/output schemas)
- Handlebars templating with 7 built-in helpers (role, media, history,
  section, json, ifEquals, unlessEquals)
- Picoschema: compact schema notation with JSON Schema conversion
- Multi-message prompts with role markers
- Named partials with recursive resolution and cycle detection
- PromptStore interface with DirStore (file system) implementation
- Custom loaders and schema/tool resolvers
- Tools/functions and safety settings via config passthrough

## Installation

```bash
npm install dotprompt
# or
pnpm add dotprompt
```

## Usage

```typescript
import { Dotprompt } from 'dotprompt';

const dp = new Dotprompt();
const source = `---
model: gemini-2.0-flash
input:
  schema:
    name: string
---
Hello, {{name}}!`;

const rendered = await dp.render(source, { input: { name: 'World' } });
```

## Building

```bash
pnpm install
pnpm run build
```

## Testing

```bash
pnpm test
```

## Published Package

- **npm**: [dotprompt](https://www.npmjs.com/package/dotprompt)

## License

Apache-2.0
