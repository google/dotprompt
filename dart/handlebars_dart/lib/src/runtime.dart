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

import "options.dart";
import "parser.dart";
import "safe_string.dart";

/// Exception thrown in strict mode when a variable or helper is undefined.
///
/// Strict mode helps catch template errors early by failing fast rather than
/// silently outputting empty strings for missing values.
class StrictModeException implements Exception {
  /// Creates a new strict mode exception.
  const StrictModeException(this.message, {this.path});

  /// The error message.
  final String message;

  /// The path that was undefined (if applicable).
  final String? path;

  @override
  String toString() => "StrictModeException: $message";
}

/// Renders a Handlebars AST with the given context and helpers.
///
/// The runtime traverses the AST and produces output by evaluating each node
/// in the context of the provided data. It handles variable lookup, helper
/// invocation, block execution, and HTML escaping.
///
/// ## Rendering Flow
///
/// ```
/// ┌──────────────────────────────────────────────────────────────────┐
/// │                      RUNTIME RENDERING FLOW                       │
/// └──────────────────────────────────────────────────────────────────┘
///
///   render(ast, context)
///        │
///        ▼
///   ┌─────────────────┐
///   │  For each node  │◀───────────────────────┐
///   │  in program     │                        │
///   └────────┬────────┘                        │
///            │                                 │
///            ├── TextNode ──▶ output text      │
///            │                                 │
///            ├── MustacheNode ──────┐          │
///            │   ┌──────────────────▼────────┐ │
///            │   │ 1. Resolve path in context│ │
///            │   │ 2. Check if helper exists │ │
///            │   │ 3. Call helper OR output  │ │
///            │   │ 4. Escape HTML if needed  │ │
///            │   └───────────────────────────┘ │
///            │                                 │
///            ├── BlockNode ────────┐           │
///            │   ┌─────────────────▼─────────┐ │
///            │   │ 1. Evaluate condition     │ │
///            │   │ 2. If truthy: render      │ │
///            │   │    program with context   │──┘
///            │   │ 3. If falsy: render       │
///            │   │    inverse block          │
///            │   └───────────────────────────┘
///            │
///            └── PartialNode ──▶ lookup & render partial
/// ```
///
/// ## Context Resolution
///
/// Path resolution follows this precedence:
///
/// 1. `.`  - Current context
/// 2. `..` - Parent context
/// 3. `@key` - Data variables (@index, @first, @last, @root)
/// 4. `path.to.value` - Nested object lookup
///
/// ## Built-in Block Helpers
///
/// | Helper   | Behavior                                        |
/// |----------|-------------------------------------------------|
/// | `if`     | Render program if truthy                        |
/// | `unless` | Render program if falsy (inverse of if)         |
/// | `each`   | Iterate over array/map, set @index, @first, etc |
/// | `with`   | Change context for nested block                 |
class Runtime {
  /// Creates a new runtime with the given helpers and partials.
  ///
  /// Parameters:
  /// - [helpers]: Map of helper name to helper function.
  /// - [partials]: Map of partial name to compiled partial template.
  /// - [escapeHtml]: Whether to escape HTML by default (default: true).
  /// - [strict]: When true, throw on missing variables (default: false).
  Runtime({required this.helpers, required this.partials, this.escapeHtml = true, this.strict = false});

  /// Registered helpers.
  final Map<String, HelperFunction> helpers;

  /// Registered partials (as compiled templates).
  final Map<String, String Function(dynamic)> partials;

  /// Whether to escape HTML by default.
  final bool escapeHtml;

  /// Whether to throw on missing variables (strict mode).
  ///
  /// When enabled, accessing an undefined variable or helper will throw
  /// a [StrictModeException] instead of returning an empty string.
  final bool strict;

  /// Renders the given AST with the provided context.
  ///
  /// The [initialData] parameter allows passing additional data hash values
  /// that are accessible via @ variables (e.g., @auth, @user).
  String render(ProgramNode ast, dynamic context, {Map<String, dynamic>? initialData}) {
    final data = <String, dynamic>{"root": context};
    if (initialData != null) {
      data.addAll(initialData);
    }
    // Initialize context stack with the root context
    final contextStack = <dynamic>[context];
    return _renderProgram(ast, context, data, contextStack);
  }

