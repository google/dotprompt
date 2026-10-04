# Changelog

All notable changes to dotprompt-dart will be documented in this file.

## [Unreleased]

Picoschema now follows the spec and behaves like the other runtimes. Schemas
that relied on the old Dart-only syntax, or on unknown names becoming `$ref`,
need updating.

### Breaking changes

- Picoschema is strict. These now throw `PicoschemaException`:

  | Before (1.x)                       | Now                                   |
  | ---------------------------------- | ------------------------------------- |
  | `email(the email): string`         | `email: string, the email`            |
  | `tags: string[]`                   | `tags(array): string`                 |
  | `status: a \| b`                   | `status(enum): [a, b]`                |
  | `wild(*): string`                  | `(*): string`                         |
  | `n: int` (also `str`, `bool`, ...) | `n: integer`                          |
  | `a` and `a?` in the same object    | pick one                              |

- Unknown named schemas throw instead of becoming `{"$ref": name}`. Names are
  looked up in `schemas`/`defineSchema`, then `DotpromptOptions.schemaResolver`
  (`Dotprompt` and `Picoschema.parse` only; `toJsonSchema` is sync and only
  sees `schemas`). Register schemas before converting prompts that use them.
- The `input: Name` / `output: Name` shorthand is parsed as
  `{"$type": Name}` (same as `schema: Name`) instead of `{"$ref": Name}`, so
  `renderMetadata` resolves it.
- `Picoschema.toJsonSchema`'s `schemas` parameter is now
  `Map<String, Map<String, dynamic>>?` (was `Map<String, dynamic>?`).
- `Picoschema.isPicoschema` returns true for anything that is not JSON Schema
  (it used to require a bare scalar value). JSON Schema is detected as in the
  other runtimes: a top-level `type` naming a JSON Schema type or a
  `properties` map, plus list-valued `type`/`anyOf`/`oneOf`/`allOf`/`enum`,
  `$schema` and `$ref`. Calling it before `toJsonSchema` is no longer needed.
- `DotpromptOptions.schemas` and `defineSchema` take JSON Schema (as in the
  other runtimes), not Picoschema. Registered schemas are inserted as-is;
  convert Picoschema with `Picoschema.toJsonSchema` first.

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
  - Passed-through JSON Schema and resolved named schemas are deep copies, so
    editing the result never changes the input or registered schemas.
  - A frontmatter schema with a `$type` field next to other fields is parsed
    as a Picoschema object instead of being collapsed to the `$type` value.
  - `x?: null` produces `{type: null}` instead of `{type: [null, null]}`.
  - `a ?: string` produces a property named `a`, not `a `.
  - Named schemas are resolved via `DotpromptOptions.schemaResolver` as well as
    `schemas`/`defineSchema`.
  - The `input: Name` / `output: Name` shorthand resolves the named schema.
    Previously it became a raw `{"$ref": name}`.
- The spec test runner now checks `output` and named `schemas`, so
  `spec/picoschema.yaml` is actually enforced.

### Added

- `Picoschema.parse(schema, {schemas, schemaResolver})`, an async variant of
  `toJsonSchema` that resolves named schemas through a `SchemaResolver`.

## [1.0.0] - 2026-08-25

### Added

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
