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

"""Sync implementation of a prompt store that uses a directory for storage.

This module provides a synchronous implementation of a prompt store that reads
from and writes to the local filesystem. Prompts and partials are stored as
files with specific naming conventions within a configurable base directory.

Key Features:
- Synchronous I/O operations for simpler usage patterns
- Support for hierarchical organization of prompts using directories
- Versioning of prompts based on content hashing
- Support for prompt variants and partials

File Naming Conventions:
- Prompts: `[name][.variant].prompt`
- Partials: `_[name][.variant].prompt`

Example Usage:
```python
from dotpromptz.stores import DirStoreSync, DirStoreOptions
from dotpromptz.typing import PromptData

# Create a store instance
store = DirStoreSync(DirStoreOptions(directory='/path/to/prompts'))

# List available prompts
prompts = store.list()

# Load a specific prompt
prompt_data = store.load('my_prompt')

# Save a new prompt
store.save(
    PromptData(
        name='new_prompt',
        source='This is a prompt template with {{variable}}',
    )
)
```
"""

import os
from pathlib import Path

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
    PromptStoreWritableSync,
)

from ._io import (
    calculate_version,
    is_partial,
    parse_prompt_filename,
    read_prompt_file_sync,
    scan_directory_sync,
)
from ._typing import DirStoreOptions

logger = structlog.get_logger(__name__)


