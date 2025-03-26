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

"""Stores module for the dotpromptz package.

This module provides implementations for storing and managing prompts and
partials.

Available store implementations:

- DirStore: Asynchronous directory-based store implementation that reads and
  writes prompts and partials from/to the local file system.

- DirStoreSync: Synchronous version of DirStore offering the same functionality
  but with a blocking API.

Features:

- File-based storage of prompts and partials with a consistent naming convention.
- Support for organizing prompts in subdirectories.
- Automatic versioning based on content hashing.
- Support for prompt variants.
- Listing, loading, saving, and deleting prompts and partials.
- Error handling with informative error messages.

File naming conventions:
- Regular prompts: `[name](.[variant]).prompt`.
- Partial prompts: `_[name](.[variant]).prompt`.

Basic Usage:

```python
from pathlib import Path
from dotpromptz.stores import DirStoreSync

# Create a store instance
store = DirStoreSync({'directory': Path('/path/to/prompts')})

# List all prompts
results = store.list_prompts()
prompts = results['prompts']

# Load a specific prompt
prompt_data = store.load('my_prompt')

# Save a prompt
from dotpromptz.stores._typing import PromptData

result = store.save(
    PromptData(
        name='example',
        source='This is an example prompt.',
        variant=None,
        version=None,
    )
)

# List all partials
results = store.list_partials()
partials = results['partials']

# Work with partials
partial_data = store.load_partial('draft')
result = store.save_partial(
    PromptData(
        name='draft',
        source='This is a draft partial.',
        variant=None,
        version=None,
    )
)
```
"""

from ._dir import DirStore
from ._dir_sync import DirStoreSync

__all__ = [
    'DirStore',
    'DirStoreSync',
]
