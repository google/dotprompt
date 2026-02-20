# Tree-sitter Grammar for Dotprompt

A [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) grammar for Dotprompt (`.prompt`) files.

## Features

- Parses YAML frontmatter
- Parses Handlebars template expressions
- Parses Dotprompt-specific syntax (markers, helpers)
- Supports license header comments

## Installation

### Using npm

```bash
npm install tree-sitter-dotprompt
```

### Building from Source

```bash
cd packages/treesitter
npm install
npm run generate
```

## Usage

### Node.js

```javascript
const Parser = require('tree-sitter');
const Dotprompt = require('tree-sitter-dotprompt');

const parser = new Parser();
parser.setLanguage(Dotprompt);

const source = `---
model: gemini-2.5-flash
---
Hello {{ name }}!`;

const tree = parser.parse(source);
console.log(tree.rootNode.toString());
```

### Neovim (nvim-treesitter)

1. Add the parser configuration:

```lua
local parser_config = require("nvim-treesitter.parsers").get_parser_configs()
parser_config.dotprompt = {
  install_info = {
    url = "https://github.com/google/dotprompt",
    files = { "packages/treesitter/src/parser.c" },
    branch = "main",
    subdirectory = "packages/treesitter",
  },
  filetype = "dotprompt",
}
```

2. Install the parser:

```vim
:TSInstall dotprompt
```

3. Copy highlight queries to your Neovim config:

```bash
mkdir -p ~/.config/nvim/queries/dotprompt
cp packages/treesitter/queries/highlights.scm ~/.config/nvim/queries/dotprompt/
```

### Helix

Add to your `languages.toml`:

```toml
[[language]]
name = "dotprompt"
scope = "source.dotprompt"
file-types = ["prompt"]
roots = []

[[grammar]]
name = "dotprompt"
source = { git = "https://github.com/google/dotprompt", subpath = "packages/treesitter", rev = "main" }
```

### Zed

Add to your `languages.toml`:

```toml
[[grammars]]
name = "dotprompt"
source = { path = "packages/treesitter" }
```

## Development

### Generate Parser

```bash
npm run generate
```

This generates `src/parser.c` from `grammar.js`.

### Test Parser

```bash
npm run test
```

Runs the test corpus in `test/corpus/`.

### Build Native Module

```bash
npm run build
```

## Grammar Structure

```
document
├── license_header?
│   └── header_comment+
├── frontmatter?
│   ├── frontmatter_delimiter (---)
│   ├── yaml_content
│   │   └── yaml_line+
│   └── frontmatter_delimiter (---)
└── template_body
    ├── text
    ├── handlebars_expression ({{ ... }})
    │   ├── expression_content
    │   ├── variable_reference
    │   ├── helper_name
    │   └── partial_reference
    ├── handlebars_block ({{#...}} ... {{/...}})
    │   ├── block_expression
    │   ├── else_expression
    │   └── close_block
    ├── handlebars_comment ({{! ... }})
    └── dotprompt_marker (<<<dotprompt:...>>>)
```

## Queries

### Highlights (`queries/highlights.scm`)

Provides syntax highlighting for:
- YAML frontmatter
- Handlebars expressions and blocks
- Dotprompt-specific helpers
- Comments and markers

## License

Apache-2.0
