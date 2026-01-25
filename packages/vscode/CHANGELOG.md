# Changelog

All notable changes to the Dotprompt VS Code extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-24

### Added
- **Status Bar Indicator**: Shows LSP connection status (connected, starting, error)
- **Format on Save**: Automatically format `.prompt` files when saving (configurable)
- **Commands**:
  - `Dotprompt: Format Document` - Format the current file
  - `Dotprompt: Restart Language Server` - Restart the LSP connection
  - `Dotprompt: Show Output` - View LSP logs
- **Improved Error Handling**: Better messages when promptly is not found with actions

### Changed
- Status bar now shows real-time LSP state
- Error messages offer actionable options (Open Settings, Retry, Show Output)

### Configuration
- `dotprompt.formatOnSave`: Enable/disable format on save (default: true)
- `dotprompt.trace.server`: Configure LSP message tracing

## [0.1.0] - 2026-01-24

### Added
- **Syntax Highlighting**: Full TextMate grammar for Dotprompt files
  - YAML frontmatter highlighting
  - Handlebars expression highlighting
  - Dotprompt-specific markers (`<<<dotprompt:...>>>`)
- **LSP Integration**: Connect to `promptly lsp` for advanced features
  - Real-time diagnostics (errors and warnings)
  - Document formatting
  - Hover documentation for helpers and frontmatter fields
- **Code Snippets**: 25+ snippets for common patterns
  - Role blocks (`role`, `system`, `user`, `model`)
  - Conditionals (`if`, `unless`, `ifEquals`)
  - Loops (`each`, `with`)
  - Helpers (`json`, `media`, `history`, `section`)
  - Partials and comments
  - Complete prompt templates
- **Configuration Options**
  - `dotprompt.promptlyPath`: Custom path to promptly binary
  - `dotprompt.enableLsp`: Toggle LSP features

### Installation

Install the `promptly` CLI for LSP features:
```bash
cargo install --path rs/promptly
# or
cargo build --release -p promptly
```

## [0.0.2] - 2026-01-22

### Added
- Initial LSP client implementation
- Basic syntax highlighting

## [0.0.1] - 2026-01-22

### Added
- Initial release with syntax highlighting
