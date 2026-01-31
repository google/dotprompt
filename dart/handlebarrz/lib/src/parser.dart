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

import "lexer.dart";

/// Base class for all AST nodes.
sealed class AstNode {
  const AstNode();
}

/// A sequence of AST nodes (the program).
class ProgramNode extends AstNode {
  const ProgramNode(this.body);
  final List<AstNode> body;
}

/// Plain text content.
class TextNode extends AstNode {
  const TextNode(this.text);
  final String text;
}

/// A comment node ({{! comment }} or {{!-- comment --}}).
class CommentNode extends AstNode {
  const CommentNode(this.text);
  final String text;
}

/// A mustache expression ({{expr}} or {{{expr}}}).
class MustacheNode extends AstNode {
  const MustacheNode({
    required this.path,
    required this.params,
    required this.hash,
    required this.escaped,
    this.openStrip = false,
    this.closeStrip = false,
  });

  /// The path/helper name.
  final PathNode path;

  /// Positional parameters.
  final List<ExpressionNode> params;

  /// Hash/named parameters.
  final Map<String, ExpressionNode> hash;

  /// Whether output should be HTML-escaped.
  final bool escaped;

  /// Whether to strip whitespace before this expression ({{~...).
  final bool openStrip;

  /// Whether to strip whitespace after this expression (...~}}).
  final bool closeStrip;
}

/// A block helper ({{#helper}}...{{/helper}}).
class BlockNode extends AstNode {
  const BlockNode({
    required this.path,
    required this.params,
    required this.hash,
    required this.program,
    required this.inverse,
    required this.isInverse,
    this.openStrip = false,
    this.closeStrip = false,
    this.blockParams = const [],
  });

  /// The helper name.
  final PathNode path;

  /// Positional parameters.
  final List<ExpressionNode> params;

  /// Hash/named parameters.
  final Map<String, ExpressionNode> hash;

  /// The main block content.
  final ProgramNode program;

  /// The else block content (may be empty).
  final ProgramNode? inverse;

  /// Whether this is an inverse block ({{^}}).
  final bool isInverse;

  /// Whether to strip whitespace before the opening tag ({{~#...).
  final bool openStrip;

  /// Whether to strip whitespace after the closing tag (...~}}).
  final bool closeStrip;

  /// Block params (e.g., [item, index] for {{#each items as |item index|}}).
  final List<String> blockParams;
}

/// A partial invocation ({{> partialName}}).
class PartialNode extends AstNode {
  const PartialNode({
    required this.name,
    required this.context,
    required this.hash,
  });

  /// The partial name.
  final String name;

  /// Optional context expression.
  final ExpressionNode? context;

  /// Hash parameters.
  final Map<String, ExpressionNode> hash;
}

/// A raw block ({{{{raw}}}}...{{{{/raw}}}}).
/// Content inside is output literally without parsing.
class RawBlockNode extends AstNode {
  const RawBlockNode({
    required this.name,
    required this.content,
  });

  /// The raw block name (e.g., "raw").
  final String name;

  /// The literal content between the tags.
  final String content;
}

/// A partial block ({{#> partialName}}...{{/partialName}}).
/// Allows providing default content for a partial.
class PartialBlockNode extends AstNode {
  const PartialBlockNode({
    required this.name,
    required this.context,
    required this.hash,
    required this.program,
  });

  /// The partial name.
  final String name;

  /// Optional context expression.
  final ExpressionNode? context;

  /// Hash parameters.
  final Map<String, ExpressionNode> hash;

  /// The default content if partial is not found.
  final ProgramNode program;
}


/// Base class for expressions (values that can be passed as parameters).
sealed class ExpressionNode extends AstNode {
  const ExpressionNode();
}

/// A path expression (variable lookup).
class PathNode extends ExpressionNode {
  const PathNode(this.parts, {this.isData = false});

  /// The path parts (e.g., ["user", "name"] for user.name).
  final List<String> parts;

