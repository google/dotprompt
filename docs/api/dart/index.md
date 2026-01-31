# Dart API

The `dotprompt` package is the Dart implementation of the Dotprompt file format.

## Installation

Add to your `pubspec.yaml`:

```yaml
dependencies:
  dotprompt: ^0.0.1
```

## Quick Start

```dart
import 'package:dotprompt/dotprompt.dart';

void main() async {
  final dotprompt = Dotprompt();

  final result = await dotprompt.render('''
---
model: gemini-pro
input:
  schema:
    name: string
---
Hello, {{name}}!
''', DataArgument(
    input: {'name': 'World'},
  ));

  for (final message in result.messages) {
    print('${message.role}: ${message.content}');
  }
}
```

## Core Types

### Dotprompt

The main entry point for working with Dotprompt templates.

```dart
class Dotprompt {
  /// Create a new Dotprompt instance with optional configuration.
  Dotprompt([DotpromptOptions? options]);

  /// Parse a template string into a ParsedPrompt.
  ParsedPrompt parse(String source);

  /// Compile a template into a reusable PromptFunction.
  Future<PromptFunction> compile(String source);

  /// Parse, compile, and render a template in one step.
  Future<RenderedPrompt> render(
    String source,
    DataArgument data, [
    Map<String, dynamic>? options,
  ]);

  /// Register a partial template.
  void definePartial(String name, String template);

  /// Register a tool definition.
  void defineTool(ToolDefinition definition);

  /// Register a schema.
  void defineSchema(String name, Map<String, dynamic> schema);
}
```

### DotpromptOptions

```dart
class DotpromptOptions {
  final String? defaultModel;
  final Map<String, Map<String, dynamic>>? modelConfigs;
  final Map<String, Function>? helpers;
  final Map<String, String>? partials;
  final Map<String, ToolDefinition>? tools;
  final Map<String, Map<String, dynamic>>? schemas;
  final DotpromptPartialResolver? partialResolver;
  final ToolResolver? toolResolver;
  final SchemaResolver? schemaResolver;
  final PromptStore? store;
}
```

## Types

### ParsedPrompt

```dart
class ParsedPrompt {
  final String template;
  final PromptMetadata metadata;

  String? get model;
  String? get name;
  String? get variant;
  String? get version;
  Map<String, dynamic>? get config;
  InputConfig? get input;
  OutputConfig? get output;
  List<String>? get tools;
  Map<String, Map<String, dynamic>>? get ext;
  Map<String, dynamic>? get raw;
}
```

### RenderedPrompt

```dart
class RenderedPrompt {
  final Map<String, dynamic> config;
  final List<Message> messages;
}
```

### Message

```dart
class Message {
  final Role role;
  final List<Part> content;
  final Map<String, dynamic>? metadata;
}

enum Role {
  user,
  model,
  tool,
  system;

  static Role fromString(String value);
}
```

### Part (Sealed Class Hierarchy)

```dart
sealed class Part {}

class TextPart extends Part {
  final String text;
  final Map<String, dynamic>? metadata;
}

class MediaPart extends Part {
  final MediaContent media;
  final Map<String, dynamic>? metadata;
}

class MediaContent {
  final String url;
  final String? contentType;
}

class DataPart extends Part {
  final Map<String, dynamic> data;
  final Map<String, dynamic>? metadata;
}

class ToolRequestPart extends Part {
  final ToolRequest toolRequest;
  final Map<String, dynamic>? metadata;
}

class ToolResponsePart extends Part {
  final ToolResponse toolResponse;
  final Map<String, dynamic>? metadata;
}

class PendingPart extends Part {
  final Map<String, dynamic>? metadata;
}
```

### DataArgument

```dart
class DataArgument {
  final Map<String, dynamic>? input;
  final List<Document>? docs;
  final List<Message>? messages;
  final Map<String, dynamic>? context;
}
```

### ToolDefinition

```dart
class ToolDefinition {
  final String name;
  final String? description;
  final Map<String, dynamic>? inputSchema;
  final Map<String, dynamic>? outputSchema;
}
```

## Error Handling

```dart
/// Base exception for all Dotprompt errors.
class DotpromptException implements Exception {
  final String message;
  final Object? cause;
}

/// Thrown when parsing fails.
class ParseException extends DotpromptException {}

/// Thrown when rendering fails.
class RenderException extends DotpromptException {}

/// Thrown when a partial cannot be resolved.
class PartialResolutionException extends DotpromptException {
  final String partialName;
}

/// Thrown when a tool cannot be resolved.
class ToolResolutionException extends DotpromptException {
  final String toolName;
}

/// Thrown when schema validation fails.
class SchemaValidationException extends DotpromptException {
  final List<String>? errors;
}

/// Thrown when Picoschema conversion fails.
class PicoschemaException extends DotpromptException {}
```

## Stores

### PromptStore Interface

```dart
abstract interface class PromptStore {
  Future<PromptData?> load(String name, LoadPromptOptions? options);
  Future<PartialData?> loadPartial(String name, LoadPartialOptions? options);
  Future<List<String>> list();
  Future<List<String>> listPartials();
}
```

## Picoschema

Convert Picoschema to JSON Schema.

```dart
import 'package:dotprompt/src/picoschema.dart';

final schema = {
  'name': 'string',
  'age?': 'integer, The person\'s age',
};

final jsonSchema = Picoschema.toJsonSchema(schema);
```

## Built-in Helpers

| Helper | Description | Example |
|--------|-------------|---------|
| `role` | Set message role | `{{role "system"}}` |
| `media` | Insert media content | `{{media url="..." contentType="image/png"}}` |
| `history` | Insert message history | `{{history}}` |
| `section` | Create a content section | `{{section "code"}}` |
| `json` | Serialize to JSON | `{{json data indent=2}}` |
| `ifEquals` | Conditional equality | `{{#ifEquals a b}}...{{/ifEquals}}` |
| `unlessEquals` | Conditional inequality | `{{#unlessEquals a b}}...{{/unlessEquals}}` |

## External Documentation

* [pub.dev](https://pub.dev/packages/dotprompt) (coming soon)
* [GitHub source](https://github.com/google/dotprompt/tree/main/dart/dotprompt)
