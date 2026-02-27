# Changelog

All notable changes to dotprompt-dart will be documented in this file.

## [0.0.2](https://github.com/google/dotprompt/compare/dotprompt-dart-0.0.1...dotprompt-dart-0.0.2) (2026-02-27)


### Features

* **dart:** add pub.dev publishing support ([#527](https://github.com/google/dotprompt/issues/527)) ([d70752b](https://github.com/google/dotprompt/commit/d70752b9dfbb86063f0b5cf0e4158d8cdd14bba7))
* **dart:** dotprompt and handlebars implementation ([#509](https://github.com/google/dotprompt/issues/509)) ([3b2982c](https://github.com/google/dotprompt/commit/3b2982c6f8dfaee84ca120da93a50bc92940ee69))
* **rules_dart,rules_flutter:** enhance Bazel rules with workers and linting fixes ([#513](https://github.com/google/dotprompt/issues/513)) ([5369b40](https://github.com/google/dotprompt/commit/5369b4046eea9805f7dbcf026434035d55e2b095))
* **rules_dart:** first-class Bazel ruleset with RBE, IDE aspects, and version conflict detection ([#512](https://github.com/google/dotprompt/issues/512)) ([1624c75](https://github.com/google/dotprompt/commit/1624c7546deac1969a836dc83d2c3531a8e66ef0))


### Bug Fixes

* add Apache-2.0 license metadata to all packages ([#528](https://github.com/google/dotprompt/issues/528)) ([c76c663](https://github.com/google/dotprompt/commit/c76c6639fb77b39ef5b45a1a8dbebacc4c9bd422))

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
