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

"""Async implementation of a prompt store that uses a directory for storage.

This module provides an asynchronous implementation of a prompt store that reads
from and writes to the local filesystem. Prompts and partials are stored as
files with specific naming conventions within a configurable base directory.

Key Features:
- Asynchronous I/O operations using asyncio and aiofiles
- Support for hierarchical organization of prompts using directories
- Versioning of prompts based on content hashing
- Support for prompt variants and partials

File Naming Conventions:
- Prompts: `[name][.variant].prompt`
- Partials: `_[name][.variant].prompt`

Example Usage:
```python
from dotpromptz.stores import DirStore, DirStoreOptions
from dotpromptz.typing import PromptData

# Create a store instance
store = DirStore(DirStoreOptions(directory='/path/to/prompts'))

# List available prompts
prompts = await store.list()

# Load a specific prompt
prompt_data = await store.load('my_prompt')

# Save a new prompt
await store.save(
    PromptData(
        name='new_prompt',
        source='This is a prompt template with {{variable}}',
    )
)
```
"""

import asyncio
import os
from pathlib import Path

import aiofiles
import structlog

from dotpromptz.typing import (
    DeletePromptOrPartialOptions,
    ListPartialsOptions,
    ListPromptsOptions,
    LoadPartialOptions,
    LoadPromptOptions,
    PaginatedPartials,
    PaginatedPrompts,
    PartialData,
    PartialRef,
    PromptData,
    PromptRef,
    PromptStoreWritable,
)

from ._io import (
    calculate_version,
    is_partial,
    parse_prompt_filename,
    read_prompt_file_async,
    scan_directory,
)
from ._typing import DirStoreOptions

logger = structlog.get_logger(__name__)


