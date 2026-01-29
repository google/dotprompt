# dotpromptz

The `dotpromptz` package is the Python implementation of the Dotprompt file
format—an executable prompt template format for Generative AI.

## Installation

```bash
pip install dotpromptz
```

## Quick Start

```python
from dotpromptz import Dotprompt

# Create a Dotprompt instance
dp = Dotprompt()

# Parse and render a prompt
source = '''
---
model: gemini-pro
input:
  schema:
    name: string
---
Hello, {{name}}!
'''

rendered = await dp.render(source, data={'input': {'name': 'World'}})
```

## Core Classes

### Dotprompt

::: dotpromptz.dotprompt.Dotprompt
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Parsing

::: dotpromptz.parse
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Picoschema

::: dotpromptz.picoschema
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Helpers

::: dotpromptz.helpers
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Resolvers

::: dotpromptz.resolvers
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Types

::: dotpromptz.typing
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Stores

::: dotpromptz.stores
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Errors

::: dotpromptz.errors
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false

## Utilities

::: dotpromptz.util
options:
show\_root\_heading: false
show\_source: true
members\_order: source
show\_docstring\_description: true
show\_docstring\_examples: false
