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

/// Main Dotprompt class for parsing and rendering prompt templates.
///
/// This is the primary entry point for the Dotprompt library, providing
/// methods for parsing, compiling, and rendering prompt templates.
///
/// ## Key Features
///
/// - Template parsing with YAML frontmatter extraction
/// - Handlebars-style variable substitution
/// - Built-in helpers for common patterns
/// - Partial template support
/// - Tool and schema resolution
/// - Model configuration management
///
/// ## Example Usage
///
/// ```dart
/// final dotprompt = Dotprompt();
///
/// // Parse a template
/// final parsed = dotprompt.parse('''
/// ---
/// model: gemini-pro
/// ---
/// Hello {{name}}!
/// ''');
///
/// // Render with data
/// final result = await dotprompt.render(parsed.template, DataArgument(
///   input: {'name': 'World'},
/// ));
///
/// print(result.messages.first.content);  // "Hello World!"
/// ```
library;

import "dart:async";
import "dart:convert";

import "package:handlebars_dart/handlebars_dart.dart";

import "error.dart";
import "helpers/media_helper.dart";
import "helpers/role_helper.dart";
import "helpers/section_helper.dart";
import "models/models.dart";
import "parse.dart";
import "picoschema.dart";
import "store.dart";
import "types.dart";

/// Configuration options for a [Dotprompt] instance.
///
/// Allows customization of model defaults, helpers, partials, and resolvers.
class DotpromptOptions {
  /// Creates a new [DotpromptOptions].
  const DotpromptOptions({
    this.defaultModel,
    this.modelConfigs,
    this.helpers,
    this.partials,
    this.tools,
    this.schemas,
    this.partialResolver,
    this.toolResolver,
    this.schemaResolver,
    this.store,
  });

  /// The default model to use if none is specified in the template.
  final String? defaultModel;

  /// Model-specific configuration overrides.
  final Map<String, Map<String, dynamic>>? modelConfigs;

  /// Custom helper functions.
  final Map<String, Function>? helpers;

  /// Pre-registered partial templates.
  final Map<String, String>? partials;

  /// Pre-registered tool definitions.
  final Map<String, ToolDefinition>? tools;

  /// Pre-registered schemas (Picoschema or JSON Schema).
  final Map<String, Map<String, dynamic>>? schemas;

  /// Resolver for loading partial templates dynamically.
  final DotpromptPartialResolver? partialResolver;

  /// Resolver for loading tool definitions dynamically.
  final ToolResolver? toolResolver;

  /// Resolver for loading schemas dynamically.
  final SchemaResolver? schemaResolver;

  /// Store for loading prompts and partials.
  final PromptStore? store;
}

/// Main entry point for the Dotprompt library.
///
/// Provides methods for parsing, compiling, and rendering prompt templates.
class Dotprompt {
  /// Creates a new [Dotprompt] instance with optional configuration.
  Dotprompt([DotpromptOptions? options])
      : _options = options ?? const DotpromptOptions(),
        _partials = Map<String, String>.from(options?.partials ?? {}),
        _tools = Map<String, ToolDefinition>.from(options?.tools ?? {}),
        _schemas = Map<String, Map<String, dynamic>>.from(options?.schemas ?? {});

  final DotpromptOptions _options;
  final Map<String, String> _partials;
  final Map<String, ToolDefinition> _tools;
  final Map<String, Map<String, dynamic>> _schemas;

  /// The default model for this instance.
  String? get defaultModel => _options.defaultModel;

  /// Custom helpers registry.
  final Map<String, HelperFunction> _helpers = {};

  /// Defines a custom helper function.
  ///
  /// The helper will be available in templates as {{helperName ...}}.
  void defineHelper(String name, HelperFunction helper) {
    _helpers[name] = helper;
  }

  /// Defines a partial template.
  ///
  /// The partial will be available in templates as {{> partialName}}.
  void definePartial(String name, String template) {
    _partials[name] = template;
  }

  /// Defines a tool for use in prompts.
  void defineTool(ToolDefinition definition) {
    _tools[definition.name] = definition;
  }

  /// Defines a schema (Picoschema or JSON Schema).
  void defineSchema(String name, Map<String, dynamic> schema) {
    _schemas[name] = schema;
  }

  /// Parses a prompt template source into a [ParsedPrompt].
  ///
  /// Extracts the YAML frontmatter and template body.
  ///
  /// Throws [ParseException] if parsing fails.
  ParsedPrompt parse(String source) => Parser.parseDocument(source);

  /// Compiles a template for repeated rendering.
  ///
  /// Returns a function that can be called multiple times with different
  /// data to render the same template.
  Future<PromptFunction> compile(String source) async {
    final parsed = parse(source);
    await _resolvePartials(parsed.template);
    return _CompiledPromptFunction(this, parsed);
  }

