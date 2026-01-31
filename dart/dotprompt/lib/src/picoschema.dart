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

/// Picoschema to JSON Schema converter.
///
/// Picoschema is a compact, human-readable schema format that compiles to
/// standard JSON Schema. It's designed to be easy to write in YAML frontmatter.
///
/// ## Picoschema Syntax
///
/// ```yaml
/// # Simple types
/// name: string
/// age: integer
/// score: number
/// active: boolean
///
/// # Arrays
/// tags: string[]
///
/// # Optional fields (with ?)
/// nickname?: string
///
/// # Descriptions (in parentheses)
/// email(User's email address): string
///
/// # Nested objects
/// address:
///   street: string
///   city: string
///   zip: string
///
/// # Enums
/// status: approved | pending | rejected
/// ```
///
/// ## Compiled JSON Schema
///
/// The above compiles to:
/// ```json
/// {
///   "type": "object",
///   "properties": {
///     "name": {"type": "string"},
///     "age": {"type": "integer"},
///     "score": {"type": "number"},
///     "active": {"type": "boolean"},
///     "tags": {"type": "array", "items": {"type": "string"}},
///     "nickname": {"type": "string"},
///     "email": {"type": "string", "description": "User's email address"},
///     "address": {
///       "type": "object",
///       "properties": {...},
///       "required": ["street", "city", "zip"]
///     },
///     "status": {"type": "string", "enum": ["approved", "pending", "rejected"]}
///   },
///   "required": ["name", "age", "score", "active", "tags", "email", "address", "status"]
/// }
/// ```
library;

import "error.dart";

/// Converts a Picoschema definition to JSON Schema.
///
/// Picoschema is a compact schema format designed for ease of use in YAML.
///
/// ## Example
///
/// ```dart
/// final picoschema = {
///   'name': 'string',
///   'age': 'integer',
///   'tags': 'string[]',
/// };
///
/// final jsonSchema = Picoschema.toJsonSchema(picoschema);
/// // Returns:
/// // {
/// //   "type": "object",
/// //   "properties": {
/// //     "name": {"type": "string"},
/// //     "age": {"type": "integer"},
/// //     "tags": {"type": "array", "items": {"type": "string"}}
/// //   },
/// //   "required": ["name", "age", "tags"]
/// // }
/// ```
class Picoschema {
  /// Private constructor to prevent instantiation.
  Picoschema._();

  /// Primitive type mappings from Picoschema to JSON Schema.
  static const Map<String, String> _primitiveTypes = {
    "string": "string",
    "str": "string",
    "number": "number",
    "num": "number",
    "float": "number",
    "double": "number",
    "integer": "integer",
    "int": "integer",
    "boolean": "boolean",
    "bool": "boolean",
    "null": "null",
    "any": "object",
    "object": "object",
  };

  /// Regex for parsing field names with optional description and optionality.
  /// Matches: fieldName(description)? or fieldName?(description)?
  static final RegExp _fieldPattern = RegExp(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)(\?)?(?:\(([^)]+)\))?$",
  );

  /// Regex for parsing array types (e.g., "string[]").
  static final RegExp _arrayPattern = RegExp(r"^(.+)\[\]$");

  /// Regex for parsing enum types (e.g., "foo | bar | baz").
  static final RegExp _enumPattern = RegExp(r"^([^|]+(?:\s*\|\s*[^|]+)+)$");

  /// Converts a Picoschema definition to JSON Schema.
  ///
  /// The input can be:
  /// - A string (primitive type, array type, or enum)
  /// - A map (object schema)
  ///
  /// Returns a JSON Schema object.
  ///
  /// Throws [PicoschemaException] if the schema is invalid.
  static Map<String, dynamic> toJsonSchema(dynamic picoschema) {
    if (picoschema == null) {
      return {"type": "object"};
    }

    if (picoschema is String) {
      return _parseTypeString(picoschema);
    }

    if (picoschema is Map) {
      return _parseObjectSchema(picoschema.cast<String, dynamic>());
    }

    throw PicoschemaException(
      "Invalid picoschema type: ${picoschema.runtimeType}",
    );
  }

  /// Parses a type string into a JSON Schema.
  static Map<String, dynamic> _parseTypeString(String typeStr) {
    final trimmed = typeStr.trim();

    // Check for array type
    final arrayMatch = _arrayPattern.firstMatch(trimmed);
    if (arrayMatch != null) {
      final itemType = arrayMatch.group(1)!.trim();
      return {
        "type": "array",
        "items": _parseTypeString(itemType),
      };
    }

    // Check for enum type
    final enumMatch = _enumPattern.firstMatch(trimmed);
    if (enumMatch != null) {
      final values =
          trimmed.split("|").map((s) => s.trim()).toList();
      return {
        "type": "string",
        "enum": values,
      };
    }

    // Check for primitive type
    final normalizedType = trimmed.toLowerCase();
    if (_primitiveTypes.containsKey(normalizedType)) {
      return {"type": _primitiveTypes[normalizedType]};
    }

    // Unknown type - treat as a reference or custom type
    throw PicoschemaException("Unknown type: $trimmed");
  }

  /// Parses an object schema definition.
  static Map<String, dynamic> _parseObjectSchema(Map<String, dynamic> schema) {
    final properties = <String, dynamic>{};
    final required = <String>[];

    for (final entry in schema.entries) {
      final fieldMatch = _fieldPattern.firstMatch(entry.key);
      if (fieldMatch == null) {
        throw PicoschemaException("Invalid field name: ${entry.key}");
      }

      final fieldName = fieldMatch.group(1)!;
      final isOptional = fieldMatch.group(2) == "?";
      final description = fieldMatch.group(3);

      // Parse the field value
      Map<String, dynamic> fieldSchema;
      if (entry.value is String) {
        fieldSchema = _parseTypeString(entry.value as String);
      } else if (entry.value is Map) {
        fieldSchema = _parseObjectSchema(
          (entry.value as Map).cast<String, dynamic>(),
        );
      } else if (entry.value == null) {
        fieldSchema = {"type": "object"};
      } else {
        throw PicoschemaException(
          "Invalid field value for '$fieldName': ${entry.value.runtimeType}",
        );
      }

      // Add description if present
      if (description != null) {
        fieldSchema["description"] = description;
      }

      properties[fieldName] = fieldSchema;

      // Track required fields
      if (!isOptional) {
        required.add(fieldName);
      }
    }

    final result = <String, dynamic>{
      "type": "object",
      "properties": properties,
    };

    if (required.isNotEmpty) {
      result["required"] = required;
    }

    return result;
  }

  /// Checks if the given schema appears to be a Picoschema (vs. JSON Schema).
  ///
  /// Returns true if the schema looks like Picoschema and should be converted.
  static bool isPicoschema(Map<String, dynamic> schema) {
    // JSON Schema typically has "type" or "$schema" at the top level
    if (schema.containsKey("\$schema") || schema.containsKey("\$ref")) {
      return false;
    }

    // If it has type=object with properties, it's likely already JSON Schema
    if (schema["type"] == "object" && schema.containsKey("properties")) {
      return false;
    }

    // If any value is a simple type string, it's Picoschema
    for (final value in schema.values) {
      if (value is String) {
        final normalized = value.toLowerCase();
        if (_primitiveTypes.containsKey(normalized) ||
            _arrayPattern.hasMatch(value) ||
            _enumPattern.hasMatch(value)) {
          return true;
        }
      }
    }

    return true;
  }
}
