# Dotprompt VS Code Extension

This extension provides syntax highlighting, diagnostics, formatting, and language support for **Dotprompt** (`.prompt`) files in Visual Studio Code.

## Features

- **Syntax Highlighting**:
    - YAML Frontmatter
    - Role markers (e.g., `{{role "user"}}`)
    - Handlebars syntax (`{{...}}`)
- **Autocomplete**: Context-aware completion for Handlebars and Dotprompt helpers
- **Diagnostics** (requires `promptly`): Real-time error detection for YAML and Handlebars syntax
- **Formatting** (requires `promptly`): Automatic formatting of `.prompt` files
- **Hover Documentation** (requires `promptly`): Documentation on hover for helpers and frontmatter fields

## Installation

### Quick Start (One-Liner)
Run the following script from the repository root:
```bash
./scripts/install_vscode_ext
```

### Manual Installation
1.  **Install Dependencies**:
    ```bash
    pnpm install
    ```
2.  **Build**:
    ```bash
    pnpm run build
    ```
3.  **Package**:
    ```bash
    pnpm run package
    ```
4.  **Install in VS Code**:
    - Run `code --install-extension dotprompt-vscode-0.0.2.vsix`
    - OR open VS Code, go to Extensions (`Cmd+Shift+X`), click `...` > `Install from VSIX...`, and select the generated file.

### Installing Promptly (Optional but Recommended)

For full LSP features (diagnostics, formatting, hover), install the `promptly` CLI:

```bash
# From source (requires Rust)
cargo install --path rs/promptly

# Or build from the repository
cargo build --release -p promptly
# Then add target/release to your PATH
```

## Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `dotprompt.promptlyPath` | string | `""` | Path to the `promptly` binary. If not set, searches PATH and common locations. |
| `dotprompt.enableLsp` | boolean | `true` | Enable LSP features. Requires `promptly` to be installed. |

## LSP Features

When `promptly` is installed, the extension provides:

### Diagnostics
Real-time detection of:
- **E001**: Invalid YAML frontmatter
- **E002**: Invalid Handlebars syntax (unclosed blocks, unbalanced braces)
- **I001**: Partial reference information

### Formatting
Automatic formatting that:
- Normalizes Handlebars spacing (`{{name}}` → `{{ name }}`)
- Trims trailing whitespace
- Ensures files end with a single newline

### Hover
Documentation on hover for:
- **Handlebars helpers**: `if`, `unless`, `each`, `with`, `json`, `role`, `media`, `section`
- **Frontmatter fields**: `model`, `input`, `output`, `config`, `tools`

## Local Development

Open this folder in VS Code and press `F5` to launch an Extension Development Host with the extension loaded for debugging.

## Syntax Support

- **Frontmatter**: The extension detects YAML frontmatter enclosed in `---` at the beginning of the file.
- **Handlebars**: Standard Handlebars syntax is supported for dynamic prompt generation.

## Contributing

This extension is part of the [Dotprompt repository](https://github.com/google/dotprompt).