  /// Renders a prompt template with the provided data.
  ///
  /// This is a convenience method that combines parsing and rendering.
  Future<RenderedPrompt> render(
    String source,
    DataArgument data, [
    Map<String, dynamic>? options,
  ]) async {
    final promptFn = await compile(source);
    return promptFn.render(data, options);
  }

  /// Renders the metadata for a template without rendering the full template.
  ///
  /// Useful when you need resolved metadata (tools, schemas) without the
  /// message content.
  Future<PromptMetadata> renderMetadata(String source) async {
    final parsed = parse(source);
    return _resolveMetadata(parsed.metadata);
  }

  /// Resolves partial references in a template.
  Future<void> _resolvePartials(String template) async {
    final partialPattern = RegExp(r"\{\{>\s*([a-zA-Z0-9_.-]+)");
    final matches = partialPattern.allMatches(template);

    for (final match in matches) {
      final name = match.group(1)!;
      if (_partials.containsKey(name)) continue;

      // Try resolver first
      if (_options.partialResolver != null) {
        final content = await _options.partialResolver!(name);
        if (content != null) {
          _partials[name] = content;
          await _resolvePartials(content); // Recursive resolution
          continue;
        }
      }

      // Try store
      if (_options.store != null) {
        final data = await _options.store!.loadPartial(name, null);
        if (data != null) {
          _partials[name] = data.source;
          await _resolvePartials(data.source); // Recursive resolution
        }
      }
    }
  }

  /// Resolves metadata, including tools and schemas.
  Future<PromptMetadata> _resolveMetadata(PromptMetadata metadata) async {
    // Resolve model
    final model = metadata.model ?? _options.defaultModel;

    // Build config from model defaults and template config
    final config = <String, dynamic>{};
    if (model != null && (_options.modelConfigs?.containsKey(model) ?? false)) {
      config.addAll(_options.modelConfigs![model]!);
    }
    if (metadata.config != null) {
      config.addAll(metadata.config!);
    }

    // Resolve tools
    final toolDefs = <ToolDefinition>[];
    final unresolvedTools = <String>[];

    if (metadata.tools != null) {
      for (final toolName in metadata.tools!) {
        if (_tools.containsKey(toolName)) {
          toolDefs.add(_tools[toolName]!);
        } else if (_options.toolResolver != null) {
          final resolved = await _options.toolResolver!(toolName);
          if (resolved != null) {
            toolDefs.add(ToolDefinition.fromJson(resolved));
          } else {
            unresolvedTools.add(toolName);
          }
        } else {
          unresolvedTools.add(toolName);
        }
      }
    }

    // Process schemas (convert Picoschema to JSON Schema)
    var input = metadata.input;
    var output = metadata.output;

    if (input?.schema != null && Picoschema.isPicoschema(input!.schema!)) {
      final jsonSchema = Picoschema.toJsonSchema(
        input.schema,
        schemas: _schemas,
      );
      input = InputConfig(
        schema: jsonSchema,
        defaultValues: input.defaultValues,
      );
    }

    if (output?.schema != null && Picoschema.isPicoschema(output!.schema!)) {
      final jsonSchema = Picoschema.toJsonSchema(
        output.schema,
        schemas: _schemas,
      );
      output = OutputConfig(format: output.format, schema: jsonSchema);
    }

    return PromptMetadata(
      model: model,
      config: config.isNotEmpty ? config : null,
      input: input,
      output: output,
      tools: unresolvedTools.isNotEmpty ? unresolvedTools : null,
      toolDefs: toolDefs.isNotEmpty ? toolDefs : null,
      ext: metadata.ext,
      raw: metadata.raw,
    );
  }

