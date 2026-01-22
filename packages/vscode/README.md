# Dotprompt VS Code Extension

This extension provides syntax highlighting and language support for **Dotprompt** (`.prompt`) files in Visual Studio Code.

## Features

- **Syntax Highlighting**:
    - YAML Frontmatter
    - Dotprompt Markers (e.g., `<<<dotprompt:role:user>>>`)
    - Handlebars syntax (`{{...}}`)
- **Snippets** (Planned)
- **Validation** (Planned)

## Installation

## Installation & Testing

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
    - Run `code --install-extension dotprompt-vscode-0.0.1.vsix`
    - OR open VS Code, go to Extensions (`Cmd+Shift+X`), click `...` > `Install from VSIX...`, and select the generated file.

### Local Development
You can also open this folder in VS Code and press `F5` to launch a localized Extension Development Host with the extension loaded for debugging.

## Syntax Support

- **Frontmatter**: The extension detects YAML frontmatter enclosed in `---` at the beginning of the file.
- **Markers**: Special Dotprompt markers like `<<<dotprompt:role:system>>>` are highlighted.
- **Handlebars**: Standard Handlebars syntax is supported for dynamic prompt generation.

## Contributing

This extension is part of the [Dotprompt repository](https://github.com/google/dotprompt).
