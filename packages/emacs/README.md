# Dotprompt Emacs Mode

Provides a major mode for editing Dotprompt (`.prompt`) files with syntax highlighting and LSP support.

## Features

- **Syntax Highlighting**: Handlebars helpers, partials, Dotprompt markers
- **LSP Integration**: Diagnostics, formatting, hover via eglot or lsp-mode
- **Format Buffer**: `C-c C-f` or `M-x dotprompt-format-buffer`
- **Format on Save**: Optional automatic formatting

## Installation

### use-package (Recommended)

```elisp
(use-package dotprompt-mode
  :load-path "path/to/dotprompt/packages/emacs"
  :mode "\\.prompt\\'"
  :custom
  (dotprompt-promptly-path "promptly")
  (dotprompt-format-on-save t))
```

### straight.el

```elisp
(straight-use-package
 '(dotprompt-mode :type git
                  :host github
                  :repo "google/dotprompt"
                  :files ("packages/emacs/*.el")))

(use-package dotprompt-mode
  :mode "\\.prompt\\'"
  :custom
  (dotprompt-format-on-save t))
```

### Doom Emacs

Add to `packages.el`:

```elisp
(package! dotprompt-mode
  :recipe (:host github
           :repo "google/dotprompt"
           :files ("packages/emacs/*.el")))
```

Add to `config.el`:

```elisp
(use-package! dotprompt-mode
  :mode "\\.prompt\\'"
  :config
  (setq dotprompt-format-on-save t)
  (add-hook 'dotprompt-mode-hook #'eglot-ensure))
```

### Spacemacs

Add to your `dotspacemacs/user-config`:

```elisp
(use-package dotprompt-mode
  :load-path "path/to/dotprompt/packages/emacs"
  :mode "\\.prompt\\'"
  :init
  (spacemacs/set-leader-keys-for-major-mode 'dotprompt-mode
    "f" 'dotprompt-format-buffer))
```

### Manual

1. Copy `dotprompt-mode.el` to your load path (e.g., `~/.emacs.d/lisp/`)
2. Add to your init file:

```elisp
(add-to-list 'load-path "~/.emacs.d/lisp/")
(require 'dotprompt-mode)
```

## Install promptly for LSP Features

```bash
cargo install --path rs/promptly
# or
cargo build --release -p promptly
```

## LSP Support

### Using Eglot (Emacs 29+, built-in)

Eglot integration is automatic. Enable in your dotprompt buffers:

```elisp
(add-hook 'dotprompt-mode-hook 'eglot-ensure)
```

### Using lsp-mode

lsp-mode integration is also automatic:

```elisp
(add-hook 'dotprompt-mode-hook 'lsp-deferred)
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `dotprompt-promptly-path` | `"promptly"` | Path to the promptly executable |
| `dotprompt-format-on-save` | `nil` | Format buffer before saving |

### Custom promptly path

```elisp
(setq dotprompt-promptly-path "/path/to/promptly")
```

### Enable format on save

```elisp
(setq dotprompt-format-on-save t)
```

## Keybindings

| Key | Command | Description |
|-----|---------|-------------|
| `C-c C-f` | `dotprompt-format-buffer` | Format the current buffer |

## LSP Features

With LSP enabled (eglot or lsp-mode), you get:

| Feature | Description |
|---------|-------------|
| **Diagnostics** | Real-time error detection for YAML and Handlebars syntax |
| **Formatting** | Format with `M-x eglot-format-buffer` or `M-x lsp-format-buffer` |
| **Hover** | Documentation with `M-x eldoc` or mouse hover |
| **Go to Definition** | Jump to partial files with `M-.` |

## Commands

- `dotprompt-format-buffer` - Format the current buffer using LSP or promptly directly
