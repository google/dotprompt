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

/// Dotprompt: Executable GenAI Prompt Templates for Dart.
///
/// This library provides a Dart implementation of the Dotprompt format, which
/// is a language-neutral executable prompt template format for Generative AI.
///
/// ## Features
///
/// - YAML frontmatter for prompt metadata
/// - Handlebars-style templating
/// - Picoschema to JSON Schema conversion
/// - Built-in helpers for common prompt patterns
/// - Type-safe prompt rendering
///
/// ## Example
///
/// ```dart
/// import 'package:dotprompt/dotprompt.dart';
///
/// void main() {
///   final dotprompt = Dotprompt();
///   final template = '''
/// ---
/// model: gemini-pro
/// ---
/// Hello {{name}}!
/// ''';
///
///   final data = DataArgument(input: {'name': 'World'});
///   final result = dotprompt.render(template, data);
///   print(result.messages);
/// }
/// ```
///
/// ## Core Components
///
/// - [Dotprompt]: Main entry point for parsing and rendering prompts
/// - [RenderedPrompt]: Result of rendering a prompt template
/// - [Message]: A chat message with role and content parts
/// - [Part]: Abstract class for message content (text, media, tools)
library;

import "dotprompt.dart" show Dotprompt, Message, Part, RenderedPrompt;

export "src/dotprompt.dart";
export "src/error.dart";
export "src/helpers/helpers.dart";
export "src/models/models.dart";
export "src/parse.dart";
export "src/picoschema.dart";
export "src/store.dart";
export "src/types.dart";
