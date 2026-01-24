# Tree-sitter Grammar for Dotprompt

A [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) grammar for Dotprompt (`.prompt`) files, providing enhanced syntax highlighting for Neovim and other Tree-sitter compatible editors.

## Features

- **YAML Frontmatter**: Parses frontmatter between `---` delimiters
- **Handlebars Expressions**: Full support for `{{ ... }}` expressions
- **Block Helpers**: `{{#if}}`, `{{#each}}`, `{{#role}}`, etc.
- **Dotprompt Markers**: Special `<<<dotprompt:...>>>` syntax
- **Comments**: Both `{{! ... }}` and `{{!-- ... --}}` styles

## Installation

### For Neovim (nvim-treesitter)

Add this configuration to register the parser:

```lua
local parser_config = require("nvim-treesitter.parsers").get_parser_configs()

parser_config.dotprompt = {
  install_info = {
    url = "https://github.com/google/dotprompt",
    location = "packages/treesitter",
    files = { "src/parser.c" },
    branch = "main",
  },
  filetype = "dotprompt",
}

-- Register the filetype
vim.filetype.add({
  extension = {
    prompt = "dotprompt",
  },
})
```

Then install the parser:

```vim
:TSInstall dotprompt
```

### Manual Installation

```bash
cd packages/treesitter
npm install
npm run generate
npm run build
```

## Highlight Groups

The grammar provides the following highlight groups:

| Group | Description |
|-------|-------------|
| `@keyword.control` | Block helpers (if, each, role) |
| `@function.call` | Helper names |
| `@variable` | Variable references |
| `@variable.builtin` | Special vars (@index, this) |
| `@string` | String literals |
| `@number` | Number literals |
| `@comment` | Handlebars comments |
| `@keyword.directive` | Dotprompt markers |
| `@punctuation.bracket` | `{{` and `}}` |

## Development

```bash
# Generate parser
npm run generate

# Run tests
npm run test

# Build native module
npm run build
```

## Query Files

- `queries/highlights.scm` - Syntax highlighting
- More query files (injections, locals, folds) can be added as needed

## License

Apache-2.0