  /// Whether this is a data variable (@root, @index, etc.).
  final bool isData;

  /// Returns the full path as a string.
  String get path => isData ? "@${parts.join(".")}" : parts.join(".");
}

/// A string literal.
class StringNode extends ExpressionNode {
  const StringNode(this.value);
  final String value;
}

/// A number literal.
class NumberNode extends ExpressionNode {
  const NumberNode(this.value);
  final num value;
}

/// A boolean literal.
class BooleanNode extends ExpressionNode {
  const BooleanNode(this.value);
  final bool value;
}

/// A subexpression (nested helper call).
///
/// Represents `(helper arg1 arg2)` syntax for calling helpers as parameters.
class SubExpressionNode extends ExpressionNode {
  const SubExpressionNode({
    required this.path,
    required this.params,
    required this.hash,
  });

  /// The helper name.
  final PathNode path;

  /// Positional parameters.
  final List<ExpressionNode> params;

  /// Hash/named parameters.
  final Map<String, ExpressionNode> hash;
}

/// Parser for Handlebars templates.
///
/// Converts the template source into an Abstract Syntax Tree (AST). The parser
/// uses a two-pass approach: first tokenizing the entire source, then building
/// the tree structure.
///
/// ## Parsing Strategy
///
/// ```
/// ┌──────────────────────────────────────────────────────────────────┐
/// │                      PARSER ALGORITHM                            │
/// └──────────────────────────────────────────────────────────────────┘
///
///   Template: "Hello {{#if user}}{{name}}{{/if}}!"
///
///   Pass 1: Tokenize
///   ┌────────────────────────────────────────────────────────────┐
///   │ [text:"Hello "] [#if] [id:user] [close] [open] [id:name]  │
///   │ [close] [/if] [close] [text:"!"]                          │
///   └────────────────────────────────────────────────────────────┘
///
///   Pass 2: Build AST
///   ┌────────────────────────────────────────────────────────────┐
///   │   ProgramNode                                              │
///   │   ├── TextNode("Hello ")                                   │
///   │   ├── BlockNode(#if)                                       │
///   │   │   ├── params: [PathNode("user")]                       │
///   │   │   └── program: ProgramNode                             │
///   │   │       └── MustacheNode                                 │
///   │   │           └── path: PathNode("name")                   │
///   │   └── TextNode("!")                                        │
///   └────────────────────────────────────────────────────────────┘
/// ```
///
/// ## Expression Grammar
///
/// ```
/// expression  := path (param)* (hash)*
/// param       := path | string | number | boolean
/// hash        := id "=" param
/// path        := id ("." id)*
/// ```
///
/// ## Block Structure
///
/// ```
/// block       := "{{#" expression "}}" program inverse? "{{/" id "}}"
/// inverse     := "{{else}}" program | "{{^}}" program
/// program     := statement*
/// statement   := text | mustache | block | partial | comment
/// ```
class Parser {
  /// Parses the given template source into an AST.
  static ProgramNode parse(String source) {
    final parser = Parser._(source);
    return parser._parseProgram();
  }

  Parser._(this.source);

  final String source;
  late List<Token> _tokens;
  int _pos = 0;

  Token get _current => _pos < _tokens.length ? _tokens[_pos] : _tokens.last;

  bool get _atEnd => _current.type == TokenType.eof;

