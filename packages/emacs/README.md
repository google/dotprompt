# Dotprompt Emacs Mode

Provides a major mode for editing Dotprompt (`.prompt`) files.

## Installation

### Manual

1. Copy `dotprompt-mode.el` to your load path (e.g., `~/.emacs.d/lisp/`).
2. Add the following to your init file:

```elisp
(add-to-list 'load-path "~/.emacs.d/lisp/")
(require 'dotprompt-mode)
```

## Features

- Syntax highlighting for:
  - Dotprompt markers (`<<<dotprompt:...>>>`)
  - Handlebars helpers (`if`, `unless`, `each`)
  - Dotprompt custom helpers (`json`, `role`, `history`)
  - Partials (`{{> ... }}`)
- Auto-detection of `.prompt` files.
