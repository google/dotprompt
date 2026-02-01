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

/// Token types for Handlebars lexer.
enum TokenType {
  /// Plain text content.
  text,

  /// Opening `{{` (escaped output).
  open,

  /// Opening `{{{` (unescaped output).
  openUnescaped,

  /// Opening `{{#` (block start).
  openBlock,

  /// Opening `{{/` (block end).
  openEndBlock,

  /// Opening `{{>` (partial).
  openPartial,

  /// Opening `{{!` or `{{!--` (comment).
  openComment,

  /// Opening `{{^` (inverse/else block).
  openInverse,

  /// Opening `{{{{` (raw block start).
  openRawBlock,

  /// Closing `}}}}` (raw block end).
  closeRawBlock,

  /// Opening `{{#>` (partial block).
  openPartialBlock,

  /// Opening `{{#*` (inline partial definition).
  openInlinePartial,

  /// Closing `}}`.
  close,

  /// Closing `}}}` (unescaped).
  closeUnescaped,

  /// Identifier (variable name, helper name).
  id,

  /// String literal (single or double quoted).
  string,

  /// Number literal.
  number,

  /// Boolean literal (true/false).
  boolean,

  /// `=` for hash arguments.
  equals,

  /// `.` path separator.
  dot,

  /// `..` parent context reference.
  dotDot,

  /// `/` path separator (for paths like ../prefix).
  slash,

  /// `@` data variable prefix.
  data,

  /// `(` for subexpressions.
  openParen,

  /// `)` for subexpressions.
  closeParen,

  /// `~` for whitespace control.
  stripLeft,

  /// `~` for whitespace control (right side).
  stripRight,

  /// `as` keyword for block params.
  asKeyword,

  /// `|` for block params delimiter.
  pipe,

  /// End of input.
  eof,
}

/// A token produced by the Handlebars lexer.
class Token {
  /// Creates a new token.
  const Token(this.type, this.value, this.line, this.column);

  /// The token type.
  final TokenType type;

  /// The token value (for identifiers, strings, numbers).
  final String value;

  /// The line number (1-based).
  final int line;

  /// The column number (1-based).
  final int column;

  @override
  String toString() => "Token($type, '$value', $line:$column)";
}

/// Lexer for Handlebars templates.
///
/// Converts a template string into a stream of tokens. The lexer operates in
/// two modes: text mode (outside `{{`) and expression mode (inside `{{}}`).
///
/// ## Tokenization Flow
///
/// ```
/// ┌──────────────────────────────────────────────────────────────────┐
/// │                      LEXER STATE MACHINE                          │
/// └──────────────────────────────────────────────────────────────────┘
///
///                           ┌─────────────┐
///                    start──▶│  TEXT MODE  │◀──────────────┐
///                           └──────┬──────┘               │
///                                  │                      │
///                           found "{{"                    │
///                                  │                 found "}}"
///                                  ▼                      │
///                    ┌─────────────────────────┐          │
///                    │    EXPRESSION MODE      │──────────┘
///                    │                         │
///                    │  Parse: identifiers,    │
///                    │  strings, numbers,      │
///                    │  hash args, paths       │
///                    └─────────────────────────┘
/// ```
///
/// ## Opening Delimiters
///
/// The lexer recognizes these opening patterns (checked in order):
///
/// | Pattern | Token Type     | Meaning                    |
/// |---------|----------------|----------------------------|
/// | `{{{`   | openUnescaped  | Raw output (no escaping)   |
/// | `{{!--` | openComment    | Long comment (until `--}}`) |
/// | `{{!`   | openComment    | Short comment (until `}}`) |
/// | `{{#`   | openBlock      | Block helper start         |
/// | `{{/`   | openEndBlock   | Block helper end           |
/// | `{{>`   | openPartial    | Partial inclusion          |
/// | `{{^`   | openInverse    | Inverse block              |
/// | `{{`    | open           | Regular expression         |
///
/// ## Example
///
/// ```dart
/// final lexer = Lexer("Hello {{name}}!");
/// final tokens = lexer.tokenize();
/// // tokens: [text:"Hello ", open:"{{", id:"name", close:"}}", text:"!", eof:""]
/// ```
class Lexer {
  /// Creates a lexer for the given template source.
  Lexer(this.source);

