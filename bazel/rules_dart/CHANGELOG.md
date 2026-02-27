# Changelog

All notable changes to rules_dart will be documented in this file.

## [0.1.1](https://github.com/google/dotprompt/compare/rules_dart-0.1.0...rules_dart-0.1.1) (2026-02-27)


### Features

* add rules_dart implementation ([#508](https://github.com/google/dotprompt/issues/508)) ([33a2562](https://github.com/google/dotprompt/commit/33a2562368bba58b86125090471d16c0f8068357))
* **dart:** add pub.dev publishing support ([#527](https://github.com/google/dotprompt/issues/527)) ([d70752b](https://github.com/google/dotprompt/commit/d70752b9dfbb86063f0b5cf0e4158d8cdd14bba7))
* **dart:** dotprompt and handlebars implementation ([#509](https://github.com/google/dotprompt/issues/509)) ([3b2982c](https://github.com/google/dotprompt/commit/3b2982c6f8dfaee84ca120da93a50bc92940ee69))
* **rules_dart,rules_flutter:** enhance Bazel rules with workers and linting fixes ([#513](https://github.com/google/dotprompt/issues/513)) ([5369b40](https://github.com/google/dotprompt/commit/5369b4046eea9805f7dbcf026434035d55e2b095))
* **rules_dart:** first-class Bazel ruleset with RBE, IDE aspects, and version conflict detection ([#512](https://github.com/google/dotprompt/issues/512)) ([1624c75](https://github.com/google/dotprompt/commit/1624c7546deac1969a836dc83d2c3531a8e66ef0))

## [0.0.1] - 2026-01-30

### Added

- Initial release of rules_dart
- `dart_library` rule for creating Dart library targets
- `dart_binary` rule for creating Dart executable targets
- `dart_test` rule for running Dart tests
- `dart_spec_test` rule for running spec-based conformance tests
- Automatic Dart SDK download from Google's official CDN
- Bzlmod module extension for SDK configuration
- Support for Linux (x64, arm64), macOS (x64, arm64), and Windows (x64)
