# dotpromptz-handlebars

A pure-Python Handlebars implementation, owned by the Genkit team. It implements the subset of Handlebars that Dotprompt templates use, and treats Handlebars.js 4.7.9 as the spec. No Rust or Node at runtime.

## Installation

```bash
uv add dotpromptz-handlebars
```

## Quick Start

```python
from dotpromptz_handlebars import Handlebars

# 1. Compile a template once
render = Handlebars().compile('Today: {{dish}} ({{price}})')

# 2. Render it with a context dict
print(render({'dish': 'Smoked Salmon Tartine', 'price': 14}))
# => Today: Smoked Salmon Tartine (14)
```

See the [package README](https://github.com/google/dotprompt/tree/main/python/handlebars) for helpers, partials, escaping, strict mode, and where Handlebars semantics differ from Python's.

## API Reference

::: dotpromptz_handlebars
    options:
      show_root_heading: false
      members_order: source
      heading_level: 3
