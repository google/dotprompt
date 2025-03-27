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

"""Directory-based store for prompts with synchronous API.

Directory-based store implementation that reads and writes prompts and partials
directly from/to the local file system within a specified directory.
"""

from __future__ import annotations

import os
from pathlib import Path

import structlog

from dotpromptz.stores._dir_util import (
    calculate_version,
    is_partial,
    parse_prompt_filename,
    scan_directory_sync,
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


class DirStoreSync(PromptStoreWritable, PromptStore):
    """Directory-based store for prompts with synchronous API.

    This is a synchronous implementation of a filesystem-based prompt store.
    """

    def __init__(self, options: DirStoreOptions) -> None:
        """Initialize the store with a directory.

        Args:
            options: DirStoreOptions instance with a directory
                property containing a string or Path value.

        Raises:
            ValueError: If directory is missing or not a valid path.
        """
        self._directory = options.directory

    def _read_prompt_file(self, file_path: Path) -> str:
        """Read the content of a prompt file.

        Args:
            file_path: Path to the file to read.

        Returns:
            The file content as a string.
        """
        with open(file_path, encoding='utf-8') as f:
            return f.read()

    def list(
        self, options: PaginationOptions | None = None
    ) -> ListPromptResults:
        """List all prompts in the store.

        Args:
            options: Optional pagination parameters (not used in
                this implementation).

        Returns:
            Dict with 'prompts' list and 'cursor' (always None).
        """
        return self.list_prompts(options)

    def list_prompts(
        self, options: PaginationOptions | None = None
    ) -> ListPromptResults:
        """List all prompts in the store.

        Args:
            options: Optional pagination parameters.

        Returns:
            ListPromptResults with 'prompts' list of PromptRef objects and
            'cursor' (always None).
        """
        prompts = []

        prompt_files = scan_directory_sync(self._directory)

        for file in prompt_files:
            if is_partial(os.path.basename(file)):
                continue

            try:
                filename = os.path.basename(file)
                parsed = parse_prompt_filename(filename)
                dir_path = os.path.dirname(file)
                if dir_path:
                    full_name = f'{dir_path}/{parsed.name}'
                else:
                    full_name = parsed.name
                content = self._read_prompt_file(self._directory / file)
                version = calculate_version(content)

                prompts.append(
                    PromptRef(
                        name=full_name,
                        variant=parsed.variant,
                        version=version,
                    )
                )
            except Exception as e:
                logger.info(
                    'Skipping file with invalid name format',
                    file=file,
                    error=str(e),
                )

        return ListPromptResults(prompts=prompts, cursor=None)

    def list_partials(
        self, options: PaginationOptions | None = None
    ) -> ListPartialResults:
        """List all partial prompts in the store.

        Args:
            options: Optional pagination parameters.

        Returns:
            ListPartialResults with 'partials' list and 'cursor' (always None).
        """
        partials = []

        partial_files = scan_directory_sync(self._directory)

        for file in partial_files:
            if not is_partial(os.path.basename(file)):
                continue

            try:
                filename = os.path.basename(file)
                # Strip the leading '_' from the filename.
                parsed = parse_prompt_filename(filename[1:])
                dir_path = os.path.dirname(file)
                if dir_path:
                    full_name = f'{dir_path}/{parsed.name}'
                else:
                    full_name = parsed.name
                content = self._read_prompt_file(self._directory / file)
                version = calculate_version(content)

                partials.append(
                    PartialRef(
                        name=full_name,
                        variant=parsed.variant,
                        version=version,
                    )
                )
            except Exception as e:
                logger.info(
                    'Skipping file with invalid name format',
                    file=file,
                    error=str(e),
                )

        return ListPartialResults(partials=partials, cursor=None)

    def load(self, name: str, options: LoadOptions | None = None) -> PromptData:
        """Load a specific prompt.

        Args:
            name: The logical name of the prompt.
            options: Optional parameters like variant and version.

        Returns:
            The prompt data including content and metadata.

        Raises:
            FileNotFoundError: If the prompt file is not found.
            ValueError: If requested version doesn't match actual version.
        """
        options_obj = options or LoadOptions()
        variant = options_obj.variant
        version_check = options_obj.version

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

        try:
            source = self._read_prompt_file(file_path)
            version = calculate_version(source)

            if version_check and version_check != version:
                variant_info = f' (variant: {variant})' if variant else ''
                raise ValueError(
                    f"Version mismatch for prompt '{name}'{variant_info}: "
                    f'requested {version_check} but found {version}'
                )

            return PromptData(
                name=name,
                variant=variant,
                version=version,
                source=source,
            )

        except FileNotFoundError:
            variant_info = f' (variant: {variant})' if variant else ''
            version_info = (
                f' (version: {version_check})' if version_check else ''
            )
            msg = (
                f"Prompt '{name}'{variant_info}{version_info} "
                f'not found at path: {file_path}'
            )
            raise FileNotFoundError(msg) from None
        except Exception as e:
            if not isinstance(e, ValueError):  # Don't re-wrap version errors
                variant_info = f' (variant: {variant})' if variant else ''
                version_info = (
                    f' (version: {version_check})' if version_check else ''
                )
                error_str = str(e)
                msg = (
                    f"Failed to load prompt '{name}'{variant_info}"
                    f'{version_info}: {error_str}'
                )
                raise RuntimeError(msg) from e
            raise

    def load_partial(
        self, name: str, options: LoadOptions | None = None
    ) -> PartialData:
        """Load a specific partial.

        Args:
            name: The logical name of the partial (without underscore).
            options: Optional parameters like variant and version.

        Returns:
            The partial data including content and metadata.

        Raises:
            FileNotFoundError: If the partial file is not found.
            ValueError: If requested version doesn't match actual version.
        """
        options_obj = options or LoadOptions()
        variant = options_obj.variant
        version_check = options_obj.version

        dir_name = os.path.dirname(name)
        base_name = os.path.basename(name)

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

        try:
            source = self._read_prompt_file(file_path)
            version = calculate_version(source)

            if version_check and version_check != version:
                variant_info = f' (variant: {variant})' if variant else ''
                raise ValueError(
                    f"Version mismatch for partial '{name}'{variant_info}: "
                    f'requested {version_check} but found {version}'
                )

            return PartialData(
                name=name,
                variant=variant,
                version=version,
                source=source,
            )

        except FileNotFoundError:
            variant_info = f' (variant: {variant})' if variant else ''
            version_info = (
                f' (version: {version_check})' if version_check else ''
            )
            msg = f"Partial '{name}'{variant_info}{version_info} not found"
            raise FileNotFoundError(msg) from None
        except Exception as e:
            if not isinstance(e, ValueError):  # Don't re-wrap version errors
                variant_info = f' (variant: {variant})' if variant else ''
                version_info = (
                    f' (version: {version_check})' if version_check else ''
                )
                error_str = str(e)
                msg = (
                    f"Failed to load partial '{name}'{variant_info}"
                    f'{version_info}: {error_str}'
                )
                raise RuntimeError(msg) from e
            raise

    def save(self, prompt: PromptData) -> PromptSaveResult:
        """Save a prompt to the filesystem.

        Args:
            prompt: The prompt data to save.

        Returns:
            Result object with success indicator and optional message.

        Raises:
            ValueError: If prompt name or source is missing.
            RuntimeError: If there's an error creating directories or writing
                file.
        """
        if not prompt.name:
            raise ValueError('Prompt name is required for saving.')

        if prompt.source is None:
            raise ValueError('Prompt source is required for saving.')

        # Check if this is a partial being saved through the main save method
        is_partial = getattr(prompt, 'is_partial', False)
        if is_partial:
            return self.save_partial(prompt)

        dir_name = os.path.dirname(prompt.name)
        base_name = os.path.basename(prompt.name)

        file_name = (
            f'{base_name}.{prompt.variant}.prompt'
            if prompt.variant
            else f'{base_name}.prompt'
        )

        try:
            if dir_name:
                dir_path = self._directory / dir_name
                os.makedirs(dir_path, exist_ok=True)
                file_path = dir_path / file_name
            else:
                file_path = self._directory / file_name

            # Create the prompt file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(prompt.source)

            version = calculate_version(prompt.source)
            return PromptSaveResult(
                success=True,
                name=prompt.name,
                variant=prompt.variant,
                version=version,
                message=f'Saved prompt with version {version}',
            )

        except Exception as e:
            error_str = str(e)
            variant_info = (
                f' (variant: {prompt.variant})' if prompt.variant else ''
            )
            msg = (
                f"Failed to save prompt '{prompt.name}'{variant_info}: "
                f'{error_str}'
            )
            logger.error(msg, exc_info=True)
            return PromptSaveResult(
                success=False,
                name=prompt.name,
                variant=prompt.variant,
                message=msg,
            )

    def save_partial(self, partial: PromptData) -> PromptSaveResult:
        """Save a partial prompt to the filesystem.

        Args:
            partial: The partial prompt data to save.

        Returns:
            Result object with success indicator and optional message.

        Raises:
            ValueError: If partial name or source is missing.
            RuntimeError: If there's an error creating directories or writing
                file.
        """
        if not partial.name:
            raise ValueError('Partial name is required for saving.')

        if partial.source is None:
            raise ValueError('Partial source is required for saving.')

        dir_name = os.path.dirname(partial.name)
        base_name = os.path.basename(partial.name)

        file_name = (
            f'_{base_name}.{partial.variant}.prompt'
            if partial.variant
            else f'_{base_name}.prompt'
        )

        try:
            if dir_name:
                dir_path = self._directory / dir_name
                os.makedirs(dir_path, exist_ok=True)
                file_path = dir_path / file_name
            else:
                file_path = self._directory / file_name

            # Create the partial file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(partial.source)

            version = calculate_version(partial.source)
            return PromptSaveResult(
                success=True,
                name=partial.name,
                variant=partial.variant,
                version=version,
                message=f'Saved partial with version {version}',
            )

        except Exception as e:
            error_str = str(e)
            variant_info = (
                f' (variant: {partial.variant})' if partial.variant else ''
            )
            msg = (
                f"Failed to save partial '{partial.name}'{variant_info}: "
                f'{error_str}'
            )
            logger.error(msg, exc_info=True)
            return PromptSaveResult(
                success=False,
                name=partial.name,
                variant=partial.variant,
                message=msg,
            )

    def delete(
        self, name: str, options: DeleteOptions | None = None
    ) -> PromptDeleteResult:
        """Delete a specific prompt.

        Args:
            name: The name of the prompt to delete.
            options: Optional parameters like variant.

        Returns:
            Result object with success indicator and optional message.
        """
        # Check if this might be a partial. If the name starts with '_',
        # or if there's a specific flag in options, use delete_partial
        if name.startswith('draft_'):
            return self.delete_partial(name, options)

        options_obj = options or DeleteOptions()
        variant = options_obj.variant

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

        try:
            if not os.path.exists(file_path):
                msg = f"Prompt '{name}' not found at path: {file_path}"
                raise FileNotFoundError(msg)

            os.remove(file_path)
            return PromptDeleteResult(
                success=True,
                name=name,
                variant=variant,
                message=f"Deleted prompt '{name}'",
            )

        except FileNotFoundError as e:
            # Re-raise the error to match the expected behavior in tests
            raise e
        except Exception as e:
            error_str = str(e)
            variant_info = f' (variant: {variant})' if variant else ''
            msg = f"Failed to delete prompt '{name}'{variant_info}: {error_str}"
            logger.error(msg, exc_info=True)
            return PromptDeleteResult(
                success=False, name=name, variant=variant, message=msg
            )

    def delete_partial(
        self, name: str, options: DeleteOptions | None = None
    ) -> PromptDeleteResult:
        """Delete a specific partial prompt.

        Args:
            name: The name of the partial to delete (without underscore).
            options: Optional parameters like variant.

        Returns:
            Result object with success indicator and optional message.
        """
        options_obj = options or DeleteOptions()
        variant = options_obj.variant

        dir_name = os.path.dirname(name)
        base_name = os.path.basename(name)

        # Construct filename with underscore prefix for partial
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

        try:
            if not os.path.exists(file_path):
                msg = f"Partial '{name}' not found"
                raise FileNotFoundError(msg)

            os.remove(file_path)
            return PromptDeleteResult(
                success=True,
                name=name,
                variant=variant,
                message=f"Partial '{name}' deleted successfully.",
            )
        except Exception as e:
            error_str = str(e)
            variant_info = f' ({variant})' if variant else ''
            msg = (
                f"Failed to delete partial '{name}'{variant_info}: {error_str}"
            )
            logger.error(msg, exc_info=True)
            return PromptDeleteResult(
                success=False, name=name, variant=variant, message=msg
            )
