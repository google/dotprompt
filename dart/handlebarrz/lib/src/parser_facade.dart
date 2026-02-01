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

/// Unified parser facade for Handlebars templates.
///
/// This module provides a single entry point for parsing Handlebars templates,
/// with the ability to switch between the hand-written parser (default) and
/// the ANTLR4-generated parser.
///
/// ## Usage
///
/// ```dart
/// // Using the default parser
/// final ast = ParserFacade.parse('Hello {{name}}!');
///
/// // Explicitly using ANTLR parser
/// final ast = ParserFacade.parse('Hello {{name}}!', useAntlr: true);
///
/// // Using the hand-written parser
/// final ast = ParserFacade.parse('Hello {{name}}!', useAntlr: false);
/// ```
///
/// ## Parser Comparison
///
/// | Feature | Hand-written | ANTLR4 |
/// |---------|-------------|--------|
/// | Speed | Faster | Slower |
/// | Spec compliance | Manual | Automatic from grammar |
/// | Error messages | Custom | Generated |
/// | Maintenance | Manual | Grammar-based |
library;

import "antlr_parser.dart";
import "parser.dart"
    as hand_written
    show
        AstNode,
        BlockNode,
        CommentNode,
        MustacheNode,
        Parser,
        PartialBlockNode,
        PartialNode,
        ProgramNode,
        RawBlockNode,
        TextNode;

/// Parser implementation type.
enum ParserType {
  /// Hand-written recursive descent parser.
  handwritten,

  /// ANTLR4-generated parser.
  antlr,
}

/// Unified facade for parsing Handlebars templates.
///
/// Provides access to both the hand-written and ANTLR-generated parsers
/// through a consistent interface.
class ParserFacade {
  ParserFacade._();

  /// The default parser type to use.
  ///
  /// Can be changed globally to switch all parsing to a different
  /// implementation.
  static ParserType defaultParser = ParserType.handwritten;

  /// Parse a Handlebars template and return the AST.
  ///
  /// By default, uses [defaultParser]. Override with [useAntlr] parameter:
  /// - `true`: Force ANTLR parser
  /// - `false`: Force hand-written parser
  /// - `null`: Use [defaultParser]
  ///
  /// Throws [FormatException] if the template has syntax errors.
  static hand_written.ProgramNode parse(String source, {bool? useAntlr}) {
    final shouldUseAntlr = useAntlr ?? (defaultParser == ParserType.antlr);

    if (shouldUseAntlr) {
      return AntlrParser.parse(source);
    }
    return hand_written.Parser.parse(source);
  }

  /// Parse using both parsers and compare results.
  ///
  /// Useful for testing parser parity. Returns tuple of
  /// (handwritten result, antlr result, are they equivalent).
  ///
  /// Note: AST comparison is done by rendering back to string and comparing,
  /// which may not catch all differences.
  static ({hand_written.ProgramNode handwritten, hand_written.ProgramNode antlr, bool equivalent}) parseAndCompare(
    String source,
  ) {
    final handwritten = hand_written.Parser.parse(source);
    final antlr = AntlrParser.parse(source);

    // Simple equivalence check by comparing string representations
    // A more thorough check would need AST comparison
    final equivalent = _compareAst(handwritten, antlr);

    return (handwritten: handwritten, antlr: antlr, equivalent: equivalent);
  }

  /// Compare two ASTs for structural equivalence.
  static bool _compareAst(hand_written.ProgramNode a, hand_written.ProgramNode b) {
    if (a.body.length != b.body.length) return false;

    for (var i = 0; i < a.body.length; i++) {
      if (!_compareNode(a.body[i], b.body[i])) {
        return false;
      }
    }
    return true;
  }

  /// Compare two AST nodes.
  static bool _compareNode(hand_written.AstNode a, hand_written.AstNode b) {
    if (a.runtimeType != b.runtimeType) return false;

    switch (a) {
      case hand_written.TextNode():
        return (b as hand_written.TextNode).text == a.text;
      case hand_written.CommentNode():
        // Comments may have slight formatting differences
        return (b as hand_written.CommentNode).text.trim() == a.text.trim();
      case hand_written.MustacheNode():
        final bm = b as hand_written.MustacheNode;
        return a.path.path == bm.path.path && a.escaped == bm.escaped && a.params.length == bm.params.length;
      case hand_written.BlockNode():
        final bb = b as hand_written.BlockNode;
        if (a.path.path != bb.path.path || a.isInverse != bb.isInverse) {
          return false;
        }
        if (!_compareAst(a.program, bb.program)) {
          return false;
        }
        // Compare inverse programs
        if (a.inverse == null && bb.inverse == null) {
          return true;
        }
        if (a.inverse == null || bb.inverse == null) {
          return false;
        }
        return _compareAst(a.inverse!, bb.inverse!);
      case hand_written.PartialNode():
        return (b as hand_written.PartialNode).name == a.name;
      case hand_written.PartialBlockNode():
        return (b as hand_written.PartialBlockNode).name == a.name;
      case hand_written.RawBlockNode():
        final br = b as hand_written.RawBlockNode;
        return a.name == br.name && a.content == br.content;
      default:
        return true; // Assume equivalent for unknown types
    }
  }
}
