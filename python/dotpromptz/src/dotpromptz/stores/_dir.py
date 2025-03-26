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

"""Directory-based store implementation."""

from __future__ import annotations

import os
from pathlib import Path

import aiofiles
import structlog

from dotpromptz.stores._dir_util import (
    calculate_version,
    is_partial,
    parse_prompt_filename,
    scan_directory,
)
from dotpromptz.stores._typing import (
    DeleteOptions,
    DirStoreOptions,
    ListPartialResults,
    ListPromptResults,
    LoadOptions,
    PaginationOptions,
    PromptDeleteResult,
    PromptSaveResult,
)
from dotpromptz.typing import (
    PartialData,
    PartialRef,
    PromptData,
    PromptRef,
    PromptStore,
    PromptStoreWritable,
)

logger = structlog.get_logger(__name__)


class DirStore(PromptStoreWritable, PromptStore):
    """Directory-based store implementation.

    A prompt store implementation that reads and writes prompts and partials
    directly from/to the local file system within a specified directory.

    Prompts are expected to be files with a `.prompt` extension.
    File naming convention: `[name](.[variant]).prompt`
    Partials follow the same convention but are prefixed with an underscore:
    `_[name](.[variant]).prompt`

    Directories can be used to organize prompts, forming part of the prompt name
    (e.g., a prompt "bar" in directory "foo" will have the name "foo/bar").
    Versions are calculated based on the SHA1 hash of the file content.
    """

    def __init__(self, options: DirStoreOptions) -> None:
        """Initialize a directory-based store.

        Args:
            options: Configuration options including the directory path.
        """
        directory = options.directory
        if not directory:
            raise ValueError('Directory is required for DirStore')
        self._directory = Path(directory)

    async def _read_prompt_file(self, file_path: Path) -> str:
        """Read the content of a prompt file.

        Args:
            file_path: Path to the prompt file.

        Returns:
            The file content as a string.
        """
        async with aiofiles.open(file_path) as f:
            return await f.read()

    async def list(
        self, options: PaginationOptions | None = None
    ) -> ListPromptResults:
        """List available prompt names and versions.

        Args:
            options: Optional pagination options.

        Returns:
            A list of prompt refs.
        """
        try:
            all_files = await scan_directory(self._directory)
            results: list[PromptRef] = []

            for file in all_files:
                file_dir, file_name = os.path.split(file)
                # Skip partials
                if is_partial(file_name):
                    continue

                try:
                    parsed = parse_prompt_filename(file_name)
                    # Convert to PromptRef object
                    full_name = (
                        f'{file_dir}/{parsed.name}' if file_dir else parsed.name
                    )
                    ref = PromptRef(
                        name=full_name,
                        variant=parsed.variant,
                        version=parsed.version,
                    )
                    results.append(ref)
                except Exception as e:
                    await logger.aerror(
                        'Error parsing file', file=file, error=str(e)
                    )

            # Sort by name, variant, and version to ensure consistent order
            results.sort(
                key=lambda ref: (ref.name, ref.variant or '', ref.version or '')
            )

            # Apply pagination if needed
            if options and options.limit is not None:
                # Implement pagination here...
                pass

            return ListPromptResults(prompts=results)
        except Exception as e:
            await logger.aerror('Error listing prompts', error=str(e))
            return ListPromptResults()

    async def list_partials(
        self, options: PaginationOptions | None = None
    ) -> ListPartialResults:
        """List available partial file names.

        Args:
            options: Optional pagination options.

        Returns:
            A list of partial refs.
        """
        try:
            all_files = await scan_directory(self._directory)
            results: list[PartialRef] = []

            for file in all_files:
                file_dir, file_name = os.path.split(file)
                # Only include partials
                if not is_partial(file_name):
                    continue

                try:
                    parsed = parse_prompt_filename(file_name)
                    # Convert to PartialRef object
                    full_name = (
                        f'{file_dir}/{parsed.name}' if file_dir else parsed.name
                    )

                    # Remove leading underscore from partial names
                    if full_name.startswith('_'):
                        full_name = full_name[1:]

                    ref = PartialRef(
                        name=full_name,
                        variant=parsed.variant,
                        version=parsed.version,
                    )
                    results.append(ref)
                except Exception as e:
                    await logger.aerror(
                        'Error parsing file', file=file, error=str(e)
                    )

            # Sort by name, variant, and version to ensure consistent order
            results.sort(
                key=lambda ref: (ref.name, ref.variant or '', ref.version or '')
            )

            # Apply pagination if needed
            if options and options.limit is not None:
                # Implement pagination here...
                pass

            return ListPartialResults(partials=results)
        except Exception as e:
            await logger.aerror('Error listing partials', error=str(e))
            return ListPartialResults()

    async def load(
        self, name: str, options: LoadOptions | None = None
    ) -> PromptData:
        """Load a prompt by name.

        Args:
            name: The name of the prompt to load.
            options: Optional parameters including variant and version.

        Returns:
            The loaded prompt data.

        Raises:
            FileNotFoundError: If the prompt is not found.
        """
        try:
            # Handle options
            variant = options.variant if options else None

            # Normalize directory path if name contains subdirectories
            dir_path, base_name = os.path.split(name)

            # Scan the directory for prompt files
            all_files = await scan_directory(self._directory)

            for file in all_files:
                file_dir, file_name = os.path.split(file)

                if is_partial(file_name):
                    # Skip partials
                    continue

                try:
                    parsed = parse_prompt_filename(file_name)
                    file_full_name = (
                        f'{file_dir}/{parsed.name}' if file_dir else parsed.name
                    )

                    # Check if this is the file we're looking for
                    if file_full_name == name and (
                        variant is None or parsed.variant == variant
                    ):
                        full_file_path = self._directory / file
                        content = await self._read_prompt_file(full_file_path)
                        version = calculate_version(content)

                        return PromptData(
                            name=name,
                            source=content,
                            variant=parsed.variant,
                            version=version,
                        )
                except Exception as e:
                    await logger.aerror(
                        'Error parsing file during load',
                        file=file,
                        error=str(e),
                    )
                    continue

            # Prompt not found
            variant_info = f' (variant: {variant})' if variant else ''
            raise FileNotFoundError(f"Prompt '{name}'{variant_info} not found")
        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        except Exception as e:
            error_msg = f"Error loading prompt '{name}': {str(e)}"
            await logger.aerror('Error loading prompt', name=name, error=str(e))
            raise FileNotFoundError(error_msg) from e

    async def load_partial(
        self, name: str, options: LoadOptions | None = None
    ) -> PartialData:
        """Load a specific partial prompt by name.

        Args:
            name: The name of the partial to load.
            options: Optional parameters including variant and version.

        Returns:
            The partial data.

        Raises:
            FileNotFoundError: If the partial is not found.
        """
        variant = options.variant if options else None
        try:
            all_files = await scan_directory(self._directory)
            for file in all_files:
                file_dir, file_name = os.path.split(file)
                if not is_partial(file_name):
                    continue
                try:
                    parsed = parse_prompt_filename(file_name)
                    file_name_without_underscore = parsed.name
                    if file_name_without_underscore.startswith('_'):
                        file_name_without_underscore = (
                            file_name_without_underscore[1:]
                        )
                    file_full_name = (
                        f'{file_dir}/{file_name_without_underscore}'
                        if file_dir
                        else file_name_without_underscore
                    )
                    if file_full_name == name and (
                        variant is None or parsed.variant == variant
                    ):
                        full_file_path = self._directory / file
                        content = await self._read_prompt_file(full_file_path)
                        version = calculate_version(content)
                        return PartialData(
                            name=name,
                            source=content,
                            variant=parsed.variant,
                            version=version,
                        )
                except Exception as e:
                    await logger.aerror(
                        'Error parsing file during load_partial',
                        file=file,
                        error=str(e),
                    )
            variant_info = f' (variant: {variant})' if variant else ''
            raise FileNotFoundError(f"Partial '{name}'{variant_info} not found")
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Error loading partial '{name}': {str(e)}"
            await logger.aerror(
                'Error loading partial', name=name, error=str(e)
            )
            raise FileNotFoundError(error_msg) from e

    async def save(self, prompt_data: PromptData) -> PromptSaveResult:
        """Save a prompt to the store.

        Args:
            prompt_data: The prompt data to save.

        Returns:
            A result object indicating success and relevant data.
        """
        if not prompt_data.name:
            return PromptSaveResult(
                success=False,
                name='unknown',
                message='Prompt name is required for saving.',
            )

        try:
            name = prompt_data.name
            content = prompt_data.source
            variant = prompt_data.variant
            version = prompt_data.version

            os.makedirs(self._directory, exist_ok=True)

            dir_path, base_name = os.path.split(name)
            if dir_path:
                full_dir = self._directory / dir_path
                os.makedirs(full_dir, exist_ok=True)

            filename = base_name
            if variant:
                filename = f'{base_name}.{variant}'
            if version:
                filename = f'{filename}.{version}'
            filename = f'{filename}.prompt'

            save_path = self._directory
            if dir_path:
                save_path = save_path / dir_path
            save_path = save_path / filename

            async with aiofiles.open(save_path, 'w') as f:
                await f.write(content)

            return PromptSaveResult(
                success=True, name=name, variant=variant, version=version
            )
        except Exception as e:
            error_message = f'Failed to save prompt: {str(e)}'
            await logger.aerror(error_message)
            return PromptSaveResult(
                success=False, name='unknown', message=error_message
            )

    async def save_partial(self, partial_data: PartialData) -> PromptSaveResult:
        """Save a partial prompt to the store.

        Args:
            partial_data: The partial prompt data to save.

        Returns:
            A result object indicating success and any message.
        """
        if not partial_data.name:
            return PromptSaveResult(
                success=False,
                name='unknown',
                message='Partial name is required for saving.',
            )

        try:
            name = partial_data.name
            content = partial_data.source
            variant = partial_data.variant
            version = partial_data.version

            os.makedirs(self._directory, exist_ok=True)

            dir_path, base_name = os.path.split(name)
            if dir_path:
                full_dir = self._directory / dir_path
                os.makedirs(full_dir, exist_ok=True)

            filename = f'_{base_name}'
            if variant:
                filename = f'{filename}.{variant}'
            if version:
                filename = f'{filename}.{version}'
            filename = f'{filename}.prompt'

            save_path = self._directory
            if dir_path:
                save_path = save_path / dir_path
            save_path = save_path / filename

            async with aiofiles.open(save_path, 'w') as f:
                await f.write(content)

            return PromptSaveResult(
                success=True, name=name, variant=variant, version=version
            )
        except Exception as e:
            error_message = f'Failed to save partial: {str(e)}'
            await logger.aerror(error_message)
            return PromptSaveResult(
                success=False, name='unknown', message=error_message
            )

    async def delete(
        self, name: str, options: DeleteOptions | None = None
    ) -> PromptDeleteResult:
        """Delete a prompt from the store.

        Args:
            name: The name of the prompt to delete.
            options: Additional options for deletion.

        Returns:
            A result object indicating success and any message.
        """
        variant = options.variant if options else None

        try:
            all_files = await scan_directory(self._directory)
            deleted = False

            for file in all_files:
                file_dir, file_name = os.path.split(file)

                if is_partial(file_name):
                    continue

                try:
                    parsed = parse_prompt_filename(file_name)
                    file_full_name = (
                        f'{file_dir}/{parsed.name}' if file_dir else parsed.name
                    )

                    if file_full_name == name and (
                        variant is None or parsed.variant == variant
                    ):
                        file_path = self._directory / file
                        os.remove(file_path)
                        deleted = True
                        break
                except Exception as e:
                    await logger.aerror(
                        'Error parsing file during delete',
                        file=file,
                        error=str(e),
                    )

            if deleted:
                return PromptDeleteResult(
                    success=True, name=name, variant=variant
                )
            else:
                variant_info = f' (variant: {variant})' if variant else ''
                message = f"Prompt '{name}'{variant_info} not found"
                return PromptDeleteResult(
                    success=False, name=name, message=message, variant=variant
                )
        except Exception as e:
            error_message = f'Failed to delete prompt: {str(e)}'
            await logger.aerror(error_message)
            return PromptDeleteResult(
                success=False, name=name, message=error_message
            )

    async def delete_partial(
        self, name: str, options: DeleteOptions | None = None
    ) -> PromptDeleteResult:
        """Delete a partial prompt from the store.

        Args:
            name: The name of the partial to delete.
            options: Additional options for deletion.

        Returns:
            A result object indicating success and any message.
        """
        variant = options.variant if options else None

        try:
            all_files = await scan_directory(self._directory)
            deleted = False

            for file in all_files:
                file_dir, file_name = os.path.split(file)

                if not is_partial(file_name):
                    continue

                try:
                    parsed = parse_prompt_filename(file_name)
                    file_full_name = (
                        f'{file_dir}/{parsed.name}' if file_dir else parsed.name
                    )

                    if file_full_name == name and (
                        variant is None or parsed.variant == variant
                    ):
                        file_path = self._directory / file
                        os.remove(file_path)
                        deleted = True
                        break
                except Exception as e:
                    await logger.aerror(
                        'Error parsing file during delete_partial',
                        file=file,
                        error=str(e),
                    )

            if deleted:
                return PromptDeleteResult(
                    success=True, name=name, variant=variant
                )
            else:
                variant_info = f' (variant: {variant})' if variant else ''
                message = f"Partial '{name}'{variant_info} not found"
                return PromptDeleteResult(
                    success=False, name=name, message=message, variant=variant
                )
        except Exception as e:
            error_message = f'Failed to delete partial: {str(e)}'
            await logger.aerror(error_message)
            return PromptDeleteResult(
                success=False, name=name, message=error_message
            )