class DirStore(PromptStoreWritable):
    """Async implementation of a directory-based prompt store.

    Reads and writes prompts and partials from/to the local file system
    within a specified directory using asynchronous operations.

    Prompts are files ending with `.prompt`.
    Naming: `[name](.[variant]).prompt`
    Partials: `_[name](.[variant]).prompt`

    Directory structure forms part of the prompt/partial name.
    Versions are calculated using SHA1 hash of file content.

    Implements the `PromptStoreWritable` protocol for async operations.

    Key Operations:
    - List prompts and partials
    - Load specific prompts and partials
    - Save new or updated prompts and partials
    - Delete existing prompts and partials

    Examples:
        ```python
        # Initialize a store with a specific directory
        store = DirStore(DirStoreOptions(directory=Path('./prompts')))

        # List all available prompts
        prompt_list = await store.list()

        # Load a prompt with a specific variant
        prompt = await store.load('greeting', LoadPromptOptions(variant='formal'))

        # Save a new prompt
        await store.save(
            PromptData(
                name='feedback',
                variant='positive',
                source='Thank you for your {{quality}} contribution!',
            )
        )

        # Delete a prompt
        await store.delete('outdated_prompt')
        ```
    """

    def __init__(self, options: DirStoreOptions) -> None:
        """Initializes the async DirStore.

        Args:
            options: Configuration options, including the base directory.
        """
        self._directory = options.directory
        # Ensure the base directory exists.
        # Although async, this check can be sync during init.
        os.makedirs(self._directory, exist_ok=True)
        logger.debug(
            'Async DirStore initialized', directory=str(self._directory)
        )

    async def list(
        self, options: ListPromptsOptions | None = None
    ) -> PaginatedPrompts:
        """Asynchronously lists available prompts (excluding partials).

        Note: Pagination options are ignored as this implementation returns all
        results at once.

        Args:
            options: Listing options (currently unused).

        Returns:
            A PaginatedPrompts object containing all found prompt references.
        """
        await logger.adebug('Listing prompts', options=options)
        files = await scan_directory(self._directory)
        prompts: list[PromptRef] = []

        async def process_file(file_rel_path: str) -> None:
            base_name = os.path.basename(file_rel_path)
            if not is_partial(base_name):
                try:
                    parsed = parse_prompt_filename(base_name)
                    dir_path = os.path.dirname(file_rel_path)
                    if dir_path and dir_path != '.':
                        full_name = (
                            f'{dir_path.replace(os.sep, "/")}/{parsed.name}'
                        )
                    else:
                        full_name = parsed.name

                    full_file_path = self._directory / file_rel_path
                    content = await read_prompt_file_async(full_file_path)
                    version = calculate_version(content)
                    prompts.append(
                        PromptRef(
                            name=full_name,
                            variant=parsed.variant,
                            version=version,
                        )
                    )
                    await logger.adebug(
                        'Found prompt',
                        name=full_name,
                        variant=parsed.variant,
                        version=version,
                    )
                except ValueError as e:
                    await logger.awarn(
                        'Skipping file with invalid name format',
                        file=file_rel_path,
                        error=str(e),
                    )
                except Exception as e:
                    await logger.aerror(
                        'Error processing prompt file',
                        file=file_rel_path,
                        error=str(e),
                    )

        await asyncio.gather(*(process_file(f) for f in files))
        await logger.ainfo('Finished listing prompts', count=len(prompts))
        return PaginatedPrompts(prompts=prompts)

    async def list_partials(
        self, options: ListPartialsOptions | None = None
    ) -> PaginatedPartials:
        """Asynchronously lists available partials.

        Note: Pagination options are ignored.

        Args:
            options: Listing options (currently unused).

        Returns:
            A PaginatedPartials object containing all found partial references.
        """
        await logger.adebug('Listing partials', options=options)
        files = await scan_directory(self._directory)
        partials: list[PartialRef] = []

        async def process_file(file_rel_path: str) -> None:
            base_name = os.path.basename(file_rel_path)
            if is_partial(base_name):
                try:
                    actual_filename = base_name[1:]
                    parsed = parse_prompt_filename(actual_filename)
                    dir_path = os.path.dirname(file_rel_path)
                    if dir_path and dir_path != '.':
                        full_name = (
                            f'{dir_path.replace(os.sep, "/")}/{parsed.name}'
                        )
                    else:
                        full_name = parsed.name

                    full_file_path = self._directory / file_rel_path
                    content = await read_prompt_file_async(full_file_path)
                    version = calculate_version(content)
                    partials.append(
                        PartialRef(
                            name=full_name,
                            variant=parsed.variant,
                            version=version,
                        )
                    )
                    await logger.adebug(
                        'Found partial',
                        name=full_name,
                        variant=parsed.variant,
                        version=version,
                    )
                except ValueError as e:
                    await logger.awarn(
                        'Skipping partial file with invalid name format',
                        file=file_rel_path,
                        error=str(e),
                    )
                except Exception as e:
                    await logger.aerror(
                        'Error processing partial file',
                        file=file_rel_path,
                        error=str(e),
                    )

        await asyncio.gather(*(process_file(f) for f in files))
        await logger.ainfo('Finished listing partials', count=len(partials))
        return PaginatedPartials(partials=partials)

    async def load(
        self, name: str, options: LoadPromptOptions | None = None
    ) -> PromptData:
        """Asynchronously loads a specific prompt from the store.

        Args:
            name: The logical name of the prompt (including subdirectories).
            options: Options like variant or version.

        Returns:
            The loaded prompt data.

        Raises:
            FileNotFoundError: If the prompt file is not found.
            ValueError: If the requested version does not match.
            OSError: If there's an error reading the file.
        """
        variant = options.variant if options else None
        version_opt = options.version if options else None
        dir_name = os.path.dirname(name)
        base_name = os.path.basename(name)
        file_name = (
            f'{base_name}.{variant}.prompt'
            if variant
            else f'{base_name}.prompt'
        )
        file_path = (
            self._directory / dir_name / file_name
            if dir_name
            else self._directory / file_name
        )

        await logger.adebug(
            'Loading prompt', name=name, variant=variant, path=str(file_path)
        )

        try:
            source = await read_prompt_file_async(file_path)
            version = calculate_version(source)

            if version_opt and version_opt != version:
                err_msg = (
                    f"Version mismatch for prompt '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f': requested {version_opt} but found {version}'
                )
                await logger.aerror(err_msg)
                raise ValueError(err_msg)

            await logger.ainfo(
                'Prompt loaded successfully',
                name=name,
                variant=variant,
                version=version,
            )
            return PromptData(
                name=name, variant=variant, version=version, source=source
            )
        except FileNotFoundError:
            err_msg = f"Prompt '{name}' not found at {file_path}"
            await logger.aerror(err_msg)
            raise FileNotFoundError(err_msg) from None
        except ValueError:
            raise
        except OSError as e:
            err_msg = f"Failed to load prompt '{name}' due to OS error: {e}"
            await logger.aerror(err_msg)
            raise OSError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error loading prompt '{name}': {e}"
            await logger.aerror(err_msg)
            raise RuntimeError(err_msg) from e

    async def load_partial(
        self, name: str, options: LoadPartialOptions | None = None
    ) -> PartialData:
        """Asynchronously loads a specific partial from the store.

        Args:
            name: The logical name of the partial (excluding leading '_').
            options: Options like variant or version.

        Returns:
            The loaded partial data.

        Raises:
            FileNotFoundError: If the partial file is not found.
            ValueError: If the requested version does not match.
            OSError: If there's an error reading the file.
        """
        variant = options.variant if options else None
        version_opt = options.version if options else None
        dir_name = os.path.dirname(name)
        base_name = os.path.basename(name)
        # Partials have leading underscore
        file_name = (
            f'_{base_name}.{variant}.prompt'
            if variant
            else f'_{base_name}.prompt'
        )
        file_path = (
            self._directory / dir_name / file_name
            if dir_name
            else self._directory / file_name
        )

        await logger.adebug(
            'Loading partial', name=name, variant=variant, path=str(file_path)
        )

        try:
            source = await read_prompt_file_async(file_path)
            version = calculate_version(source)

            if version_opt and version_opt != version:
                err_msg = (
                    f"Version mismatch for partial '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f': requested {version_opt} but found {version}'
                )
                await logger.aerror(err_msg)
                raise ValueError(err_msg)

            await logger.ainfo(
                'Partial loaded successfully',
                name=name,
                variant=variant,
                version=version,
            )
            return PartialData(
                name=name, variant=variant, version=version, source=source
            )
        except FileNotFoundError:
            err_msg = f"Partial '{name}' not found at {file_path}"
            await logger.aerror(err_msg)
            raise FileNotFoundError(err_msg) from None
        except ValueError:
            raise
        except OSError as e:
            err_msg = f"Failed to load partial '{name}' due to OS error: {e}"
            await logger.aerror(err_msg)
            raise OSError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error loading partial '{name}': {e}"
            await logger.aerror(err_msg)
            raise RuntimeError(err_msg) from e

    async def save(self, prompt: PromptData) -> None:
        """Asynchronously saves a prompt or partial to the store.

        Determines the filename based on name and variant, creates directories
        if needed, and writes the source content.

        Args:
            prompt: The PromptData (or PartialData) to save.

        Raises:
            ValueError: If prompt name or source is missing.
            OSError: If there's an error creating directories or writing file.
        """
        if not prompt.name:
            await logger.aerror('Save failed: prompt name is required')
            raise ValueError('Prompt name is required for saving.')
        if prompt.source is None:
            await logger.aerror('Save failed: prompt source is required')
            raise ValueError('Prompt source content is required for saving.')

        dir_name = os.path.dirname(prompt.name)
        base_name = os.path.basename(prompt.name)
        file_name = (
            f'{base_name}.{prompt.variant}.prompt'
            if prompt.variant
            else f'{base_name}.prompt'
        )
        file_path = (
            self._directory / dir_name / file_name
            if dir_name
            else self._directory / file_name
        )
        file_dir = file_path.parent

        await logger.adebug(
            'Saving prompt',
            name=prompt.name,
            variant=prompt.variant,
            path=str(file_path),
        )

        try:
            if not file_dir.exists():
                # os.makedirs is potentially blocking so run in a worker thread
                # and await the result.
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None, lambda: os.makedirs(file_dir, exist_ok=True)
                )
                await logger.adebug(
                    'Created directory', directory=str(file_dir)
                )

            async with aiofiles.open(
                file_path, mode='w', encoding='utf-8'
            ) as f:
                await f.write(prompt.source)
            await logger.ainfo('Prompt saved successfully', path=str(file_path))
        except OSError as e:
            err_msg = (
                f"Failed to save prompt '{prompt.name}' to {file_path} "
                f'due to OS error: {e}'
            )
            await logger.aerror(err_msg)
            raise OSError(err_msg) from e
        except Exception as e:
            err_msg = (
                f"Unexpected error saving prompt '{prompt.name}' "
                f'to {file_path}: {e}'
            )
            await logger.aerror(err_msg)
            raise RuntimeError(err_msg) from e

    async def delete(
        self, name: str, options: DeletePromptOrPartialOptions | None = None
    ) -> None:
        """Asynchronously deletes a prompt or partial file.

        Tries deleting the prompt file first, then the partial file if the
        prompt file doesn't exist.

        Args:
            name: The logical name of the prompt or partial.
            options: Options specifying the variant to delete.

        Raises:
            FileNotFoundError: If neither the prompt nor partial file exists.
            OSError: If there's an error deleting the file.
        """
        variant = options.variant if options else None
        dir_name = os.path.dirname(name)
        base_name = os.path.basename(name)

        prompt_file_name = (
            f'{base_name}.{variant}.prompt'
            if variant
            else f'{base_name}.prompt'
        )
        prompt_file_path = (
            self._directory / dir_name / prompt_file_name
            if dir_name
            else self._directory / prompt_file_name
        )

        partial_file_name = (
            f'_{base_name}.{variant}.prompt'
            if variant
            else f'_{base_name}.prompt'
        )
        partial_file_path = (
            self._directory / dir_name / partial_file_name
            if dir_name
            else self._directory / partial_file_name
        )

        file_to_delete: Path | None = None
        item_type = 'item'

        await logger.adebug(
            'Attempting to delete',
            name=name,
            variant=variant,
            prompt_path=str(prompt_file_path),
            partial_path=str(partial_file_path),
        )

        loop = asyncio.get_running_loop()

        try:
            prompt_exists = await loop.run_in_executor(
                None, prompt_file_path.exists
            )
            if prompt_exists:
                file_to_delete = prompt_file_path
                item_type = 'prompt'
            else:
                partial_exists = await loop.run_in_executor(
                    None, partial_file_path.exists
                )
                if partial_exists:
                    file_to_delete = partial_file_path
                    item_type = 'partial'
        except OSError as e:
            await logger.aerror(
                'OS Error checking file existence during delete',
                name=name,
                variant=variant,
                error=str(e),
            )
            raise OSError(
                f"OS Error checking existence for '{name}'"
                f'{f" (variant: {variant})" if variant else ""}: {e}'
            ) from e
        except Exception as e:
            await logger.aerror(
                'Unexpected error checking file existence during delete',
                name=name,
                variant=variant,
                error=str(e),
            )
            raise RuntimeError(
                f"Unexpected error checking existence for '{name}'"
                f'{f" (variant: {variant})" if variant else ""}: {e}'
            ) from e

        if file_to_delete:
            try:
                # os.remove is potentially blocking so run in a worker thread
                # and await.
                await loop.run_in_executor(None, os.remove, file_to_delete)
                await logger.ainfo(
                    f'{item_type.capitalize()} deleted successfully',
                    path=str(file_to_delete),
                )
            except OSError as e:
                err_msg = (
                    f"Failed to delete {item_type} '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f' at {file_to_delete} due to OS error: {e}'
                )
                await logger.aerror(err_msg)
                raise OSError(err_msg) from e
            except Exception as e:
                err_msg = (
                    f"Unexpected error deleting {item_type} '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f' at {file_to_delete}: {e}'
                )
                await logger.aerror(err_msg)
                raise RuntimeError(err_msg) from e
        else:
            err_msg = (
                f"Failed to delete '{name}'"
                f'{f" (variant: {variant})" if variant else ""}:'
                f' File not found at expected paths {prompt_file_path}'
                f' or {partial_file_path}'
            )
            await logger.aerror(err_msg)
            raise FileNotFoundError(err_msg)