  /// The template source string.
  final String source;

  int _pos = 0;
  int _line = 1;
  int _column = 1;

  // Fields for raw block handling (internal, used by parser)
  /// internal
  String? rawBlockName;

  /// internal
  String? rawBlockContent;

  /// Current position in the source.
  int get position => _pos;

  /// Reads the next token from the source.
  Token nextToken() => _nextToken();

  /// Tokenizes the entire source into a list of tokens.
  List<Token> tokenize() {
    final tokens = <Token>[];

    while (_pos < source.length) {
      final token = _nextToken();
      tokens.add(token);

      // If this was a raw block, add the content token
      if (token.type == TokenType.openRawBlock && rawBlockContent != null) {
        tokens.add(Token(TokenType.text, rawBlockContent!, token.line, token.column));
        rawBlockName = null;
        rawBlockContent = null;
      }

      if (token.type == TokenType.eof) break;
    }

    if (tokens.isEmpty || tokens.last.type != TokenType.eof) {
      tokens.add(Token(TokenType.eof, "", _line, _column));
    }

    return tokens;
  }

  Token _nextToken() {
    if (_pos >= source.length) {
      return Token(TokenType.eof, "", _line, _column);
    }

    // Check for handlebars opening
    if (_lookingAt("{{")) {
      return _readHandlebarsOpen();
    }

    // Read text until next handlebars or end
    return _readText();
  }

  Token _readText() {
    final startLine = _line;
    final startColumn = _column;
    final buffer = StringBuffer();

    while (_pos < source.length) {
      // Check for escape sequence: \{{ outputs literal {{
      // Check if current char is backslash followed by {{
      // TODO(user): Escape sequence detection has caching issues with Bazel - needs investigation.
      // See https://github.com/google/dotprompt/issues/999
      if (_pos <= source.length - 3 &&
          source.codeUnitAt(_pos) == 92 &&
          source.codeUnitAt(_pos + 1) == 123 &&
          source.codeUnitAt(_pos + 2) == 123) {
        // Skip the backslash, output literal {{
        _advance();
        buffer.write("{{");
        _advance(2);
        continue;
      }

      // Check for handlebars opening
      if (_lookingAt("{{")) {
        break;
      }

      final char = source[_pos];
      buffer.write(char);
      _advance();
    }

    return Token(TokenType.text, buffer.toString(), startLine, startColumn);
  }

