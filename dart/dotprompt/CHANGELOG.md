# Changelog

All notable changes to dotprompt-dart will be documented in this file.

## [1.1.0] - 2026-10-03

### Fixed

- Picoschema now follows the spec and the JavaScript reference implementation
  ([genkit-dart#562](https://github.com/genkit-ai/genkit-dart/issues/562)):
  - `field(array[, desc]): type`, `field(object[, desc]):` and
    `field(enum[, desc]): [...]` produce arrays, objects and enums. Previously
    the parenthesized qualifier was treated as a description.
  - `(*)` wildcards and every Picoschema form are always converted. Previously
    some schemas skipped conversion and were passed through raw.
  - Top-level JSON Schema (`type: string`, a bare `properties` map, `anyOf`,
    `enum`, `type: [string, "null"]`, etc.) is passed through instead of being
    parsed as Picoschema.
  - Picoschema fields named like JSON Schema keywords (`type: string`,
    `properties:`, `items:`) are converted instead of being mistaken for JSON
    Schema and passed through raw.
  - `x?: null` produces `{type: null}` instead of `{type: [null, null]}`.
  - Named schemas are resolved via `DotpromptOptions.schemaResolver` as well as
    `schemas`/`defineSchema`.
  - The `input: Name` / `output: Name` shorthand resolves the named schema.
    Previously it became a raw `{"$ref": name}`.
- The spec test runner now checks `output` and named `schemas`, so
  `spec/picoschema.yaml` is actually enforced.

### Changed

- Picoschema is strict, like the other runtimes. These now throw
  `PicoschemaException`:
  - free-text parentheses such as `email(the email): string` (use
    `email: string, the email`);
  - parenthetical types other than `array`, `object` and `enum`, e.g.
    `wild(*)`;
  - non-standard types (`string[]`, `a | b`, aliases like `int`/`str`);
  - unknown named schemas. Previously these became `{"$ref": name}`;
  - duplicate property names such as `a` and `a?` in the same object.
- `DotpromptOptions.schemas` and `defineSchema` are documented as taking JSON
  Schema (as in the other runtimes), not Picoschema. Registered schemas are
  inserted as-is; convert Picoschema with `Picoschema.toJsonSchema` first.

### Added

- `Picoschema.parse(schema, {schemas, schemaResolver})`, an async variant of
  `toJsonSchema` that resolves named schemas through a `SchemaResolver`.
- `renderMetadata` and `compile` now accept an optional `additionalMetadata`
  argument that is merged on top of the prompt's parsed frontmatter (scalar
  fields override, `config` map is shallow-merged with additional winning on
  conflict), matching the JavaScript reference implementation.

## [0.0.1] - 2026-01-30

### Added

- Initial release of Dotprompt for Dart
- YAML frontmatter parsing with `Parser` class
- Handlebars-style templating using the pure-Dart `handlebars_dart` library
- Picoschema to JSON Schema conversion
- Core types: `Message`, `Part`, `Role`, `DataArgument`
- Built-in helpers: `role`, `media`, `history`, `json`, `section`, `ifEquals`, `unlessEquals`
- Partial template support with resolver callbacks
- Tool and schema resolution
- Comprehensive error handling with custom exceptions
- Full spec test suite for cross-runtime conformance
