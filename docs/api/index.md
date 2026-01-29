# API Reference

Dotprompt provides implementations in multiple languages. Each implementation
follows the same specification and provides equivalent functionality.

## Language Implementations

| Language | Package | Status | Documentation |
|----------|---------|--------|---------------|
| [Python](python/dotpromptz.md) | `dotpromptz` | Stable | This site |
| [TypeScript/JavaScript](typescript/index.md) | `dotprompt` | Stable | This site |
| [Go](go/index.md) | `github.com/google/dotprompt/go/dotprompt` | Stable | This site |
| [Rust](rust/index.md) | `dotprompt` | Stable | This site |
| [Java](java/index.md) | `com.google.dotprompt` | Stable | This site |

## Quick Links

### Python

* [dotpromptz](python/dotpromptz.md) - Core Python library
* [handlebarrz](python/handlebarrz.md) - Handlebars templating engine

### TypeScript/JavaScript

* [dotprompt](typescript/index.md) - Core TypeScript library

### Go

* [dotprompt](go/index.md) - Core Go package

### Rust

* [dotprompt](rust/index.md) - Core Rust crate

### Java

* [com.google.dotprompt](java/index.md) - Core Java package

## Cross-Language Compatibility

All implementations are tested against the same specification files in the
`spec/` directory. This ensures consistent behavior across languages for:

* Template parsing and rendering
* Picoschema to JSON Schema conversion
* Helper functions (role, media, history, etc.)
* Partial template resolution
* Message history handling
