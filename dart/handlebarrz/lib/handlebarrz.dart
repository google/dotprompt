// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

/// A pure Dart implementation of the Handlebars template engine.
///
/// Handlebarrz provides Handlebars-compatible templating with support for:
/// - Variable substitution: `{{name}}`
/// - Dot notation paths: `{{user.name}}`
/// - Helpers with arguments: `{{helper arg1 arg2}}`
/// - Hash arguments: `{{helper key="value"}}`
/// - Block helpers: `{{#if condition}}...{{/if}}`
/// - Inverse blocks: `{{#if}}...{{else}}...{{/if}}`
/// - Partials: `{{> partialName}}`
/// - Comments: `{{! comment }}`
/// - Raw/unescaped output: `{{{rawHtml}}}`
///
/// ## Architecture
///
/// The template compilation pipeline follows this flow:
///
/// ```
/// ┌─────────────────────────────────────────────────────────────────────────┐
/// │                    HANDLEBARRZ COMPILATION PIPELINE                     │
/// └─────────────────────────────────────────────────────────────────────────┘
///
///   Template Source                   Context Data
///        │                                 │
///        ▼                                 │
/// ┌─────────────┐                          │
/// │   LEXER     │  Tokenizes source        │
/// │             │  into token stream       │
/// └─────┬───────┘                          │
///       │                                  │
///       ▼ Token Stream                     │
/// ┌─────────────┐                          │
/// │   PARSER    │  Builds Abstract         │
/// │             │  Syntax Tree (AST)       │
/// └─────┬───────┘                          │
///       │                                  │
///       ▼ AST (ProgramNode)                │
/// ┌─────────────┐                          │
/// │   RUNTIME   │◄─────────────────────────┘
/// │             │  Renders AST with
/// │             │  context, helpers,
/// │             │  and partials
/// └─────┬───────┘
///       │
///       ▼
///   Rendered String
/// ```
///
/// ## Token Types
///
/// The lexer recognizes these token types:
///
/// | Token          | Pattern        | Example               |
/// |----------------|----------------|-----------------------|
/// | text           | plain text     | `Hello `              |
/// | open           | `{{`           | `{{name}}`            |
/// | openUnescaped  | `{{{`          | `{{{html}}}`          |
/// | openBlock      | `{{#`          | `{{#if}}`             |
/// | openEndBlock   | `{{/`          | `{{/if}}`             |
/// | openPartial    | `{{>`          | `{{>header}}`         |
/// | openComment    | `{{!`          | `{{!comment}}`        |
/// | openInverse    | `{{^`          | `{{^if}}`             |
/// | close          | `}}`           | `}}`                  |
/// | closeUnescaped | `}}}`          | `}}}`                 |
/// | id             | identifier     | `name`, `user.email`  |
/// | string         | `"..."`, `'.'` | `"hello"`             |
/// | number         | digits         | `42`, `3.14`          |
/// | boolean        | true/false     | `true`                |
/// | equals         | `=`            | `key=value`           |
///
/// ## AST Node Types
///
/// The parser produces these AST node types:
///
/// ```
/// AstNode (abstract)
///    │
///    ├── ProgramNode      Container for a sequence of statements
///    │      └── body: List<AstNode>
///    │
///    ├── TextNode         Plain text content
///    │      └── text: String
///    │
///    ├── MustacheNode     Variable/helper expression {{ ... }}
///    │      ├── path: PathNode
///    │      ├── params: List<ExpressionNode>
///    │      ├── hash: Map<String, ExpressionNode>
///    │      └── escaped: bool
///    │
///    ├── BlockNode        Block helper {{#...}}...{{/...}}
///    │      ├── path: PathNode
///    │      ├── params: List<ExpressionNode>
///    │      ├── hash: Map<String, ExpressionNode>
///    │      ├── program: ProgramNode
///    │      ├── inverse: ProgramNode?
///    │      └── isInverse: bool
///    │
///    ├── PartialNode      Partial inclusion {{> ...}}
///    │      ├── name: String
///    │      ├── context: ExpressionNode?
///    │      └── hash: Map<String, ExpressionNode>
///    │
///    └── CommentNode      Comment {{! ... }}
///           └── text: String
/// ```
///
/// ## Example
///
/// ```dart
/// import 'package:handlebarrz/handlebarrz.dart';
///
/// void main() {
///   final hb = Handlebars();
///
///   // Register a helper
///   hb.registerHelper('loud', (args, options) => args[0].toString().toUpperCase());
///
///   // Compile and render
///   final template = hb.compile('Hello {{loud name}}!');
///   print(template({'name': 'world'}));  // "Hello WORLD!"
/// }
/// ```
library;

export "src/antlr_parser.dart" show AntlrParser;
export "src/handlebars.dart";
export "src/options.dart";
export "src/parser.dart" show AstNode, ProgramNode;
export "src/parser_facade.dart" show ParserFacade, ParserType;
export "src/runtime.dart" show StrictModeException;
export "src/safe_string.dart";
export "src/template.dart";
