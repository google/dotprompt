# dotpromptz

The `dotpromptz` package is the Python implementation of the Dotprompt file
format—an executable prompt template format for Generative AI.

## Installation

```bash
uv add dotpromptz
```

## Quick Start

```python
from dotpromptz import DataArgument, Dotprompt

# 1. Create a Dotprompt instance
dp = Dotprompt()

# 2. Parse and render a prompt
source = '''
---
model: gemini-pro
input:
  schema:
    name: string
---
Hello, {{name}}!
'''

rendered = await dp.render(source, data=DataArgument(input={'name': 'World'}))
```

## Module Reference

::: dotpromptz.Dotprompt
    options:
      show_root_heading: true
      members_order: source
      heading_level: 3

::: dotpromptz.DataArgument
    options:
      show_root_heading: true
      members_order: source
      heading_level: 3

::: dotpromptz.RenderedPrompt
    options:
      show_root_heading: true
      members_order: source
      heading_level: 3

::: dotpromptz.Message
    options:
      show_root_heading: true
      members_order: source
      heading_level: 3

::: dotpromptz.Role
    options:
      show_root_heading: true
      members_order: source
      heading_level: 3

::: dotpromptz.DirStore
    options:
      show_root_heading: true
      members_order: source
      heading_level: 3

::: dotpromptz.DotpromptError
    options:
      show_root_heading: true
      members_order: source
      heading_level: 3

