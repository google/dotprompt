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

/// Error types for the Dotprompt library.
///
/// Provides a hierarchy of exception types for precise error handling.
library;

/// Base exception class for all Dotprompt errors.
///
/// All exceptions thrown by the Dotprompt library extend this class,
/// allowing for catch-all error handling.
class DotpromptException implements Exception {
  /// Creates a new [DotpromptException].
  const DotpromptException(this.message, [this.cause]);

  /// The error message.
  final String message;

  /// The underlying cause, if any.
  final Object? cause;

  @override
  String toString() {
    if (cause != null) {
      return "DotpromptException: $message\nCaused by: $cause";
    }
    return "DotpromptException: $message";
  }
}

/// Exception thrown when parsing a prompt template fails.
///
/// This can occur when:
/// - YAML frontmatter is malformed
/// - Required metadata fields are missing
/// - Template syntax is invalid
class ParseException extends DotpromptException {
  /// Creates a new [ParseException].
  const ParseException(super.message, [super.cause, this.line, this.column]);

  /// The line number where the error occurred, if known.
  final int? line;

  /// The column number where the error occurred, if known.
  final int? column;

  @override
  String toString() {
    final location = line != null ? " at line $line" : "";
    final col = column != null ? ", column $column" : "";
    return "ParseException$location$col: $message";
  }
}

/// Exception thrown when rendering a template fails.
///
/// This can occur when:
/// - Template variables are undefined
/// - Helper functions fail
/// - Invalid data types are provided
class RenderException extends DotpromptException {
  /// Creates a new [RenderException].
  const RenderException(super.message, [super.cause]);

  @override
  String toString() => "RenderException: $message";
}

/// Exception thrown when a partial template cannot be resolved.
class PartialResolutionException extends DotpromptException {
  /// Creates a new [PartialResolutionException].
  PartialResolutionException(this.partialName, [String? customMessage])
      : super(customMessage ?? "Could not resolve partial: $partialName");

  /// The name of the partial that couldn't be resolved.
  final String partialName;

  @override
  String toString() => "PartialResolutionException: $message";
}

/// Exception thrown when a tool cannot be resolved.
class ToolResolutionException extends DotpromptException {
  /// Creates a new [ToolResolutionException].
  ToolResolutionException(this.toolName, [String? customMessage])
      : super(customMessage ?? "Could not resolve tool: $toolName");

  /// The name of the tool that couldn't be resolved.
  final String toolName;

  @override
  String toString() => "ToolResolutionException: $message";
}

/// Exception thrown when schema validation fails.
class SchemaValidationException extends DotpromptException {
  /// Creates a new [SchemaValidationException].
  const SchemaValidationException(super.message, {this.errors});

  /// List of validation error details.
  final List<String>? errors;

  @override
  String toString() {
    if (errors != null && errors!.isNotEmpty) {
      return "SchemaValidationException: $message\nErrors:\n"
          "${errors!.map((e) => "  - $e").join("\n")}";
    }
    return "SchemaValidationException: $message";
  }
}

/// Exception thrown when a store operation fails.
class StoreException extends DotpromptException {
  /// Creates a new [StoreException].
  const StoreException(super.message, [super.cause]);

  @override
  String toString() => "StoreException: $message";
}

/// Exception thrown when Picoschema conversion fails.
class PicoschemaException extends DotpromptException {
  /// Creates a new [PicoschemaException].
  const PicoschemaException(super.message, [super.cause]);

  @override
  String toString() => "PicoschemaException: $message";
}
