# Handlebars Dart

A pure Dart implementation of the [Handlebars](https://handlebarsjs.com/) template engine.

## Features

- **Variable substitution**: `{{name}}`, `{{user.email}}`
- **Dot notation paths**: `{{user.profile.name}}`
- **Helpers with arguments**: `{{helper arg1 arg2}}`
- **Hash arguments**: `{{helper key="value"}}`
- **Block helpers**: `{{#if condition}}...{{/if}}`
- **Inverse blocks**: `{{#if}}...{{else}}...{{/if}}`
- **Built-in block helpers**: `if`, `unless`, `each`, `with`
- **Partials**: `{{> partialName}}`
- **Comments**: `{{! comment }}` and `{{!-- long comment --}}`
- **Raw/unescaped output**: `{{{rawHtml}}}`
- **Data variables**: `{{@index}}`, `{{@first}}`, `{{@last}}`, `{{@root}}`
- **SafeString for bypassing HTML escaping**

## Installation

Add `handlebars_dart` to your `pubspec.yaml`:

```yaml
dependencies:
  handlebars_dart: ^0.0.1
```

## Usage

### Basic Variable Substitution

```dart
import 'package:handlebars_dart/handlebars_dart.dart';

void main() {
  final hb = Handlebars();
  final template = hb.compile('Hello {{name}}!');
  print(template({'name': 'World'}));  // "Hello World!"
}
```

### Custom Helpers

```dart
final hb = Handlebars();

// Simple helper
hb.registerHelper('upper', (args, options) {
  return args[0].toString().toUpperCase();
});

// Helper with hash arguments
hb.registerHelper('link', (args, options) {
  final url = options.hash['url'];
  final text = args.isNotEmpty ? args[0] : 'click';
  return SafeString('<a href="$url">$text</a>');
});

final template = hb.compile('{{upper name}} - {{link "Go" url="https://example.com"}}');
print(template({'name': 'hello'}));  // "HELLO - <a href="https://example.com">Go</a>"
```

### Block Helpers

```dart
final hb = Handlebars();

// if/else
final template = hb.compile('{{#if show}}visible{{else}}hidden{{/if}}');
print(template({'show': true}));   // "visible"
print(template({'show': false}));  // "hidden"

// each
final listTemplate = hb.compile('{{#each items}}{{.}} {{/each}}');
print(listTemplate({'items': ['a', 'b', 'c']}));  // "a b c "

// with index
final indexTemplate = hb.compile('{{#each items}}{{@index}}:{{.}} {{/each}}');
print(indexTemplate({'items': ['a', 'b']}));  // "0:a 1:b "
```

### Custom Block Helpers

```dart
final hb = Handlebars();

hb.registerHelper('ifEquals', (args, options) {
  if (args[0] == args[1]) {
    return options.fn(options.context);
  } else {
    return options.inverse(options.context);
  }
});

final template = hb.compile('{{#ifEquals status "active"}}Active{{else}}Inactive{{/ifEquals}}');
print(template({'status': 'active'}));  // "Active"
```

### Partials

```dart
final hb = Handlebars();

hb.registerPartial('greeting', 'Hello {{name}}!');
final template = hb.compile('{{> greeting}}');
print(template({'name': 'World'}));  // "Hello World!"
```

### HTML Escaping

By default, output is HTML-escaped:

```dart
final hb = Handlebars();
final template = hb.compile('{{content}}');
print(template({'content': '<script>alert("xss")</script>'}));
// "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;"

// Use triple braces for unescaped output
final unsafe = hb.compile('{{{content}}}');
print(unsafe({'content': '<b>bold</b>'}));  // "<b>bold</b>"

// Or use SafeString in helpers
hb.registerHelper('bold', (args, options) {
  return SafeString('<b>${args[0]}</b>');
});
```

## Why handlebars_dart?

- **Pure Dart**: No JavaScript dependencies or FFI bindings
- **Handlebars compatible**: Follows the Handlebars.js specification
- **Built for Dotprompt**: Perfect for AI prompt templating
- **Type safe**: Full Dart type safety and null safety

## License

Apache License 2.0 - see [LICENSE](../../LICENSE) file.
