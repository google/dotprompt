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
from collections.abc import Generator
from pathlib import Path

import pytest

from dotpromptz.stores import DirStoreSync
from dotpromptz.stores._testutils import (
    create_test_partial,
    create_test_prompt,
)
from dotpromptz.stores._typing import (
    DeleteOptions,
    DirStoreOptions,
    LoadOptions,
)
from dotpromptz.typing import PromptData


class TestDirStoreSync:
    """Test the synchronous directory store."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_list_prompts(self, temp_dir: Path) -> None:
        """Test listing prompts synchronously."""
        # Create test prompts
        create_test_prompt(temp_dir, 'test1')
        create_test_prompt(temp_dir, 'test2')
        create_test_prompt(temp_dir, 'test3', 'v1')
        create_test_prompt(temp_dir, 'subdir/test4')

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))
        results = store.list()

        # Verify results
        assert len(results.prompts) == 4
        prompt_names = [p.name for p in results.prompts]
        assert 'test1' in prompt_names
        assert 'test2' in prompt_names
        assert 'test3' in prompt_names
        assert 'subdir/test4' in prompt_names

    def test_list_partials(self, temp_dir: Path) -> None:
        """Test listing partial prompts synchronously."""
        # Create test partials
        create_test_partial(temp_dir, 'draft1')
        create_test_partial(temp_dir, 'draft2', 'v1')

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))
        results = store.list_partials()

        # Verify results
        assert len(results.partials) == 2
        partial_names = [p.name for p in results.partials]
        assert 'draft1' in partial_names
        assert 'draft2' in partial_names

    def test_load_prompt(self, temp_dir: Path) -> None:
        """Test loading a prompt synchronously."""
        # Create a test prompt
        create_test_prompt(temp_dir, 'test1')

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))
        prompt = store.load('test1')

        # Verify the loaded prompt
        assert prompt is not None
        assert prompt.name == 'test1'
        assert prompt.source == 'Test content for test1'
        assert prompt.version is not None

    def test_load_prompt_with_variant(self, temp_dir: Path) -> None:
        """Test loading a prompt with variant synchronously."""
        # Create a test prompt with variant
        create_test_prompt(temp_dir, 'test2', 'v1')

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))
        prompt = store.load('test2', LoadOptions(variant='v1'))

        # Verify the loaded prompt
        assert prompt.name == 'test2'
        assert prompt.variant == 'v1'
        assert prompt.source == 'Test content for test2'

    def test_load_prompt_not_found(self, temp_dir: Path) -> None:
        """Test loading a non-existent prompt synchronously."""
        store = DirStoreSync(DirStoreOptions(directory=temp_dir))
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            store.load('nonexistent')

    def test_load_partial(self, temp_dir: Path) -> None:
        """Test loading a partial prompt synchronously."""
        # Create a test partial
        create_test_partial(temp_dir, 'draft1')

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))
        partial = store.load_partial('draft1')

        # Verify the loaded partial
        assert partial is not None
        assert partial.name == 'draft1'
        assert partial.source == 'Partial content for draft1'

    def test_save_prompt(self, temp_dir: Path) -> None:
        """Test saving a prompt synchronously."""
        store = DirStoreSync(DirStoreOptions(directory=temp_dir))

        # Create a prompt object
        prompt = PromptData(
            name='new_prompt',
            source='This is a new prompt',
            variant=None,
            version=None,
        )

        # Save the prompt
        result = store.save(prompt)

        # Verify the result
        assert result.name == 'new_prompt'

        # Verify file was created
        file_path = temp_dir / 'new_prompt.prompt'
        assert os.path.exists(file_path)

        # Verify content
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        assert content == 'This is a new prompt'

    def test_save_prompt_with_variant(self, temp_dir: Path) -> None:
        """Test saving a prompt with variant synchronously."""
        store = DirStoreSync(DirStoreOptions(directory=temp_dir))

        # Create a prompt object with variant
        prompt = PromptData(
            name='new_prompt',
            source='This is a new prompt with variant',
            variant='v1',
            version=None,
        )

        # Save the prompt
        result = store.save(prompt)

        # Verify the result
        assert result.name == 'new_prompt'
        assert result.variant == 'v1'

        # Verify file was created
        file_path = temp_dir / 'new_prompt.v1.prompt'
        assert os.path.exists(file_path)

    def test_save_partial(self, temp_dir: Path) -> None:
        """Test saving a partial prompt synchronously."""
        store = DirStoreSync(DirStoreOptions(directory=temp_dir))

        # Create a partial object without is_partial as it's not part
        # of the model
        partial = PromptData(
            name='new_draft',
            source='Draft prompt',
            variant=None,
            version=None,
        )

        # Save the partial
        store.save_partial(partial)

        # Verify file was created with underscore prefix
        file_path = temp_dir / '_new_draft.prompt'
        assert os.path.exists(file_path)

        # Verify content
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
        assert content == 'Draft prompt'

    def test_delete_prompt(self, temp_dir: Path) -> None:
        """Test deleting a prompt synchronously."""
        file_path = create_test_prompt(temp_dir, 'to_delete')
        assert os.path.exists(file_path)

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))

        # Delete the prompt
        result = store.delete('to_delete')

        # Verify deletion
        assert result.success
        assert not os.path.exists(file_path)

    def test_delete_prompt_not_found(self, temp_dir: Path) -> None:
        """Test deleting a non-existent prompt synchronously."""
        store = DirStoreSync(DirStoreOptions(directory=temp_dir))

        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            store.delete('nonexistent')

    def test_delete_partial(self, temp_dir: Path) -> None:
        """Test deleting a partial prompt synchronously."""
        file_path = create_test_partial(temp_dir, 'draft_to_delete')
        assert os.path.exists(file_path)

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))

        # Delete the partial
        result = store.delete('draft_to_delete')

        # Verify deletion
        assert result.success
        assert not os.path.exists(file_path)

    def test_delete_variant(self, temp_dir: Path) -> None:
        """Test deleting a prompt with variant synchronously."""
        file_path = create_test_prompt(temp_dir, 'test', 'v1')
        assert os.path.exists(file_path)

        store = DirStoreSync(DirStoreOptions(directory=temp_dir))

        # Delete the prompt with variant
        result = store.delete('test', DeleteOptions(variant='v1'))

        # Verify deletion
        assert result.success
        assert not os.path.exists(file_path)
