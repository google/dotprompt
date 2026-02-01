# Handlebars Feature Parity

This document tracks Handlebars template engine implementation status across all
language runtimes in the Dotprompt project.

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully implemented and tested |
| 🔶 | Partially implemented |
| ❌ | Not implemented |
| N/A | Not applicable |

## Runtime Overview

| Runtime | Package Name | Parser Type | Test Coverage |
|---------|--------------|-------------|---------------|
| Dart | `handlebarrz` | Hand-written + ANTLR4 | 84 tests |
| JavaScript | Native Handlebars | ANTLR4 | Reference impl |
| Python | `dotpromptz-handlebars` | Rust bindings | TBD |
| Go | `dotprompt-go` | Hand-written | TBD |
| Rust | `dotprompt-rs` | Hand-written | TBD |
| Java | `dotprompt-java` | Hand-written | TBD |

## Core Features

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| **Basic Expressions** | | | | | | |
| Variable substitution `{{var}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dot-path access `{{a.b.c}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bracket notation `{{a.[b]}}` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| This context `{{.}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Parent context `{{../var}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HTML escaping (default) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Unescaped Output** | | | | | | |
| Triple braces `{{{var}}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Ampersand `{{&var}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **Comments** | | | | | | |
| Short comment `{{! text }}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Long comment `{{!-- text --}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Literals** | | | | | | |
| String literals | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Number literals | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Boolean literals | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Negative numbers | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |

## Block Helpers

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| **Built-in Helpers** | | | | | | |
| `{{#if}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{#unless}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{#each}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{#with}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{else}}` clause | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Inverse block `{{^if}}` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| **Block Parameters** | | | | | | |
| `as \|item\|` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| `as \|item index\|` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| **Custom Block Helpers** | | | | | | |
| Register block helper | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `options.fn(context)` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `options.inverse(context)` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Helper Functions

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| **Built-in Helpers** | | | | | | |
| `{{lookup obj key}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `{{log value}}` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| **Custom Helpers** | | | | | | |
| Simple helper `(args) -> result` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Hash arguments `key=value` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SafeString return | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Subexpressions** | | | | | | |
| `{{outer (inner arg)}}` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| Nested subexpressions | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |

## Partials

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| **Basic Partials** | | | | | | |
| Named partial `{{> name}}` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Partial with context | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Partial with hash | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| **Partial Blocks** | | | | | | |
| `{{#> partial}}default{{/partial}}` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| **Inline Partials** | | | | | | |
| `{{#*inline "name"}}...{{/inline}}` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Dynamic partial name | 🔶 | ✅ | ❌ | ❌ | ❌ | ❌ |

## Data Variables

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| `@root` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `@index` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `@first` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `@last` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `@key` | ✅ | ✅ | ✅ | 🔶 | 🔶 | 🔶 |
| `@root.path.to.value` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |

## Whitespace Control

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| `{{~var}}` strip left | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| `{{var~}}` strip right | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| `{{~var~}}` strip both | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| Block-level whitespace control | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |

## Raw Blocks

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| `{{{{raw}}}}...{{{{/raw}}}}` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

## Escape Sequences

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| `\{{` outputs literal `{{` | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| `\\{{` outputs `\` + variable | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

## Strict Mode

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| Throw on undefined variable | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |
| Exception includes path info | ✅ | ✅ | 🔶 | 🔶 | 🔶 | 🔶 |

## Advanced Features

| Feature | Dart | JS | Python | Go | Rust | Java |
|---------|------|----|---------|----|------|------|
| **String Params Mode** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Track IDs** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Decorators** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

## Parser Implementation

| Aspect | Dart | JS | Python | Go | Rust | Java |
|--------|------|----|---------|----|------|------|
| Parser type | Hand-written + ANTLR4 | ANTLR4 | Rust bindings | Hand-written | Hand-written | Hand-written |
| ANTLR4 parity tests | 38/38 ✅ | N/A | N/A | TBD | TBD | TBD |
| Grammar source | `spec/handlebars/antlr/` | Official | N/A | N/A | N/A | N/A |

## Test Coverage by Runtime

| Runtime | Unit Tests | Integration Tests | Spec Tests |
|---------|------------|-------------------|------------|
| Dart | 84 passing | ✅ | 38 parity tests |
| JavaScript | Reference | ✅ | Reference |
| Python | TBD | TBD | TBD |
| Go | TBD | TBD | TBD |
| Rust | TBD | TBD | TBD |
| Java | TBD | TBD | TBD |

---

## Notes

### Dart Implementation

The Dart `handlebarrz` library provides a complete Handlebars implementation with:

- **Dual parser architecture**: Hand-written parser for speed, ANTLR4 parser for
  spec compliance verification
- **100% parity**: 38/38 ANTLR parity tests confirm structural equivalence
- **Full feature set**: All core Handlebars features including raw blocks, inline
  partials, and strict mode

### JavaScript Implementation

JavaScript uses the canonical Handlebars.js library as the reference implementation.

### Python Implementation

Python uses Rust bindings via `dotpromptz-handlebars` for Handlebars functionality,
leveraging the `handlebars-rust` crate.

---

*Last updated: 2026-01-31*
