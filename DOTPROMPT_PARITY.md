# Dotprompt Feature Parity

This document tracks Dotprompt implementation status across all language runtimes.
Dotprompt is an executable prompt template file format for Generative AI.

> **Last audited: 2026-02-19.** Status verified by running all spec tests and
> inspecting source code in each language runtime.

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
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| **Frontmatter Parsing** | | | | | | |
| YAML frontmatter extraction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Model specification | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Config (temperature, etc.) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Input schema | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Output schema | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Template Body** | | | | | | |
| Handlebars template parsing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-message format | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Role markers (`{{role}}`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Schema Features

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| **Picoschema** | | | | | | |
| Basic type definitions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nested objects | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Arrays | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Required fields | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Optional fields `?` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Descriptions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Enums | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **JSON Schema Conversion** | | | | | | |
| Picoschema to JSON Schema | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| JSON Schema to Picoschema | 🔶 | 🔶 | ✅ | ❌ | ❌ | ❌ |

## Dotprompt Helpers

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| **Role Helpers** | | | | | | |
| `{{role "user"}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{role "model"}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{role "system"}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Media Helpers** | | | | | | |
| `{{media url=...}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{media url=... mime=...}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Base64 data URLs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **History Helper** | | | | | | |
| `{{history}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Section Helper** | | | | | | |
| `{{section "name"}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **JSON Helper** | | | | | | |
| `{{json value}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{json value indent=2}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Template Resolution

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| **Partial Resolution** | | | | | | |
| Named partials | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Recursive partials + cycle detection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Template Loading** | | | | | | |
| File system loader (PromptStore) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Custom loaders / resolvers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Directory watching | ✅ | 🔶 | 🔶 | ❌ | ❌ | ❌ |

## Output Handling

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| **Message Generation** | | | | | | |
| Single message output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Multi-message output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Structured Output** | | | | | | |
| JSON mode (`output.format: json`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Output schema validation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Integration Features

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| **Genkit Integration** | | | | | | |
| Action registration | ✅ | N/A | ✅ | ❌ | ❌ | ❌ |
| Prompt store | ✅ | N/A | ✅ | ❌ | ❌ | ❌ |
| **Tooling** | | | | | | |
| CLI (`promptly`) | N/A | N/A | N/A | N/A | ✅ | N/A |
| LSP support | N/A | N/A | N/A | N/A | ✅ | N/A |
| IDE extensions | ✅ | N/A | N/A | N/A | ✅ | ✅ |

## Error Handling

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| Syntax error location | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Missing variable errors | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Schema validation errors | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Helpful error messages | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Configuration

| Feature | JS | Dart | Python | Go | Rust | Java |
|---------|:--:|:----:|:------:|:--:|:----:|:----:|
| **Model Config** | | | | | | |
| `model` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `temperature` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `maxOutputTokens` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `topP` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `topK` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `stopSequences` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Advanced Config** | | | | | | |
| Tools/functions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Safety settings | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Custom metadata | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Specification Compliance

All runtimes pass the full spec test suite.

| Test Suite | JS | Dart | Python | Go | Rust | Java |
|------------|:--:|:----:|:------:|:--:|:----:|:----:|
| `spec/helpers/` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `spec/metadata.yaml` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `spec/partials.yaml` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `spec/picoschema.yaml` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `spec/variables.yaml` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `spec/whitespace.yaml` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `spec/unicode.yaml` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Test Coverage

| Runtime | Unit Tests | Integration | Spec Tests | Total |
|---------|:----------:|:-----------:|:----------:|:-----:|
| JavaScript | ✅ | ✅ | Reference | -- |
| Dart | ✅ (84+) | ✅ | ✅ | 84+ |
| Python | ✅ (398+) | ✅ | ✅ (81) | 479 |
| Go | ✅ | ✅ | ✅ (200) | 200+ |
| Rust | ✅ (43) | ✅ | ✅ (117) | 160+ |
| Java | ✅ | ✅ | ✅ | 27+ |

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
- Output schema validation via `jsonschema` (Draft 2020-12)
- JSON Schema to Picoschema reverse conversion
- Recursive partials with cycle detection
- 479 tests (81 spec tests, 398 unit/integration tests), 88% coverage

### Go Implementation

- Uses `raymond` for Handlebars templating
- Full Picoschema support including enums
- Recursive partials with cycle detection
- ToolDefinition/ToolResolver for tool support
- 200+ spec tests passing

### Rust Implementation (Promptly CLI)

- Uses `handlebars` crate for Handlebars templating
- Provides `promptly` CLI tool for working with .prompt files
- Includes LSP server for IDE support
- Powers editor extensions
- 43 unit tests + 117 spec tests passing

### Java Implementation

- Uses `com.github.jknack:handlebars` for Handlebars templating
- Full Picoschema support including enums
- Recursive partials with cycle detection (async)
- ToolDefinition/ToolResolver for tool support
- 27+ tests passing

### Configuration Passthrough

All config fields (`stopSequences`, safety settings, custom metadata, etc.)
are stored in a generic map type in every language (`Record<string, any>` in
JS, `map[string]any` in Go, `Map<String, Object>` in Java,
`Map<String, dynamic>` in Dart, generic `M` in Rust). Frontmatter config is
parsed and passed through without language-specific handling. This means any
model config key works in any language without explicit support.

### Tools and Functions

All languages define `tools` (list of tool names) and `toolDefs` (inline tool
definitions) fields in their `PromptMetadata` types. Go, Rust, and Java also
provide `ToolResolver` interfaces for dynamic tool lookup.

### Schema Validation

Output schema validation is a Genkit integration concern, not a core dotprompt
library feature. The JS reference implementation does not validate output
against schemas in the dotprompt library itself. Python provides a standalone
`validate_output()` utility. All languages parse and expose the output schema
for downstream consumers (Genkit SDKs) to validate against.

---

## Remaining Gaps

| Feature | Languages | Notes |
|---------|-----------|-------|
| JSON Schema to Picoschema | Go, Rust, Java | Reverse conversion utility (Python has it) |
| Directory watching | Go, Rust, Java | Planned future feature |
| Genkit integration | Go, Rust, Java | Standalone libraries, not Genkit-integrated |

---

*Last updated: 2026-02-19*
