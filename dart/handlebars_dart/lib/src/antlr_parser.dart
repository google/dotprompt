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

/// AST Builder Visitor for the ANTLR4-generated Handlebars parser.
///
/// This visitor traverses the ANTLR parse tree and builds the same AST nodes
/// used by the hand-written parser, allowing both parsers to share the same
/// runtime and evaluation logic.
library;

import "package:antlr4/antlr4.dart";

import "antlr/HandlebarsLexer.dart";
import "antlr/HandlebarsParser.dart";
import "antlr/HandlebarsParserBaseVisitor.dart";
import "parser.dart";

/// Visitor that builds AST nodes from the ANTLR parse tree.
///
/// Usage:
/// ```dart
/// final parser = AntlrParser();
/// final ast = parser.parse('Hello {{name}}!');
/// ```
class AstBuilderVisitor extends HandlebarsParserBaseVisitor<AstNode?> {
  /// Visit the root and return the program.
  @override
  AstNode? visitRoot(RootContext ctx) => visitProgram(ctx.program()!);

  /// Visit a program (sequence of statements).
  @override
  AstNode? visitProgram(ProgramContext ctx) {
    final body = <AstNode>[];
    for (final stmt in ctx.statements()) {
      final node = visitStatement(stmt);
      if (node != null) {
        body.add(node);
      }
    }
    return ProgramNode(body);
  }

  /// Visit a statement (dispatch to appropriate type).
  @override
  AstNode? visitStatement(StatementContext ctx) {
    if (ctx.mustache() != null) {
      return visitMustache(ctx.mustache()!);
    }
    if (ctx.block() != null) {
      return visitBlock(ctx.block()!);
    }
    if (ctx.rawBlock() != null) {
      return visitRawBlock(ctx.rawBlock()!);
    }
    if (ctx.partial() != null) {
      return visitPartial(ctx.partial()!);
    }
    if (ctx.partialBlock() != null) {
      return visitPartialBlock(ctx.partialBlock()!);
    }
    if (ctx.content() != null) {
      return visitContent(ctx.content()!);
    }
    if (ctx.comment() != null) {
      return visitComment(ctx.comment()!);
    }
    // Note: inverse tokens ({{else}}, {{^}}) are now only handled within blocks
    // as part of inverseChain, not as standalone statements.
    return null;
  }

  /// Visit content (plain text).
  @override
  AstNode? visitContent(ContentContext ctx) => TextNode(ctx.text);

  /// Visit a comment.
  @override
  AstNode? visitComment(CommentContext ctx) {
    var text = ctx.text;
    // Strip {{! and }} or {{!-- and --}}
    if (text.startsWith("{{!--") && text.endsWith("--}}")) {
      text = text.substring(5, text.length - 4);
    } else if (text.startsWith("{{!") && text.endsWith("}}")) {
      text = text.substring(3, text.length - 2);
    }
    // Strip whitespace control markers
    text = text.replaceAll(RegExp(r"^~|~$"), "");
    return CommentNode(text.trim());
  }

  /// Visit a mustache expression.
  @override
  AstNode? visitMustache(MustacheContext ctx) {
    final helperName = ctx.helperName();
    if (helperName == null) return null;

    final path = _buildPath(helperName);
    final params = _buildParams(ctx.params());
    final hash = _buildHash(ctx.hash());

    // Check if escaped (double braces) or unescaped (triple braces)
    final escaped = ctx.OPEN_UNESCAPED() == null;

    // Check for whitespace control
    final openToken = ctx.OPEN() ?? ctx.OPEN_UNESCAPED();
    final closeToken = ctx.CLOSE() ?? ctx.CLOSE_UNESCAPED();
    final openStrip = openToken?.text?.contains("~") ?? false;
    final closeStrip = closeToken?.text?.contains("~") ?? false;

    return MustacheNode(
      path: path,
      params: params,
      hash: hash,
      escaped: escaped,
      openStrip: openStrip,
      closeStrip: closeStrip,
    );
  }

