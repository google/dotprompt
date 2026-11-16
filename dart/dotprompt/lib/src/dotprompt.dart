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
/// model: googleai/gemini-flash-latest
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
import "helpers/history_helper.dart";
import "helpers/media_helper.dart";
import "helpers/role_helper.dart";
import "helpers/section_helper.dart";
import "markers.dart";
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

  /// Pre-registered JSON Schemas, referenced by name from Picoschema.
  ///
  /// Values must already be JSON Schema; they are inserted as-is (same as the
  /// other runtimes). Convert Picoschema first with [Picoschema.toJsonSchema].
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

  /// Registers a named JSON Schema that Picoschema can reference by name.
  ///
  /// [schema] must already be JSON Schema; it is inserted as-is. To register a
  /// schema written in Picoschema, convert it first:
  ///
  /// ```dart
  /// dotprompt.defineSchema('Address', Picoschema.toJsonSchema({'street': 'string', 'zip': 'integer'}));
  /// ```
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
  ///
  /// The optional [additionalMetadata] is merged on top of the metadata parsed
  /// from [source] using the same rules as [renderMetadata], and applies to
  /// every render produced by the returned function. This mirrors the
  /// `additionalMetadata` argument of the JavaScript reference implementation's
  /// `compile`.
  Future<PromptFunction> compile(
    String source, [
    PromptMetadata? additionalMetadata,
  ]) async {
    final parsed = parse(source);
    await _resolvePartials(parsed.template);
    return _CompiledPromptFunction(this, parsed, additionalMetadata);
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
  ///
  /// The optional [additionalMetadata] is merged on top of the metadata parsed
  /// from [source], overriding conflicting scalar fields (model, input, output,
  /// tools, ext) while shallow-merging the `config` map (additional config keys
  /// override base keys; nested objects are replaced wholesale). This mirrors
  /// the `additionalMetadata` argument of the JavaScript reference
  /// implementation and lets callers override or supplement a prompt's declared
  /// metadata at resolution time without editing the prompt source.
  Future<PromptMetadata> renderMetadata(
    String source, [
    PromptMetadata? additionalMetadata,
  ]) async {
    final parsed = parse(source);
    return _resolveMetadata(parsed.metadata, additionalMetadata);
  }

  /// Resolves partial references in a template.
  Future<void> _resolvePartials(String template) async {
    final partialPattern = RegExp(r"\{\{>\s*([a-zA-Z0-9_-]+)");
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
  ///
  /// When [additionalMetadata] is provided, its fields override those parsed
  /// from the prompt (scalar fields win outright) while the `config` map is
  /// shallow-merged (additional config keys override base keys; nested objects
  /// are replaced wholesale). This mirrors the merge behaviour of the
  /// JavaScript reference implementation's `resolveMetadata`/`renderMetadata`.
  Future<PromptMetadata> _resolveMetadata(
    PromptMetadata metadata, [
    PromptMetadata? additionalMetadata,
  ]) async {
    // Resolve model (additional metadata overrides parsed frontmatter).
    final model = additionalMetadata?.model ?? metadata.model ?? _options.defaultModel;

    // Build config from model defaults, template config, then additional config.
    final config = <String, dynamic>{};
    if (model != null && (_options.modelConfigs?.containsKey(model) ?? false)) {
      config.addAll(_options.modelConfigs![model]!);
    }
    if (metadata.config != null) {
      config.addAll(metadata.config!);
    }
    if (additionalMetadata?.config != null) {
      config.addAll(additionalMetadata!.config!);
    }

    // Additional metadata overrides parsed values for structured fields.
    final effectiveTools = additionalMetadata?.tools ?? metadata.tools;
    final effectiveInput = additionalMetadata?.input ?? metadata.input;
    final effectiveOutput = additionalMetadata?.output ?? metadata.output;
    final effectiveExt = additionalMetadata?.ext ?? metadata.ext;
    final effectiveRaw = additionalMetadata?.raw ?? metadata.raw;

    // Resolve tools
    final toolDefs = <ToolDefinition>[];
    final unresolvedTools = <String>[];

    if (effectiveTools != null) {
      for (final toolName in effectiveTools) {
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

    // Convert Picoschema to JSON Schema. JSON Schema input is passed through by
    // the converter itself.
    var input = effectiveInput;
    var output = effectiveOutput;

    final inputSchema = input?.schema;
    if (input != null && inputSchema != null) {
      input = InputConfig(
        schema: await _resolveSchema(inputSchema),
        defaultValues: input.defaultValues,
      );
    }

    final outputSchema = output?.schema;
    if (output != null && outputSchema != null) {
      output = OutputConfig(format: output.format, schema: await _resolveSchema(outputSchema));
    }

    return PromptMetadata(
      model: model,
      config: config.isNotEmpty ? config : null,
      input: input,
      output: output,
      tools: unresolvedTools.isNotEmpty ? unresolvedTools : null,
      toolDefs: toolDefs.isNotEmpty ? toolDefs : null,
      ext: effectiveExt,
      raw: effectiveRaw,
    );
  }

  /// Converts a frontmatter schema to JSON Schema, resolving named schemas from
  /// [defineSchema]/[DotpromptOptions.schemas] first and then
  /// [DotpromptOptions.schemaResolver].
  Future<Map<String, dynamic>> _resolveSchema(Map<String, dynamic> schema) => Picoschema.parse(
        schema,
        schemas: _schemas,
        schemaResolver: _options.schemaResolver,
      );

  /// Renders a template with the given data.
  Future<RenderedPrompt> _renderInternal(
    ParsedPrompt parsed,
    DataArgument data,
    Map<String, dynamic>? options, [
    PromptMetadata? additionalMetadata,
  ]) async {
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

    // Fresh per render so user-supplied values can't forge role/media/etc.
    // markers in the rendered string (see markers.dart). The marker helpers
    // below are registered per render and capture it directly, so it never
    // passes through template data or context and can't be overridden there.
    final nonce = generateMarkerNonce();

    // Render template using Handlebars
    final hb = Handlebars(escapeHtml: false)
      // Register built-in Dotprompt helpers
      ..registerHelper("role", (args, options) {
        final role = args.isNotEmpty ? args[0].toString() : "user";
        return SafeString(RoleHelper.createMarkerFromString(nonce, role));
      })
      ..registerHelper(
        "history",
        (args, options) => SafeString(HistoryHelper.createMarker(nonce)),
      )
      ..registerHelper("section", (args, options) {
        final name = args.isNotEmpty ? args[0].toString() : "default";
        return SafeString(SectionHelper.createMarker(nonce, name));
      })
      ..registerHelper("media", (args, options) {
        final url = options.hash["url"]?.toString() ?? "";
        final contentType = options.hash["contentType"]?.toString();
        return SafeString(
          MediaHelper.createMarker(nonce, url: url, contentType: contentType),
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
    var messages = _toMessages(renderedString, nonce, historyMessages: data.messages);

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
    final resolvedMetadata = await _resolveMetadata(parsed.metadata, additionalMetadata);
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

  /// Converts a rendered template string to messages.
  ///
  /// Only markers carrying [nonce] are honored; anything else, including
  /// marker look-alikes in user-supplied values, stays text. If
  /// [historyMessages] is provided and the template contains a history
  /// marker, the history is inserted there.
  ///
  /// ```text
  /// "<<<..:role:system>>>Be safe.\n<<<..:history>>>\n<<<..:role:user>>>Hi"
  ///   -> [system "Be safe.\n"], ...history, [user "Hi"]
  /// ```
  List<Message> _toMessages(String rendered, String nonce, {List<Message>? historyMessages}) {
    final messages = <Message>[];
    var currentRole = Role.user; // Default role
    final currentText = StringBuffer();
    var historyInserted = false;

    void flushMessage() {
      final text = currentText.toString();
      currentText.clear();
      if (text.isEmpty) return;
      final parts = _toParts(text, nonce);
      if (parts.isNotEmpty) {
        messages.add(Message(role: currentRole, content: parts));
      }
    }

    for (final piece in splitByMarkers(rendered, roleAndHistoryMarkerRegex(nonce))) {
      switch (piece) {
        case TextPiece(:final text):
          // Newlines are dropped while the current message is still empty, so
          // a marker on its own line doesn't leave a leading "\n" behind.
          currentText.write(currentText.isEmpty ? text.replaceFirst(_leadingNewlines, "") : text);
        case MarkerBodyPiece(body: historyMarkerBody):
          // Whitespace-only text before the history marker is discarded.
          if (currentText.toString().trim().isEmpty) currentText.clear();
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
        case MarkerBodyPiece(:final body):
          // The regex guarantees a `role:{name}` body here.
          final role = Role.fromString(body.substring(roleMarkerBodyPrefix.length));
          // Whitespace-only text doesn't start a message of its own; it is
          // carried over into the new role's message.
          if (currentText.toString().trim().isNotEmpty) flushMessage();
          currentRole = role;
      }
    }

    flushMessage();
    return messages;
  }

  static final RegExp _leadingNewlines = RegExp(r"^\n+");

  /// Converts message text into parts, turning media and section markers
  /// carrying [nonce] into media and pending metadata parts.
  List<Part> _toParts(String text, String nonce) => [
        for (final piece in splitByMarkers(text, mediaAndSectionMarkerRegex(nonce)))
          switch (piece) {
            TextPiece(:final text) => TextPart(text: text),
            MarkerBodyPiece(:final body) => _markerPart(body),
          },
      ];

  /// Converts a media or section marker body into a part.
  Part _markerPart(String body) {
    final media = MediaHelper.mediaFromBody(body);
    if (media != null) return MediaPart(media: media);
    final section = SectionHelper.sectionNameFromBody(body);
    if (section != null) {
      return MetadataPart(metadata: {"pending": true, "purpose": section});
    }
    // Unreachable: mediaAndSectionMarkerRegex only captures the bodies above.
    throw StateError("Unexpected dotprompt marker body: $body");
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
  _CompiledPromptFunction(this._dotprompt, this._parsed, [this._additionalMetadata]);

  final Dotprompt _dotprompt;
  final ParsedPrompt _parsed;
  final PromptMetadata? _additionalMetadata;

  @override
  Future<RenderedPrompt> render(
    DataArgument data, [
    Map<String, dynamic>? options,
  ]) =>
      _dotprompt._renderInternal(_parsed, data, options, _additionalMetadata);

  @override
  ParsedPrompt get prompt => _parsed;
}
