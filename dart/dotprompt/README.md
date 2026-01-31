# Dotprompt for Dart

Dart implementation of [Dotprompt](https://github.com/google/dotprompt), an
executable prompt template file format for Generative AI.

## Overview

Dotprompt provides a structured way to create, manage, and render prompt
templates for Large Language Models. This Dart implementation offers:

- **YAML frontmatter** for configuration and metadata
- **Handlebars-style templating** for dynamic content
- **Picoschema support** for input/output validation
- **Tool and schema resolution** for complex workflows
- **Cross-runtime conformance** with JavaScript, Python, Go, Rust, and Java

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
  
  // Parse and render a prompt
  final result = await dotprompt.render('''
---
model: gemini-pro
config:
  temperature: 0.7
---
Hello {{name}}! You are a {{role}}.
''', DataArgument(
    input: {'name': 'World', 'role': 'helpful assistant'},
  ));
  
  print(result.messages.first.content);
  // Output: [TextPart(text: "Hello World! You are a helpful assistant.")]
}
```

## Features

### Template Parsing

```dart
final parsed = dotprompt.parse('''
---
model: gemini-pro
input:
  schema:
    name: string
    age: integer?
  default:
    name: User
---
Hello {{name}}!
''');

print(parsed.model);  // "gemini-pro"
print(parsed.input?.schema);  // Schema definition
```

### Compiled Templates

For repeated rendering with different data:

```dart
final compiled = await dotprompt.compile(templateSource);

// Render multiple times
final result1 = await compiled.render(DataArgument(input: {'name': 'Alice'}));
final result2 = await compiled.render(DataArgument(input: {'name': 'Bob'}));
```

### Partials

```dart
final dotprompt = Dotprompt(DotpromptOptions(
  partials: {
    'header': 'Welcome, {{user}}!',
    'footer': 'Best regards, {{sender}}',
  },
));

final result = await dotprompt.render('''
{{> header}}
Your message here.
{{> footer}}
''', DataArgument(
    input: {'user': 'Alice', 'sender': 'Bot'},
  ));
```

### Role Markers

Control message roles in multi-turn conversations:

```dart
final result = await dotprompt.render('''
{{role "system"}}
You are a helpful assistant.

{{role "user"}}
Hello!

{{role "model"}}
Hi there! How can I help?
''', DataArgument());

// Results in 3 messages with appropriate roles
```

### Media Embedding

```dart
final result = await dotprompt.render('''
Please analyze this image:
{{media url="https://example.com/image.png" contentType="image/png"}}
''', DataArgument());
```

## API Reference

### Core Classes

| Class | Description |
|-------|-------------|
| `Dotprompt` | Main entry point for parsing and rendering |
| `ParsedPrompt` | Result of parsing a template |
| `RenderedPrompt` | Result of rendering with data |
| `Message` | A chat message with role and content |
| `Part` | Message content (TextPart, MediaPart, etc.) |

### Configuration

```dart
final dotprompt = Dotprompt(DotpromptOptions(
  defaultModel: 'gemini-pro',
  modelConfigs: {
    'gemini-pro': {'temperature': 0.7},
  },
  partials: {'...': '...'},
  tools: {'...': ToolDefinition(...)},
  schemas: {'...': {...}},
  partialResolver: (name) async => '...',
  toolResolver: (name) async => {...},
  schemaResolver: (name) async => {...},
));
```

## Built-in Helpers

| Helper | Usage | Description |
|--------|-------|-------------|
| `role` | `{{role "system"}}` | Sets message role |
| `media` | `{{media url="..." contentType="..."}}` | Embeds media |
| `history` | `{{history}}` | Inserts conversation history |
| `json` | `{{json data}}` | JSON serialization |
| `section` | `{{#section "name"}}...{{/section}}` | Named sections |
| `ifEquals` | `{{#ifEquals a b}}...{{/ifEquals}}` | Conditional |
| `unlessEquals` | `{{#unlessEquals a b}}...{{/unlessEquals}}` | Inverse conditional |

## Building with Bazel

This package is built using [rules_dart](../../bazel/rules_dart/README.md):

```bash
# Build the library
bazel build //dart/dotprompt

# Run tests
bazel test //dart/dotprompt/test:...
```

## License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.
