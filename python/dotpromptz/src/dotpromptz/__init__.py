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

Dotprompt combines YAML frontmatter metadata with Handlebars templating to define
self-contained, executable prompt templates for Generative AI applications.

Example:
    ```python
    from dotpromptz import DataArgument, Dotprompt

    # 1. Initialize compiler
    prompt = Dotprompt()

    # 2. Render prompt source with input data
    rendered = await prompt.render(
        '''---
        model: googleai/gemini-2.5-pro
        input:
          schema:
            customer: string
            dish: string
        ---
        {{role "system"}}
        You are a restaurant server confirming an order.

        {{role "user"}}
        Please confirm order for {{customer}}: {{dish}}.
        ''',
        DataArgument(input={'customer': 'Ada', 'dish': 'Smoked Salmon Tartine'}),
    )

    # 3. Inspect structured messages
    print(rendered.messages[1].content[0].text)
    # => Please confirm order for Ada: Smoked Salmon Tartine.
    ```
"""

# Primary Engine
from dotpromptz._dotprompt import Dotprompt

# Exceptions
from dotpromptz._errors import (
    DotpromptError,
    FrontmatterError,
    PartialCycleError,
    ResolverFailedError,
)

# Parsing & Schema Functions
from dotpromptz._parse import parse_document
from dotpromptz._picoschema import picoschema_to_json_schema
from dotpromptz._picoschema_reverse import json_schema_to_picoschema

# Storage Implementations & Protocols
from dotpromptz._stores import (
    DirStore,
    DirStoreOptions,
    DirStoreSync,
)

# Runtime Data, Models & Resolver Protocols
from dotpromptz._typing import (
    DataArgument,
    DataPart,
    Document,
    MediaPart,
    Message,
    ParsedPrompt,
    Part,
    PartialData,
    PartialRef,
    PartialResolver,
    PromptBundle,
    PromptData,
    PromptMetadata,
    PromptRef,
    PromptStore,
    PromptStoreSync,
    PromptStoreWritable,
    PromptStoreWritableSync,
    RenderedPrompt,
    Role,
    SchemaResolver,
    TextPart,
    ToolArgument,
    ToolDefinition,
    ToolRequestPart,
    ToolResolver,
    ToolResponsePart,
)

# Shorthand alias matching JS and Go conventions
picoschema = picoschema_to_json_schema

__all__ = [
    # Engine & Functional Parsing
    'Dotprompt',
    'parse_document',
    # Runtime & Data Models
    'DataArgument',
    'Document',
    'ParsedPrompt',
    'PromptBundle',
    'PromptData',
    'PromptMetadata',
    'PromptRef',
    'RenderedPrompt',
    # Messages & Parts
    'DataPart',
    'MediaPart',
    'Message',
    'Part',
    'Role',
    'TextPart',
    'ToolArgument',
    'ToolDefinition',
    'ToolRequestPart',
    'ToolResponsePart',
    # Partials & Resolvers
    'PartialData',
    'PartialRef',
    'PartialResolver',
    'SchemaResolver',
    'ToolResolver',
    # Storage
    'DirStore',
    'DirStoreOptions',
    'DirStoreSync',
    'PromptStore',
    'PromptStoreSync',
    'PromptStoreWritable',
    'PromptStoreWritableSync',
    # Schema
    'json_schema_to_picoschema',
    'picoschema',
    'picoschema_to_json_schema',
    # Errors
    'DotpromptError',
    'FrontmatterError',
    'PartialCycleError',
    'ResolverFailedError',
]
