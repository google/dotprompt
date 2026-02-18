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
import "template.dart";

export "options.dart" show HelperFunction, HelperOptions;
export "safe_string.dart" show SafeString;
export "template.dart" show Template;

/// A Handlebars template engine instance.
///
/// Provides methods for compiling templates, registering helpers,
/// and registering partials.
///
/// ## Example
///
/// ```dart
/// final hb = Handlebars();
///
/// // Register a helper
/// hb.registerHelper('upper', (args, options) {
///   return args[0].toString().toUpperCase();
/// });
///
/// // Register a partial
/// hb.registerPartial('header', '<h1>{{title}}</h1>');
///
/// // Compile and render
/// final template = hb.compile('{{> header}}Hello {{upper name}}!');
/// print(template({'title': 'Welcome', 'name': 'world'}));
/// // Output: <h1>Welcome</h1>Hello WORLD!
/// ```
class Handlebars {
  /// Creates a new Handlebars instance.
  ///
  /// Parameters:
  /// - [escapeHtml]: Whether to HTML-escape output by default (default: true).
  /// - [strict]: When true, throw on undefined variables (default: false).
  ///
  /// Automatically registers the built-in `lookup` and `log` helpers.
  Handlebars({bool escapeHtml = true, bool strict = false}) : _escapeHtml = escapeHtml, _strict = strict {
    _registerBuiltinHelpers();
  }

  final bool _escapeHtml;
  final bool _strict;
  final Map<String, HelperFunction> _helpers = {};
  final Map<String, String> _partialSources = {};
  final Map<String, String Function(dynamic)> _compiledPartials = {};

  /// Registers built-in Handlebars helpers: lookup, log.
  void _registerBuiltinHelpers() {
    // lookup helper: {{lookup obj key}}
    // Allows dynamic property access
    _helpers["lookup"] = (args, options) {
      if (args.length < 2) return null;
      final obj = args[0];
      final key = args[1];
      if (obj is Map) {
        return obj[key];
      }
      if (obj is List && key is int) {
        return (key >= 0 && key < obj.length) ? obj[key] : null;
      }
      if (obj is List && key is String) {
        final index = int.tryParse(key);
        if (index != null && index >= 0 && index < obj.length) {
          return obj[index];
        }
      }
      return null;
    };

    // log helper: {{log value}}
    // Logs a value to the console (for debugging templates)
    _helpers["log"] = (args, options) {
      for (final arg in args) {
        // Using print instead of console.log for Dart compatibility
        // ignore: avoid_print
        print("[Handlebars] $arg");
      }
      return ""; // log helper returns nothing
    };
  }

  /// Compiles a template string into a reusable template function.
  ///
  /// The returned function accepts a context object and optionally a data
  /// hash for @ variables, and returns the rendered string.
  ///
  /// ```dart
  /// final template = hb.compile('Hello {{name}} (@{{@user}})!');
  /// print(template({'name': 'World'}, data: {'user': 'admin'}));
  /// // Output: "Hello World (@admin)!"
  /// ```
  String Function(dynamic context, {Map<String, dynamic>? data}) compile(String source) {
    // Compile any partials that haven't been compiled yet
    _ensurePartialsCompiled();

    final template = Template.compile(
      source,
      helpers: _helpers,
      partials: _compiledPartials,
      escapeHtml: _escapeHtml,
      strict: _strict,
    );

    return template.call;
  }

  /// Parses a template into an AST.
  ///
  /// Useful for template analysis or custom processing.
  ProgramNode parse(String source) => Parser.parse(source);

  /// Registers a helper function.
  ///
  /// Helpers are invoked in templates using `{{helperName arg1 arg2}}`.
  ///
  /// ## Simple Helper
  ///
  /// ```dart
  /// hb.registerHelper('loud', (args, options) {
  ///   return args[0].toString().toUpperCase();
  /// });
  /// // Usage: {{loud name}}
  /// ```
  ///
  /// ## Helper with Hash Arguments
  ///
  /// ```dart
  /// hb.registerHelper('link', (args, options) {
  ///   final url = options.hash['url'];
  ///   final text = args.isNotEmpty ? args[0] : 'Click here';
  ///   return SafeString('<a href="$url">$text</a>');
  /// });
  /// // Usage: {{link "Go" url="https://example.com"}}
  /// ```
  ///
  /// ## Block Helper
  ///
  /// ```dart
  /// hb.registerHelper('list', (args, options) {
  ///   final items = args[0] as List;
  ///   final buffer = StringBuffer('<ul>');
  ///   for (final item in items) {
  ///     buffer.write('<li>${options.fn(item)}</li>');
  ///   }
  ///   buffer.write('</ul>');
  ///   return SafeString(buffer.toString());
  /// });
  /// // Usage: {{#list items}}{{name}}{{/list}}
  /// ```
  void registerHelper(String name, HelperFunction fn) {
    _helpers[name] = fn;
  }

  /// Unregisters a helper.
  void unregisterHelper(String name) {
    _helpers.remove(name);
  }

  /// Registers a partial template.
  ///
  /// Partials are invoked using `{{> partialName}}`.
  ///
  /// ```dart
  /// hb.registerPartial('userCard', '''
  ///   <div class="card">
  ///     <h2>{{name}}</h2>
  ///     <p>{{email}}</p>
  ///   </div>
  /// ''');
  /// // Usage: {{> userCard}}
  /// ```
  void registerPartial(String name, String source) {
    _partialSources[name] = source;
    _compiledPartials.remove(name); // Clear cached compilation
  }

  /// Unregisters a partial.
  void unregisterPartial(String name) {
    _partialSources.remove(name);
    _compiledPartials.remove(name);
  }

  /// Returns a map of all registered helpers.
  Map<String, HelperFunction> get helpers => Map.unmodifiable(_helpers);

  /// Returns a map of all registered partial sources.
  Map<String, String> get partials => Map.unmodifiable(_partialSources);

  void _ensurePartialsCompiled() {
    // Compile partials in multiple passes to handle nested partials.
    // Each pass may compile partials that reference other partials,
    // which need to be compiled in subsequent passes.
    var compiledCount = 0;
    do {
      compiledCount = 0;
      for (final entry in _partialSources.entries) {
        if (!_compiledPartials.containsKey(entry.key)) {
          // Compile this partial with all currently available compiled partials
          final template = Template.compile(
            entry.value,
            helpers: _helpers,
            partials: _compiledPartials,
            escapeHtml: _escapeHtml,
          );
          _compiledPartials[entry.key] = template.call;
          compiledCount++;
        }
      }
    } while (compiledCount > 0);

    // If there are nested partials, recompile all partials with the complete set
    // to ensure they all have access to each other
    if (_partialSources.length > 1) {
      for (final entry in _partialSources.entries) {
        final template = Template.compile(
          entry.value,
          helpers: _helpers,
          partials: _compiledPartials,
          escapeHtml: _escapeHtml,
        );
        _compiledPartials[entry.key] = template.call;
      }
    }
  }

  /// Creates a SafeString that won't be HTML-escaped.
  static SafeString safeString(String value) => SafeString(value);
}
