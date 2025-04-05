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

"""Sync tests for the directory-based prompt store.

This module contains test cases for the synchronous directory store
implementation (DirStoreSync). The tests verify all core functionality
of the prompt store using synchronous operations:

Core Test Areas:
- Listing prompts and partials
- Loading prompts and partials with different variants
- Saving prompts and partials to the filesystem
- Deleting prompts and partials
- Version verification and error handling

Test Strategy:
Tests use temporary directories with fixture prompts/partials to validate
the store's behavior. Tests are isolated and clean up resources after execution.
Each test focuses on a specific capability of the DirStoreSync class.

The synchronous implementation mirrors the functionality of the asynchronous
version but uses standard blocking I/O operations, making it suitable for
simpler applications or those that don't require async operations.
"""

import os
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

from dotpromptz.stores import DirStoreOptions, DirStoreSync
from dotpromptz.stores._io import calculate_version
from dotpromptz.stores._testutils import (
    create_test_partial as create_test_partial_sync,
    create_test_prompt as create_test_prompt_sync,
)
from dotpromptz.typing import (
    DeletePromptOrPartialOptions,
    LoadPartialOptions,
    LoadPromptOptions,
    PromptData,
)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Pytest fixture to provide a temporary directory for sync tests."""
    # tmp_path is automatically created and cleaned up by pytest
    return tmp_path


@pytest.fixture
def sync_store(temp_dir: Path) -> DirStoreSync:
    """Fixture to provide an instance of the sync DirStore."""
    return DirStoreSync(DirStoreOptions(directory=temp_dir))


def test_list_prompts(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test listing prompts synchronously."""
    content1 = 'test source 1'
    content2 = 'test source 2'
    content_variant = 'test variant source'
    content_subdir = 'test subdir source'

    create_test_prompt_sync(temp_dir, 'test.prompt', content1)
    create_test_prompt_sync(temp_dir, 'other.prompt', content2)
    create_test_prompt_sync(temp_dir, 'test.v1.prompt', content_variant)
    nested_path = str(Path('subdir') / 'sub.prompt')
    create_test_prompt_sync(temp_dir, nested_path, content_subdir)
    # Create a partial, which should be ignored by list()
    create_test_partial_sync(temp_dir, '_partial.prompt', 'partial')

    result = sync_store.list()
    assert len(result.prompts) == 4  # Should ignore the partial

    prompts = sorted(result.prompts, key=lambda p: (p.name, p.variant or ''))

    assert prompts[0].name == 'other'
    assert prompts[0].variant is None
    assert prompts[0].version == calculate_version(content2)

    assert prompts[1].name == 'subdir/sub'
    assert prompts[1].variant is None
    assert prompts[1].version == calculate_version(content_subdir)

    assert prompts[2].name == 'test'
    assert prompts[2].variant is None
    assert prompts[2].version == calculate_version(content1)

    assert prompts[3].name == 'test'
    assert prompts[3].variant == 'v1'
    assert prompts[3].version == calculate_version(content_variant)


