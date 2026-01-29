# handlebarrz

The `handlebarrz` package (published as `dotpromptz-handlebars` on PyPI) provides
Python bindings to the Handlebars templating engine via Rust FFI.

## Installation

```bash
pip install dotpromptz-handlebars
```

## Quick Start

```python
from handlebarrz import Handlebars

# Create a Handlebars instance
hbs = Handlebars()

# Register and render a template
hbs.register_template('greeting', 'Hello, {{name}}!')
result = hbs.render('greeting', {'name': 'World'})
print(result)  # "Hello, World!"
```

## Features

- Block helpers with inverse sections (`else` blocks)
- Built-in helpers (`each`, `if`, `unless`, `with`, `lookup`, `log`)
- Context navigation (`this`, `../parent`, `@root`)
- Custom helper functions
- HTML escaping options and customization
- Partial templates and blocks
- Strict mode for missing fields
- Subexpressions and parameter literals
- Whitespace control with `~` operator

## Module Reference

::: handlebarrz
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Template Class

::: handlebarrz.Template
    options:
      show_root_heading: true
      show_source: true
      members_order: source
      heading_level: 3

## Escape Functions

::: handlebarrz.EscapeFunction
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## Helper Options

::: handlebarrz.HelperOptions
    options:
      show_root_heading: true
      show_source: true
      members_order: source
      heading_level: 3
