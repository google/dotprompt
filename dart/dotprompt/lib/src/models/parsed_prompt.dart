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

/// Parsed prompt representation.
///
/// Contains both the raw template string and parsed metadata from the
/// YAML frontmatter.
library;

import "package:meta/meta.dart";

import "prompt_metadata.dart";

/// A parsed prompt with template and metadata.
///
/// This represents a prompt file after parsing the YAML frontmatter,
/// containing both the raw template body and the structured metadata.
///
/// ## Example
///
/// ```dart
/// final source = '''
/// ---
/// model: gemini-pro
/// config:
///   temperature: 0.7
/// ---
/// Hello {{name}}!
/// ''';
///
/// final parsed = Parser.parseDocument(source);
/// print(parsed.template);  // "Hello {{name}}!"
/// print(parsed.model);     // "gemini-pro"
/// ```
@immutable
class ParsedPrompt {
  /// Creates a new [ParsedPrompt].
  const ParsedPrompt({required this.template, required this.metadata});

  /// Creates a [ParsedPrompt] from the template and metadata.
  factory ParsedPrompt.fromMetadata(String template, PromptMetadata metadata) =>
      ParsedPrompt(template: template, metadata: metadata);

  /// Creates a [ParsedPrompt] from a JSON map.
  factory ParsedPrompt.fromJson(Map<String, dynamic> json) => ParsedPrompt(
        template: json["template"] as String,
        metadata: PromptMetadata.fromJson(
          json["metadata"] as Map<String, dynamic>? ?? {},
        ),
      );

  /// The template body (after frontmatter).
  final String template;

  /// The parsed metadata.
  final PromptMetadata metadata;

  /// The model name from metadata.
  String? get model => metadata.model;

  /// The generation config from metadata.
  Map<String, dynamic>? get config => metadata.config;

  /// The tools list from metadata.
  List<String>? get tools => metadata.tools;

  /// The input schema from metadata.
  InputConfig? get input => metadata.input;

  /// The output config from metadata.
  OutputConfig? get output => metadata.output;

  /// The resolved tool definitions.
  List<ToolDefinition>? get toolDefs => metadata.toolDefs;

  /// Extension fields from metadata.
  Map<String, Map<String, dynamic>>? get ext => metadata.ext;

  /// Raw frontmatter as parsed.
  Map<String, dynamic>? get raw => metadata.raw;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "template": template,
        "metadata": metadata.toJson(),
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is ParsedPrompt && template == other.template && metadata == other.metadata;

  @override
  int get hashCode => Object.hash(template, metadata);

  @override
  String toString() => "ParsedPrompt(template: $template, metadata: $metadata)";
}

/// A tool definition.
@immutable
class ToolDefinition {
  /// Creates a new [ToolDefinition].
  const ToolDefinition({
    required this.name,
    this.description,
    this.inputSchema,
    this.outputSchema,
  });

  /// Creates a [ToolDefinition] from a JSON map.
  factory ToolDefinition.fromJson(Map<String, dynamic> json) => ToolDefinition(
        name: json["name"] as String,
        description: json["description"] as String?,
        inputSchema: json["inputSchema"] as Map<String, dynamic>?,
        outputSchema: json["outputSchema"] as Map<String, dynamic>?,
      );

  /// The tool name.
  final String name;

  /// A description of what the tool does.
  final String? description;

  /// JSON Schema for the tool's input.
  final Map<String, dynamic>? inputSchema;

  /// JSON Schema for the tool's output.
  final Map<String, dynamic>? outputSchema;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        "name": name,
        if (description != null) "description": description,
        if (inputSchema != null) "inputSchema": inputSchema,
        if (outputSchema != null) "outputSchema": outputSchema,
      };

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is ToolDefinition && name == other.name && description == other.description;

  @override
  int get hashCode => Object.hash(name, description);

  @override
  String toString() => "ToolDefinition(name: $name, description: $description)";
}
