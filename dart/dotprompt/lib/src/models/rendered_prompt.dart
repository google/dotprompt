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

/// Rendered prompt result.
///
/// Contains the final configuration and messages after rendering a template.
library;

import "package:meta/meta.dart";

import "../types.dart";

/// The result of rendering a prompt template.
///
/// Contains the resolved configuration map (after merging model configs,
/// template config, and render options) and the list of generated messages.
///
/// ## Example
///
/// ```dart
/// final dotprompt = Dotprompt();
/// final result = dotprompt.render(template, data);
///
/// print(result.config['model']);  // "gemini-pro"
/// for (final message in result.messages) {
///   print('${message.role}: ${message.content}');
/// }
/// ```
@immutable
class RenderedPrompt {
  /// Creates a new [RenderedPrompt].
  const RenderedPrompt({required this.config, required this.messages});

  /// Creates a [RenderedPrompt] from a JSON map.
  factory RenderedPrompt.fromJson(Map<String, dynamic> json) => RenderedPrompt(
        config: json["config"] as Map<String, dynamic>? ?? {},
        messages: json["messages"] != null
            ? (json["messages"] as List).map((e) => Message.fromJson(e as Map<String, dynamic>)).toList()
            : [],
      );

  /// The resolved configuration map.
  ///
  /// This contains merged configuration from:
  /// 1. Model-specific defaults
  /// 2. Template frontmatter config
  /// 3. Render options
  final Map<String, dynamic> config;

  /// The generated messages.
  ///
  /// These are the messages produced by rendering the template, with all
  /// variables substituted and helper functions evaluated.
  final List<Message> messages;

  /// Gets the model name from config.
  String? get model => config["model"] as String?;

  /// Gets input configuration from config.
  Map<String, dynamic>? get input => config["input"] as Map<String, dynamic>?;

  /// Gets output configuration from config.
  Map<String, dynamic>? get output => config["output"] as Map<String, dynamic>?;

  /// Gets raw frontmatter from config.
  Map<String, dynamic>? get raw => config["raw"] as Map<String, dynamic>?;

  /// Gets extension fields from config.
  Map<String, dynamic>? get ext => config["ext"] as Map<String, dynamic>?;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "config": config,
        "messages": messages.map((m) => m.toJson()).toList(),
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is RenderedPrompt && _mapEquals(config, other.config) && _listEquals(messages, other.messages);

  @override
  int get hashCode => Object.hash(config.hashCode, messages.hashCode);

  @override
  String toString() => "RenderedPrompt(config: $config, messages: $messages)";
}

// Helper functions for equality
bool _mapEquals<K, V>(Map<K, V>? a, Map<K, V>? b) {
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (final key in a.keys) {
    if (!b.containsKey(key) || a[key] != b[key]) return false;
  }
  return true;
}

bool _listEquals<T>(List<T>? a, List<T>? b) {
  if (a == null && b == null) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;
  for (var i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}
