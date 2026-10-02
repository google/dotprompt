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

"""Common test utilities for both sync and async directory store tests.

This module provides utility functions to create test prompts and partials
with proper directory structures and file naming conventions for testing
directory-based prompt stores. These utilities make it easier to set up test
fixtures and create the necessary file structures for tests.

Key Functions:
- create_test_prompt: Creates a regular prompt file with optional custom
  content.
- create_test_partial: Creates a partial prompt file (with leading underscore).

These utilities handle subdirectory creation, file naming, and content
generation to match the conventions expected by the DirStore implementations.
"""

import os
from pathlib import Path


def create_test_prompt(
    directory: Path,
    name: str,
    content: str | None = None,
) -> Path:
    """Create a test prompt file.

    Creates a prompt file for testing with the specified name and optional
    content. The name can include subdirectory paths, which will be created
    automatically. If no content is provided, generates default content based
    on the prompt name.

    Args:
        directory: Base directory where the file will be created.
        name: Filename (e.g., 'my.prompt', 'my.v1.prompt', 'subdir/my.prompt').
            Can include subdirectory path.
        content: Optional content to write into the file. If None, default
            content will be generated.

    Returns:
        Path to the created prompt file.

    Example:
        ```python
        # Create a simple prompt
        path = create_test_prompt(Path('./test-prompts'), 'greeting.prompt')

        # Create a prompt with variant in a subdirectory
        path = create_test_prompt(
            Path('./test-prompts'),
            'models/chat.v1.prompt',
            'This is a {{type}} model prompt.',
        )
        ```
    """
    # Split name into directory and basename.
    dir_name = os.path.dirname(name)
    file_name = os.path.basename(name)  # Use the provided name directly

    # Create full directory path if needed.
    if dir_name:
        full_dir = directory / dir_name
        os.makedirs(full_dir, exist_ok=True)
    else:
        full_dir = directory

    # Default content if none provided
    if content is None:
        # Try to parse name/variant for default content message
        parsed_name = file_name.split('.')[0]
        content = f'Test content for {parsed_name}'

    # Create the file.
    file_path = full_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path


def create_test_partial(
    directory: Path,
    name: str,
    content: str | None = None,
) -> Path:
    """Create a test partial prompt file (prepends '_' to name).

    Creates a partial file for testing with the specified name (prefixed with
    an underscore) and optional content. The name can include subdirectory
    paths, which will be created automatically. If no content is provided,
    generates default content based on the partial name.

    Args:
        directory: Base directory where the file will be created.
        name: Filename (e.g., 'my.prompt', 'my.v1.prompt', 'subdir/my.prompt').
            The actual filename will be created with a leading '_'.
            Can include subdirectory path.
        content: Optional content to write into the file. If None, default
            content will be generated.

    Returns:
        Path to the created partial file.

    Example:
        ```python
        # Create a simple partial
        path = create_test_partial(Path('./test-prompts'), 'header.prompt')
        # Creates _header.prompt with default content

        # Create a partial with variant in a subdirectory
        path = create_test_partial(
            Path('./test-prompts'),
            'commons/footer.v2.prompt',
            'Common footer with {{copyright}}',
        )
        # Creates _footer.v2.prompt in commons/ subdirectory
    ```
    """
    # Split name into directory and basename.
    dir_name = os.path.dirname(name)
    base_name = os.path.basename(name)

    # Create full directory path if needed.
    if dir_name:
        full_dir = directory / dir_name
        os.makedirs(full_dir, exist_ok=True)
    else:
        full_dir = directory

    # Construct filename with underscore prefix for partial.
    file_name = f'_{base_name}'  # Prepend underscore

    # Default content if none provided
    if content is None:
        # Try to parse name/variant for default content message
        parsed_name = base_name.split('.')[0]
        content = f'Partial content for {parsed_name}'

    # Create the file.
    file_path = full_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path
