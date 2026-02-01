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

/// Prompt metadata representation.
///
/// Contains all configuration extracted from the YAML frontmatter of a
/// prompt file, including model settings, input/output schemas, and tools.
library;

import "package:meta/meta.dart";

import "parsed_prompt.dart";

/// Metadata parsed from prompt frontmatter.
///
/// This class contains all the configuration options that can be specified
/// in the YAML frontmatter of a .prompt file.
///
/// ## Frontmatter Fields
///
/// | Field    | Type                  | Description                        |
/// |----------|-----------------------|------------------------------------|
/// | model    | String                | Model identifier                   |
/// | config   | Map                   | Generation configuration           |
/// | input    | InputConfig           | Input schema and defaults          |
/// | output   | OutputConfig          | Output format and schema           |
/// | tools    | List\<String\>          | Tool names to enable               |
/// | ext.*    | Map                   | Extension fields                   |
///
/// ## Example Frontmatter
///
/// ```yaml
/// ---
/// model: gemini-pro
/// config:
///   temperature: 0.7
///   maxOutputTokens: 1024
/// input:
///   schema:
///     name: string
///     topic: string
///   default:
///     topic: "AI"
/// output:
///   format: json
///   schema:
///     summary: string
///     keyPoints: string[]
/// tools:
///   - searchWeb
///   - calculator
/// ext.custom:
///   myField: value
/// ---
/// ```
@immutable
class PromptMetadata {
  /// Creates a new [PromptMetadata].
  const PromptMetadata({
    this.model,
    this.config,
    this.input,
    this.output,
    this.tools,
    this.toolDefs,
    this.ext,
    this.raw,
  });

  /// Creates [PromptMetadata] from a configuration map.
  factory PromptMetadata.fromConfig(Map<String, dynamic> config) {
    final ext = <String, Map<String, dynamic>>{};

    // Extract extension fields (keys containing dots)
    for (final entry in config.entries) {
      if (entry.key.contains(".")) {
        final parts = entry.key.split(".");
        final extKey = parts[0];
        ext.putIfAbsent(extKey, () => {});
        if (parts.length == 2) {
          ext[extKey]![parts[1]] = entry.value;
        } else {
          // Handle nested ext keys like ext1.sub1.foo
          ext["${parts[0]}.${parts[1]}"] ??= {};
          ext["${parts[0]}.${parts[1]}"]![parts.sublist(2).join(".")] = entry.value;
        }
      }
    }

    return PromptMetadata(
      model: config["model"] as String?,
      config: config["config"] as Map<String, dynamic>?,
      input: config["input"] != null ? InputConfig.fromValue(config["input"]) : null,
      output: config["output"] != null ? OutputConfig.fromValue(config["output"]) : null,
      tools: config["tools"] != null ? (config["tools"] as List).cast<String>() : null,
      toolDefs: config["toolDefs"] != null
          ? (config["toolDefs"] as List).map((e) => ToolDefinition.fromJson(e as Map<String, dynamic>)).toList()
          : null,
      ext: ext.isNotEmpty ? ext : null,
      raw: config,
    );
  }

  /// Creates [PromptMetadata] from a JSON map.
  factory PromptMetadata.fromJson(Map<String, dynamic> json) => PromptMetadata.fromConfig(json);

  /// The model identifier.
  final String? model;

  /// Generation configuration (temperature, maxTokens, etc.).
  final Map<String, dynamic>? config;

  /// Input configuration.
  final InputConfig? input;

  /// Output configuration.
  final OutputConfig? output;

  /// List of tool names to enable.
  final List<String>? tools;

  /// Resolved tool definitions.
  final List<ToolDefinition>? toolDefs;

  /// Extension fields.
  final Map<String, Map<String, dynamic>>? ext;

  /// Raw frontmatter as parsed.
  final Map<String, dynamic>? raw;