  ProgramNode _parseProgram({String? endBlock}) {
    _tokens = [];
    final lexer = Lexer(source);

    // First pass: get all tokens including text
    var pos = 0;
    while (pos < source.length) {
      // Find next {{ or end, accounting for escape sequences
      var nextOpen = _findNextMustacheOpen(source, pos);
      if (nextOpen == -1) {
        // Rest is text - process escape sequences
        if (pos < source.length) {
          final text = _processEscapeSequences(source.substring(pos));
          _tokens.add(Token(TokenType.text, text, 1, 1));
        }
        break;
      }

      // Add text before (with escape sequence processing)
      if (nextOpen > pos) {
        final text = _processEscapeSequences(source.substring(pos, nextOpen));
        _tokens.add(Token(TokenType.text, text, 1, 1));
      }

      // Parse the handlebars expression
      final subLexer = Lexer(source.substring(nextOpen));
      final openToken = subLexer.nextToken();
      _tokens.add(Token(openToken.type, openToken.value, 1, nextOpen + 1));

      // For comments, we already have the full content
      if (openToken.type == TokenType.openComment) {
        pos = nextOpen + 3 + openToken.value.length + 2; // {{! (3) + content + }} (2)
        if (source.substring(nextOpen).startsWith("{{!--")) {
          pos = nextOpen + 5 + openToken.value.length + 4; // {{!-- (5) + content + --}} (4)
        }
        continue;
      }

      // For raw blocks, the lexer has already consumed everything up to the end tag
      if (openToken.type == TokenType.openRawBlock) {
        // The lexer's rawBlockContent contains the literal content
        // Add it as a text token
        if (subLexer.rawBlockContent != null) {
          _tokens.add(Token(TokenType.text, subLexer.rawBlockContent!, 1, nextOpen + 1));
        }
        // Update position to after the entire raw block
        pos = nextOpen + subLexer.position;
        continue;
      }

      // Read expression tokens
      final exprTokens = subLexer.readExpression();
      _tokens.addAll(exprTokens);

      // Update position
      pos = nextOpen + subLexer.position;
    }

    _tokens.add(Token(TokenType.eof, "", 1, source.length));

    // Parse the token stream
    _pos = 0;
    return _parseProgramFromTokens(endBlock: endBlock);
  }

  ProgramNode _parseProgramFromTokens({String? endBlock}) {
    final body = <AstNode>[];

    while (!_atEnd) {
      // Check for end block
      if (endBlock != null && _current.type == TokenType.openEndBlock) {
        break;
      }

      // Check for else
      if (_current.type == TokenType.openInverse ||
          (_current.type == TokenType.open && _peek()?.value == "else")) {
        break;
      }

      final node = _parseStatement();
      if (node != null) {
        body.add(node);
      }
    }

    return ProgramNode(body);
  }

  AstNode? _parseStatement() {
    switch (_current.type) {
      case TokenType.text:
        final text = _current.value;
        _advance();
        return TextNode(text);

      case TokenType.openComment:
        final comment = _current.value;
        _advance();
        return CommentNode(comment);

      case TokenType.open:
        return _parseMustache(escaped: true);

      case TokenType.openUnescaped:
        return _parseMustache(escaped: false);

      case TokenType.openBlock:
        return _parseBlock(isInverse: false);

      case TokenType.openInverse:
        return _parseBlock(isInverse: true);

      case TokenType.openPartial:
        return _parsePartial();

      case TokenType.openRawBlock:
        return _parseRawBlock();

      case TokenType.openPartialBlock:
        return _parsePartialBlock();

      default:
        _advance();
        return null;
    }
  }

  MustacheNode _parseMustache({required bool escaped}) {
    // Check for open strip marker ({{~ or {{{~)
    final openToken = _current;
    final openStrip = openToken.value.contains("~");
    _advance(); // Skip open

    final (path, params, hash) = _parseExpressionParts();

    // Check for close strip marker (~}} or ~}}})
    final closeStrip = _current.value.startsWith("~");

    // Expect close
    _expectClose(escaped);

    return MustacheNode(
      path: path,
      params: params,
      hash: hash,
      escaped: escaped,
      openStrip: openStrip,
      closeStrip: closeStrip,
    );
  }

