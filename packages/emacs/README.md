# Dotprompt Emacs Mode

Provides a major mode for editing Dotprompt (`.prompt`) files with syntax highlighting and LSP support.

## Installation

### Manual

1. Copy `dotprompt-mode.el` to your load path (e.g., `~/.emacs.d/lisp/`).
2. Add the following to your init file:

```elisp
(add-to-list 'load-path "~/.emacs.d/lisp/")
(require 'dotprompt-mode)
```

### use-package

```elisp
(use-package dotprompt-mode
  :load-path "path/to/dotprompt/packages/emacs"
  :mode "\\.prompt\\'")
```

## Features

- **Syntax highlighting** for:
  - Dotprompt markers (`<<<dotprompt:...>>>`)
  - Handlebars helpers (`if`, `unless`, `each`)
  - Dotprompt custom helpers (`json`, `role`, `history`)
  - Partials (`{{> ... }}`)
- **Auto-detection** of `.prompt` files
- **LSP integration** via eglot or lsp-mode

## LSP Support

For diagnostics, formatting, and hover documentation, install `promptly`:

```bash
cargo install --path rs/promptly
# or
cargo build --release -p promptly
```

### Using Eglot (Emacs 29+, built-in)

Eglot integration is automatic. Just enable eglot in your dotprompt buffers:

```elisp
(add-hook 'dotprompt-mode-hook 'eglot-ensure)
```

If `promptly` is not in your PATH, customize the path:

```elisp
(setq dotprompt-promptly-path "/path/to/promptly")
```

### Using lsp-mode

lsp-mode integration is also automatic:

```elisp
(add-hook 'dotprompt-mode-hook 'lsp-deferred)
```

### LSP Features

With LSP enabled, you get:
- **Diagnostics**: Real-time error detection for YAML and Handlebars syntax
- **Formatting**: Format buffer with `M-x lsp-format-buffer` or `M-x eglot-format-buffer`
- **Hover**: Documentation for Handlebars helpers and frontmatter fields (`M-x eldoc` or hover)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `dotprompt-promptly-path` | `"promptly"` | Path to the promptly executable |
