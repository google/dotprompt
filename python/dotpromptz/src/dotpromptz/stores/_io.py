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

"""I/O utilities for prompt store implementations.

This module provides common I/O functions used by both synchronous and
asynchronous implementations of the directory-based prompt store. These include
functions for reading files, calculating version hashes, parsing filenames,
and scanning directories for prompt files.

Key Functions:
- read_prompt_file_sync/async: Read prompt file contents
- calculate_version: Generate a stable version identifier from content
- parse_prompt_filename: Extract name and variant from filename
- is_partial: Determine if a filename represents a partial
- scan_directory_sync/async: Recursively find all prompt files
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import aiofiles
import structlog

from ._typing import ParsedPromptInfo

logger = structlog.get_logger(__name__)


def read_prompt_file_sync(file_path: Path) -> str:
    """Synchronously reads the content of a prompt file.

    Args:
        file_path: The full path to the prompt file.

    Returns:
        The file content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If there's an error reading the file.
    """
    logger.debug('Reading prompt file (sync)', path=str(file_path))
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
            logger.debug('Successfully read file (sync)', path=str(file_path))
            return content
    except FileNotFoundError:
        logger.error('File not found (sync)', path=str(file_path))
        raise
    except OSError as e:
        logger.error('Error reading file (sync)', path=str(file_path), error=str(e))
        raise


async def read_prompt_file_async(file_path: Path) -> str:
    """Asynchronously reads the content of a prompt file.

    Args:
        file_path: The full path to the prompt file.

    Returns:
        The file content as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If there's an error reading the file.
    """
    await logger.adebug('Reading prompt file', path=str(file_path))
    try:
        async with aiofiles.open(file_path, encoding='utf-8') as f:
            content = await f.read()
            await logger.adebug('Successfully read file', path=str(file_path))
            return content
    except FileNotFoundError:
        await logger.aerror('File not found', path=str(file_path))
        raise
    except OSError as e:
        await logger.aerror('Error reading file', path=str(file_path), error=str(e))
        raise


def calculate_version(content: str) -> str:
    """Calculate a deterministic version identifier for a prompt.

    Generates a version hash based on the content of the prompt or partial.
    This enables version checking and comparison.

    Args:
        content: The string content to hash.

    Returns:
        A SHA1 hash string representing the version.

    Example:
        ```python
        version = calculate_version('Hello {{name}}')
        # Returns a string like: "a123b456c789d0ef"
        ```
    """
    sha1 = hashlib.sha1(content.encode('utf-8'), usedforsecurity=False)
    return sha1.hexdigest()[:8]


def is_partial(filename: str) -> bool:
    """Determine if a filename represents a partial.

    Partials are identified by filenames that start with an underscore.

    Args:
        filename: The filename to check.

    Returns:
        True if the filename starts with an underscore, False otherwise.

    Example:
        ```python
        is_partial('greeting.prompt')  # Returns False
        is_partial('_header.prompt')  # Returns True
        ```
    """
    return filename.startswith('_')


def parse_prompt_filename(filename: str) -> ParsedPromptInfo:
    """Parse a prompt filename to extract name and variant.

    Extracts the base name and optional variant from a filename that follows
    the naming convention [name][.variant].prompt.

    Args:
        filename: The filename to parse (e.g., "greeting.formal.prompt").

    Returns:
        A ParsedPromptInfo object containing the name and optional variant.

    Raises:
        ValueError: If the filename doesn't match the expected format.

    Example:
        ```python
        info = parse_prompt_filename('greeting.formal.prompt')
        # info.name == "greeting", info.variant == "formal"

        info = parse_prompt_filename('simple.prompt')
        # info.name == "simple", info.variant == None
        ```
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
        return ParsedPromptInfo(name=parts[0])
    elif len(parts) == 2:
        # With variant: {name}.{variant}.prompt.
        return ParsedPromptInfo(name=parts[0], variant=parts[1])
    else:
        # Invalid format.
        raise ValueError(f'Invalid prompt filename format: {filename}')


async def scan_directory(base_dir: Path, dir_path: str = '', results: list[str] | None = None) -> list[str]:
    """Asynchronously scan a directory for prompt files.

    Recursively searches for .prompt files in the given directory and its
    subdirectories, returning relative paths to all found files.

    Args:
        base_dir: The base directory to start from.
        dir_path: The relative subdirectory to scan (defaults to '').
        results: Optional list to accumulate results (for recursive calls).

    Returns:
        A list of relative paths to all found .prompt files.

    Example:
        ```python
        files = await scan_directory(Path('./prompts'))
        # Returns ["greeting.prompt", "subdir/welcome.prompt", ...]
        ```
    """
    if results is None:
        results = []

    full_path = base_dir / dir_path if dir_path else base_dir
    await logger.adebug('Scanning directory', path=str(full_path))

    try:
        entries = [entry for entry in os.scandir(full_path) if not entry.name.startswith('.')]

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
        await logger.aerror('Error scanning directory', path=str(full_path), error=str(e))

    return results


def scan_directory_sync(base_dir: Path, dir_path: str = '', results: list[str] | None = None) -> list[str]:
    """Synchronously scan a directory for prompt files.

    Recursively searches for .prompt files in the given directory and its
    subdirectories, returning relative paths to all found files.

    Args:
        base_dir: The base directory to start from.
        dir_path: The relative subdirectory to scan (defaults to '').
        results: Optional list to accumulate results (for recursive calls).

    Returns:
        A list of relative paths to all found .prompt files.

    Example:
        ```python
        files = scan_directory_sync(Path('./prompts'))
        # Returns ["greeting.prompt", "subdir/welcome.prompt", ...]
        ```
    """
    if results is None:
        results = []

    full_path = base_dir / dir_path if dir_path else base_dir

    try:
        entries = [entry for entry in os.scandir(full_path) if not entry.name.startswith('.')]

        for entry in entries:
            relative_path = os.path.join(dir_path, entry.name)

            if entry.is_dir():
                # Recurse into subdirectories.
                scan_directory_sync(base_dir, relative_path, results)
            elif entry.is_file() and entry.name.endswith('.prompt'):
                # Add matching files to results.
                results.append(relative_path)
    except Exception as e:
        logger.error('Error scanning directory (sync)', path=str(full_path), error=str(e))

    return results
