# ANTLR-Based Handlebars Parser for Dart

## Overview

This document outlines the plan to implement an ANTLR4-based Handlebars parser
for the Dart `handlebarrz` library, providing a robust, spec-compliant parser
generated from the official Handlebars.js grammar.

## Goals

1. **Spec Compliance**: Full compatibility with Handlebars.js 4.7.x
2. **Maintainability**: Single grammar file as source of truth
3. **Fallback Support**: Keep hand-written parser as backup/verification
4. **CI Integration**: Automated grammar validation and parser generation

## Architecture

```
spec/handlebars/antlr/
├── Handlebars.g4           # ANTLR4 grammar (converted from Jison)
└── README.md               # Grammar documentation

dart/handlebars_dart/
├── lib/src/
│   ├── parser.dart         # Hand-written parser (fallback)
│   ├── antlr/              # Generated ANTLR parser
│   │   ├── HandlebarsLexer.dart
│   │   ├── HandlebarsParser.dart
│   │   └── HandlebarsVisitor.dart
│   └── parser_facade.dart  # Unified parser interface
└── pubspec.yaml            # Add antlr4 dependency
```

## Implementation Plan

### Phase 1: Grammar Conversion (Day 1-2)

1. **Complete ANTLR4 Grammar**
   - Convert `handlebars.yy` parser rules → ANTLR4 syntax
   - Convert `handlebars.l` lexer rules → ANTLR4 syntax
   - Handle lexer modes for raw blocks and mustaches
   - Validate with ANTLR4 tools

2. **Grammar Features**
   - [x] Basic mustache expressions
   - [x] Block helpers (if/each/with/unless)
   - [x] Partials and partial blocks
   - [x] Raw blocks
   - [x] Block parameters
   - [x] Subexpressions
   - [x] Escape sequences (\{{)
   - [x] Whitespace control (~)
   - [x] Comments

### Phase 2: Dart Integration (Day 3-4)

1. **Add ANTLR4 Dependency**
   ```yaml
   # pubspec.yaml
   dependencies:
     antlr4: ^4.13.2
   ```

2. **Generate Dart Parser**
   ```bash
   antlr4 -Dlanguage=Dart -visitor -no-listener Handlebars.g4
   ```

3. **Create Visitor for AST**
   - Implement `HandlebarsBaseVisitor` to build runtime AST nodes
   - Map ANTLR parse tree to existing `AstNode` types

4. **Unified Parser Facade**
   ```dart
   class ParserFacade {
     static ProgramNode parse(String source, {bool useAntlr = true}) {
       if (useAntlr) {
         return _parseWithAntlr(source);
       }
       return Parser.parse(source);  // Fallback
     }
   }
   ```

### Phase 3: Testing & Validation (Day 5-6)

1. **Parity Testing**
   - Parse templates with both parsers
   - Compare AST output for equivalence
   - Add conformance test suite

2. **Performance Benchmarks**
   - Compare parse times: ANTLR vs hand-written
   - Memory usage comparison

### Phase 4: CI/CD Integration (Day 7)

1. **Bazel Rules**
   ```starlark
   # Generate parser at build time
   genrule(
       name = "generate_antlr_parser",
       srcs = ["//spec/handlebars/antlr:Handlebars.g4"],
       outs = ["HandlebarsLexer.dart", "HandlebarsParser.dart", ...],
       cmd = "antlr4 -Dlanguage=Dart ...",
   )
   ```

2. **GitHub Actions**
   ```yaml
   # Validate grammar on PR
   - name: Validate ANTLR Grammar
     run: antlr4 -Dlanguage=Dart Handlebars.g4
   ```

3. **Pre-commit Hook**
   - Regenerate parser if grammar changes
   - Verify generated files are committed

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `spec/handlebars/antlr/Handlebars.g4` | Create | ANTLR4 grammar |
| `dart/handlebars_dart/pubspec.yaml` | Modify | Add antlr4 dependency |
| `dart/handlebars_dart/lib/src/antlr/` | Create | Generated parser files |
| `dart/handlebars_dart/lib/src/parser_facade.dart` | Create | Unified parser interface |
| `.github/workflows/dart.yml` | Modify | Add ANTLR validation |
| `scripts/generate_antlr_parser` | Create | Parser generation script |

## Dependencies

- **ANTLR4 Tool**: v4.13.2 (for grammar validation and code generation)
- **antlr4 Dart Package**: v4.13.2 (runtime library)

## Success Criteria

1. ✅ ANTLR grammar compiles without errors
2. ✅ Generated Dart parser passes all 71+ existing tests
3. ✅ Parity with hand-written parser on all test cases
4. ✅ CI validates grammar on every PR
5. ✅ Documentation updated

## Timeline

| Day | Milestone |
|-----|-----------|
| 1-2 | Complete ANTLR grammar |
| 3-4 | Dart integration + visitor |
| 5-6 | Testing + validation |
| 7 | CI/CD + documentation |

## References

- [ANTLR4 Dart Target](https://pub.dev/packages/antlr4)
- [Official Handlebars.js Grammar](https://github.com/handlebars-lang/handlebars.js/tree/4.x/src)
- [ANTLR4 Grammar Reference](https://github.com/antlr/antlr4/blob/master/doc/grammars.md)