  /// Visit a block helper.
  @override
  AstNode? visitBlock(BlockContext ctx) {
    // Handle openBlock variant
    if (ctx.openBlock() != null) {
      final openBlock = ctx.openBlock()!;
      final helperName = openBlock.helperName();
      if (helperName == null) return null;

      final path = _buildPath(helperName);
      final params = _buildParams(openBlock.params());
      final hash = _buildHash(openBlock.hash());
      final blockParams = _buildBlockParams(openBlock.blockParams());

      final program = visitProgram(ctx.program()!) as ProgramNode?;
      final inverseChain = ctx.inverseChain();
      final inverse = inverseChain != null ? _buildInverseProgram(inverseChain) : null;

      return BlockNode(
        path: path,
        params: params,
        hash: hash,
        program: program ?? const ProgramNode([]),
        inverse: inverse,
        isInverse: false,
        blockParams: blockParams,
        isInline: ctx.start?.line == ctx.stop?.line,
      );
    }

    // Handle openInverse variant ({{^if}})
    if (ctx.openInverse() != null) {
      final openInverse = ctx.openInverse()!;
      final helperName = openInverse.helperName();
      if (helperName == null) return null;

      final path = _buildPath(helperName);
      final params = _buildParams(openInverse.params());
      final hash = _buildHash(openInverse.hash());
      final blockParams = _buildBlockParams(openInverse.blockParams());

      final program = visitProgram(ctx.program()!) as ProgramNode?;
      final inverseAndProgram = ctx.inverseAndProgram();
      final inverse = inverseAndProgram != null ? visitProgram(inverseAndProgram.program()!) as ProgramNode? : null;

      return BlockNode(
        path: path,
        params: params,
        hash: hash,
        program: program ?? const ProgramNode([]),
        inverse: inverse,
        isInverse: true,
        blockParams: blockParams,
        isInline: ctx.start?.line == ctx.stop?.line,
      );
    }

    return null;
  }

  /// Visit a raw block.
  @override
  AstNode? visitRawBlock(RawBlockContext ctx) {
    final openRaw = ctx.openRawBlock();
    if (openRaw == null) return null;

    final helperName = openRaw.helperName();
    if (helperName == null) return null;

    // Get the raw content from the program
    final program = ctx.program();
    final content = program?.text ?? "";

    return RawBlockNode(name: _getHelperNameText(helperName), content: content);
  }

  /// Visit a partial.
  @override
  AstNode? visitPartial(PartialContext ctx) {
    final partialName = ctx.partialName();
    if (partialName == null) return null;

    final name = _getPartialNameText(partialName);
    final params = _buildParams(ctx.params());
    final hash = _buildHash(ctx.hash());

    return PartialNode(name: name, context: params.isNotEmpty ? params.first : null, hash: hash);
  }

  /// Visit a partial block.
  @override
  AstNode? visitPartialBlock(PartialBlockContext ctx) {
    final openPartialBlock = ctx.openPartialBlock();
    if (openPartialBlock == null) return null;

    final partialName = openPartialBlock.partialName();
    if (partialName == null) return null;

    final name = _getPartialNameText(partialName);
    final params = _buildParams(openPartialBlock.params());
    final hash = _buildHash(openPartialBlock.hash());
    final program = visitProgram(ctx.program()!) as ProgramNode?;

    return PartialBlockNode(
      name: name,
      context: params.isNotEmpty ? params.first : null,
      hash: hash,
      program: program ?? const ProgramNode([]),
    );
  }

  // =========================================================================
  // Helper methods
  // =========================================================================

