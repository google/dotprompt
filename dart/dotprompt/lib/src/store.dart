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

/// Prompt storage abstraction for Dotprompt.
///
/// Provides interfaces for loading and storing prompt templates, enabling
/// various storage backends (filesystem, database, remote API, etc.).
library;

import "dart:async";

/// Data returned when loading a prompt.
class PromptData {
  /// Creates a new [PromptData].
  const PromptData({
    required this.source,
    this.name,
    this.variant,
    this.hash,
    this.version,
    this.metadata,
  });

  /// The prompt source content.
  final String source;

  /// The prompt name.
  final String? name;

  /// The variant name, if any.
  final String? variant;

  /// Content hash for caching.
  final String? hash;

  /// Version identifier.
  final String? version;

  /// Additional metadata.
  final Map<String, dynamic>? metadata;
}

/// Data returned when loading a partial.
class PartialData {
  /// Creates a new [PartialData].
  const PartialData({required this.source, this.name, this.hash});

  /// The partial source content.
  final String source;

  /// The partial name.
  final String? name;

  /// Content hash for caching.
  final String? hash;
}

/// Options for loading a prompt.
class LoadPromptOptions {
  /// Creates new [LoadPromptOptions].
  const LoadPromptOptions({this.variant, this.version});

  /// The variant to load.
  final String? variant;

  /// The version to load.
  final String? version;
}

/// Options for loading a partial.
class LoadPartialOptions {
  /// Creates new [LoadPartialOptions].
  const LoadPartialOptions({this.version});

  /// The version to load.
  final String? version;
}

/// Abstract interface for prompt storage.
///
/// Implementations provide mechanisms for loading and optionally storing
/// prompt templates and partials.
///
/// ## Example Implementation
///
/// ```dart
/// class FileSystemStore implements PromptStore {
///   final String basePath;
///
///   FileSystemStore(this.basePath);
///
///   @override
///   Future<PromptData?> load(String name, LoadPromptOptions? options) async {
///     final file = File('$basePath/$name.prompt');
///     if (await file.exists()) {
///       return PromptData(source: await file.readAsString(), name: name);
///     }
///     return null;
///   }
///
///   // ... other methods
/// }
/// ```
abstract interface class PromptStore {
  /// Loads a prompt by name.
  ///
  /// Returns null if the prompt is not found.
  Future<PromptData?> load(String name, LoadPromptOptions? options);

  /// Loads a partial by name.
  ///
  /// Returns null if the partial is not found.
  Future<PartialData?> loadPartial(String name, LoadPartialOptions? options);

  /// Lists all available prompts.
  Future<List<String>> list();

  /// Lists all available partials.
  Future<List<String>> listPartials();
}

/// Interface for writable prompt stores.
///
/// Extends [PromptStore] with write operations.
abstract interface class PromptStoreWritable implements PromptStore {
  /// Saves a prompt.
  Future<void> save(String name, String source, {String? variant});

  /// Saves a partial.
  Future<void> savePartial(String name, String source);

  /// Deletes a prompt.
  Future<void> delete(String name, {String? variant});

  /// Deletes a partial.
  Future<void> deletePartial(String name);
}

/// Function type for resolving partial templates.
typedef DotpromptPartialResolver = Future<String?> Function(String name);

/// Function type for resolving tool definitions.
typedef ToolResolver = Future<Map<String, dynamic>?> Function(String name);

/// Function type for resolving schemas.
typedef SchemaResolver = Future<Map<String, dynamic>?> Function(String name);