  String _renderProgram(
    ProgramNode program,
    dynamic context,
    Map<String, dynamic> data,
    List<dynamic> contextStack, {
    bool stripStart = false,
    bool stripEnd = false,
  }) {
    final buffer = StringBuffer();
    final body = program.body;

    for (var i = 0; i < body.length; i++) {
      final node = body[i];
      var output = _renderNode(node, context, data, contextStack);

      // Apply block content strip to first node if stripStart is set
      if (stripStart && i == 0 && node is TextNode) {
        output = _stripLeadingWhitespace(output);
      }
      // Apply block content strip to last node if stripEnd is set
      if (stripEnd && i == body.length - 1 && node is TextNode) {
        output = _stripTrailingWhitespace(output);
      }

      // Handle standalone statements for blocks, comments, and partials
      // A standalone is a block/comment/partial that is alone on its line
      if (_isStandaloneEligible(node)) {
        // Check if previous text ends with only whitespace after newline
        final prevEndsWithLineStart =
            i == 0 || (body[i - 1] is TextNode && _endsWithLineStart((body[i - 1] as TextNode).text));

        // Check if next text starts with only whitespace before newline
        final nextStartsWithLineEnd =
            i == body.length - 1 || (body[i + 1] is TextNode && _startsWithLineEnd((body[i + 1] as TextNode).text));

        // If standalone, strip the surrounding line content
        if (prevEndsWithLineStart && nextStartsWithLineEnd) {
          // Strip trailing whitespace + newline from previous text
          if (i > 0 && body[i - 1] is TextNode) {
            // Already written to buffer, need to handle differently
            // We'll use strip markers instead
          }
          // The output itself should not add anything for standalone blocks
          // (blocks already return their content, the issue is the surrounding text)
        }
      }

      // Apply whitespace stripping based on adjacent nodes' strip markers
      if (output.isNotEmpty) {
        // Check if previous node wants to strip trailing whitespace
        if (i > 0) {
          final prevNode = body[i - 1];
          if (_hasCloseStrip(prevNode) && node is TextNode) {
            output = _stripLeadingWhitespace(output);
          }
        }

        // Check if next node wants to strip leading whitespace
        if (i < body.length - 1) {
          final nextNode = body[i + 1];
          if (_hasOpenStrip(nextNode) && node is TextNode) {
            output = _stripTrailingWhitespace(output);
          }
        }
      }

      // For TextNodes followed by a standalone-eligible node, strip line-trailing content
      if (node is TextNode && i < body.length - 1) {
        final nextNode = body[i + 1];
        if (_isStandaloneEligible(nextNode)) {
          final nextNextIsLineEnd =
              i + 2 >= body.length || (body[i + 2] is TextNode && _startsWithLineEnd((body[i + 2] as TextNode).text));
          if (_endsWithLineStart(output) && nextNextIsLineEnd) {
            // Strip the trailing whitespace (but keep content before it)
            output = _stripTrailingWhitespaceOnLine(output);
          }
        }
      }

      // For TextNodes preceded by a standalone-eligible node, strip line-leading content
      if (node is TextNode && i > 0) {
        final prevNode = body[i - 1];
        if (_isStandaloneEligible(prevNode)) {
          final prevPrevEndsWithLineStart =
              i - 2 < 0 || (body[i - 2] is TextNode && _endsWithLineStart((body[i - 2] as TextNode).text));
          if (_startsWithLineEnd(output) && prevPrevEndsWithLineStart) {
            // Strip the leading whitespace and newline
            output = _stripLeadingWhitespaceAndNewline(output);
          }
        }
      }

      buffer.write(output);
    }
    return buffer.toString();
  }

