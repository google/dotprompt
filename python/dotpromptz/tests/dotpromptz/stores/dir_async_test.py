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

"""Async tests for the directory-based prompt store.

This module contains test cases for the asynchronous directory store
implementation. The tests verify all core
functionality of the prompt store:

Core Test Areas:
- Listing prompts and partials
- Loading prompts and partials with different variants
- Saving prompts and partials to the filesystem
- Deleting prompts and partials
- Version verification and error handling

Test Strategy:
Tests use temporary directories with fixture prompts/partials to validate
the store's behavior. Tests are isolated and clean up resources after execution.
Each test focuses on a specific capability of the DirStore class.

Each test begins with setup (creating test files), executes operations on the
store, and verifies the correct behavior through assertions.
"""

from __future__ import annotations

import os
from pathlib import Path

import aiofiles
import pytest
import pytest_asyncio

from dotpromptz.stores import DirStore, DirStoreOptions
from dotpromptz.stores._io import calculate_version
from dotpromptz.typing import (
    DeletePromptOrPartialOptions,
    LoadPartialOptions,
    LoadPromptOptions,
    PromptData,
)


async def _create_test_file_async(directory: Path, name: str, content: str = 'test source') -> Path:
    """Asynchronously create a test file."""
    file_path = directory / name
    os.makedirs(file_path.parent, exist_ok=True)
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.write(content)
    return file_path


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Pytest fixture to provide a temporary directory for tests."""
    # tmp_path is automatically created and cleaned up by pytest
    return tmp_path


@pytest_asyncio.fixture
async def async_store(temp_dir: Path) -> DirStore:
    """Fixture to provide an instance of the async DirStore."""
    return DirStore(DirStoreOptions(directory=temp_dir))


@pytest.mark.asyncio
async def test_list_prompts(async_store: DirStore, temp_dir: Path) -> None:
    """Test listing prompts asynchronously."""
    content1 = 'test source 1'
    content2 = 'test source 2'
    content_variant = 'test variant source'
    content_subdir = 'test subdir source'

    await _create_test_file_async(temp_dir, 'test.prompt', content1)
    await _create_test_file_async(temp_dir, 'other.prompt', content2)
    await _create_test_file_async(temp_dir, 'test.v1.prompt', content_variant)
    nested_path = str(Path('subdir') / 'sub.prompt')
    await _create_test_file_async(temp_dir, nested_path, content_subdir)
    # Create a partial, which should be ignored by list()
    await _create_test_file_async(temp_dir, '_partial.prompt', 'partial')

    result = await async_store.list()
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


@pytest.mark.asyncio
async def test_list_partials(async_store: DirStore, temp_dir: Path) -> None:
    """Test listing partials asynchronously."""
    content1 = 'partial source 1'
    content2 = 'partial source 2'
    content_variant = 'test partial variant source'
    content_subdir = 'test subdir partial source'

    await _create_test_file_async(temp_dir, '_partial.prompt', content1)
    await _create_test_file_async(temp_dir, '_other.prompt', content2)
    await _create_test_file_async(temp_dir, '_test.v1.prompt', content_variant)
    nested_path = str(Path('subdir') / '_sub.prompt')
    await _create_test_file_async(temp_dir, nested_path, content_subdir)
    # Create a non-partial, which should be ignored by list_partials()
    await _create_test_file_async(temp_dir, 'not_partial.prompt', 'nonpartial')

    result = await async_store.list_partials()
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


@pytest.mark.asyncio
async def test_load_prompt(async_store: DirStore, temp_dir: Path) -> None:
    """Test loading prompts asynchronously."""
    source = 'test source content'
    version = calculate_version(source)
    await _create_test_file_async(temp_dir, 'test.prompt', source)
    await _create_test_file_async(temp_dir, 'subdir/nested.prompt', source)
    await _create_test_file_async(temp_dir, 'variant.v1.prompt', source)

    # Load basic prompt
    result = await async_store.load('test')
    assert result.name == 'test'
    assert result.source == source
    assert result.version == version
    assert result.variant is None

    # Load nested prompt
    result_nested = await async_store.load('subdir/nested')
    assert result_nested.name == 'subdir/nested'
    assert result_nested.source == source
    assert result_nested.version == version

    # Load variant
    result_variant = await async_store.load('variant', LoadPromptOptions(variant='v1'))
    assert result_variant.name == 'variant'
    assert result_variant.variant == 'v1'
    assert result_variant.source == source
    assert result_variant.version == version

    # Load with specific version
    result_version = await async_store.load('test', LoadPromptOptions(version=version))
    assert result_version.version == version

    # Load non-existent prompt
    with pytest.raises(FileNotFoundError):
        await async_store.load('nonexistent')

    # Load with wrong version
    with pytest.raises(ValueError, match='Version mismatch'):
        await async_store.load('test', LoadPromptOptions(version='wrongversion'))


@pytest.mark.asyncio
async def test_load_partial(async_store: DirStore, temp_dir: Path) -> None:
    """Test loading partials asynchronously."""
    source = 'partial source content'
    version = calculate_version(source)
    await _create_test_file_async(temp_dir, '_test.prompt', source)
    nested_path = str(Path('subdir') / '_nested.prompt')
    await _create_test_file_async(temp_dir, nested_path, source)
    await _create_test_file_async(temp_dir, '_variant.v1.prompt', source)

    # Load basic partial
    result = await async_store.load_partial('test')
    assert result.name == 'test'
    assert result.source == source
    assert result.version == version
    assert result.variant is None

    # Load nested partial
    result_nested = await async_store.load_partial('subdir/nested')
    assert result_nested.name == 'subdir/nested'
    assert result_nested.source == source
    assert result_nested.version == version

    # Load variant partial
    result_variant = await async_store.load_partial('variant', LoadPartialOptions(variant='v1'))
    assert result_variant.name == 'variant'
    assert result_variant.variant == 'v1'
    assert result_variant.source == source
    assert result_variant.version == version

    # Load with specific version
    result_version = await async_store.load_partial('test', LoadPartialOptions(version=version))
    assert result_version.version == version

    # Load non-existent partial
    with pytest.raises(FileNotFoundError):
        await async_store.load_partial('nonexistent')

    # Load with wrong version
    with pytest.raises(ValueError, match='Version mismatch'):
        await async_store.load_partial('test', LoadPartialOptions(version='wrongversion'))


@pytest.mark.asyncio
async def test_save_prompt(async_store: DirStore, temp_dir: Path) -> None:
    """Test saving prompts asynchronously."""
    source = 'new source content'
    version = calculate_version(source)
    prompt = PromptData(name='new_prompt', source=source, version=version)

    await async_store.save(prompt)

    file_path = temp_dir / 'new_prompt.prompt'
    assert file_path.exists()
    async with aiofiles.open(file_path, encoding='utf-8') as f:
        saved_content = await f.read()
    assert saved_content == source

    # Verify version after loading
    loaded = await async_store.load('new_prompt')
    assert loaded.version == version


@pytest.mark.asyncio
async def test_save_prompt_variant(async_store: DirStore, temp_dir: Path) -> None:
    """Test saving prompt variants asynchronously."""
    source = 'new variant source'
    version = calculate_version(source)
    prompt = PromptData(name='new_prompt', variant='beta', source=source, version=version)

    await async_store.save(prompt)

    file_path = temp_dir / 'new_prompt.beta.prompt'
    assert file_path.exists()
    async with aiofiles.open(file_path, encoding='utf-8') as f:
        saved_content = await f.read()
    assert saved_content == source

    loaded = await async_store.load('new_prompt', LoadPromptOptions(variant='beta'))
    assert loaded.version == version


@pytest.mark.asyncio
async def test_save_prompt_subdir(async_store: DirStore, temp_dir: Path) -> None:
    """Test saving prompts in subdirectories asynchronously."""
    source = 'new subdir source'
    version = calculate_version(source)
    prompt = PromptData(name='subdir/new_prompt', source=source, version=version)

    await async_store.save(prompt)

    file_path = temp_dir / 'subdir' / 'new_prompt.prompt'
    assert file_path.exists()
    async with aiofiles.open(file_path, encoding='utf-8') as f:
        saved_content = await f.read()
    assert saved_content == source

    loaded = await async_store.load('subdir/new_prompt')
    assert loaded.version == version


@pytest.mark.asyncio
async def test_save_partial(async_store: DirStore, temp_dir: Path) -> None:
    """Test saving partials asynchronously."""
    # Note: `save` uses the name directly, including '_'.
    source = 'new partial content'
    version = calculate_version(source)
    partial = PromptData(name='_new_partial', source=source, version=version)

    await async_store.save(partial)

    file_path = temp_dir / '_new_partial.prompt'
    assert file_path.exists()
    async with aiofiles.open(file_path, encoding='utf-8') as f:
        saved_content = await f.read()
    assert saved_content == source

    # Use load_partial (without '_') to verify
    loaded = await async_store.load_partial('new_partial')
    assert loaded.version == version


@pytest.mark.asyncio
async def test_delete_prompt(async_store: DirStore, temp_dir: Path) -> None:
    """Test deleting prompts asynchronously."""
    await _create_test_file_async(temp_dir, 'test_delete.prompt')
    await _create_test_file_async(temp_dir, 'subdir/nested_delete.prompt')
    await _create_test_file_async(temp_dir, 'variant_delete.v1.prompt')

    # Delete basic prompt
    await async_store.delete('test_delete')
    assert not (temp_dir / 'test_delete.prompt').exists()

    # Delete nested prompt
    await async_store.delete('subdir/nested_delete')
    assert not (temp_dir / 'subdir' / 'nested_delete.prompt').exists()

    # Delete variant
    await async_store.delete('variant_delete', DeletePromptOrPartialOptions(variant='v1'))
    assert not (temp_dir / 'variant_delete.v1.prompt').exists()

    # Delete non-existent
    with pytest.raises(FileNotFoundError):
        await async_store.delete('nonexistent')


@pytest.mark.asyncio
async def test_delete_partial(async_store: DirStore, temp_dir: Path) -> None:
    """Test deleting partials asynchronously."""
    await _create_test_file_async(temp_dir, '_test_delete_partial.prompt')
    await _create_test_file_async(temp_dir, '_variant_delete_partial.v1.prompt')

    # Delete basic partial (using name without '_')
    await async_store.delete('test_delete_partial')
    assert not (temp_dir / '_test_delete_partial.prompt').exists()

    # Delete variant partial (using name without '_')
    await async_store.delete('variant_delete_partial', DeletePromptOrPartialOptions(variant='v1'))
    assert not (temp_dir / '_variant_delete_partial.v1.prompt').exists()


@pytest.mark.asyncio
async def test_delete_prioritizes_prompt_over_partial(async_store: DirStore, temp_dir: Path) -> None:
    """Test that delete removes prompt if both prompt and partial exist."""
    await _create_test_file_async(temp_dir, 'conflict.prompt', 'prompt')
    await _create_test_file_async(temp_dir, '_conflict.prompt', 'partial')

    await async_store.delete('conflict')

    assert not (temp_dir / 'conflict.prompt').exists()  # Prompt should be gone
    assert (temp_dir / '_conflict.prompt').exists()  # Partial should remain