  /// Build a PathNode from a helperName context.
  PathNode _buildPath(HelperNameContext ctx) {
    // Check for data variable (@root, @index, etc.)
    if (ctx.dataName() != null) {
      final dataName = ctx.dataName()!;
      final segments = dataName.pathSegments();
      final parts = _extractPathParts(segments);
      return PathNode(parts, isData: true);
    }

    // Check for path
    if (ctx.path() != null) {
      final path = ctx.path()!;
      final segments = path.pathSegments();
      final parts = _extractPathParts(segments);
      return PathNode(parts);
    }

    // Check for string literal (used as path)
    if (ctx.STRING() != null) {
      final text = ctx.STRING()!.text!;
      // Remove quotes
      final value = text.substring(1, text.length - 1);
      return PathNode([value]);
    }

    // Fallback to the text content
    return PathNode([ctx.text]);
  }

  /// Extract path parts from pathSegments context.
  List<String> _extractPathParts(PathSegmentsContext? ctx) {
    if (ctx == null) return [];

    final parts = <String>[];
    for (final id in ctx.IDs()) {
      var text = id.text!;
      // Handle bracket notation [foo]
      if (text.startsWith("[") && text.endsWith("]")) {
        text = text.substring(1, text.length - 1);
      }
      parts.add(text);
    }
    return parts;
  }

  /// Build params list from param contexts.
  List<ExpressionNode> _buildParams(List<ParamContext> params) =>
      params.map(_buildParam).whereType<ExpressionNode>().toList();

  /// Build a single param expression.
  ExpressionNode? _buildParam(ParamContext ctx) {
    // Helper name (path or literal)
    if (ctx.helperName() != null) {
      return _buildExpression(ctx.helperName()!);
    }
    // Subexpression
    if (ctx.sexpr() != null) {
      return _buildSubExpression(ctx.sexpr()!);
    }
    return null;
  }

  /// Build an expression from a helperName context.
  ExpressionNode _buildExpression(HelperNameContext ctx) {
    // String literal
    if (ctx.STRING() != null) {
      var text = ctx.STRING()!.text!;
      // Remove quotes and unescape
      text = text.substring(1, text.length - 1);
      text = text.replaceAll(r'\"', '"').replaceAll(r"\'", "'");
      return StringNode(text);
    }

    // Number literal
    if (ctx.NUMBER() != null) {
      final text = ctx.NUMBER()!.text!;
      final value = num.parse(text);
      return NumberNode(value);
    }

    // Boolean literal
    if (ctx.BOOLEAN() != null) {
      return BooleanNode(value: ctx.BOOLEAN()!.text == "true");
    }

    // Undefined/null
    if (ctx.UNDEFINED() != null) {
      return const PathNode(["undefined"]);
    }
    if (ctx.NULL_LIT() != null) {
      return const PathNode(["null"]);
    }

    // Path or data variable
    return _buildPath(ctx);
  }

  /// Build a subexpression.
  SubExpressionNode _buildSubExpression(SexprContext ctx) {
    final helperName = ctx.helperName();
    final path = helperName != null ? _buildPath(helperName) : const PathNode([]);
    final params = _buildParams(ctx.params());
    final hash = _buildHash(ctx.hash());

    return SubExpressionNode(path: path, params: params, hash: hash);
  }

  /// Build hash map from hash context.
  Map<String, ExpressionNode> _buildHash(HashContext? ctx) {
    if (ctx == null) return {};

    final hash = <String, ExpressionNode>{};
    for (final segment in ctx.hashSegments()) {
      final key = segment.ID()?.text;
      if (key != null && segment.param() != null) {
        final value = _buildParam(segment.param()!);
        if (value != null) {
          hash[key] = value;
        }
      }
    }
    return hash;
  }

  /// Build block params list.
  List<String> _buildBlockParams(BlockParamsContext? ctx) {
    if (ctx == null) return [];
    return ctx.IDs().map((id) => id.text!).toList();
  }