  /// Renders a template with the given data.
  Future<RenderedPrompt> _renderInternal(
    ParsedPrompt parsed,
    DataArgument data,
    Map<String, dynamic>? options,
  ) async {
    // Build merged data context
    final mergedData = <String, dynamic>{};

    // Add input defaults
    if (parsed.input?.defaultValues != null) {
      mergedData.addAll(parsed.input!.defaultValues!);
    }

    // Add options input defaults
    if (options?["input"] case {"default": final Map<dynamic, dynamic> defaults}) {
      mergedData.addAll(defaults.cast<String, dynamic>());
    }

    // Add provided input (overrides defaults)
    if (data.input != null) {
      mergedData.addAll(data.input!);
    }

    // Context data is passed as the data parameter to template rendering
    // for access via @ variables (e.g., @auth.email, @user.role)

    // Render template using Handlebars
    final hb = Handlebars(escapeHtml: false)
      // Register built-in Dotprompt helpers
      ..registerHelper("role", (args, options) {
        final role = args.isNotEmpty ? args[0].toString() : "user";
        return SafeString("<<<dotprompt:role:$role>>>");
      })
      ..registerHelper(
        "history",
        (args, options) => const SafeString("<<<dotprompt:history>>>"),
      )
      ..registerHelper("section", (args, options) {
        final name = args.isNotEmpty ? args[0].toString() : "default";
        return SafeString("<<<dotprompt:section $name>>>");
      })
      ..registerHelper("media", (args, options) {
        final url = options.hash["url"]?.toString() ?? "";
        final contentType = options.hash["contentType"]?.toString();
        return SafeString(
          MediaHelper.createMarker(url: url, contentType: contentType),
        );
      })
      ..registerHelper("json", (args, options) {
        if (args.isEmpty) return "null";
        final value = args[0];
        final indent = options.hash["indent"];

        // Use proper JSON encoding
        if (indent != null && indent is int && indent > 0) {
          return JsonEncoder.withIndent(" " * indent).convert(value);
        }
        return jsonEncode(value);
      })
      // Register ifEquals block helper
      ..registerHelper("ifEquals", (args, options) {
        if (args.length >= 2 && args[0] == args[1]) {
          return options.fn(options.context);
        } else {
          return options.inverse(options.context);
        }
      })
      // Register unlessEquals block helper
      ..registerHelper("unlessEquals", (args, options) {
        if (args.length >= 2 && args[0] != args[1]) {
          return options.fn(options.context);
        } else {
          return options.inverse(options.context);
        }
      });

    // Register custom user-defined helpers
    for (final entry in _helpers.entries) {
      hb.registerHelper(entry.key, entry.value);
    }

    // Register partials
    for (final entry in _partials.entries) {
      hb.registerPartial(entry.key, entry.value);
    }

    // Compile and render template
    final renderFn = hb.compile(parsed.template);
    final renderedString = renderFn(mergedData, data: data.context?.toJson());

    // Convert rendered string to messages
    var messages = _toMessages(renderedString, historyMessages: data.messages);

    // Fallback: If history was provided but no history marker in template,
    // insert history after any system messages
    final historyAlreadyInserted = messages.any(
      (m) => m.metadata?["purpose"] == "history",
    );
    if (data.messages != null && data.messages!.isNotEmpty && !historyAlreadyInserted) {
      final historyMessages = data.messages!;
      final finalMessages = <Message>[];

      // Find the index after the last system message
      var insertIndex = 0;
      for (var i = 0; i < messages.length; i++) {
        if (messages[i].role == Role.system) {
          insertIndex = i + 1;
        }
      }

      // Insert system messages, then history, then rest
      finalMessages
        ..addAll(messages.sublist(0, insertIndex))
        ..addAll(
          historyMessages.map(
            (m) => Message(
              role: m.role,
              content: m.content,
              metadata: {...?m.metadata, "purpose": "history"},
            ),
          ),
        )
        ..addAll(messages.sublist(insertIndex));
      messages = finalMessages;
    }

    // Build result config
    final resolvedMetadata = await _resolveMetadata(parsed.metadata);
    final resultConfig = resolvedMetadata.toConfig();

    // Add input config showing defaults that were used
    final inputOptions = options?["input"];
    final inputDefault = (inputOptions is Map) ? inputOptions["default"] : null;

    if (parsed.input?.defaultValues != null || inputDefault != null) {
      final inputConfig =
          resultConfig["input"] != null ? Map<String, dynamic>.from(resultConfig["input"] as Map) : <String, dynamic>{};

      if (parsed.input?.defaultValues != null) {
        inputConfig["default"] = parsed.input!.defaultValues;
      }
      if (inputDefault != null) {
        inputConfig["default"] = inputDefault;
      }

      resultConfig["input"] = inputConfig;
    }

    return RenderedPrompt(config: resultConfig, messages: messages);
  }

