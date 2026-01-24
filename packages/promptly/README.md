# @dotprompt/promptly

Promptly: Cargo for prompts - lint, format, and validate `.prompt` files.

## Installation

```bash
# Using npm
npm install -g @dotprompt/promptly

# Using pnpm
pnpm add -g @dotprompt/promptly

# Using yarn
yarn global add @dotprompt/promptly

# Or as a dev dependency
npm install -D @dotprompt/promptly
```

## Usage

```bash
# Check .prompt files for errors
promptly check .

# Format .prompt files
promptly fmt .

# Check formatting without modifying files
promptly fmt --check .

# Start LSP server (for editor integration)
promptly lsp

# Generate shell completions
promptly completions generate bash
promptly completions generate zsh
promptly completions generate fish

# Install shell completions
promptly completions install
```

## Commands

| Command | Description |
|---------|-------------|
| `check` | Check .prompt files for errors and warnings |
| `fmt` | Format .prompt files |
| `lsp` | Start the Language Server Protocol server |
| `completions` | Generate or install shell completions |

## Supported Platforms

| Platform | Architecture |
|----------|--------------|
| macOS | Apple Silicon (arm64) |
| macOS | Intel (x64) |
| Linux | ARM64 |
| Linux | x64 |
| Windows | x64 |

## Editor Integration

The `promptly lsp` command starts a Language Server that provides:
- Real-time diagnostics
- Document formatting
- Hover documentation

See the [VS Code extension](https://marketplace.visualstudio.com/items?itemName=google.dotprompt) for the easiest integration.

## License

Apache-2.0