  /// Build inverse program from inverseChain.
  ///
  /// The `inverseChain` rule has two alternatives:
  /// 1. `openInverseChain program inverseChain?` - for {{else if ...}}
  /// 2. `inverseAndProgram` - for simple {{else}}
  ProgramNode? _buildInverseProgram(InverseChainContext ctx) {
    // Alternative 2: Check for inverseAndProgram (simple {{else}})
    final inverseAndProgram = ctx.inverseAndProgram();
    if (inverseAndProgram != null) {
      final program = inverseAndProgram.program();
      if (program != null) {
        return visitProgram(program) as ProgramNode?;
      }
      // If we have inverseAndProgram but no program, return empty program
      return const ProgramNode([]);
    }

    // Alternative 1: Check for openInverseChain ({{else if}})
    final openInverseChain = ctx.openInverseChain();
    if (openInverseChain != null) {
      final program = ctx.program();
      if (program == null) return null;

      final innerProgram = visitProgram(program) as ProgramNode?;
      final helperName = openInverseChain.helperName();
      if (helperName == null) return null;

      final path = _buildPath(helperName);
      final params = _buildParams(openInverseChain.params());
      final hash = _buildHash(openInverseChain.hash());
      final blockParams = _buildBlockParams(openInverseChain.blockParams());

      // Get nested inverse (for chained else-if-else)
      final nestedInverseChain = ctx.inverseChain();
      final nestedInverse = nestedInverseChain != null ? _buildInverseProgram(nestedInverseChain) : null;

      final elseIfBlock = BlockNode(
        path: path,
        params: params,
        hash: hash,
        program: innerProgram ?? const ProgramNode([]),
        inverse: nestedInverse,
        isInverse: false,
        blockParams: blockParams,
      );

      return ProgramNode([elseIfBlock]);
    }

    return null;
  }

  /// Get the text of a helper name.
  String _getHelperNameText(HelperNameContext ctx) {
    if (ctx.path() != null) {
      return ctx.path()!.text;
    }
    if (ctx.dataName() != null) {
      return ctx.dataName()!.text;
    }
    if (ctx.STRING() != null) {
      final text = ctx.STRING()!.text!;
      return text.substring(1, text.length - 1);
    }
    return ctx.text;
  }

  /// Get the text of a partial name.
  String _getPartialNameText(PartialNameContext ctx) {
    if (ctx.helperName() != null) {
      return _getHelperNameText(ctx.helperName()!);
    }
    if (ctx.sexpr() != null) {
      // Dynamic partial name
      return ctx.sexpr()!.text;
    }
    return ctx.text;
  }
}

/// ANTLR-based Handlebars parser.
///
/// Provides the same interface as the hand-written parser but uses ANTLR4
/// for parsing. This ensures spec compliance with the official Handlebars
/// grammar.
class AntlrParser {
  AntlrParser._();

  /// Parse a Handlebars template and return the AST.
  ///
  /// Throws [FormatException] if the template has syntax errors.
  static ProgramNode parse(String source) {
    // Create input stream and lexer
    final input = InputStream.fromString(source);
    final lexer = HandlebarsLexer(input);
    final tokens = CommonTokenStream(lexer);

    // Create parser
    final parser = HandlebarsParser(tokens);

    // Add error listener
    final errors = <String>[];
    parser
      ..removeErrorListeners()
      ..addErrorListener(_ErrorCollector(errors));

    // Parse
    final tree = parser.root();

    // Check for errors
    if (errors.isNotEmpty) {
      throw FormatException('Handlebars syntax errors:\n${errors.join('\n')}');
    }

    // Build AST
    final visitor = AstBuilderVisitor();
    final ast = visitor.visitRoot(tree);

    return ast as ProgramNode? ?? const ProgramNode([]);
  }
}

/// Error collector for ANTLR parsing errors.
class _ErrorCollector extends BaseErrorListener {
  _ErrorCollector(this.errors);

  final List<String> errors;

  @override
  void syntaxError(
    Recognizer<ATNSimulator> recognizer,
    Object? offendingSymbol,
    int? line,
    int charPositionInLine,
    String msg,
    RecognitionException? e,
  ) {
    errors.add('Line ${line ?? '?'}:$charPositionInLine - $msg');
  }
}
