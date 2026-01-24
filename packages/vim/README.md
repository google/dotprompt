# Dotprompt Vim Plugin

Provides syntax highlighting and filetype detection for Dotprompt (`.prompt`) files.

## Installation

### Vundle
```vim
Plugin 'google/dotprompt', {'rtp': 'packages/vim'}
```

### Plug
```vim
Plug 'google/dotprompt', {'rtp': 'packages/vim'
```

### lazy.nvim (Neovim)
```lua
{
  "google/dotprompt",
  config = function()
    vim.filetype.add({ extension = { prompt = "dotprompt" } })
  end,
}
```

### Manual
Copy the contents of `syntax/` and `ftdetect/` to your `~/.vim/` directory.

## LSP Support (Neovim)

For diagnostics, formatting, and hover documentation, install `promptly` and configure nvim-lspconfig:

### 1. Install promptly

```bash
cargo install --path rs/promptly
# or
cargo build --release -p promptly
```

### 2. Configure nvim-lspconfig

Add to your Neovim configuration:

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

## LSP Support (Vim with vim-lsp)

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

## Features

With LSP enabled, you get:
- **Diagnostics**: Real-time error detection for YAML and Handlebars syntax
- **Formatting**: Format buffer with `promptly fmt` rules
- **Hover**: Documentation for Handlebars helpers and frontmatter fields