  BlockNode _parseBlock({required bool isInverse}) {
    // Check for open strip marker ({{~# or {{#~)
    final openToken = _current;
    final openStrip = openToken.value.contains("~");
    _advance(); // Skip open

    final (path, params, hash) = _parseExpressionParts();

    // Parse block params: as |item index|
    final blockParams = <String>[];
    if (_current.type == TokenType.asKeyword) {
      _advance(); // Skip 'as'
      if (_current.type == TokenType.pipe) {
        _advance(); // Skip opening |
        // Read identifiers until closing |
        while (_current.type == TokenType.id) {
          blockParams.add(_current.value);
          _advance();
        }
        if (_current.type == TokenType.pipe) {
          _advance(); // Skip closing |
        }
      }
    }

    // Check for close strip marker on opening tag (~}})
    var closeStrip = _current.value.startsWith("~");

    // Expect close
    _expect(TokenType.close);

    // Parse program body - we need to re-parse from current position
    final bodyStart = _pos;
    final body = _parseBlockBody(path.parts.first);

    // Check for else block
    ProgramNode? inverse;
    if (_current.type == TokenType.openInverse ||
        (_current.type == TokenType.open && _peek()?.value == "else")) {
      if (_current.type == TokenType.open) {
        _advance(); // Skip {{
        _advance(); // Skip else
        _expect(TokenType.close);
      } else {
        _advance(); // Skip {{^
        _expect(TokenType.close);
      }
      inverse = _parseBlockBody(path.parts.first);
    }

    // Expect end block - check for close strip marker on closing tag
    if (_current.type == TokenType.openEndBlock) {
      // Check if end block has strip marker ({{~/)
      if (_current.value.contains("~")) {
        closeStrip = true;
      }
      _advance();
      _expect(TokenType.id); // Block name
      // Check for close strip on end tag (~}})
      if (_current.value.startsWith("~")) {
        closeStrip = true;
      }
      _expect(TokenType.close);
    }

    return BlockNode(
      path: path,
      params: params,
      hash: hash,
      program: body,
      inverse: inverse,
      isInverse: isInverse,
      openStrip: openStrip,
      closeStrip: closeStrip,
      blockParams: blockParams,
    );
  }

  ProgramNode _parseBlockBody(String blockName) {
    final body = <AstNode>[];

    while (!_atEnd) {
      // Check for end block or else
      if (_current.type == TokenType.openEndBlock) {
        // Peek ahead to see if this ends our block
        final nextPos = _pos + 1;
        if (nextPos < _tokens.length && _tokens[nextPos].value == blockName) {
          break;
        }
      }

      // Check for else
      if (_current.type == TokenType.openInverse) {
        break;
      }
      if (_current.type == TokenType.open) {
        final next = _peek();
        if (next?.value == "else") {
          break;
        }
      }

      final node = _parseStatement();
      if (node != null) {
        body.add(node);
      }
    }

    return ProgramNode(body);
  }

  PartialNode _parsePartial() {
    _advance(); // Skip {{>

    // Get partial name
    final name = _current.value;
    _advance();

    // Optional context and hash
    ExpressionNode? context;
    final hash = <String, ExpressionNode>{};

    while (_current.type != TokenType.close &&
        _current.type != TokenType.closeUnescaped &&
        _current.type != TokenType.eof) {
      // Check for hash param
      if (_peek()?.type == TokenType.equals) {
        final key = _current.value;
        _advance(); // Skip key
        _advance(); // Skip =
        hash[key] = _parseExpression()!;
      } else {
        context = _parseExpression();
      }
    }

    _expect(TokenType.close);

    return PartialNode(name: name, context: context, hash: hash);
  }

  /// Parses a raw block: {{{{raw}}}}...{{{{/raw}}}}
  /// The content between the tags is output literally without parsing.
  /// Note: The lexer has already extracted the name and content.
  RawBlockNode _parseRawBlock() {
    // The token value is the raw block name (e.g., "raw")
    final name = _current.value;
    _advance(); // Skip openRawBlock token

    // The next token should be the raw content (added by the lexer)
    String content = "";
    if (_current.type == TokenType.text) {
      content = _current.value;
      _advance(); // Skip the content token
    }

    return RawBlockNode(name: name, content: content);
  }