def test_list_partials(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test listing partials synchronously."""
    content1 = 'partial source 1'
    content2 = 'partial source 2'
    content_variant = 'test partial variant source'
    content_subdir = 'test subdir partial source'

    create_test_partial_sync(temp_dir, 'partial.prompt', content1)
    create_test_partial_sync(temp_dir, 'other.prompt', content2)
    create_test_partial_sync(temp_dir, 'test.v1.prompt', content_variant)
    nested_path = str(Path('subdir') / 'sub.prompt')
    create_test_partial_sync(temp_dir, nested_path, content_subdir)
    # Create a non-partial, which should be ignored by list_partials()
    create_test_prompt_sync(temp_dir, 'not_partial.prompt', 'nonpartial')

    result = sync_store.list_partials()
    assert len(result.partials) == 4  # Should ignore the non-partial

    partials = sorted(result.partials, key=lambda p: (p.name, p.variant or ''))

    assert partials[0].name == 'other'
    assert partials[0].variant is None
    assert partials[0].version == calculate_version(content2)

    assert partials[1].name == 'partial'
    assert partials[1].variant is None
    assert partials[1].version == calculate_version(content1)

    assert partials[2].name == 'subdir/sub'
    assert partials[2].variant is None
    assert partials[2].version == calculate_version(content_subdir)

    assert partials[3].name == 'test'
    assert partials[3].variant == 'v1'
    assert partials[3].version == calculate_version(content_variant)


def test_load_prompt(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test loading prompts synchronously."""
    source = 'test source content'
    version = calculate_version(source)
    create_test_prompt_sync(temp_dir, 'test.prompt', source)
    nested_path = str(Path('subdir') / 'nested.prompt')
    create_test_prompt_sync(temp_dir, nested_path, source)
    create_test_prompt_sync(temp_dir, 'variant.v1.prompt', source)

    # Load basic prompt
    result = sync_store.load('test')
    assert result.name == 'test'
    assert result.source == source
    assert result.version == version
    assert result.variant is None

    # Load nested prompt
    result_nested = sync_store.load('subdir/nested')
    assert result_nested.name == 'subdir/nested'
    assert result_nested.source == source
    assert result_nested.version == version

    # Load variant
    result_variant = sync_store.load('variant', LoadPromptOptions(variant='v1'))
    assert result_variant.name == 'variant'
    assert result_variant.variant == 'v1'
    assert result_variant.source == source
    assert result_variant.version == version

    # Load with specific version
    result_version = sync_store.load('test', LoadPromptOptions(version=version))
    assert result_version.version == version

    # Load non-existent prompt
    with pytest.raises(FileNotFoundError):
        sync_store.load('nonexistent')

    # Load with wrong version
    with pytest.raises(ValueError, match='Version mismatch'):
        sync_store.load('test', LoadPromptOptions(version='wrongversion'))


def test_load_partial(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test loading partials synchronously."""
    source = 'partial source content'
    version = calculate_version(source)
    create_test_partial_sync(temp_dir, 'test.prompt', source)
    nested_path = str(Path('subdir') / 'nested.prompt')
    create_test_partial_sync(temp_dir, nested_path, source)
    create_test_partial_sync(temp_dir, 'variant.v1.prompt', source)

    # Load basic partial
    result = sync_store.load_partial('test')
    assert result.name == 'test'
    assert result.source == source
    assert result.version == version
    assert result.variant is None

    # Load nested partial
    result_nested = sync_store.load_partial('subdir/nested')
    assert result_nested.name == 'subdir/nested'
    assert result_nested.source == source
    assert result_nested.version == version

    # Load variant partial
    result_variant = sync_store.load_partial('variant', LoadPartialOptions(variant='v1'))
    assert result_variant.name == 'variant'
    assert result_variant.variant == 'v1'
    assert result_variant.source == source
    assert result_variant.version == version

    # Load with specific version
    result_version = sync_store.load_partial('test', LoadPartialOptions(version=version))
    assert result_version.version == version

    # Load non-existent partial
    with pytest.raises(FileNotFoundError):
        sync_store.load_partial('nonexistent')

    # Load with wrong version
    with pytest.raises(ValueError, match='Version mismatch'):
        sync_store.load_partial('test', LoadPartialOptions(version='wrongversion'))


def test_save_prompt(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test saving prompts synchronously."""
    source = 'new source content'
    version = calculate_version(source)
    prompt = PromptData(name='new_prompt', source=source, version=version)

    sync_store.save(prompt)

    file_path = temp_dir / 'new_prompt.prompt'
    assert file_path.exists()
    with open(file_path, encoding='utf-8') as f:
        saved_content = f.read()
    assert saved_content == source

    # Verify version after loading
    loaded = sync_store.load('new_prompt')
    assert loaded.version == version


def test_save_prompt_variant(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test saving prompt variants synchronously."""
    source = 'new variant source'
    version = calculate_version(source)
    prompt = PromptData(name='new_prompt', variant='beta', source=source, version=version)

    sync_store.save(prompt)

    file_path = temp_dir / 'new_prompt.beta.prompt'
    assert file_path.exists()
    with open(file_path, encoding='utf-8') as f:
        saved_content = f.read()
    assert saved_content == source

    loaded = sync_store.load('new_prompt', LoadPromptOptions(variant='beta'))
    assert loaded.version == version


def test_save_prompt_subdir(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test saving prompts in subdirectories synchronously."""
    source = 'new subdir source'
    version = calculate_version(source)
    prompt = PromptData(name='subdir/new_prompt', source=source, version=version)

    sync_store.save(prompt)

    file_path = temp_dir / 'subdir' / 'new_prompt.prompt'
    assert file_path.exists()
    with open(file_path, encoding='utf-8') as f:
        saved_content = f.read()
    assert saved_content == source

    loaded = sync_store.load('subdir/new_prompt')
    assert loaded.version == version


def test_save_partial(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test saving partials synchronously."""
    # Note: `save` uses the name directly, including '_'.
    source = 'new partial content'
    version = calculate_version(source)
    partial = PromptData(name='_new_partial', source=source, version=version)  # Name includes '_' for saving

    sync_store.save(partial)

    file_path = temp_dir / '_new_partial.prompt'
    assert file_path.exists()
    with open(file_path, encoding='utf-8') as f:
        saved_content = f.read()
    assert saved_content == source

    # Use load_partial (without '_') to verify
    loaded = sync_store.load_partial('new_partial')
    assert loaded.version == version


def test_delete_prompt(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test deleting prompts synchronously."""
    create_test_prompt_sync(temp_dir, 'test_delete.prompt')
    nested_path = str(Path('subdir') / 'nested_delete.prompt')
    create_test_prompt_sync(temp_dir, nested_path)
    create_test_prompt_sync(temp_dir, 'variant_delete.v1.prompt')

    # Delete basic prompt
    sync_store.delete('test_delete')
    assert not (temp_dir / 'test_delete.prompt').exists()

    # Delete nested prompt
    sync_store.delete('subdir/nested_delete')
    assert not (temp_dir / 'subdir' / 'nested_delete.prompt').exists()

    # Delete variant
    sync_store.delete('variant_delete', DeletePromptOrPartialOptions(variant='v1'))
    assert not (temp_dir / 'variant_delete.v1.prompt').exists()

    # Delete non-existent
    with pytest.raises(FileNotFoundError):
        sync_store.delete('nonexistent')


def test_delete_partial(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test deleting partials synchronously."""
    create_test_partial_sync(temp_dir, 'test_delete_partial.prompt')
    create_test_partial_sync(temp_dir, 'variant_delete_partial.v1.prompt')

    # Delete basic partial (using name without '_')
    sync_store.delete('test_delete_partial')
    assert not (temp_dir / '_test_delete_partial.prompt').exists()

    # Delete variant partial (using name without '_')
    sync_store.delete('variant_delete_partial', DeletePromptOrPartialOptions(variant='v1'))
    assert not (temp_dir / '_variant_delete_partial.v1.prompt').exists()


def test_delete_prioritizes_prompt_over_partial(sync_store: DirStoreSync, temp_dir: Path) -> None:
    """Test that delete removes prompt if both prompt and partial exist."""
    create_test_prompt_sync(temp_dir, 'conflict.prompt', 'prompt')
    create_test_partial_sync(temp_dir, 'conflict.prompt', 'partial')  # Creates _conflict.prompt

    sync_store.delete('conflict')

    assert not (temp_dir / 'conflict.prompt').exists()  # Prompt should be gone
    assert (temp_dir / '_conflict.prompt').exists()  # Partial should remain