  /// Converts rendered template string to messages.
  ///
  /// If [historyMessages] is provided and the template contains a
  /// `<<<dotprompt:history>>>` marker, the history will be inserted there.
  List<Message> _toMessages(String rendered, {List<Message>? historyMessages}) {
    const historyMarker = "<<<dotprompt:history>>>";
    final messages = <Message>[];
    var currentRole = Role.user; // Default role
    final currentParts = <Part>[];
    final currentText = StringBuffer();
    var historyInserted = false;

    void flushText() {
      final text = currentText.toString();
      if (text.isNotEmpty) {
        // Check for media or section markers in text
        if (MediaHelper.containsMarker(text) || SectionHelper.containsMarker(text)) {
          final parts = _parseMarkers(text);
          currentParts.addAll(parts);
        } else {
          currentParts.add(TextPart(text: text));
        }
        currentText.clear();
      }
    }

    void flushMessage() {
      flushText();
      if (currentParts.isNotEmpty) {
        messages.add(
          Message(role: currentRole, content: List.from(currentParts)),
        );
        currentParts.clear();
      }
    }

    // Process the rendered string
    final lines = rendered.split("\n");
    for (var i = 0; i < lines.length; i++) {
      final line = lines[i];

      // Check for history marker
      if (line.contains(historyMarker)) {
        // Remove history marker from the line
        final cleanLine = line.replaceAll(historyMarker, "");

        // Add trailing newline to previous content (the newline before this marker)
        if (currentText.isNotEmpty) {
          currentText.write("\n");
        }

        // Add remaining content before history (if any text on same line as marker)
        if (cleanLine.trim().isNotEmpty) {
          currentText.write(cleanLine);
        }
        flushMessage();

        // Insert history messages with purpose metadata
        if (historyMessages != null && historyMessages.isNotEmpty && !historyInserted) {
          for (final msg in historyMessages) {
            messages.add(
              Message(
                role: msg.role,
                content: msg.content,
                metadata: {...?msg.metadata, "purpose": "history"},
              ),
            );
          }
          historyInserted = true;
        }

        // Reset to model role after history
        currentRole = Role.model;
        continue;
      }

      // Check for role markers
      if (RoleHelper.containsMarker(line)) {
        final roleMatch = RegExp(
          "${RegExp.escape(RoleHelper.markerPrefix)}([^>]+)${RegExp.escape(RoleHelper.markerSuffix)}",
        ).firstMatch(line);
        if (roleMatch != null) {
          // Before switching roles, add trailing newline if not at start
          // (the newline that was between previous content and this role marker)
          if (currentText.isNotEmpty) {
            currentText.write("\n");
          }
          flushMessage();
          currentRole = Role.fromString(roleMatch.group(1)!);
          final remaining = line.replaceAll(roleMatch.group(0)!, "");
          // Don't trim - preserve leading/trailing whitespace in content
          if (remaining.isNotEmpty) {
            currentText.write(remaining);
          }
          continue;
        }
      }

      // Regular line
      if (currentText.isNotEmpty) {
        currentText.write("\n");
      }
      currentText.write(line);
    }

    flushMessage();

    // If no messages were created, create a single user message
    if (messages.isEmpty && rendered.trim().isNotEmpty) {
      return [
        Message(
          role: Role.user,
          content: [TextPart(text: rendered.trim())],
        ),
      ];
    }

    return messages;
  }

  /// Parses media and section markers in text into parts.
  List<Part> _parseMarkers(String text) {
    final parts = <Part>[];
    // Combined pattern for both media and section markers
    final pattern = RegExp("<<<dotprompt:(media:[^>]+|section [^>]+)>>>");

    var lastEnd = 0;
    for (final match in pattern.allMatches(text)) {
      // Add text before marker
      if (match.start > lastEnd) {
        final textBefore = text.substring(lastEnd, match.start);
        if (textBefore.isNotEmpty) {
          parts.add(TextPart(text: textBefore));
        }
      }

      final markerContent = match.group(1)!;

      if (markerContent.startsWith("media:")) {
        // Parse media marker
        final media = MediaHelper.extractMedia(match.group(0)!);
        if (media != null) {
          parts.add(MediaPart(media: media));
        }
      } else if (markerContent.startsWith("section ")) {
        // Parse section marker
        final sectionName = markerContent.substring("section ".length);
        parts.add(
          MetadataPart(metadata: {"pending": true, "purpose": sectionName}),
        );
      }

      lastEnd = match.end;
    }

    // Add remaining text
    if (lastEnd < text.length) {
      final remaining = text.substring(lastEnd);
      if (remaining.isNotEmpty) {
        parts.add(TextPart(text: remaining));
      }
    }

    return parts;
  }
}

/// A compiled prompt function for repeated rendering.
abstract interface class PromptFunction {
  /// Renders the prompt with the given data.
  Future<RenderedPrompt> render(
    DataArgument data, [
    Map<String, dynamic>? options,
  ]);

  /// Gets the parsed prompt.
  ParsedPrompt get prompt;
}

/// Internal implementation of [PromptFunction].
class _CompiledPromptFunction implements PromptFunction {
  _CompiledPromptFunction(this._dotprompt, this._parsed);

  final Dotprompt _dotprompt;
  final ParsedPrompt _parsed;

  @override
  Future<RenderedPrompt> render(
    DataArgument data, [
    Map<String, dynamic>? options,
  ]) =>
      _dotprompt._renderInternal(_parsed, data, options);

  @override
  ParsedPrompt get prompt => _parsed;
}
