# @dotprompt/monaco

Monaco Editor language support for Dotprompt (`.prompt`) files.

## Features

- **Syntax Highlighting**: YAML frontmatter, Handlebars templates, Dotprompt markers
- **Autocompletion**: Helpers, frontmatter fields, model names, role snippets
- **Hover Documentation**: Helper and frontmatter field documentation
- **Bracket Matching**: Auto-closing for `{{ }}`, `{{# }}`, etc.
- **Folding**: Collapse Handlebars blocks
- **Themes**: Dark theme rules included

## Installation

```bash
npm install @dotprompt/monaco monaco-editor
# or
pnpm add @dotprompt/monaco monaco-editor
```

## Usage

### Basic Registration

```typescript
import * as monaco from 'monaco-editor';
import { registerDotpromptLanguage } from '@dotprompt/monaco';

// Register the Dotprompt language
registerDotpromptLanguage(monaco);

// Create an editor
const editor = monaco.editor.create(document.getElementById('container')!, {
  value: `---
model: gemini-2.5-flash
config:
  temperature: 0.7
---

{{#role "system"}}
You are a helpful assistant.
{{/role}}

{{#role "user"}}
Hello, {{ name }}!
{{/role}}`,
  language: 'dotprompt',
  theme: 'vs-dark',
});
```

### With Custom Options

```typescript
import { registerDotpromptLanguage, createDotpromptTheme } from '@dotprompt/monaco';

const disposable = registerDotpromptLanguage(monaco, {
  completions: true,   // Enable autocompletion (default: true)
  hover: true,         // Enable hover docs (default: true)
  themes: {
    'dotprompt-dark': createDotpromptTheme('vs-dark'),
  },
});

// Use the custom theme
monaco.editor.setTheme('dotprompt-dark');

// Cleanup when done
disposable.dispose();
```

### React Integration

```tsx
import { Editor } from '@monaco-editor/react';
import { registerDotpromptLanguage } from '@dotprompt/monaco';

function DotpromptEditor({ value, onChange }) {
  const handleEditorWillMount = (monaco) => {
    registerDotpromptLanguage(monaco);
  };

  return (
    <Editor
      height="400px"
      language="dotprompt"
      value={value}
      onChange={onChange}
      beforeMount={handleEditorWillMount}
      theme="vs-dark"
    />
  );
}
```

### Angular Integration

```typescript
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import * as monaco from 'monaco-editor';
import { registerDotpromptLanguage } from '@dotprompt/monaco';

@Component({
  selector: 'app-prompt-editor',
  template: '<div #editorContainer style="height: 400px;"></div>',
})
export class PromptEditorComponent implements OnInit {
  @ViewChild('editorContainer', { static: true })
  editorContainer!: ElementRef;

  ngOnInit() {
    registerDotpromptLanguage(monaco);

    monaco.editor.create(this.editorContainer.nativeElement, {
      value: '',
      language: 'dotprompt',
      theme: 'vs-dark',
    });
  }
}
```

## API

### `registerDotpromptLanguage(monaco, options?)`

Registers the Dotprompt language with Monaco Editor.

| Parameter | Type | Description |
|-----------|------|-------------|
| `monaco` | `typeof monaco` | Monaco Editor instance |
| `options.completions` | `boolean` | Enable completion provider (default: `true`) |
| `options.hover` | `boolean` | Enable hover provider (default: `true`) |
| `options.themes` | `Record<string, IStandaloneThemeData>` | Custom themes to register |

Returns: `IDisposable` to unregister the language

### `createDotpromptTheme(base?, name?)`

Creates a theme with Dotprompt token color rules.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base` | `'vs' \| 'vs-dark' \| 'hc-black'` | `'vs-dark'` | Base theme |
| `name` | `string` | `'dotprompt-dark'` | Theme name |

### `dotpromptThemeRules`

Array of token theme rules for Dotprompt syntax. Can be merged into existing themes.

### `LANGUAGE_ID`

The language ID: `'dotprompt'`

### `monarchLanguage`

The Monarch tokenizer definition. Use for custom language registration.

### `languageConfiguration`

Language configuration (brackets, comments, folding). Use for custom registration.

## Completions

The completion provider offers:

| Context | Completions |
|---------|-------------|
| `{{` | Handlebars helpers, Dotprompt helpers |
| `{{#` | Block helpers (if, each, role, section) |
| `{{>` | Partial template reference |
| `model:` | Model names (Gemini, GPT, Claude) |
| Frontmatter | Field names (model, config, input, output) |

## Theming

Token types available for theming:

| Token | Description |
|-------|-------------|
| `delimiter.frontmatter` | `---` delimiters |
| `delimiter.handlebars` | `{{` and `}}` |
| `delimiter.handlebars.block` | `{{#` and `{{/` |
| `keyword.handlebars` | if, each, with, etc. |
| `keyword.dotprompt` | role, json, history, etc. |
| `keyword.yaml` | YAML frontmatter keys |
| `keyword.marker` | `<<<dotprompt:...>>>` |
| `variable` | Template variables |
| `variable.partial` | Partial names |
| `variable.special` | @index, @first, etc. |
| `comment.block` | `{{! comment }}` |
| `comment.yaml` | `# YAML comment` |

## License

Apache-2.0