  Token _readHandlebarsOpen() {
    final startLine = _line;
    final startColumn = _column;

    // Check for various opening patterns
    // Note: Order matters - check longer patterns first

    // Raw block {{{{ - must be checked before {{{ (unescaped)
    // For raw blocks, we need to read the name, then collect everything
    // until the closing {{{{/name}}}} as literal content
    if (_lookingAt("{{{{")) {
      _advance(4);
      _skipWhitespace();

      // Read the block name
      final name = _readIdentifier();

      // Skip optional whitespace and expect }}}}
      _skipWhitespace();
      if (_lookingAt("}}}}")) {
        _advance(4);
      }

      // Now read everything until {{{{/name}}}}
      final endTag = "{{{{/$name}}}}";
      final contentBuffer = StringBuffer();

      while (_pos < source.length) {
        if (_lookingAt(endTag)) {
          _advance(endTag.length);
          break;
        }
        if (source[_pos] == "\n") {
          _line++;
          _column = 1;
        } else {
          _column++;
        }
        contentBuffer.write(source[_pos]);
        _pos++;
      }

      // Store raw block content for the parser to use
      rawBlockName = name;
      rawBlockContent = contentBuffer.toString();
      return Token(TokenType.openRawBlock, name, startLine, startColumn);
    }

    // Unescaped {{{
    if (_lookingAt("{{{")) {
      _advance(3);
      return Token(TokenType.openUnescaped, "{{{", startLine, startColumn);
    }

    // Long comment with whitespace control {{~!--
    if (_lookingAt("{{~!--")) {
      _advance(6);
      final commentStart = _pos;
      while (_pos < source.length && !_lookingAt("--~}}") && !_lookingAt("--}}")) {
        _advance();
      }
      final comment = source.substring(commentStart, _pos);
      final hasRightStrip = _lookingAt("--~}}");
      if (hasRightStrip) {
        _advance(5);
      } else if (_lookingAt("--}}")) {
        _advance(4);
      }
      return Token(TokenType.openComment, "~$comment${hasRightStrip ? '~' : ''}", startLine, startColumn);
    }

    // Long comment {{!--
    if (_lookingAt("{{!--")) {
      _advance(5);
      final commentStart = _pos;
      while (_pos < source.length && !_lookingAt("--~}}") && !_lookingAt("--}}")) {
        _advance();
      }
      final comment = source.substring(commentStart, _pos);
      final hasRightStrip = _lookingAt("--~}}");
      if (hasRightStrip) {
        _advance(5);
      } else if (_lookingAt("--}}")) {
        _advance(4);
      }
      return Token(TokenType.openComment, hasRightStrip ? "$comment~" : comment, startLine, startColumn);
    }

    // Short comment with whitespace control {{~!
    if (_lookingAt("{{~!")) {
      _advance(4);
      final commentStart = _pos;
      while (_pos < source.length && !_lookingAt("~}}") && !_lookingAt("}}")) {
        _advance();
      }
      final comment = source.substring(commentStart, _pos);
      final hasRightStrip = _lookingAt("~}}");
      if (hasRightStrip) {
        _advance(3);
      } else if (_lookingAt("}}")) {
        _advance(2);
      }
      return Token(TokenType.openComment, "~$comment${hasRightStrip ? '~' : ''}", startLine, startColumn);
    }

    // Short comment {{!
    if (_lookingAt("{{!")) {
      _advance(3);
      final commentStart = _pos;
      while (_pos < source.length && !_lookingAt("~}}") && !_lookingAt("}}")) {
        _advance();
      }
      final comment = source.substring(commentStart, _pos);
      final hasRightStrip = _lookingAt("~}}");
      if (hasRightStrip) {
        _advance(3);
      } else if (_lookingAt("}}")) {
        _advance(2);
      }
      return Token(TokenType.openComment, hasRightStrip ? "$comment~" : comment, startLine, startColumn);
    }

    // Block with left strip {{~#
    if (_lookingAt("{{~#")) {
      _advance(4);
      return Token(TokenType.openBlock, "{{~#", startLine, startColumn);
    }

    // Partial block {{#> - must be checked before {{#*
    if (_lookingAt("{{#>")) {
      _advance(4);
      return Token(TokenType.openPartialBlock, "{{#>", startLine, startColumn);
    }

    // Inline partial {{#* - must be checked before {{#
    if (_lookingAt("{{#*")) {
      _advance(4);
      return Token(TokenType.openInlinePartial, "{{#*", startLine, startColumn);
    }

    // Block {{#
    if (_lookingAt("{{#")) {
      _advance(3);
      return Token(TokenType.openBlock, "{{#", startLine, startColumn);
    }

    // End block with left strip {{~/
    if (_lookingAt("{{~/")) {
      _advance(4);
      return Token(TokenType.openEndBlock, "{{~/", startLine, startColumn);
    }

    // End block {{/
    if (_lookingAt("{{/")) {
      _advance(3);
      return Token(TokenType.openEndBlock, "{{/", startLine, startColumn);
    }

    // Partial with left strip {{~>
    if (_lookingAt("{{~>")) {
      _advance(4);
      return Token(TokenType.openPartial, "{{~>", startLine, startColumn);
    }

    // Partial {{>
    if (_lookingAt("{{>")) {
      _advance(3);
      return Token(TokenType.openPartial, "{{>", startLine, startColumn);
    }

    // Inverse with left strip {{~^
    if (_lookingAt("{{~^")) {
      _advance(4);
      return Token(TokenType.openInverse, "{{~^", startLine, startColumn);
    }

    // Inverse {{^
    if (_lookingAt("{{^")) {
      _advance(3);
      return Token(TokenType.openInverse, "{{^", startLine, startColumn);
    }

    // Ampersand unescaped with left strip {{~&
    if (_lookingAt("{{~&")) {
      _advance(4);
      return Token(TokenType.openUnescaped, "{{~&", startLine, startColumn);
    }

    // Ampersand unescaped {{&
    if (_lookingAt("{{&")) {
      _advance(3);
      return Token(TokenType.openUnescaped, "{{&", startLine, startColumn);
    }

    // Regular open with left strip {{~
    if (_lookingAt("{{~")) {
      _advance(3);
      return Token(TokenType.open, "{{~", startLine, startColumn);
    }

    // Regular open {{
    _advance(2);
    return Token(TokenType.open, "{{", startLine, startColumn);
  }

