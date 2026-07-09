# @dotprompt/codemirror

CodeMirror 6 language support for Dotprompt (`.prompt`) files.

## Features

- **Syntax Highlighting**: YAML frontmatter, Handlebars templates
- **Autocompletion**: Helpers, frontmatter fields, model names
- **Theming**: Dark and light theme support

## Installation

```bash
npm install @dotprompt/codemirror
# or
pnpm add @dotprompt/codemirror
```

## Usage

```typescript
import { dotprompt } from '@dotprompt/codemirror';
import { EditorView, basicSetup } from 'codemirror';

const view = new EditorView({
  doc: `---
model: gemini-2.0-flash
---
Hello, {{name}}!`,
  extensions: [basicSetup, dotprompt()],
  parent: document.getElementById('editor')!,
});
```

## Building

```bash
pnpm install
pnpm run build
```

## License

Apache-2.0