  /// Checks if a node is eligible for standalone line handling.
  /// Blocks, comments, and partials can be standalone.
  bool _isStandaloneEligible(AstNode node) =>
      (node is BlockNode && !node.isInline) || node is CommentNode || node is PartialNode;

  /// Checks if text ends with only whitespace after the last newline (or is all whitespace).
  bool _endsWithLineStart(String text) {
    if (text.isEmpty) return true;
    // Find last newline
    final lastNewline = text.lastIndexOf("\n");
    if (lastNewline == -1) {
      // No newline - check if entire text is whitespace
      return text.trim().isEmpty;
    }
    // Check if everything after the newline is whitespace
    final afterNewline = text.substring(lastNewline + 1);
    return afterNewline.isEmpty || RegExp(r"^[ \t]*$").hasMatch(afterNewline);
  }

  /// Checks if text starts with only whitespace before the first newline.
  bool _startsWithLineEnd(String text) {
    if (text.isEmpty) return true;
    // Find first newline
    final firstNewline = text.indexOf("\n");
    if (firstNewline == -1) {
      // No newline - check if entire text is whitespace
      return text.trim().isEmpty;
    }
    // Check if everything before the newline is whitespace
    final beforeNewline = text.substring(0, firstNewline);
    return beforeNewline.isEmpty || RegExp(r"^[ \t]*$").hasMatch(beforeNewline);
  }

  /// Strips trailing whitespace on the current line only (after last newline).
  String _stripTrailingWhitespaceOnLine(String str) {
    final lastNewline = str.lastIndexOf("\n");
    if (lastNewline == -1) {
      // No newline - strip all trailing whitespace but not the content
      return str.replaceFirst(RegExp(r"[ \t]+$"), "");
    }
    // Keep everything up to and including the newline, strip whitespace after
    final beforeNewline = str.substring(0, lastNewline + 1);
    return beforeNewline;
  }

  /// Strips leading whitespace and the first newline from text.
  String _stripLeadingWhitespaceAndNewline(String str) => str.replaceFirst(RegExp(r"^[ \t]*\n"), "");

  /// Checks if a node has an open strip marker ({{~ or {{#~).
  bool _hasOpenStrip(AstNode node) {
    if (node is MustacheNode) return node.openStrip;
    if (node is BlockNode) return node.openStrip;
    return false;
  }

  /// Checks if a node has a close strip marker (~}} or ~}}).
  bool _hasCloseStrip(AstNode node) {
    if (node is MustacheNode) return node.closeStrip;
    if (node is BlockNode) return node.closeStrip;
    return false;
  }

  /// Strips leading whitespace (spaces, tabs, newlines) from a string.
  String _stripLeadingWhitespace(String str) => str.replaceFirst(RegExp(r"^[\s\n\r]+"), "");

  /// Strips trailing whitespace (spaces, tabs, newlines) from a string.
  String _stripTrailingWhitespace(String str) => str.replaceFirst(RegExp(r"[\s\n\r]+$"), "");

  String _renderNode(AstNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) =>
      switch (node) {
        TextNode(:final text) => text,
        CommentNode() => "",
        MustacheNode() => _renderMustache(node, context, data, contextStack),
        BlockNode() => _renderBlock(node, context, data, contextStack),
        PartialNode() => _renderPartial(node, context, data),
        RawBlockNode(:final content) => content, // Output literally
        PartialBlockNode() => _renderPartialBlock(node, context, data, contextStack),
        InlinePartialNode() => _registerInlinePartial(node, context, data, contextStack),
        ProgramNode() => _renderProgram(node, context, data, contextStack),
        _ => "",
      };

  /// Registers an inline partial for later use.
  ///
  /// Inline partials are defined with {{#*inline "name"}}...{{/inline}}.
  /// They are registered as partials and can be used with {{> name}}.
  /// Returns empty string as inline partials produce no direct output.
  String _registerInlinePartial(
    InlinePartialNode node,
    dynamic context,
    Map<String, dynamic> data,
    List<dynamic> contextStack,
  ) {
    // Create a partial function that renders the inline partial's program
    // in the context where it was defined
    partials[node.name] = (ctx) => _renderProgram(node.program, ctx, data, contextStack);
    return ""; // Inline partial definition produces no output
  }

