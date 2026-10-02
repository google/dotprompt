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
model: googleai/gemini-flash-latest
input:
  schema:
    name: string
---
Hello, {{name}}!
'''

rendered = await dp.render(source, data=DataArgument(input={'name': 'Ada'}))

# 3. Access rendered message
print(rendered.messages[0].content[0].text)
# => Hello, Ada!
```

## API Reference

::: dotpromptz
    options:
      show_root_heading: false
      members_order: source
      heading_level: 3