  /// Converts this to a configuration map.
  Map<String, dynamic> toConfig() {
    final result = <String, dynamic>{};
    if (model != null) result["model"] = model;
    // Spread config values at top level (temperature, maxTokens, etc.)
    if (config != null) result.addAll(config!);
    if (raw != null) result["raw"] = raw;
    if (input != null) result["input"] = input!.toJson();
    if (output != null) result["output"] = output!.toJson();
    if (tools != null) result["tools"] = tools;
    if (toolDefs != null) {
      result["toolDefs"] = toolDefs!.map((t) => t.toJson()).toList();
    }
    if (ext != null) {
      result["ext"] = ext;
    }
    return result;
  }

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => toConfig();

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is PromptMetadata && model == other.model && tools == other.tools;

  @override
  int get hashCode => Object.hash(model, tools);

  @override
  String toString() => "PromptMetadata(model: $model, config: $config, "
      "input: $input, output: $output, tools: $tools)";
}

/// Input configuration for a prompt.
@immutable
class InputConfig {
  /// Creates a new [InputConfig].
  const InputConfig({this.schema, this.defaultValues});

  /// Creates an [InputConfig] from a JSON map.
  factory InputConfig.fromJson(Map<String, dynamic> json) {
    final schemaValue = json["schema"];
    Map<String, dynamic>? schema;
    if (schemaValue is String) {
      // Schema is a type string (Picoschema), use as-is for later conversion
      schema = {r"$type": schemaValue};
    } else if (schemaValue is Map) {
      schema = schemaValue.cast<String, dynamic>();
    }
    return InputConfig(
      schema: schema,
      defaultValues: json["default"] as Map<String, dynamic>?,
    );
  }

  /// Creates an [InputConfig] from a value that can be a String or Map.
  ///
  /// If the value is a String, it's treated as a schema name reference.
  factory InputConfig.fromValue(dynamic value) {
    if (value is String) {
      // String value is a schema name reference
      return InputConfig(schema: {r"$ref": value});
    } else if (value is Map<String, dynamic>) {
      return InputConfig.fromJson(value);
    }
    throw ArgumentError.value(value, "value", "Expected String or Map");
  }

  /// JSON Schema for input validation.
  final Map<String, dynamic>? schema;

  /// Default values for input variables.
  final Map<String, dynamic>? defaultValues;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        if (schema != null) "schema": schema,
        if (defaultValues != null) "default": defaultValues,
      };

  @override
  bool operator ==(Object other) => identical(this, other) || other is InputConfig;

  @override
  int get hashCode => Object.hash(schema, defaultValues);

  @override
  String toString() => "InputConfig(schema: $schema, defaultValues: $defaultValues)";
}

/// Output configuration for a prompt.
@immutable
class OutputConfig {
  /// Creates a new [OutputConfig].
  const OutputConfig({this.format, this.schema});

  /// Creates an [OutputConfig] from a JSON map.
  factory OutputConfig.fromJson(Map<String, dynamic> json) {
    final schemaValue = json["schema"];
    Map<String, dynamic>? schema;
    if (schemaValue is String) {
      // Schema is a type string (Picoschema), use as-is for later conversion
      schema = {r"$type": schemaValue};
    } else if (schemaValue is Map) {
      schema = schemaValue.cast<String, dynamic>();
    }
    return OutputConfig(format: json["format"] as String?, schema: schema);
  }

  /// Creates an [OutputConfig] from a value that can be a String or Map.
  ///
  /// If the value is a String, it's treated as a schema name reference.
  factory OutputConfig.fromValue(dynamic value) {
    if (value is String) {
      // String value is a schema name reference
      return OutputConfig(schema: {r"$ref": value});
    } else if (value is Map<String, dynamic>) {
      return OutputConfig.fromJson(value);
    }
    throw ArgumentError.value(value, "value", "Expected String or Map");
  }

  /// Output format (e.g., "json", "text").
  final String? format;

  /// JSON Schema for output validation.
  final Map<String, dynamic>? schema;

  /// Converts this to a JSON-serializable map.
  Map<String, dynamic> toJson() => {
        if (format != null) "format": format,
        if (schema != null) "schema": schema,
      };

  @override
  bool operator ==(Object other) => identical(this, other) || other is OutputConfig;

  @override
  int get hashCode => Object.hash(format, schema);

  @override
  String toString() => "OutputConfig(format: $format, schema: $schema)";
}
