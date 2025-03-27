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

"""Common test utilities for both sync and async directory store tests."""

import os
from pathlib import Path


def create_test_prompt(
    directory: Path, name: str, variant: str | None = None
) -> Path:
    """Create a test prompt file.

    Args:
        directory: Base directory.
        name: Prompt name.
        variant: Optional variant.

    Returns:
        Path to the created prompt file.
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

    # Construct filename.
    file_name = (
        f'{base_name}.{variant}.prompt' if variant else f'{base_name}.prompt'
    )

    # Create the file.
    file_path = full_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f'Test content for {name}')

    return file_path


def create_test_partial(
    directory: Path, name: str, variant: str | None = None
) -> Path:
    """Create a test partial prompt file.

    Args:
        directory: Base directory.
        name: Prompt name.
        variant: Optional variant.

    Returns:
        Path to the created partial file.
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
    file_name = (
        f'_{base_name}.{variant}.prompt' if variant else f'_{base_name}.prompt'
    )

    # Create the file.
    file_path = full_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f'Partial content for {name}')

    return file_path