  String _renderMustache(MustacheNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    final result = _evaluateMustache(node, context, data, contextStack);
    if (result == null) return "";

    final str = result.toString();

    // SafeString bypasses escaping
    if (result is SafeString) {
      return str;
    }

    // Escape if needed
    if (node.escaped && escapeHtml) {
      return _escapeHtml(str);
    }

    return str;
  }

  dynamic _evaluateMustache(MustacheNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    final pathStr = node.path.parts.join(".");

    // Check if it's a helper
    if (helpers.containsKey(pathStr)) {
      return _invokeHelper(pathStr, node.params, node.hash, context, data, contextStack, null, null);
    }

    // It's a variable lookup
    if (node.params.isEmpty && node.hash.isEmpty) {
      return _resolvePath(node.path, context, data, contextStack);
    }

    // If it has params but isn't a registered helper, try as helper anyway
    // (might be a built-in or late-registered helper)
    if (helpers.containsKey(node.path.parts.first)) {
      return _invokeHelper(node.path.parts.first, node.params, node.hash, context, data, contextStack, null, null);
    }

    // Fall back to path resolution
    return _resolvePath(node.path, context, data, contextStack);
  }

  String _renderBlock(BlockNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    final pathStr = node.path.parts.first;

    // Check for built-in block helpers
    if (pathStr == "if") {
      return _renderIfBlock(node, context, data, contextStack);
    } else if (pathStr == "unless") {
      return _renderUnlessBlock(node, context, data, contextStack);
    } else if (pathStr == "each") {
      return _renderEachBlock(node, context, data, contextStack);
    } else if (pathStr == "with") {
      return _renderWithBlock(node, context, data, contextStack);
    }

    // Check for custom block helper
    if (helpers.containsKey(pathStr)) {
      return _invokeBlockHelper(pathStr, node, context, data, contextStack);
    }

    // Unknown block - just render content if truthy
    final value =
        node.params.isNotEmpty
            ? _evaluateExpression(node.params.first, context, data, contextStack)
            : _resolvePath(node.path, context, data, contextStack);

    if (_isTruthy(value)) {
      return _renderProgram(
        node.program,
        context,
        data,
        contextStack,
        stripStart: node.contentStartStrip,
        stripEnd: node.contentEndStrip,
      );
    } else if (node.inverse != null) {
      return _renderProgram(
        node.inverse!,
        context,
        data,
        contextStack,
        stripStart: node.contentStartStrip,
        stripEnd: node.contentEndStrip,
      );
    }

    return "";
  }

  String _renderIfBlock(BlockNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    final condition =
        node.params.isNotEmpty ? _evaluateExpression(node.params.first, context, data, contextStack) : true;

    if (_isTruthy(condition)) {
      return _renderProgram(
        node.program,
        context,
        data,
        contextStack,
        stripStart: node.contentStartStrip,
        stripEnd: node.contentEndStrip,
      );
    } else if (node.inverse != null) {
      return _renderProgram(
        node.inverse!,
        context,
        data,
        contextStack,
        stripStart: node.contentStartStrip,
        stripEnd: node.contentEndStrip,
      );
    }
    return "";
  }

  String _renderUnlessBlock(BlockNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    final condition =
        node.params.isNotEmpty ? _evaluateExpression(node.params.first, context, data, contextStack) : false;

    if (!_isTruthy(condition)) {
      return _renderProgram(
        node.program,
        context,
        data,
        contextStack,
        stripStart: node.contentStartStrip,
        stripEnd: node.contentEndStrip,
      );
    } else if (node.inverse != null) {
      return _renderProgram(
        node.inverse!,
        context,
        data,
        contextStack,
        stripStart: node.contentStartStrip,
        stripEnd: node.contentEndStrip,
      );
    }
    return "";
  }

