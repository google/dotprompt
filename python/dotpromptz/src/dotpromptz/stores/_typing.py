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

"""Types for prompt stores.

This module contains type definitions used by the directory-based prompt stores
to configure behavior and represent internal data structures. These types
facilitate the storage, retrieval, and manipulation of prompts and partials
in the filesystem.

The types in this module are not intended to be imported directly by users.
Instead, users should import from the public API in `dotpromptz.stores`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DirStoreOptions:
    """Options for configuring the DirStore.

    This dataclass encapsulates the configuration options for initializing
    a directory-based prompt store (DirStore or DirStoreSync).

    Attributes:
        directory: Path to the base directory where prompts and partials are
            stored. The store will read from and write to this directory and
            its subdirectories. The directory structure forms part of the
            prompt/partial names.

    Example:
        ```python
        from pathlib import Path
        from dotpromptz.stores import DirStore, DirStoreOptions

        options = DirStoreOptions(directory=Path('/path/to/prompts'))
        store = DirStore(options)
        ```
    """

    directory: Path


@dataclass
class ParsedPromptInfo:
    """Parsed prompt filename information.

    This dataclass represents information extracted from a prompt filename
    according to the naming conventions used by directory-based stores.

    Attributes:
        name: The base name of the prompt, extracted from the filename.
        variant: Optional variant name for the prompt, indicated by `.variant`
            in the filename. If not present, this is None.
        version: Optional version string for the prompt, usually computed from
            the content hash. If not computed or provided, this is None.

    Note:
        This class is primarily for internal use by the directory store
        implementation and is not typically needed by end users.
    """

    name: str
    variant: str | None = None
    version: str | None = None