class DirStoreSync(PromptStoreWritableSync):
    """Sync implementation of a directory-based prompt store.

    Reads and writes prompts and partials from/to the local file system
    within a specified directory using standard synchronous operations.

    Prompts are files ending with `.prompt`.
    Naming: `[name](.[variant]).prompt`
    Partials: `_[name](.[variant]).prompt`

    Directory structure forms part of the prompt/partial name.
    Versions are calculated using SHA1 hash of file content.

    Implements the `PromptStoreWritableSync` protocol for sync operations.

    Key Operations:
    - List prompts and partials
    - Load specific prompts and partials
    - Save new or updated prompts and partials
    - Delete existing prompts and partials

    Examples:
        ```python
        # Initialize a store with a specific directory
        store = DirStoreSync(DirStoreOptions(directory=Path('./prompts')))

        # List all available prompts
        prompt_list = store.list()

        # Load a prompt with a specific variant
        prompt = store.load('greeting', LoadPromptOptions(variant='formal'))

        # Save a new prompt
        store.save(
            PromptData(
                name='feedback',
                variant='positive',
                source='Thank you for your {{quality}} contribution!',
            )
        )

        # Delete a prompt
        store.delete('outdated_prompt')
        ```
    """

    def __init__(self, options: DirStoreOptions) -> None:
        """Initializes the sync DirStore.

        Args:
            options: Configuration options, including the base directory.
        """
        self._directory = options.directory
        # Ensure the base directory exists.
        os.makedirs(self._directory, exist_ok=True)
        logger.debug('Sync DirStore initialized', directory=str(self._directory))

    def list(self, options: ListPromptsOptions | None = None) -> PaginatedPrompts:
        """Synchronously lists available prompts (excluding partials).

        Note: Pagination options are ignored.

        Args:
            options: Listing options (currently unused).

        Returns:
            A PaginatedPrompts object containing all found prompt references.
        """
        logger.debug('Listing prompts (sync)', options=options)
        files = scan_directory_sync(self._directory)
        prompts: list[PromptRef] = []

        for file_rel_path in files:
            base_name = os.path.basename(file_rel_path)
            if not is_partial(base_name):
                try:
                    parsed = parse_prompt_filename(base_name)
                    dir_path = os.path.dirname(file_rel_path)
                    # Corrected name construction
                    if dir_path and dir_path != '.':
                        full_name = f'{dir_path.replace(os.sep, "/")}/{parsed.name}'
                    else:
                        full_name = parsed.name

                    full_file_path = self._directory / file_rel_path
                    content = read_prompt_file_sync(full_file_path)
                    version = calculate_version(content)
                    prompts.append(
                        PromptRef(
                            name=full_name,
                            variant=parsed.variant,
                            version=version,
                        )
                    )
                    logger.debug(
                        'Found prompt (sync)',
                        name=full_name,
                        variant=parsed.variant,
                        version=version,
                    )
                except ValueError as e:
                    logger.warn(
                        'Skipping file with invalid name format (sync)',
                        file=file_rel_path,
                        error=str(e),
                    )
                except Exception as e:
                    logger.error(
                        'Error processing prompt file (sync)',
                        file=file_rel_path,
                        error=str(e),
                    )

        logger.info('Finished listing prompts (sync)', count=len(prompts))
        return PaginatedPrompts(prompts=prompts)

    def list_partials(self, options: ListPartialsOptions | None = None) -> PaginatedPartials:
        """Synchronously lists available partials.

        Note: Pagination options are ignored.

        Args:
            options: Listing options (currently unused).

        Returns:
            A PaginatedPartials object containing all found partial references.
        """
        logger.debug('Listing partials (sync)', options=options)
        files = scan_directory_sync(self._directory)
        partials: list[PartialRef] = []

        for file_rel_path in files:
            base_name = os.path.basename(file_rel_path)
            if is_partial(base_name):
                try:
                    actual_filename = base_name[1:]
                    parsed = parse_prompt_filename(actual_filename)
                    dir_path = os.path.dirname(file_rel_path)
                    # Corrected name construction
                    if dir_path and dir_path != '.':
                        full_name = f'{dir_path.replace(os.sep, "/")}/{parsed.name}'
                    else:
                        full_name = parsed.name

                    full_file_path = self._directory / file_rel_path
                    content = read_prompt_file_sync(full_file_path)
                    version = calculate_version(content)
                    partials.append(
                        PartialRef(
                            name=full_name,
                            variant=parsed.variant,
                            version=version,
                        )
                    )
                    logger.debug(
                        'Found partial (sync)',
                        name=full_name,
                        variant=parsed.variant,
                        version=version,
                    )
                except ValueError as e:
                    logger.warn(
                        'Skipping partial file with invalid name format (sync)',
                        file=file_rel_path,
                        error=str(e),
                    )
                except Exception as e:
                    logger.error(
                        'Error processing partial file (sync)',
                        file=file_rel_path,
                        error=str(e),
                    )

        logger.info('Finished listing partials (sync)', count=len(partials))
        return PaginatedPartials(partials=partials)

    def load(self, name: str, options: LoadPromptOptions | None = None) -> PromptData:
        """Synchronously loads a specific prompt from the store.

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
        file_name = f'{base_name}.{variant}.prompt' if variant else f'{base_name}.prompt'
        file_path = self._directory / dir_name / file_name if dir_name else self._directory / file_name

        logger.debug(
            'Loading prompt (sync)',
            name=name,
            variant=variant,
            path=str(file_path),
        )

        try:
            source = read_prompt_file_sync(file_path)
            version = calculate_version(source)

            if version_opt and version_opt != version:
                err_msg = (
                    f"Version mismatch for prompt '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f': requested {version_opt} but found {version}'
                )
                logger.error(err_msg)
                raise ValueError(err_msg)

            logger.info(
                'Prompt loaded successfully (sync)',
                name=name,
                variant=variant,
                version=version,
            )
            return PromptData(name=name, variant=variant, version=version, source=source)
        except FileNotFoundError:
            err_msg = f"Prompt '{name}' not found at {file_path}"
            logger.error(err_msg)
            raise FileNotFoundError(err_msg) from None
        except ValueError:
            raise
        except OSError as e:
            err_msg = f"Failed to load prompt '{name}' due to OS error: {e}"
            logger.error(err_msg)
            raise OSError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error loading prompt '{name}': {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e

    def load_partial(self, name: str, options: LoadPartialOptions | None = None) -> PartialData:
        """Synchronously loads a specific partial from the store.

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
        file_name = f'_{base_name}.{variant}.prompt' if variant else f'_{base_name}.prompt'
        file_path = self._directory / dir_name / file_name if dir_name else self._directory / file_name

        logger.debug(
            'Loading partial (sync)',
            name=name,
            variant=variant,
            path=str(file_path),
        )

        try:
            source = read_prompt_file_sync(file_path)
            version = calculate_version(source)

            if version_opt and version_opt != version:
                err_msg = (
                    f"Version mismatch for partial '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f': requested {version_opt} but found {version}'
                )
                logger.error(err_msg)
                raise ValueError(err_msg)

            logger.info(
                'Partial loaded successfully (sync)',
                name=name,
                variant=variant,
                version=version,
            )
            return PartialData(name=name, variant=variant, version=version, source=source)
        except FileNotFoundError:
            err_msg = f"Partial '{name}' not found at {file_path}"
            logger.error(err_msg)
            raise FileNotFoundError(err_msg) from None
        except ValueError:
            raise
        except OSError as e:
            err_msg = f"Failed to load partial '{name}' due to OS error: {e}"
            logger.error(err_msg)
            raise OSError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error loading partial '{name}': {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e

    def save(self, prompt: PromptData) -> None:
        """Synchronously saves a prompt or partial to the store.

        Args:
            prompt: The PromptData (or PartialData) to save.

        Raises:
            ValueError: If prompt name or source is missing.
            OSError: If there's an error creating directories or writing file.
        """
        if not prompt.name:
            logger.error('Save failed (sync): prompt name is required')
            raise ValueError('Prompt name is required for saving.')
        if prompt.source is None:
            logger.error('Save failed (sync): prompt source is required')
            raise ValueError('Prompt source content is required for saving.')

        dir_name = os.path.dirname(prompt.name)
        base_name = os.path.basename(prompt.name)
        file_name = f'{base_name}.{prompt.variant}.prompt' if prompt.variant else f'{base_name}.prompt'
        file_path = self._directory / dir_name / file_name if dir_name else self._directory / file_name
        file_dir = file_path.parent

        logger.debug(
            'Saving prompt (sync)',
            name=prompt.name,
            variant=prompt.variant,
            path=str(file_path),
        )

        try:
            # Ensure the target directory exists.
            os.makedirs(file_dir, exist_ok=True)
            logger.debug('Ensured directory exists (sync)', directory=str(file_dir))

            # Write the prompt source content synchronously.
            with open(file_path, mode='w', encoding='utf-8') as f:
                f.write(prompt.source)
            logger.info('Prompt saved successfully (sync)', path=str(file_path))
        except OSError as e:
            err_msg = f"Failed to save prompt '{prompt.name}' to {file_path} due to OS error: {e}"
            logger.error(err_msg)
            raise OSError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error saving prompt '{prompt.name}' to {file_path}: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e

    def delete(self, name: str, options: DeletePromptOrPartialOptions | None = None) -> None:
        """Synchronously deletes a prompt or partial file.

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

        prompt_file_name = f'{base_name}.{variant}.prompt' if variant else f'{base_name}.prompt'
        prompt_file_path = (
            self._directory / dir_name / prompt_file_name if dir_name else self._directory / prompt_file_name
        )

        partial_file_name = f'_{base_name}.{variant}.prompt' if variant else f'_{base_name}.prompt'
        partial_file_path = (
            self._directory / dir_name / partial_file_name if dir_name else self._directory / partial_file_name
        )

        file_to_delete: Path | None = None
        item_type = 'item'

        logger.debug(
            'Attempting to delete (sync)',
            name=name,
            variant=variant,
            prompt_path=str(prompt_file_path),
            partial_path=str(partial_file_path),
        )

        try:
            if prompt_file_path.exists():
                file_to_delete = prompt_file_path
                item_type = 'prompt'
            elif partial_file_path.exists():
                file_to_delete = partial_file_path
                item_type = 'partial'
        except OSError as e:
            logger.error(
                'OS Error checking file existence during delete (sync)',
                name=name,
                variant=variant,
                error=str(e),
            )
            raise OSError(
                f"OS Error checking existence for '{name}'{f' (variant: {variant})' if variant else ''}: {e}"
            ) from e
        except Exception as e:
            logger.error(
                'Unexpected error checking file existence during delete (sync)',
                name=name,
                variant=variant,
                error=str(e),
            )
            raise RuntimeError(
                f"Unexpected error checking existence for '{name}'{f' (variant: {variant})' if variant else ''}: {e}"
            ) from e

        if file_to_delete:
            try:
                os.remove(file_to_delete)
                logger.info(
                    f'{item_type.capitalize()} deleted successfully (sync)',
                    path=str(file_to_delete),
                )
            except OSError as e:
                err_msg = (
                    f"Failed to delete {item_type} '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f' at {file_to_delete} due to OS error: {e}'
                )
                logger.error(err_msg)
                raise OSError(err_msg) from e
            except Exception as e:
                err_msg = (
                    f"Unexpected error deleting {item_type} '{name}'"
                    f'{f" (variant: {variant})" if variant else ""}'
                    f' at {file_to_delete}: {e}'
                )
                logger.error(err_msg)
                raise RuntimeError(err_msg) from e
        else:
            err_msg = (
                f"Failed to delete '{name}'"
                f'{f" (variant: {variant})" if variant else ""}:'
                f' File not found at expected paths {prompt_file_path}'
                f' or {partial_file_path}'
            )
            logger.error(err_msg)
            raise FileNotFoundError(err_msg)