  String _renderEachBlock(BlockNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    if (node.params.isEmpty) return "";

    final items = _evaluateExpression(node.params.first, context, data, contextStack);
    if (items == null) {
      if (node.inverse != null) {
        return _renderProgram(node.inverse!, context, data, contextStack);
      }
      return "";
    }

    final buffer = StringBuffer();
    final blockParams = node.blockParams;

    if (items is List) {
      if (items.isEmpty && node.inverse != null) {
        return _renderProgram(node.inverse!, context, data, contextStack);
      }

      for (var i = 0; i < items.length; i++) {
        final itemData = Map<String, dynamic>.from(data);
        itemData["index"] = i;
        itemData["first"] = i == 0;
        itemData["last"] = i == items.length - 1;

        // Build the context for this iteration
        dynamic itemContext = items[i];

        // If block params are specified, create a Map context with the param names
        if (blockParams.isNotEmpty) {
          final paramContext = <String, dynamic>{};
          // First block param is the item value
          if (blockParams.isNotEmpty) {
            paramContext[blockParams[0]] = items[i];
          }
          // Second block param is the index
          if (blockParams.length > 1) {
            paramContext[blockParams[1]] = i;
          }
          // If original context is a Map, merge it
          if (context is Map) {
            itemContext = {...(context as Map<String, dynamic>), ...paramContext};
          } else {
            itemContext = paramContext;
          }
        }

        // Push new context onto stack for parent access
        final newStack = [...contextStack, itemContext];
        buffer.write(
          _renderProgram(
            node.program,
            itemContext,
            itemData,
            newStack,
            stripStart: node.contentStartStrip,
            stripEnd: node.contentEndStrip,
          ),
        );
      }
    } else if (items is Map) {
      if (items.isEmpty && node.inverse != null) {
        return _renderProgram(node.inverse!, context, data, contextStack);
      }

      final keys = items.keys.toList();
      for (var i = 0; i < keys.length; i++) {
        final key = keys[i];
        final itemData = Map<String, dynamic>.from(data);
        itemData["key"] = key;
        itemData["index"] = i;
        itemData["first"] = i == 0;
        itemData["last"] = i == keys.length - 1;

        // Build the context for this iteration
        dynamic itemContext = items[key];

        // If block params are specified, create a Map context with the param names
        if (blockParams.isNotEmpty) {
          final paramContext = <String, dynamic>{};
          // First block param is the value
          if (blockParams.isNotEmpty) {
            paramContext[blockParams[0]] = items[key];
          }
          // Second block param is the key
          if (blockParams.length > 1) {
            paramContext[blockParams[1]] = key;
          }
          // If original context is a Map, merge it
          if (context is Map) {
            itemContext = {...(context as Map<String, dynamic>), ...paramContext};
          } else {
            itemContext = paramContext;
          }
        }

        // Push new context onto stack for parent access
        final newStack = [...contextStack, itemContext];
        buffer.write(
          _renderProgram(
            node.program,
            itemContext,
            itemData,
            newStack,
            stripStart: node.contentStartStrip,
            stripEnd: node.contentEndStrip,
          ),
        );
      }
    }

    return buffer.toString();
  }

  String _renderWithBlock(BlockNode node, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    if (node.params.isEmpty) return "";

    final newContext = _evaluateExpression(node.params.first, context, data, contextStack);
    if (newContext == null || newContext == false) {
      if (node.inverse != null) {
        return _renderProgram(
          node.inverse!,
          context,
          data,
          contextStack,
          stripStart: node.contentStartStrip,
          stripEnd: node.contentEndStrip,
        );
      }
      return "";
    }

    // Push new context onto stack for parent access
    final newStack = [...contextStack, newContext];
    return _renderProgram(
      node.program,
      newContext,
      data,
      newStack,
      stripStart: node.contentStartStrip,
      stripEnd: node.contentEndStrip,
    );
  }

