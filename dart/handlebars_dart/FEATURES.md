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
- **Runtime**: Whitespace stripping implemented for adjacent text nodes and at
  the start/end of block content

### Escape Sequences

- `\{{` outputs a literal `{{`
- `\\{{` outputs a `\` followed by the rendered variable

### Raw Blocks

- `{{{{raw}}}}...{{{{/raw}}}}` outputs its content literally, without processing
  the inner `{{ }}` expressions

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

**127 tests passing**

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

### ANTLR4 Parser (Test-only)

An ANTLR4-based parser, generated from the official Handlebars.js grammar, is
kept purely as a testing aid. It is **not** part of the published library and
the package does not depend on the `antlr4` runtime. It exists so the CI parity
suite can confirm the hand-written parser stays structurally equivalent to the
grammar-derived one.

The parser, its `ParserFacade`, and the generated grammar live under
`test/antlr/`. The generated files can be regenerated with:

```bash
./scripts/generate_handlebars_parser
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

## Compatibility Notes

- Follows Handlebars.js 4.x specification
- `0` is treated as falsy (matching JavaScript/Handlebars.js behavior)
- Empty arrays are treated as falsy
- Empty strings are treated as falsy
