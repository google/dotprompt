#!/usr/bin/env python
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for directory store utility functions."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from dotpromptz.stores._dir_util import (
    is_partial,
    parse_prompt_filename,
    scan_directory,
)


class TestParsePromptFilename:
    """Tests for parse_prompt_filename function."""

    def test_basic_prompt(self) -> None:
        """Test parsing a basic prompt filename."""
        result = parse_prompt_filename('basic.prompt')
        assert result.name == 'basic'
        assert result.variant is None
        assert result.version is None

    def test_prompt_with_variant(self) -> None:
        """Test parsing a prompt filename with a variant."""
        result = parse_prompt_filename('example.variant.prompt')
        assert result.name == 'example'
        assert result.variant == 'variant'
        assert result.version is None

    def test_prompt_with_version(self) -> None:
        """Test parsing a prompt filename with a version-like variant."""
        result = parse_prompt_filename('example.v1.prompt')
        assert result.name == 'example'
        assert result.variant == 'v1'
        assert result.version is None

    def test_invalid_prompt_format(self) -> None:
        """Test that filenames with too many segments are rejected."""
        with pytest.raises(ValueError) as exc_info:
            parse_prompt_filename('example.partial.variant.prompt')
        assert 'Invalid prompt filename format' in str(exc_info.value)

    def test_name_with_underscore(self) -> None:
        """Test parsing a prompt filename with underscores in the name."""
        result = parse_prompt_filename('complex_name.prompt')
        assert result.name == 'complex_name'
        assert result.variant is None
        assert result.version is None

    def test_name_with_hyphen(self) -> None:
        """Test parsing a prompt filename with hyphens in the name."""
        result = parse_prompt_filename('complex-name.prompt')
        assert result.name == 'complex-name'
        assert result.variant is None
        assert result.version is None

    def test_invalid_file_extension(self) -> None:
        """Test parsing a filename with an invalid extension."""
        with pytest.raises(ValueError, match='Invalid prompt file'):
            parse_prompt_filename('example.txt')


class TestIsPartial:
    """Tests for is_partial function."""

    def test_partial_filename(self) -> None:
        """Test identifying a partial prompt filename."""
        assert is_partial('_partial.prompt') is True

    def test_non_partial_filename(self) -> None:
        """Test identifying a non-partial prompt filename."""
        assert is_partial('regular.prompt') is False

    def test_filename_with_underscore_later(self) -> None:
        """Test a filename with an underscore but not at the beginning."""
        assert is_partial('example_with_underscore.prompt') is False


class TestScanDirectory:
    """Tests for scan_directory function."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory with test prompt files."""
        with tempfile.TemporaryDirectory() as tempdir:
            # Create a basic prompt file.
            with open(os.path.join(tempdir, 'basic.prompt'), 'w') as f:
                f.write('content')

            # Create a prompt with variant.
            with open(
                os.path.join(tempdir, 'example.variant.prompt'), 'w'
            ) as f:
                f.write('content with variant')

            # Create a nested directory.
            nested_dir = os.path.join(tempdir, 'nested')
            os.makedirs(nested_dir)

            # Create a prompt in the nested directory.
            with open(os.path.join(nested_dir, 'nested.prompt'), 'w') as f:
                f.write('nested content')

            # Create a non-prompt file.
            with open(os.path.join(tempdir, 'not_a_prompt.txt'), 'w') as f:
                f.write('not a prompt')

            yield Path(tempdir)

    @pytest.mark.asyncio
    async def test_scan_root_directory(self, temp_dir: Path) -> None:
        """Test scanning the root directory for prompt files."""
        results: list[str] = []
        await scan_directory(temp_dir, results=results)

        # Should find basic, example.variant, and nested prompt files
        assert len(results) == 3
        assert 'basic.prompt' in results
        assert 'example.variant.prompt' in results
        assert os.path.join('nested', 'nested.prompt') in results

        # Should not include non-prompt files
        assert 'not_a_prompt.txt' not in results

    @pytest.mark.asyncio
    async def test_scan_nested_directory(self, temp_dir: Path) -> None:
        """Test scanning a nested directory for prompt files."""
        results: list[str] = []
        await scan_directory(temp_dir, dir_path='nested', results=results)

        # Should only find 'nested.prompt' in the nested directory
        assert len(results) == 1
        assert os.path.join('nested', 'nested.prompt') in results

    @pytest.mark.asyncio
    async def test_scan_empty_directory(self, temp_dir: Path) -> None:
        """Test scanning an empty directory."""
        # Create an empty directory
        empty_dir = os.path.join(temp_dir, 'empty')
        os.makedirs(empty_dir)

        results: list[str] = []
        await scan_directory(temp_dir, dir_path='empty', results=results)

        # Should not find any files
        assert len(results) == 0
