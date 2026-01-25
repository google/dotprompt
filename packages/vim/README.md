# Dotprompt Vim/Neovim Plugin

Provides syntax highlighting, LSP integration, and filetype detection for Dotprompt (`.prompt`) files.

## Features

- **Syntax Highlighting**: YAML frontmatter, Handlebars templates, Dotprompt markers
- **LSP Integration**: Diagnostics, formatting, hover documentation via `promptly`
- **Format on Save**: Automatic formatting when saving (configurable)
- **Keymaps**: Quick access to LSP features

## Installation

### Neovim (lazy.nvim) - Recommended

```lua
{
  "google/dotprompt",
  config = function()
    require("dotprompt").setup({
      -- Optional: custom path to promptly binary
      promptly_path = "",
      -- Enable format on save
      format_on_save = true,
    })
  end,
}
```

### Neovim (Packer)

```lua
use {
  "google/dotprompt",
  config = function()
    require("dotprompt").setup()
  end,
}
```

### Vundle

```vim
Plugin 'google/dotprompt', {'rtp': 'packages/vim'}
```

### vim-plug

```vim
Plug 'google/dotprompt', {'rtp': 'packages/vim'}
```

### Manual

Copy the contents of `syntax/`, `ftdetect/`, and `lua/` to your `~/.vim/` or `~/.config/nvim/` directory.

## Install promptly for LSP Features

```bash
cargo install --path rs/promptly
# or
cargo build --release -p promptly
```

## Configuration

### Using the Lua Module (Recommended)

The Lua module handles everything automatically:

```lua
require("dotprompt").setup({
  -- Path to promptly binary (empty = auto-detect)
  promptly_path = "",
  -- Enable format on save
  format_on_save = true,
  -- Enable diagnostics
  diagnostics = true,
})
```

### Manual LSP Configuration

If you prefer manual setup with nvim-lspconfig:

```lua
local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

-- Register promptly as an LSP server
if not configs.promptly then
  configs.promptly = {
    default_config = {
      cmd = { "promptly", "lsp" },
      filetypes = { "dotprompt" },
      root_dir = lspconfig.util.find_git_ancestor,
    },
  }
end

-- Start the server
lspconfig.promptly.setup({
  on_attach = function(client, bufnr)
    -- Enable formatting
    vim.keymap.set("n", "<leader>f", function()
      vim.lsp.buf.format({ async = true })
    end, { buffer = bufnr })
  end,
})
```

### Vim 8+ with vim-lsp

For Vim 8+ with [vim-lsp](https://github.com/prabirshrestha/vim-lsp):

```vim
if executable('promptly')
  au User lsp_setup call lsp#register_server({
    \ 'name': 'promptly',
    \ 'cmd': {server_info->['promptly', 'lsp']},
    \ 'allowlist': ['dotprompt'],
    \ })
endif
```

## Tree-sitter Support

For enhanced syntax highlighting with Tree-sitter:

### 1. Add the parser to nvim-treesitter

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

### 2. Install the parser

```vim
:TSInstall dotprompt
```

### 3. Enable highlighting

```lua
require("nvim-treesitter.configs").setup({
  highlight = {
    enable = true,
    additional_vim_regex_highlighting = false,
  },
})
```

## Keymaps

When using the Lua module, these keymaps are set automatically:

| Keymap | Action |
|--------|--------|
| `<leader>f` | Format document |
| `K` | Show hover documentation |
| `gd` | Go to definition |
| `gr` | Find references |
| `<leader>rn` | Rename symbol |
| `<leader>ca` | Code action |

## LSP Features

With LSP enabled, you get:

| Feature | Description |
|---------|-------------|
| **Diagnostics** | Real-time error detection for YAML and Handlebars syntax |
| **Formatting** | Format buffer with promptly fmt rules |
| **Hover** | Documentation for Handlebars helpers and frontmatter fields |
| **Go to Definition** | Jump to partial files |
| **References** | Find all uses of partials |

## Commands

```lua
-- Format current document
require("dotprompt").format()

-- Restart LSP server
require("dotprompt").restart()
```
