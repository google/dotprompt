# ANTLR4 Handlebars Grammar

This directory contains ANTLR4 grammar files for generating Handlebars parsers.

## Files

- `HandlebarsLexer.g4` - Lexer grammar (tokenization)
- `HandlebarsParser.g4` - Parser grammar (syntax rules)

## Grammar Source

These grammars are converted from the official Handlebars.js 4.x Jison grammars:
- [handlebars.yy](https://github.com/handlebars-lang/handlebars.js/blob/4.x/src/handlebars.yy)
- [handlebars.l](https://github.com/handlebars-lang/handlebars.js/blob/4.x/src/handlebars.l)

## Generating Dart Parser

Run the generation script:

```bash
./scripts/generate_handlebars_parser
```

This generates Dart files in `dart/handlebars_dart/lib/src/antlr/`.

## Manual Generation

To manually generate the parser:

```bash
# Install ANTLR4
brew install antlr

# Generate lexer
antlr4 -Dlanguage=Dart HandlebarsLexer.g4

# Generate parser with visitor
antlr4 -Dlanguage=Dart -visitor -no-listener HandlebarsParser.g4
```

## Grammar Features

| Feature | Status |
|---------|--------|
| Mustache expressions `{{name}}` | ✅ |
| Unescaped output `{{{name}}}` | ✅ |
| Ampersand unescaped `{{&name}}` | ✅ |
| Block helpers `{{#if}}...{{/if}}` | ✅ |
| Inverse blocks `{{^if}}...{{/if}}` | ✅ |
| Else chains `{{else if}}` | ✅ |
| Each with block params `{{#each items as \|item index\|}}` | ✅ |
| Partials `{{> partialName}}` | ✅ |
| Partial blocks `{{#> partial}}...{{/partial}}` | ✅ |
| Raw blocks `{{{{raw}}}}...{{{{/raw}}}}` | ✅ |
| Subexpressions `(helper arg)` | ✅ |
| Hash parameters `key=value` | ✅ |
| Data variables `@index`, `@root` | ✅ |
| Path expressions `foo.bar`, `../parent` | ✅ |
| Comments `{{! comment }}` | ✅ |
| Long comments `{{!-- comment --}}` | ✅ |
| Whitespace control `{{~name~}}` | ✅ |
| Escape sequences `\{{literal}}` | ✅ |
| String literals `"string"` | ✅ |
| Number literals `42`, `-3.14` | ✅ |
| Boolean literals `true`, `false` | ✅ |

## Other Language Targets

ANTLR4 can generate parsers for other languages:

```bash
# TypeScript
antlr4 -Dlanguage=TypeScript -visitor HandlebarsParser.g4

# Python
antlr4 -Dlanguage=Python3 -visitor HandlebarsParser.g4

# Go
antlr4 -Dlanguage=Go -visitor HandlebarsParser.g4

# Java
antlr4 -Dlanguage=Java -visitor HandlebarsParser.g4
```

## References

- [ANTLR4 Documentation](https://github.com/antlr/antlr4/blob/master/doc/index.md)
- [ANTLR4 Dart Runtime](https://pub.dev/packages/antlr4)
- [Handlebars.js](https://handlebarsjs.com/)