  /// Reads tokens inside a handlebars expression.
  List<Token> readExpression() {
    final tokens = <Token>[];

    _skipWhitespace();

    while (_pos < source.length) {
      _skipWhitespace();

      // Raw block close }}}} - must be checked before }}}
      if (_lookingAt("}}}}")) {
        _advance(4);
        tokens.add(Token(TokenType.closeRawBlock, "}}}}", _line, _column));
        break;
      }

      // Unescaped close with right strip ~}}}
      if (_lookingAt("~}}}")) {
        _advance(4);
        tokens.add(Token(TokenType.closeUnescaped, "~}}}", _line, _column));
        break;
      }

      // Unescaped close }}}
      if (_lookingAt("}}}")) {
        _advance(3);
        tokens.add(Token(TokenType.closeUnescaped, "}}}", _line, _column));
        break;
      }

      // Regular close with right strip ~}}
      if (_lookingAt("~}}")) {
        _advance(3);
        tokens.add(Token(TokenType.close, "~}}", _line, _column));
        break;
      }

      // Regular close }}
      if (_lookingAt("}}")) {
        _advance(2);
        tokens.add(Token(TokenType.close, "}}", _line, _column));
        break;
      }

      final token = _readExpressionToken();
      if (token != null) {
        tokens.add(token);
      } else {
        break;
      }
    }

    return tokens;
  }