  /// Parses a partial block: {{#> partialName}}...{{/partialName}}
  PartialBlockNode _parsePartialBlock() {
    _advance(); // Skip {{#>

    // Get partial name
    final name = _current.value;
    _advance();

    // Optional context and hash
    ExpressionNode? context;
    final hash = <String, ExpressionNode>{};

    while (_current.type != TokenType.close &&
        _current.type != TokenType.closeUnescaped &&
        _current.type != TokenType.eof) {
      // Check for hash param
      if (_peek()?.type == TokenType.equals) {
        final key = _current.value;
        _advance(); // Skip key
        _advance(); // Skip =
        hash[key] = _parseExpression()!;
      } else {
        context = _parseExpression();
      }
    }

    _expect(TokenType.close);

    // Parse the block content
    final program = _parseBlockBody(name);

    // Expect closing tag {{/name}}
    if (_current.type == TokenType.openEndBlock) {
      _advance(); // Skip {{/
      if (_current.value == name) {
        _advance(); // Skip name
      }
      _expect(TokenType.close);
    }

    return PartialBlockNode(
      name: name,
      context: context,
      hash: hash,
      program: program,
    );
  }


  (PathNode, List<ExpressionNode>, Map<String, ExpressionNode>) _parseExpressionParts() {
    // First expression is the path/helper name
    final path = _parsePath();

    final params = <ExpressionNode>[];
    final hash = <String, ExpressionNode>{};

    // Parse remaining params and hash
    // Stop when we hit close, closeUnescaped, eof, or 'as' keyword (for block params)
    while (_current.type != TokenType.close &&
        _current.type != TokenType.closeUnescaped &&
        _current.type != TokenType.asKeyword &&
        _current.type != TokenType.eof) {
      // Check for hash param (key=value)
      if (_peek()?.type == TokenType.equals) {
        final key = _current.value;
        _advance(); // Skip key
        _advance(); // Skip =
        hash[key] = _parseExpression()!;
      } else {
        final expr = _parseExpression();
        if (expr != null) {
          params.add(expr);
        } else {
          // Unknown token - avoid infinite loop
          break;
        }
      }
    }

    return (path, params, hash);
  }

  PathNode _parsePath() {
    final parts = <String>[];
    var isData = false;

    // Check for data prefix
    if (_current.type == TokenType.data) {
      isData = true;
      final dataPath = _current.value.substring(1); // Remove @
      // Split by . for paths like @root.company
      if (dataPath.contains(".")) {
        parts.addAll(dataPath.split("."));
      } else {
        parts.add(dataPath);
      }
      _advance();
      return PathNode(parts, isData: true);
    }

    // Handle .. (parent context)
    while (_current.type == TokenType.dotDot) {
      parts.add("..");
      _advance();
      // Handle separator after .. (either . or /)
      if (_current.type == TokenType.dot || _current.type == TokenType.slash) {
        _advance();
      }
    }

    // Read path parts
    if (_current.type == TokenType.id) {
      // Split by . and / for paths like a.b/c.d
      final id = _current.value;
      // Use regex to split by either . or /
      final pathParts = id.split(RegExp(r"[./]"));
      parts.addAll(pathParts.where((p) => p.isNotEmpty));
      _advance();
    } else if (_current.type == TokenType.dot && parts.isEmpty) {
      // Standalone dot (this context) - only if we haven't parsed anything yet
      parts.add(".");
      _advance();
    }

    return PathNode(parts.isEmpty ? ["."] : parts, isData: isData);
  }