  String _invokeBlockHelper(
    String name,
    BlockNode node,
    dynamic context,
    Map<String, dynamic> data,
    List<dynamic> contextStack,
  ) {
    final helper = helpers[name]!;

    // Evaluate params
    final params = node.params.map((p) => _evaluateExpression(p, context, data, contextStack)).toList();

    // Evaluate hash
    final hash = <String, dynamic>{};
    for (final entry in node.hash.entries) {
      hash[entry.key] = _evaluateExpression(entry.value, context, data, contextStack);
    }

    // Create fn and inverse functions
    String fn(dynamic ctx) {
      final newStack = [...contextStack, ctx ?? context];
      return _renderProgram(node.program, ctx ?? context, data, newStack);
    }

    String inverse(dynamic ctx) {
      if (node.inverse == null) return "";
      final newStack = [...contextStack, ctx ?? context];
      return _renderProgram(node.inverse!, ctx ?? context, data, newStack);
    }

    final options = HelperOptions(hash: hash, fn: fn, inverse: inverse, data: data, context: context);

    final result = helper(params, options);
    if (result is SafeString) {
      return result.value;
    }
    return result?.toString() ?? "";
  }

  dynamic _invokeHelper(
    String name,
    List<ExpressionNode> paramNodes,
    Map<String, ExpressionNode> hashNodes,
    dynamic context,
    Map<String, dynamic> data,
    List<dynamic>? contextStack,
    ProgramNode? program,
    ProgramNode? inverse,
  ) {
    final helper = helpers[name];
    if (helper == null) return null;

    final stack = contextStack ?? <dynamic>[context];

    // Evaluate params
    final params = paramNodes.map((p) => _evaluateExpression(p, context, data, stack)).toList();

    // Evaluate hash
    final hash = <String, dynamic>{};
    for (final entry in hashNodes.entries) {
      hash[entry.key] = _evaluateExpression(entry.value, context, data, stack);
    }

    // Create fn and inverse functions
    String fn(dynamic ctx) {
      if (program == null) return "";
      final newStack = [...stack, ctx ?? context];
      return _renderProgram(program, ctx ?? context, data, newStack);
    }

    String inverseFn(dynamic ctx) {
      if (inverse == null) return "";
      final newStack = [...stack, ctx ?? context];
      return _renderProgram(inverse, ctx ?? context, data, newStack);
    }

    final options = HelperOptions(hash: hash, fn: fn, inverse: inverseFn, data: data, context: context);

    return helper(params, options);
  }

  String _renderPartial(PartialNode node, dynamic context, Map<String, dynamic> data) {
    final partial = partials[node.name];
    if (partial == null) return "";

    // For partials, we don't have the context stack, so create a minimal one
    final contextStack = <dynamic>[context];

    // Determine context for partial
    dynamic partialContext = context;
    if (node.context != null) {
      partialContext = _evaluateExpression(node.context!, context, data, contextStack);
    }

    // Merge hash into context if it's a map
    if (node.hash.isNotEmpty && partialContext is Map) {
      final merged = Map<String, dynamic>.from(partialContext as Map<String, dynamic>);
      for (final entry in node.hash.entries) {
        merged[entry.key] = _evaluateExpression(entry.value, context, data, contextStack);
      }
      partialContext = merged;
    }

    return partial(partialContext);
  }

  String _renderPartialBlock(
    PartialBlockNode node,
    dynamic context,
    Map<String, dynamic> data,
    List<dynamic> contextStack,
  ) {
    final partial = partials[node.name];

    // Determine context for partial
    dynamic partialContext = context;
    if (node.context != null) {
      partialContext = _evaluateExpression(node.context!, context, data, contextStack);
    }

    // Merge hash into context if it's a map
    if (node.hash.isNotEmpty && partialContext is Map) {
      final merged = Map<String, dynamic>.from(partialContext as Map<String, dynamic>);
      for (final entry in node.hash.entries) {
        merged[entry.key] = _evaluateExpression(entry.value, context, data, contextStack);
      }
      partialContext = merged;
    }

    // If partial exists, use it; otherwise render the default block content
    if (partial != null) {
      return partial(partialContext);
    } else {
      // Render the default content from the block
      final newStack = [...contextStack, partialContext];
      return _renderProgram(node.program, partialContext, data, newStack);
    }
  }

