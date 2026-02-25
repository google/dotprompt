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
import "runtime.dart";

/// A compiled Handlebars template.
///
/// Templates are compiled once and can be rendered multiple times
/// with different contexts.
///
/// ## Example
///
/// ```dart
/// final template = Template.compile('Hello {{name}}!');
/// print(template({'name': 'World'}));  // "Hello World!"
/// ```
class Template {
  /// Compiles a template from source.
  ///
  /// Parameters:
  /// - [source]: The template source string.
  /// - [helpers]: Optional map of helper functions.
  /// - [partials]: Optional map of compiled partial templates.
  /// - [escapeHtml]: Whether to HTML-escape output by default (default: true).
  /// - [strict]: When true, throw on undefined variables (default: false).
  factory Template.compile(
    String source, {
    Map<String, HelperFunction>? helpers,
    Map<String, String Function(dynamic)>? partials,
    bool escapeHtml = true,
    bool strict = false,
  }) {
    final ast = Parser.parse(source);
    return Template._(
      ast: ast,
      source: source,
      helpers: helpers ?? {},
      partials: partials ?? {},
      escapeHtml: escapeHtml,
      strict: strict,
    );
  }

  Template._({
    required this.ast,
    required this.source,
    required Map<String, HelperFunction> helpers,
    required Map<String, String Function(dynamic)> partials,
    required this.escapeHtml,
    required this.strict,
  }) : _helpers = Map.from(helpers),
       _partials = Map.from(partials);

  /// The parsed AST.
  final ProgramNode ast;

  /// The original source.
  final String source;

  /// Whether to escape HTML by default.
  final bool escapeHtml;

  /// Whether to throw on undefined variables (strict mode).
  final bool strict;

  final Map<String, HelperFunction> _helpers;
  final Map<String, String Function(dynamic)> _partials;

  /// Renders the template with the given context.
  ///
  /// The context can be a `Map<String, dynamic>` or any object.
  /// Map keys and object properties are accessed using dot notation
  /// in the template.
  ///
  /// The optional [data] parameter provides values accessible via @ variables
  /// (e.g., @auth, @user) in addition to the built-in @root.
  String call(dynamic context, {Map<String, dynamic>? data}) {
    final runtime = Runtime(helpers: _helpers, partials: _partials, escapeHtml: escapeHtml, strict: strict);
    return runtime.render(ast, context, initialData: data);
  }

  /// Registers a helper for this template.
  void registerHelper(String name, HelperFunction fn) {
    _helpers[name] = fn;
  }

  /// Registers a partial for this template.
  void registerPartial(String name, String Function(dynamic) partial) {
    _partials[name] = partial;
  }
}
