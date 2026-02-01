# Changelog

All notable changes to dotprompt-dart will be documented in this file.

## [0.0.1] - 2026-01-30

### Added

- Initial release of Dotprompt for Dart
- YAML frontmatter parsing with `Parser` class
- Handlebars-style templating using `mustache_template`
- Picoschema to JSON Schema conversion
- Core types: `Message`, `Part`, `Role`, `DataArgument`
- Built-in helpers: `role`, `media`, `history`, `json`, `section`, `ifEquals`, `unlessEquals`
- Partial template support with resolver callbacks
- Tool and schema resolution
- Comprehensive error handling with custom exceptions
- Full spec test suite for cross-runtime conformance
