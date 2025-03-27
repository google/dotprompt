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

import os
import tempfile
from pathlib import Path

import pytest

from dotpromptz.stores import DirStore
from dotpromptz.stores._testutils import create_test_partial, create_test_prompt
from dotpromptz.stores._typing import DirStoreOptions, LoadOptions
from dotpromptz.typing import PromptData

pytestmark = pytest.mark.asyncio


class TestDirStore:
    """Test the directory store."""

    @pytest.fixture
    def temp_dir(self) -> Path:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    async def test_list_prompts(self, temp_dir: Path) -> None:
        """Test listing prompts."""
        # Create test prompts
        create_test_prompt(temp_dir, 'test1')
        create_test_prompt(temp_dir, 'test2')
        create_test_prompt(temp_dir, 'test3', 'v1')
        create_test_prompt(temp_dir, 'subdir/test4')

        store = DirStore(DirStoreOptions(directory=temp_dir))
        results = await store.list()

        # Verify results
        assert len(results.prompts) == 4
        prompt_names = [p.name for p in results.prompts]
        assert 'test1' in prompt_names
        assert 'test2' in prompt_names
        assert 'test3' in prompt_names
        assert 'subdir/test4' in prompt_names

    async def test_list_partials(self, temp_dir: Path) -> None:
        """Test listing partial prompts."""
        # Create test partials
        create_test_partial(temp_dir, 'draft1')
        create_test_partial(temp_dir, 'draft2', 'v1')

        store = DirStore(DirStoreOptions(directory=temp_dir))
        results = await store.list_partials()

        # Verify results
        assert len(results.partials) == 2
        partial_names = [p.name for p in results.partials]
        assert 'draft1' in partial_names
        assert 'draft2' in partial_names

    async def test_load_prompt(self, temp_dir: Path) -> None:
        """Test loading a prompt asynchronously."""
        # Create a test prompt
        create_test_prompt(temp_dir, 'test1')

        store = DirStore(DirStoreOptions(directory=temp_dir))
        prompt = await store.load('test1')

        # Verify the loaded prompt
        assert prompt is not None
        assert prompt.name == 'test1'
        assert prompt.source == 'Test content for test1'
        assert prompt.version is not None

    async def test_load_prompt_with_variant(self, temp_dir: Path) -> None:
        """Test loading a prompt with variant asynchronously."""
        # Create a test prompt with variant
        create_test_prompt(temp_dir, 'test2', 'v1')

        store = DirStore(DirStoreOptions(directory=temp_dir))
        options = LoadOptions(variant='v1')
        prompt = await store.load('test2', options)

        # Verify the loaded prompt
        assert prompt is not None
        assert prompt.name == 'test2'
        assert prompt.variant == 'v1'
        assert prompt.source == 'Test content for test2'

    async def test_load_prompt_not_found(self, temp_dir: Path) -> None:
        """Test loading a non-existent prompt asynchronously."""
        store = DirStore(DirStoreOptions(directory=temp_dir))
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            await store.load('nonexistent')

    async def test_load_partial(self, temp_dir: Path) -> None:
        """Test loading a partial prompt asynchronously."""
        # Create a test partial
        create_test_partial(temp_dir, 'draft1')

        store = DirStore(DirStoreOptions(directory=temp_dir))
        partial = await store.load_partial('draft1')

        # Verify the loaded partial
        assert partial is not None
        assert partial.name == 'draft1'
        assert partial.source == 'Partial content for draft1'

    async def test_save_prompt(self, temp_dir: Path) -> None:
        """Test saving a prompt asynchronously."""
        store = DirStore(DirStoreOptions(directory=temp_dir))

        # Create a prompt object
        prompt = PromptData(
            name='new_prompt',
            source='This is a new prompt',
            variant=None,
            version=None,
        )

        # Save the prompt
        result = await store.save(prompt)

        # Verify the result
        assert result.name == 'new_prompt'

        # Verify file was created
        file_path = temp_dir / 'new_prompt.prompt'
        assert os.path.exists(file_path)

        # Verify content
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        assert content == 'This is a new prompt'

    async def test_delete_prompt(self, temp_dir: Path) -> None:
        """Test deleting a prompt asynchronously."""
        # Create a test prompt
        file_path = create_test_prompt(temp_dir, 'to_delete')
        assert os.path.exists(file_path)

        store = DirStore(DirStoreOptions(directory=temp_dir))

        # Delete the prompt
        result = await store.delete('to_delete')

        # Verify result
        assert result.name == 'to_delete'

        # Verify file was deleted
        assert not os.path.exists(file_path)
