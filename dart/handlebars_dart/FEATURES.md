# handlebars_dart Feature Implementation Status

This document tracks the implementation status of Handlebars features in the
Dart `handlebars_dart` library.

## Implemented Features ✅

### Core Features

- **Variable Substitution**: `{{name}}`, `{{user.name}}`, `{{user/name}}`
- **HTML Escaping**: Default HTML escaping with override via `{{{triple}}}` or `{{&ampersand}}`
- **Comments**: Short `{{! comment }}` and long `{{!-- comment --}}`
- **Literals**: Strings (`"..."` or `'...'`), numbers (including negative), booleans (`true`/`false`)
- **Path Notation**: Dot (`.`) and slash (`/`) separators, deeply nested paths
- **Parent Context**: `../` path navigation - access parent context in nested blocks
  - Single parent: `{{../name}}` - access parent context
  - Multi-level: `{{../../root}}` - access grandparent context

### Block Helpers

- **if/unless**: Conditional rendering with `{{else}}` support
- **each**: Iteration over arrays and objects with:
  - `@index` - current index
  - `@key` - current key (for objects)
  - `@first` / `@last` - boolean flags
  - Nested each support
  - `{{else}}` for empty collections
- **with**: Context switching
- **Block Params**: `{{#each items as |item index|}}` - Named block parameters
  - Item-only: `{{#each items as |item|}}`
  - Item and index: `{{#each items as |item index|}}`
  - Object iteration: `{{#each obj as |value key|}}`

### Custom Helpers

- Positional parameters
- Hash (named) parameters
- Block helpers with `fn()` and `inverse()` callbacks
- `SafeString` for unescaped output

### Built-in Helpers

- **lookup**: `{{lookup obj key}}` - Dynamic property access for maps and lists
- **log**: `{{log value}}` - Logs value to console (for debugging)

### Partials

- Named partials: `{{> partialName}}`
- Partials with context: `{{> partialName contextExpr}}`
- **Partial Blocks**: `{{#> partialName}}default content{{/partialName}}`
  - Falls back to default content if partial not found
- **Inline Partials**: `{{#*inline "name"}}...{{/inline}}`
  - Define reusable template snippets within a template
  - Use with `{{> name}}` after definition

### Subexpressions

- Helper calls as parameters: `{{outer (inner arg)}}`
- Nested subexpressions: `{{mult (add 2 3) 4}}`
- Subexpressions with hash args

### Data Variables

- `@root` - Access root context from nested blocks
- `@root.path` - Navigate from root
- `@index` - Loop index
- `@first` / `@last` - Loop boundary flags
- `@key` - Object key in each

### Whitespace Control

- **Lexer support**: `{{~` and `~}}` tokens recognized
- **Parser support**: Strip markers tracked in AST nodes
- **Runtime**: Whitespace stripping implemented for adjacent text nodes

## Partially Implemented 🚧

### Escape Sequences

- `\{{` to output literal `{{` - code implemented but Bazel caching prevents testing

### Block-level Whitespace Control

- Stripping at start/end of block content not yet implemented

### Raw Blocks

- `{{{{raw}}}}...{{{{/raw}}}}` - Lexer/parser infrastructure added but parser
  tokenization loop needs refactoring to handle raw content properly

## Runtime Modes

- **Strict Mode**: Enabled via `Handlebars(strict: true)` - throws `StrictModeException`
  on undefined variables instead of returning empty string

## Not Yet Implemented ❌

### Modes

- **String Params Mode**: Pass paths as strings to helpers
- **Track IDs**: Source mapping for paths

### Advanced Features

- **Decorators**: `{{*decorator}}` meta-programming feature

## Test Coverage

**71 tests passing** (2 skipped for investigation)

| Category              | Tests |
| --------------------- | ----- |
| Variable Substitution | 6     |
| HTML Escaping         | 2     |
| Helpers               | 4     |
| Block Helpers         | 11    |
| Custom Block Helpers  | 2     |
| Partials              | 2     |
| Comments              | 2     |
| Dotprompt Helpers     | 5     |
| Escape Sequences      | 3     |
| Ampersand Unescaped   | 1     |
| Whitespace Control    | 5     |
| Subexpressions        | 3     |
| Data Variables        | 2     |
| Parent Context        | 4     |
| Built-in Helpers      | 5     |
| Block Params          | 3     |
| Partial Blocks        | 2     |
| Literals              | 5     |
| Edge Cases            | 6     |

## Parser Implementation

### Hand-written Parser (Current Default)

The library includes a hand-written recursive descent parser optimized for
performance and ease of debugging. This is the current default parser.

### ANTLR4 Parser (Generated)

An ANTLR4-based parser is available, generated from the official Handlebars.js
grammar. This parser provides:

- **Spec Compliance**: Direct conversion from official Handlebars.js grammar
- **Maintainability**: Automatic parser generation from `.g4` grammar files
- **Cross-Language Potential**: Same grammar can generate parsers for other languages

Generated files are in `lib/src/antlr/`. To regenerate:

```bash
./scripts/generate_handlebars_parser
```

### Using the ANTLR Parser

The `ParserFacade` class provides a unified interface for both parsers:

```dart
import 'package:handlebars_dart/handlebars_dart.dart';

// Parse with default (hand-written) parser
final ast = ParserFacade.parse('Hello {{name}}!');

// Force ANTLR parser
final antlrAst = ParserFacade.parse('Hello {{name}}!', useAntlr: true);

// Compare parsers for testing
final result = ParserFacade.parseAndCompare('{{name}}');
print('Equivalent: ${result.equivalent}');
```

You can also set the default globally:

```dart
ParserFacade.defaultParser = ParserType.antlr;
```

### Parser Feature Comparison

| Feature              | Hand-written | ANTLR4                 |
| -------------------- | ------------ | ---------------------- |
| Speed                | Faster       | Slower                 |
| Spec compliance      | Manual       | Automatic from grammar |
| Error messages       | Custom       | Generated              |
| Maintenance          | Manual       | Grammar-based          |
| `{{else}}` blocks    | ✅ Full      | ✅ Full                |
| `{{else if}}` chains | ✅ Full      | ✅ Full                |
| Nested blocks        | ✅ Full      | ✅ Full                |

## Known Limitations

1. Escape sequences require parser integration for edge cases
2. Block-level whitespace control (inside blocks) not yet implemented
3. Raw blocks require further parser work

## Compatibility Notes

- Follows Handlebars.js 4.x specification
- `0` is treated as falsy (matching JavaScript/Handlebars.js behavior)
- Empty arrays are treated as falsy
- Empty strings are treated as falsy
