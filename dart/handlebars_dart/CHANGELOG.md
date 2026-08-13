# Changelog

All notable changes to handlebars_dart will be documented in this file.

## [1.0.0] - 2026-08-13

### Added

- First stable release of the pure-Dart Handlebars template engine.
- Variable substitution with dot and slash path access, parent context (`../`),
  and the `this`/`.` current-context reference.
- HTML escaping by default, with unescaped output via `{{{ }}}`, `{{& }}`, and
  `SafeString`.
- Built-in block helpers: `if`, `unless`, `each`, `with`, including `{{else}}`
  and inverse (`{{^}}`) sections.
- Iteration data variables `@index`, `@key`, `@first`, `@last`, `@root`, and
  block parameters (`as |item index|`).
- Custom helpers with positional and hash arguments, block helpers with `fn` and
  `inverse` callbacks, and subexpressions.
- Built-in `lookup` and `log` helpers.
- Partials, partial blocks (`{{#> }}`), and inline partials
  (`{{#*inline}}`).
- Comments (`{{! }}` and `{{!-- --}}`), literals, raw blocks
  (`{{{{raw}}}}`), whitespace control (`{{~ ~}}`), and the `\{{` escape
  sequence.
- Strict mode that throws `StrictModeException` on undefined variables.

### Changed

- The ANTLR4-based parser and its generated grammar are now test-only. The
  published library ships the hand-written parser exclusively and no longer
  depends on the `antlr4` runtime.
