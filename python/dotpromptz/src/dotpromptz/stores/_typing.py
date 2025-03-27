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

"""Type definitions for dir store implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dotpromptz.typing import PartialRef, PromptRef


@dataclass
class DirStoreOptions:
    """Options for configuring the DirStore."""

    directory: Path


@dataclass
class PaginationOptions:
    """Options for listing prompts with pagination."""

    cursor: str | None = None
    limit: int | None = None


@dataclass
class LoadOptions:
    """Options for loading a prompt."""

    variant: str | None = None
    version: str | None = None


@dataclass
class DeleteOptions:
    """Options for deleting a prompt or partial."""

    variant: str | None = None


@dataclass
class PromptSaveResult:
    """Result of saving a prompt."""

    name: str
    success: bool
    variant: str | None = None
    version: str | None = None
    message: str | None = None


@dataclass
class PromptDeleteResult:
    """Result of deleting a prompt."""

    name: str
    success: bool
    variant: str | None = None
    message: str | None = None


@dataclass
class ListPromptResults:
    """A paginated list of prompt names available in a store."""

    prompts: list[PromptRef] = field(default_factory=list)
    cursor: str | None = None


@dataclass
class ListPartialResults:
    """A paginated list of partial names available in a store."""

    partials: list[PartialRef] = field(default_factory=list)
    cursor: str | None = None


@dataclass
class ParsedPrompt:
    """Parsed prompt filename information."""

    name: str
    variant: str | None = None
    version: str | None = None
