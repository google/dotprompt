# dotpromptz-handlebars

[![PyPI](https://img.shields.io/pypi/v/dotpromptz-handlebars)](https://pypi.org/project/dotpromptz-handlebars/)
[![Python](https://img.shields.io/pypi/pyversions/dotpromptz-handlebars)](https://pypi.org/project/dotpromptz-handlebars/)
[![License](https://img.shields.io/pypi/l/dotpromptz-handlebars)](https://github.com/google/dotprompt/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/dotpromptz-handlebars)](https://pypi.org/project/dotpromptz-handlebars/)

[![CI](https://github.com/google/dotprompt/actions/workflows/handlebarrz-tests.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/handlebarrz-tests.yml)
[![codecov](https://codecov.io/gh/google/dotprompt/graph/badge.svg?flag=handlebarrz)](https://codecov.io/gh/google/dotprompt)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/google/dotprompt/badge)](https://scorecard.dev/viewer/?uri=github.com/google/dotprompt)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10359/badge)](https://www.bestpractices.dev/projects/10359)

A high-performance [Handlebars](https://handlebarsjs.com/) template engine for Python, powered by Rust.

This package provides Python bindings to [handlebars-rust](https://github.com/sunng87/handlebars-rust), offering near-native performance for template rendering while maintaining a Pythonic API.

## Features

- **Fast**: Rust-powered template compilation and rendering
- **Compatible**: Implements the Handlebars specification
- **Safe**: HTML escaping by default, with options for raw output
- **Extensible**: Support for custom helpers and partials
- **Type-safe**: Full type hints for IDE support

## Installation

```bash
pip install dotpromptz-handlebars
```

## Quick Start

```python
from handlebarrz import Template

# Create a template instance
template = Template()

# Register and render a template
template.register_template("greeting", "Hello, {{name}}!")
result = template.render("greeting", {"name": "World"})
print(result)  # Output: Hello, World!
```

## Usage

### Basic Templating

```python
from handlebarrz import Template

template = Template()

# Simple variable substitution
template.register_template("simple", "Welcome, {{user}}!")
print(template.render("simple", {"user": "Alice"}))
# Output: Welcome, Alice!

# Nested properties
template.register_template("nested", "{{person.name}} is {{person.age}} years old")
print(template.render("nested", {"person": {"name": "Bob", "age": 30}}))
# Output: Bob is 30 years old
```

### Built-in Helpers

```python
# Conditionals
template.register_template("conditional", """
{{#if active}}
  User is active
{{else}}
  User is inactive
{{/if}}
""")

# Iteration
template.register_template("list", """
{{#each items}}
  - {{this}}
{{/each}}
""")

# With helper for context switching
template.register_template("with", """
{{#with user}}
  Name: {{name}}, Email: {{email}}
{{/with}}
""")
```

### Custom Helpers

```python
from handlebarrz import Template

template = Template()

# Register a custom helper
def uppercase(value):
    return str(value).upper()

template.register_helper("uppercase", uppercase)
template.register_template("custom", "{{uppercase name}}")
print(template.render("custom", {"name": "alice"}))
# Output: ALICE
```

### Partials

```python
template = Template()

# Register a partial
template.register_partial("header", "<h1>{{title}}</h1>")
template.register_template("page", "{{> header}}<p>{{content}}</p>")
print(template.render("page", {"title": "Welcome", "content": "Hello!"}))
# Output: <h1>Welcome</h1><p>Hello!</p>
```

### HTML Escaping

```python
template = Template()

# HTML is escaped by default
template.register_template("escaped", "{{content}}")
print(template.render("escaped", {"content": "<script>alert('xss')</script>"}))
# Output: &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;

# Use triple braces for raw output
template.register_template("raw", "{{{content}}}")
print(template.render("raw", {"content": "<b>bold</b>"}))
# Output: <b>bold</b>
```

## API Reference

### Template Class

| Method | Description |
|--------|-------------|
| `register_template(name, source)` | Register a template with a name |
| `render(name, context)` | Render a registered template with context |
| `render_template_string(source, context)` | Render a template string directly |
| `register_helper(name, func)` | Register a custom helper function |
| `register_partial(name, source)` | Register a partial template |
| `unregister_template(name)` | Remove a registered template |
| `set_strict_mode(enabled)` | Enable/disable strict mode |
| `set_dev_mode(enabled)` | Enable/disable development mode |

## Part of Dotprompt

This package is part of the [Dotprompt](https://github.com/google/dotprompt) project, providing the Handlebars templating engine for the `dotpromptz` Python package. While primarily designed for Dotprompt, it can be used as a standalone Handlebars implementation for Python.

## License

Apache-2.0
