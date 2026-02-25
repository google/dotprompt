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

import "safe_string.dart";

/// Options passed to helper functions.
///
/// Contains the hash arguments, block content functions, and context data
/// available to helpers during template rendering.
///
/// ## Block Helper Example
///
/// ```dart
/// hb.registerHelper('list', (args, options) {
///   final items = args[0] as List;
///   final buffer = StringBuffer('<ul>');
///   for (final item in items) {
///     buffer.write('<li>${options.fn({'item': item})}</li>');
///   }
///   buffer.write('</ul>');
///   return SafeString(buffer.toString());
/// });
/// ```
class HelperOptions {
  /// Creates helper options.
  HelperOptions({
    required this.hash,
    required this.fn,
    required this.inverse,
    required this.data,
    required this.context,
  });

  /// Named hash arguments: `{{helper key="value" other=123}}`.
  ///
  /// Accessed as `options.hash['key']` and `options.hash['other']`.
  final Map<String, dynamic> hash;

  /// The block content function for block helpers.
  ///
  /// Call `fn(context)` to render the block content with a given context.
  /// For non-block helpers, this returns an empty string.
  ///
  /// Example: `{{#each items}}...{{/each}}`
  final String Function(dynamic context) fn;

  /// The inverse/else block content function.
  ///
  /// Call `inverse(context)` to render the `{{else}}` content.
  /// Returns empty string if no else block is present.
  ///
  /// Example: `{{#if condition}}...{{else}}...{{/if}}`
  final String Function(dynamic context) inverse;

  /// Private data for the current rendering frame.
  ///
  /// Contains special variables like `@root`, `@first`, `@last`, `@index`.
  final Map<String, dynamic> data;

  /// The current context (this) value for the helper.
  final dynamic context;
}

/// Function signature for helper functions.
///
/// Helpers receive:
/// - [args]: Positional arguments from the template
/// - [options]: Hash arguments, block functions, and context
///
/// Helpers should return a value that will be inserted into the output.
/// Return a [SafeString] to prevent HTML escaping.
typedef HelperFunction = dynamic Function(List<dynamic> args, HelperOptions options);
