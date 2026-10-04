# Changelog

All notable changes to dotprompt-dart will be documented in this file.

## [0.0.2](https://github.com/google/dotprompt/compare/dotprompt-dart-0.0.1...dotprompt-dart-0.0.2) (2026-10-04)


### Features

* **dart:** add pub.dev publishing support ([#527](https://github.com/google/dotprompt/issues/527)) ([d70752b](https://github.com/google/dotprompt/commit/d70752b9dfbb86063f0b5cf0e4158d8cdd14bba7))
* **dart:** dotprompt and handlebars implementation ([#509](https://github.com/google/dotprompt/issues/509)) ([3b2982c](https://github.com/google/dotprompt/commit/3b2982c6f8dfaee84ca120da93a50bc92940ee69))
* **dart:** support additionalMetadata in renderMetadata ([#596](https://github.com/google/dotprompt/issues/596)) ([c43729a](https://github.com/google/dotprompt/commit/c43729a118c8b23ae78d7fa548d1708f7cd07c8b))
* **rules_dart,rules_flutter:** enhance Bazel rules with workers and linting fixes ([#513](https://github.com/google/dotprompt/issues/513)) ([5369b40](https://github.com/google/dotprompt/commit/5369b4046eea9805f7dbcf026434035d55e2b095))
* **rules_dart:** first-class Bazel ruleset with RBE, IDE aspects, and version conflict detection ([#512](https://github.com/google/dotprompt/issues/512)) ([1624c75](https://github.com/google/dotprompt/commit/1624c7546deac1969a836dc83d2c3531a8e66ef0))


### Bug Fixes

* add Apache-2.0 license metadata to all packages ([#528](https://github.com/google/dotprompt/issues/528)) ([c76c663](https://github.com/google/dotprompt/commit/c76c6639fb77b39ef5b45a1a8dbebacc4c9bd422))
* **bazel:** remove stale dart_deps repository imports from dart.MODULE.bazel ([#595](https://github.com/google/dotprompt/issues/595)) ([64acecd](https://github.com/google/dotprompt/commit/64acecd48c54d1c66aecdad00f964281c929f3fa))
* **dart:** parse Picoschema parenthetical types per spec ([#627](https://github.com/google/dotprompt/issues/627)) ([4eb29ee](https://github.com/google/dotprompt/commit/4eb29eead28d1ea6d1bdc63e562e0887b6d3dd01))

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