  dynamic _evaluateExpression(
    ExpressionNode expr,
    dynamic context,
    Map<String, dynamic> data,
    List<dynamic> contextStack,
  ) => switch (expr) {
    StringNode(:final value) => value,
    NumberNode(:final value) => value,
    BooleanNode(:final value) => value,
    PathNode() => _resolvePath(expr, context, data, contextStack),
    SubExpressionNode() => _evaluateSubExpression(expr, context, data, contextStack),
  };

  /// Evaluates a subexpression by calling the helper and returning its result.
  dynamic _evaluateSubExpression(
    SubExpressionNode node,
    dynamic context,
    Map<String, dynamic> data,
    List<dynamic> contextStack,
  ) {
    final helperName = node.path.path;
    final helper = helpers[helperName];

    if (helper == null) {
      return null;
    }

    // Evaluate parameters
    final params = node.params.map((p) => _evaluateExpression(p, context, data, contextStack)).toList();

    // Evaluate hash
    final hash = <String, dynamic>{};
    for (final entry in node.hash.entries) {
      hash[entry.key] = _evaluateExpression(entry.value, context, data, contextStack);
    }

    // Create options
    final options = HelperOptions(hash: hash, context: context, data: data, fn: (_) => "", inverse: (_) => "");

    return helper(params, options);
  }

  dynamic _resolvePath(PathNode path, dynamic context, Map<String, dynamic> data, List<dynamic> contextStack) {
    // Handle data variables (@root, @index, etc.)
    if (path.isData) {
      final key = path.parts.first;
      dynamic current = data[key];
      // Navigate remaining path parts (e.g., @root.company -> data["root"]["company"])
      for (var i = 1; i < path.parts.length; i++) {
        if (current == null) {
          if (strict) {
            throw StrictModeException('"${path.path}" is not defined', path: path.path);
          }
          return null;
        }
        if (current is Map) {
          current = current[path.parts[i]];
        } else {
          if (strict) {
            throw StrictModeException('"${path.path}" is not defined', path: path.path);
          }
          return null;
        }
      }
      if (strict && current == null && !data.containsKey(key)) {
        throw StrictModeException('"${path.path}" is not defined', path: path.path);
      }
      return current;
    }

    // Handle this context (.) or 'this' keyword
    if (path.parts.length == 1 && (path.parts.first == "." || path.parts.first == "this")) {
      return context;
    }

    // Navigate the path, handling parent context (..)
    dynamic current = context;
    var stackIndex = contextStack.length - 1;

    for (final part in path.parts) {
      if (part == "..") {
        // Navigate to parent context
        stackIndex--;
        if (stackIndex >= 0) {
          current = contextStack[stackIndex];
        } else {
          // No more parents
          if (strict) {
            throw StrictModeException(
              '"${path.path}" is not defined - attempted to access parent beyond root',
              path: path.path,
            );
          }
          return null;
        }
        continue;
      }

      if (current == null) {
        if (strict) {
          throw StrictModeException('"${path.path}" is not defined', path: path.path);
        }
        return null;
      }

      if (current is Map) {
        // Check if key exists in strict mode
        if (strict && !current.containsKey(part)) {
          throw StrictModeException('"${path.path}" is not defined - "$part" not found in context', path: path.path);
        }
        current = current[part];
      } else {
        // For non-map types, we can't navigate further
        if (strict) {
          throw StrictModeException(
            '"${path.path}" is not defined - cannot access property "$part" on non-object',
            path: path.path,
          );
        }
        return null;
      }
    }

    return current;
  }

  bool _isTruthy(dynamic value) {
    if (value == null) return false;
    if (value == false) return false;
    if (value == 0) return false;
    if (value == "") return false;
    if (value is List && value.isEmpty) return false;
    return true;
  }

  String _escapeHtml(String str) => str
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#x27;");
}