  Token? _readExpressionToken() {
    _skipWhitespace();

    if (_pos >= source.length) return null;

    final startLine = _line;
    final startColumn = _column;
    final char = source[_pos];

    // String literal
    if (char == '"' || char == "'") {
      return _readString(char);
    }

    // Number
    if (_isDigit(char) || (char == "-" && _pos + 1 < source.length && _isDigit(source[_pos + 1]))) {
      return _readNumber();
    }

    // Open parenthesis for subexpressions
    if (char == "(") {
      _advance();
      return Token(TokenType.openParen, "(", startLine, startColumn);
    }

    // Close parenthesis for subexpressions
    if (char == ")") {
      _advance();
      return Token(TokenType.closeParen, ")", startLine, startColumn);
    }

    // Equals
    if (char == "=") {
      _advance();
      return Token(TokenType.equals, "=", startLine, startColumn);
    }

    // Data variable (@root, @index, etc.)
    if (char == "@") {
      _advance();
      final id = _readIdentifier();
      return Token(TokenType.data, "@$id", startLine, startColumn);
    }

    // Dot or dotdot
    if (char == ".") {
      if (_lookingAt("..")) {
        _advance(2);
        return Token(TokenType.dotDot, "..", startLine, startColumn);
      }
      // Check if it's part of a path or standalone
      if (_pos + 1 < source.length && _isIdContinue(source[_pos + 1])) {
        // It's a path separator, skip and continue
        _advance();
        return Token(TokenType.dot, ".", startLine, startColumn);
      }
      // Standalone dot (this context)
      _advance();
      return Token(TokenType.dot, ".", startLine, startColumn);
    }

    // Slash (path separator, used after .. like ../prefix)
    if (char == "/") {
      _advance();
      return Token(TokenType.slash, "/", startLine, startColumn);
    }

    // Pipe (for block params: as |item index|)
    if (char == "|") {
      _advance();
      return Token(TokenType.pipe, "|", startLine, startColumn);
    }

    // Identifier (including reserved words)
    if (_isIdStart(char)) {
      final id = _readIdentifier();
      // Check for boolean literals
      if (id == "true" || id == "false") {
        return Token(TokenType.boolean, id, startLine, startColumn);
      }
      // Check for 'as' keyword (used for block params)
      if (id == "as") {
        return Token(TokenType.asKeyword, id, startLine, startColumn);
      }
      return Token(TokenType.id, id, startLine, startColumn);
    }

    // Unknown character - skip
    _advance();
    return null;
  }

  Token _readString(String quote) {
    final startLine = _line;
    final startColumn = _column;
    _advance(); // Skip opening quote

    final buffer = StringBuffer();
    while (_pos < source.length && source[_pos] != quote) {
      if (source[_pos] == r"\" && _pos + 1 < source.length) {
        _advance();
        // Handle escape sequences
        switch (source[_pos]) {
          case "n":
            buffer.write("\n");
          case "t":
            buffer.write("\t");
          case "r":
            buffer.write("\r");
          default:
            buffer.write(source[_pos]);
        }
      } else {
        buffer.write(source[_pos]);
      }
      _advance();
    }

    if (_pos < source.length) {
      _advance(); // Skip closing quote
    }

    return Token(TokenType.string, buffer.toString(), startLine, startColumn);
  }

  Token _readNumber() {
    final startLine = _line;
    final startColumn = _column;
    final buffer = StringBuffer();

    if (source[_pos] == "-") {
      buffer.write("-");
      _advance();
    }

    while (_pos < source.length && (_isDigit(source[_pos]) || source[_pos] == ".")) {
      buffer.write(source[_pos]);
      _advance();
    }

    return Token(TokenType.number, buffer.toString(), startLine, startColumn);
  }

  String _readIdentifier() {
    final buffer = StringBuffer();
    while (_pos < source.length && _isIdContinue(source[_pos])) {
      buffer.write(source[_pos]);
      _advance();
    }
    return buffer.toString();
  }

  void _skipWhitespace() {
    while (_pos < source.length && _isWhitespace(source[_pos])) {
      _advance();
    }
  }

  bool _lookingAt(String pattern) {
    if (_pos + pattern.length > source.length) return false;
    return source.substring(_pos, _pos + pattern.length) == pattern;
  }

  void _advance([int count = 1]) {
    for (var i = 0; i < count && _pos < source.length; i++) {
      if (source[_pos] == "\n") {
        _line++;
        _column = 1;
      } else {
        _column++;
      }
      _pos++;
    }
  }

  bool _isWhitespace(String char) => char == " " || char == "\t" || char == "\n" || char == "\r";

  bool _isDigit(String char) => char.codeUnitAt(0) >= 48 && char.codeUnitAt(0) <= 57;

  bool _isIdStart(String char) {
    final code = char.codeUnitAt(0);
    return (code >= 65 && code <= 90) || // A-Z
        (code >= 97 && code <= 122) || // a-z
        char == "_" ||
        char == r"$";
  }

  bool _isIdContinue(String char) => _isIdStart(char) || _isDigit(char) || char == "-" || char == "/" || char == ".";
}
