# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Dotpromptz: Executable prompt templates for Python.

Dotpromptz is the Python implementation of the Dotprompt file format—an executable
prompt template format for Generative AI. It provides a structured way to define,
manage, and render prompts with metadata, schemas, tools, and templating.

## What is Dotprompt?

Dotprompt files (`.prompt`) combine YAML frontmatter metadata with Handlebars
templates to create self-contained, executable prompt definitions:

```
+---------------------------+
|     YAML Frontmatter      |  <- Model config, schemas, tools
|---------------------------|
|                           |
|   Handlebars Template     |  <- Dynamic prompt with variables
|                           |
+---------------------------+
```

## Key Concepts

| Concept          | Description                                                      |
|------------------|------------------------------------------------------------------|
| **Frontmatter**  | YAML metadata block at the top of `.prompt` files (model,        |
|                  | schemas, tools, config)                                          |
| **Template**     | Handlebars template body with variables, helpers, and partials   |
| **Picoschema**   | Compact schema format that compiles to JSON Schema               |
| **Partials**     | Reusable template fragments (prefixed with `_` in filenames)     |
| **Helpers**      | Custom Handlebars functions (`{{role}}`, `{{media}}`, etc.)      |
| **Resolvers**    | Functions to dynamically resolve tools, schemas, and partials    |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Dotprompt                               │
│  (Main entry point - compiles and renders prompt templates)     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │    parse     │  │  picoschema  │  │      resolvers       │  │
│  │  (YAML +     │  │  (Schema     │  │  (Tools, schemas,    │  │
│  │   template)  │  │   compiler)  │  │   partials lookup)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   helpers    │  │    stores    │  │      handlebarrz     │  │
│  │  (Built-in   │  │  (Prompt     │  │  (Handlebars engine  │  │
│  │   functions) │  │   storage)   │  │   via Rust FFI)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
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
Hello, {{name}}! How can I help you today?
'''

rendered = await dp.render(source, data={'input': {'name': 'Alice'}})

# Access rendered messages
for message in rendered.messages:
    print(f'{message.role}: {message.content}')
```

## Example `.prompt` File

```handlebars
---
model: googleai/gemini-1.5-pro
input:
  schema:
    topic: string, The topic to explain
    level: string, Expertise level (beginner, intermediate, advanced)
output:
  format: json
  schema:
    explanation: string, Clear explanation of the topic
    examples(array): string, Illustrative examples
---

{{role "system"}}
You are an expert educator who adapts explanations to the learner's level.

{{role "user"}}
Please explain {{topic}} for someone at the {{level}} level.
Provide clear examples to illustrate key points.
```

## Module Structure

| Module          | Purpose                                              |
|-----------------|------------------------------------------------------|
| `dotprompt`     | Main `Dotprompt` class for compiling/rendering       |
| `parse`         | YAML frontmatter extraction and message parsing      |
| `picoschema`    | Picoschema to JSON Schema compilation                |
| `helpers`       | Built-in Handlebars helpers (`role`, `media`, etc.)  |
| `resolvers`     | Async resolution of tools, schemas, and partials     |
| `stores`        | Filesystem-based prompt storage (`DirStore`)         |
| `typing`        | Pydantic models and type definitions                 |
| `errors`        | Custom exception classes                             |

## See Also

- Dotprompt specification: https://github.com/google/dotprompt
- Handlebars templating: https://handlebarsjs.com
- JSON Schema: https://json-schema.org
"""

from .dotprompt import Dotprompt


def package_name() -> str:
    """Return the package name for smoke testing.

    Returns:
        The string 'dotpromptz'.
    """
    return 'dotpromptz'


__all__ = [
    Dotprompt.__name__,
]
