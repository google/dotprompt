# Promptly

> Cargo for prompts: lint, format, test, and publish `.prompt` files

Promptly is a comprehensive Rust-based CLI toolchain for `.prompt` files. It provides
everything developers need to write, test, evaluate, package, and share prompts.

## Quick Start

```bash
# Lint prompts
promptly check prompts/

# Format prompts
promptly fmt

# Run a prompt
promptly run greeting.prompt -i '{"name": "Alice"}'
```

## Features

- **Fast**: Written in Rust for sub-second response times
- **Comprehensive**: Lint, format, test, and publish
- **Developer-friendly**: Rust-style error messages with context and suggestions
- **Editor-agnostic**: LSP support for all major editors

## License

Apache-2.0
