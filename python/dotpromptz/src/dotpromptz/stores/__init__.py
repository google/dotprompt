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

"""Stores for prompt templates and partials.

This module provides implementations of prompt stores for managing, retrieving,
and persisting prompt templates and partials. A prompt store is responsible for
storing and retrieving prompt templates and their associated metadata.

Available Store Implementations:
- DirStore: Asynchronous filesystem-based store
- DirStoreSync: Synchronous filesystem-based store
- DirStoreOptions: Configuration options for directory-based stores

Directory-based stores organize prompts using the following conventions:
- Prompts are stored as files with extension `.prompt`
- Regular prompts: `[name][.variant].prompt`
- Partial prompts: `_[name][.variant].prompt`
- Directory structure forms part of the prompt/partial name
- Versions are calculated based on content hashing

Usage Example:
```python
# Using the async store
from dotpromptz.stores import DirStore, DirStoreOptions

store = DirStore(DirStoreOptions(directory='/path/to/prompts'))
prompts = await store.list()

# Using the sync store
from dotpromptz.stores import DirStoreSync, DirStoreOptions

sync_store = DirStoreSync(DirStoreOptions(directory='/path/to/prompts'))
prompts = sync_store.list()
```
"""

from ._dir_async import DirStore as DirStore
from ._dir_sync import DirStoreSync
from ._typing import DirStoreOptions

__all__ = [
    'DirStore',
    'DirStoreOptions',
    'DirStoreSync',
]