  ExpressionNode? _parseExpression() {
    switch (_current.type) {
      case TokenType.string:
        final value = _current.value;
        _advance();
        return StringNode(value);

      case TokenType.number:
        final value = num.parse(_current.value);
        _advance();
        return NumberNode(value);

      case TokenType.boolean:
        final value = _current.value == "true";
        _advance();
        return BooleanNode(value);

      case TokenType.openParen:
        return _parseSubExpression();

      case TokenType.id:
      case TokenType.dotDot:
      case TokenType.dot:
      case TokenType.data:
        return _parsePath();

      default:
        return null;
    }
  }

  /// Parses a subexpression: (helper arg1 arg2 key=value)
  SubExpressionNode _parseSubExpression() {
    _expect(TokenType.openParen);

    // Parse the helper path
    final path = _parsePath();
    if (path == null) {
      throw FormatException(
        "Expected helper name in subexpression at ${_current.line}:${_current.column}",
      );
    }

    // Parse params and hash
    final params = <ExpressionNode>[];
    final hash = <String, ExpressionNode>{};

    while (_current.type != TokenType.closeParen && !_atEnd) {
      // Check for hash argument (key=value)
      if (_current.type == TokenType.id && _peek()?.type == TokenType.equals) {
        final key = _current.value;
        _advance(); // skip key
        _advance(); // skip =
        final value = _parseExpression();
        if (value != null) {
          hash[key] = value;
        }
      } else {
        final expr = _parseExpression();
        if (expr != null) {
          params.add(expr);
        } else {
          break;
        }
      }
    }

    _expect(TokenType.closeParen);

    return SubExpressionNode(path: path, params: params, hash: hash);
  }

  void _expectClose(bool escaped) {
    if (escaped) {
      _expect(TokenType.close);
    } else {
      if (_current.type == TokenType.closeUnescaped) {
        _advance();
      } else {
        _expect(TokenType.close);
      }
    }
  }

  void _expect(TokenType type) {
    if (_current.type != type) {
      throw FormatException(
        "Expected $type but got ${_current.type} at ${_current.line}:${_current.column}",
      );
    }
    _advance();
  }

  Token? _peek() {
    if (_pos + 1 < _tokens.length) {
      return _tokens[_pos + 1];
    }
    return null;
  }

  void _advance() {
    if (_pos < _tokens.length - 1) {
      _pos++;
    }
  }

  /// Finds the next unescaped {{ in the source string, starting at pos.
  /// Returns -1 if not found.
  /// Skips over \{{ which is an escaped literal (but not \\{{ which is \ + {{).
  int _findNextMustacheOpen(String source, int startPos) {
    var pos = startPos;
    while (pos < source.length - 1) {
      // Check for {{ at this position
      if (source.codeUnitAt(pos) == 123 && source.codeUnitAt(pos + 1) == 123) {
        // Check if preceded by single backslash (escape sequence)
        // \{{ is escape, \\{{ is literal backslash + variable
        if (pos > 0 && source.codeUnitAt(pos - 1) == 92) {
          // Check if the backslash is escaped (preceded by another backslash)
          if (pos > 1 && source.codeUnitAt(pos - 2) == 92) {
            // \\{{ - the first backslash escapes the second, {{ is real
            return pos;
          }
          // \{{ - this is an escape sequence, skip it
          pos += 2;
          continue;
        }
        return pos;
      }
      pos++;
    }
    return -1;
  }

  /// Processes escape sequences in text, converting \{{ to {{.
  String _processEscapeSequences(String text) {
    if (!text.contains(r"\{{")) {
      return text;
    }
    // Replace \{{ with {{
    final buffer = StringBuffer();
    var i = 0;
    while (i < text.length) {
      if (i < text.length - 2 &&
          text.codeUnitAt(i) == 92 && // backslash
          text.codeUnitAt(i + 1) == 123 && // {
          text.codeUnitAt(i + 2) == 123) {
        // {
        // Replace \{{ with {{
        buffer.write("{{");
        i += 3;
      } else {
        buffer.write(text[i]);
        i++;
      }
    }
    return buffer.toString();
  }
}
