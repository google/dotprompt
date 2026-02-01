# Dotprompt Feature Parity

This document tracks Dotprompt implementation status across all language runtimes.
Dotprompt is an executable prompt template file format for Generative AI.

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully implemented and tested |
| 🔶 | Partially implemented |
| ❌ | Not implemented |
| N/A | Not applicable |

## Runtime Overview

| Runtime | Package Name | Status | Build System |
|---------|--------------|--------|--------------|
| JavaScript | `dotprompt` | Reference impl | pnpm |
| Dart | `dotprompt` | Production | Bazel |
| Python | `dotpromptz` | Production | uv + Bazel |
| Go | `dotprompt-go` | Development | Go modules + Bazel |
| Rust | `dotprompt-rs` | Development | Cargo + Bazel |
| Java | `dotprompt-java` | Development | Bazel |

## Core Parsing

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| **Frontmatter Parsing** | | | | | | |
| YAML frontmatter extraction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Model specification | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Config (temperature, etc.) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Input schema | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Output schema | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Template Body** | | | | | | |
| Handlebars template parsing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-message format | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| Role markers (`{{role}}`) | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |

## Schema Features

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| **Picoschema** | | | | | | |
| Basic type definitions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nested objects | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Arrays | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Required fields | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Optional fields `?` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Descriptions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enums | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **JSON Schema Conversion** | | | | | | |
| Picoschema → JSON Schema | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| JSON Schema → Picoschema | 🔶 | 🔶 | 🔶 | ❌ | ❌ | ❌ |

## Dotprompt Helpers

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| **Role Helpers** | | | | | | |
| `{{role "user"}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `{{role "model"}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `{{role "system"}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **Media Helpers** | | | | | | |
| `{{media url=...}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `{{media url=... mime=...}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| Base64 data URLs | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **History Helper** | | | | | | |
| `{{history}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **Section Helper** | | | | | | |
| `{{section "name"}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **JSON Helper** | | | | | | |
| `{{json value}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `{{json value indent=2}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |

## Template Resolution

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| **Partial Resolution** | | | | | | |
| Named partials | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Recursive partials | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| **Template Loading** | | | | | | |
| File system loader | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Custom loaders | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| Directory watching | ✅ | 🔶 | 🔶 | ❌ | ❌ | ❌ |

## Output Handling

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| **Message Generation** | | | | | | |
| Single message output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-message output | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **Structured Output** | | | | | | |
| JSON mode | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| Schema validation | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |

## Integration Features

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| **Genkit Integration** | | | | | | |
| Action registration | ✅ | N/A | ✅ | ❌ | ❌ | ❌ |
| Prompt store | ✅ | N/A | ✅ | ❌ | ❌ | ❌ |
| **Tooling** | | | | | | |
| CLI (`promptly`) | N/A | N/A | N/A | N/A | ✅ | N/A |
| LSP support | N/A | N/A | N/A | N/A | ✅ | N/A |
| IDE extensions | ✅ | N/A | N/A | N/A | ✅ | ✅ |

## Error Handling

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| Syntax error location | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| Missing variable errors | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| Schema validation errors | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| Helpful error messages | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |

## Configuration

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|----|---------|----|------|------|------|
| **Model Config** | | | | | | |
| `model` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `temperature` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `maxOutputTokens` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `topP` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `topK` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `stopSequences` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **Advanced Config** | | | | | | |
| Tools/functions | ✅ | 🔶 | ✅ | 🔶 | 🔶 | 🔶 |
| Safety settings | ✅ | 🔶 | ✅ | 🔶 | 🔶 | 🔶 |
| Custom metadata | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |

## Specification Compliance

| Test Suite | JS | Dart | Python | Go | Rust | Java |
|------------|----|---------|----|------|------|------|
| `spec/helpers/` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| `spec/metadata.yaml` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `spec/partials.yaml` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| `spec/picoschema.yaml` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `spec/variables.yaml` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |

## Test Coverage

| Runtime | Unit Tests | Integration | Spec Tests |
|---------|------------|-------------|------------|
| JavaScript | ✅ | ✅ | Reference |
| Dart | ✅ (84+) | ✅ | ✅ |
| Python | ✅ | ✅ | 🔶 |
| Go | 🔶 | 🔶 | 🔶 |
| Rust | 🔶 | 🔶 | 🔶 |
| Java | 🔶 | 🔶 | 🔶 |

## Build & CI

| Runtime | CI Workflow | Format | Lint | Type Check |
|---------|-------------|--------|------|------------|
| JavaScript | `js.yml` | Biome | Biome | tsc |
| Dart | `dart.yml` | dart format | dart analyze | Built-in |
| Python | `python.yml` | Ruff | Ruff | ty + pyrefly |
| Go | `go.yml` | gofmt | golangci-lint | Built-in |
| Rust | `rust.yml` | cargo fmt | Clippy | Built-in |
| Java | `java.yml` | google-java-format | Built-in | Built-in |

---

## Implementation Notes

### JavaScript (Reference Implementation)

The JavaScript/TypeScript implementation is the canonical reference. All other
implementations should maintain behavioral parity with it.

### Dart Implementation

- Uses `handlebarrz` for Handlebars templating
- ANTLR4 parser integrated with 100% structural parity
- Bazel-built for hermetic builds
- Full Picoschema support

### Python Implementation

- Uses `dotpromptz-handlebars` Rust bindings for templating
- Fully typed with ty and pyrefly type checkers
- Integrates with Genkit Python SDK

### Rust Implementation (Promptly CLI)

- Provides `promptly` CLI tool for working with .prompt files
- Includes LSP server for IDE support
- Powers editor extensions

---

## Roadmap

### Q1 2026

- [ ] Complete Go implementation core features
- [ ] Complete Rust implementation core features
- [ ] Python specification test coverage

### Q2 2026

- [ ] Java production readiness
- [ ] Cross-language specification test framework
- [ ] Performance benchmarking suite

---

*Last updated: 2026-01-31*
