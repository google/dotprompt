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

/// Parser for Dotprompt template files.
///
/// Handles extraction of YAML frontmatter and template body from .prompt files.
///
/// ## File Format
///
/// A .prompt file consists of two parts:
/// 1. Optional YAML frontmatter enclosed in `---` delimiters
/// 2. The template body (Handlebars syntax)
///
/// ```
/// ---
/// model: gemini-pro
/// config:
///   temperature: 0.7
/// ---
/// Hello {{name}}!
/// ```
library;

import "package:yaml/yaml.dart";

import "error.dart";
import "models/parsed_prompt.dart";
import "models/prompt_metadata.dart";

/// The YAML frontmatter delimiter.
const String _frontmatterDelimiter = "---";

/// Regex pattern for matching the frontmatter section.
/// Matches optional content between --- delimiters.
final RegExp _frontmatterPattern = RegExp(
  r"^---\s*\n([\s\S]*?)\n?---\s*\n?",
  multiLine: true,
);

/// Parser for Dotprompt template files.
///
/// Provides static methods for parsing prompt templates into structured
/// [ParsedPrompt] objects.
///
/// ## Example
///
/// ```dart
/// final source = '''
/// ---
/// model: gemini-pro
/// ---
/// Hello {{name}}!
/// ''';
///
/// final parsed = Parser.parseDocument(source);
/// print(parsed.model);     // "gemini-pro"
/// print(parsed.template);  // "Hello {{name}}!"
/// ```
class Parser {
  /// Private constructor to prevent instantiation.
  Parser._();

  /// Parses a prompt template source into a [ParsedPrompt].
  ///
  /// Extracts the YAML frontmatter and template body, returning a structured
  /// [ParsedPrompt] object.
  ///
  /// Throws [ParseException] if the YAML frontmatter is malformed.
  static ParsedPrompt parseDocument(String source) {
    final prompt = parse(source);
    final metadata = PromptMetadata.fromConfig(prompt.config);
    return ParsedPrompt(template: prompt.template, metadata: metadata);
  }

  /// Parses a prompt template source into a raw [Prompt] record.
  ///
  /// This is a lower-level parsing method that returns the template and
  /// config as raw types without further processing.
  static Prompt parse(String source) {
    // Handle empty input
    if (source.isEmpty) {
      return const Prompt(template: "", config: {});
    }

    // Check for frontmatter
    if (!source.startsWith(_frontmatterDelimiter)) {
      // No frontmatter, entire source is template
      return Prompt(template: source, config: const {});
    }

    // Find the end of frontmatter
    final match = _frontmatterPattern.firstMatch(source);
    if (match == null) {
      // Malformed frontmatter (no closing ---)
      throw const ParseException(
        "Malformed frontmatter: missing closing '---' delimiter",
      );
    }

    final yamlContent = match.group(1) ?? "";
    final template = source.substring(match.end);

    // Parse YAML
    Map<String, dynamic> config;
    try {
      final yaml = loadYaml(yamlContent);
      if (yaml == null) {
        config = const {};
      } else if (yaml is Map) {
        config = _convertYamlMap(yaml);
      } else {
        throw ParseException(
          "Invalid frontmatter: expected a YAML map, got ${yaml.runtimeType}",
        );
      }
    } on YamlException catch (e) {
      throw ParseException("Failed to parse YAML frontmatter", e);
    }

    return Prompt(template: template.trim(), config: config);
  }

  /// Converts a YAML map to a Dart map with proper types.
  static Map<String, dynamic> _convertYamlMap(Map<dynamic, dynamic> yaml) {
    final result = <String, dynamic>{};
    for (final entry in yaml.entries) {
      final key = entry.key as String;
      result[key] = _convertYamlValue(entry.value);
    }
    return result;
  }

  /// Converts a YAML value to a Dart value.
  static dynamic _convertYamlValue(dynamic value) {
    if (value is YamlMap) {
      return _convertYamlMap(value);
    } else if (value is Map) {
      return _convertYamlMap(value);
    } else if (value is YamlList) {
      return value.map(_convertYamlValue).toList();
    } else if (value is List) {
      return value.map(_convertYamlValue).toList();
    }
    return value;
  }
}

/// A raw parsed prompt with template and config.
///
/// This is the low-level representation before metadata is extracted.
class Prompt {
  /// Creates a new [Prompt].
  const Prompt({required this.template, required this.config});

  /// The template body.
  final String template;

  /// The raw configuration map from frontmatter.
  final Map<String, dynamic> config;
}
