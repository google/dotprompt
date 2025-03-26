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

"""Shared utility functions for directory-based stores."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import structlog

from ._typing import ParsedPrompt

logger = structlog.get_logger(__name__)


def calculate_version(content: str) -> str:
    """Calculate a deterministic version identifier for a prompt.

    The version is calculated as the first 8 characters of the SHA1 hash of
    the content.

    Args:
        content: Prompt content to hash.

    Returns:
        An 8-character SHA1 hash of the content.
    """
    sha1 = hashlib.sha1(content.encode('utf-8'), usedforsecurity=False)
    return sha1.hexdigest()[:8]


def parse_prompt_filename(filename: str) -> ParsedPrompt:
    """Parse a prompt filename into its components.

    This function parses prompt filenames according to two possible formats:
    - Basic prompt: '{name}.prompt'
    - Prompt with variant: '{name}.{variant}.prompt'

    All prompt files must have the '.prompt' extension.

    Args:
        filename: Prompt filename to parse.

    Returns:
        A ParsedPrompt object with the extracted name and optional variant.

    Raises:
        ValueError: If the filename does not end with '.prompt' or does not
            match the expected format.
    """
    # Check if filename ends with .prompt.
    if not filename.endswith('.prompt'):
        raise ValueError(f'Invalid prompt file: {filename}')

    # Remove .prompt extension.
    base = filename[: -len('.prompt')]

    # Split by dots.
    parts = base.split('.')

    if len(parts) == 1:
        # Simple case: {name}.prompt.
        return ParsedPrompt(name=parts[0])
    elif len(parts) == 2:
        # With variant: {name}.{variant}.prompt.
        return ParsedPrompt(name=parts[0], variant=parts[1])
    else:
        # Invalid format.
        raise ValueError(f'Invalid prompt filename format: {filename}')


def is_partial(filename: str) -> bool:
    """Determine if a given filename represents a partial prompt.

    Args:
        filename: The filename to check.

    Returns:
        True if the filename starts with '_', False otherwise.
    """
    return filename.startswith('_')


async def scan_directory(
    base_dir: Path, dir_path: str = '', results: list[str] | None = None
) -> list[str]:
    """Recursively scan for prompt files.

    Args:
        base_dir: Base directory of the store.
        dir_path: The subdirectory relative to the base directory.
        results: An accumulator for file paths.

    Returns:
        A list of relative paths to all found .prompt files.
    """
    if results is None:
        results = []

    full_path = base_dir / dir_path if dir_path else base_dir
    await logger.adebug('Scanning directory', path=str(full_path))

    try:
        entries = [
            entry
            for entry in os.scandir(full_path)
            if not entry.name.startswith('.')
        ]

        await logger.adebug(
            'Found entries',
            count=len(entries),
            entries=[e.name for e in entries],
        )

        for entry in entries:
            relative_path = os.path.join(dir_path, entry.name)

            if entry.is_dir():
                # Recurse into subdirectories.
                await scan_directory(base_dir, relative_path, results)
            elif entry.is_file() and entry.name.endswith('.prompt'):
                # Add matching files to results.
                results.append(relative_path)
                await logger.adebug('Found prompt file', file=relative_path)
    except Exception as e:
        await logger.aerror(
            'Error scanning directory', path=str(full_path), error=str(e)
        )

    return results


def scan_directory_sync(
    base_dir: Path, dir_path: str = '', results: list[str] | None = None
) -> list[str]:
    """Recursively scan for prompt files (synchronous version).

    Args:
        base_dir: Base directory of the store.
        dir_path: The subdirectory relative to the base directory.
        results: An accumulator for file paths.

    Returns:
        A list of relative paths to all found .prompt files.
    """
    if results is None:
        results = []

    full_path = base_dir / dir_path if dir_path else base_dir

    entries = [
        entry
        for entry in os.scandir(full_path)
        if not entry.name.startswith('.')
    ]

    for entry in entries:
        relative_path = os.path.join(dir_path, entry.name)

        if entry.is_dir():
            # Recurse into subdirectories.
            scan_directory_sync(base_dir, relative_path, results)
        elif entry.is_file() and entry.name.endswith('.prompt'):
            # Add matching files to results.
            results.append(relative_path)

    return results
