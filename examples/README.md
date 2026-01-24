# Example Prompt Files

This directory contains sample `.prompt` files to test the Promptly LSP and linter.

## Valid Examples

| File | Description |
|------|-------------|
| `valid-greeting.prompt` | Basic prompt with variables and conditionals |
| `valid-customer-support.prompt` | Multi-turn conversation with role markers |
| `valid-blog-generator.prompt` | Structured JSON output with schema |
| `valid-comments-and-partials.prompt` | Comments and partial template references |

## Error Examples

Each file demonstrates a specific error that the linter can detect:

| File | Error Code | Description |
|------|------------|-------------|
| `error-invalid-yaml.prompt` | `invalid-yaml` | YAML configuration has a syntax error |
| `error-unclosed-block.prompt` | `unclosed-block` | A `{{#if}}` block was never closed |
| `error-unmatched-closing-block.prompt` | `unmatched-closing-block` | A `{{/if}}` without matching `{{#if}}` |
| `error-unbalanced-brace.prompt` | `unbalanced-brace` | Extra `}}` without matching `{{` |
| `error-multiple-issues.prompt` | Multiple | File with multiple errors for testing |
| `partials/circular-partial-a.prompt` | `circular-partial` | Circular dependency between partials |

## Warning Examples

| File | Warning Code | Description |
|------|--------------|-------------|
| `warning-unused-variable.prompt` | `unused-variable` | Variable in schema but not used in template |
| `warning-undefined-variable.prompt` | `undefined-variable` | Variable used but not defined in schema |

## Hint Examples

| File | Hint Code | Description |
|------|-----------|-------------|
| `partials.prompt` | `unverified-partial` | Uses `{{>partial}}` — verify partial exists |

## Testing with Promptly CLI

```bash
# Check all examples
scripts/promptly check ./examples

# Check a specific file
scripts/promptly check ./examples/error-invalid-yaml.prompt

# Format a file
scripts/promptly fmt ./examples/valid-greeting.prompt

# Get JSON output for IDE integration
scripts/promptly check --format=json ./examples
```

## Testing with VS Code

1. Run the VS Code installer:
   ```bash
   ./scripts/install_vscode_ext
   ```

2. Open VS Code and reload:
   ```
   Cmd+Shift+P → "Developer: Reload Window"
   ```

3. Open any `.prompt` file from this directory

4. You should see:
   - ✅ No squiggles: Valid files with no issues
   - 🔴 Red squiggles: Errors
   - 🟡 Yellow squiggles: Warnings
   - 💡 Blue hints: Info messages

## Error Reference

### Errors (🔴)

| Code | Message Pattern |
|------|-----------------|
| `invalid-yaml` | "The YAML configuration at the top of this file has a syntax error" |
| `unclosed-block` | "Block '{{#X}}' was never closed" |
| `unmatched-closing-block` | "Found '{{/X}}' but no matching '{{#X}}' was opened" |
| `unbalanced-brace` | "Found a closing '}}' without a matching opening '{{'" |
| `circular-partial` | "Circular dependency detected: A → B → A" |

### Warnings (🟡)

| Code | Message Pattern |
|------|-----------------|
| `unused-variable` | "Variable 'X' is defined in schema but never used in template" |
| `undefined-variable` | "Variable 'X' is used in template but not defined in schema" |

### Hints (💡)

| Code | Message Pattern |
|------|-----------------|
| `unverified-partial` | "Uses partial template 'X' — ensure this partial exists" |
