# Handlebars Grammar Reference

This directory contains the official Handlebars grammar files from
[handlebars-lang/handlebars.js](https://github.com/handlebars-lang/handlebars.js).

## Grammar Files

- `handlebars.yy` - The Jison parser grammar (YACC/Bison-style)
- `handlebars.l` - The Jison lexer grammar (Lex-style)

These files define the authoritative Handlebars syntax and are useful for
implementing Handlebars parsers in other languages using parser generators.

## License

The Handlebars.js grammar files are licensed under the MIT License:

```
Copyright (C) 2011-2019 by Yehuda Katz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

## Source

- Repository: https://github.com/handlebars-lang/handlebars.js
- Branch: 4.x
- Downloaded: 2026-01-30

## Parser Generator Options

| Language | Parser Generator | Notes |
|----------|------------------|-------|
| Dart | [petitparser](https://pub.dev/packages/petitparser) | PEG combinator library |
| Dart | ANTLR4 | Has Dart target |
| Python | [handlebars-rust](https://github.com/nickel-org/handlebars-rust) via PyO3 | Rust bindings approach |
| Rust | [handlebars-rust](https://docs.rs/handlebars/) | Full implementation |
| Go | [raymond](https://github.com/aymerick/raymond) | Go implementation |
| Java | [handlebars.java](https://github.com/jknack/handlebars.java) | Java implementation |

## Our Test Specifications

Dotprompt has its own specification tests in the parent `spec/` directory that
test Handlebars features relevant to prompt templates:

- `spec/helpers/` - Helper function specifications
- `spec/variables.yaml` - Variable substitution specifications
- `spec/partials.yaml` - Partial template specifications
- `spec/picoschema.yaml` - Picoschema specifications
