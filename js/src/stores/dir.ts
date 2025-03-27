/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import type {
  DeletePromptOrPartialOptions,
  ListPartialsOptions,
  ListPromptsOptions,
  LoadPartialOptions,
  LoadPromptOptions,
  PaginatedPartials,
  PaginatedPrompts,
  PartialRef,
  PromptData,
  PromptRef,
  PromptStoreWritable,
} from '../types';

/**
 * Options for configuring the DirStore.
 */
export interface DirStoreOptions {
  /**
   * Base directory to read prompts from and write prompts to. This directory
   * will serve as the root for all prompt file operations.
   */
  directory: string;
}

/**
 * A prompt store implementation that reads and writes prompts and partials
 * directly from/to the local file system within a specified directory.
 *
 * Prompts are expected to be files with a `.prompt` extension.
 * File naming convention: `[name](.[variant]).prompt`
 * Partials follow the same convention but are prefixed with an underscore:
 * `_[name](.[variant]).prompt`
 *
 * Directories can be used to organize prompts, forming part of the prompt name
 * (e.g., a prompt "bar" in directory "foo" will have the name "foo/bar").
 * Versions are calculated based on the SHA1 hash of the file content.
 *
 * This class provides methods to list, load, save, and delete prompts and
 * partials according to the `PromptStoreWritable` interface.
 */
export class DirStore implements PromptStoreWritable {
  private directory: string;

  /**
   * Creates an instance of DirStore and initializes the store with the base
   * directory where prompt files will be managed.
   *
   * @param options Configuration options for the store.
   */
  constructor(options: DirStoreOptions) {
    this.directory = options.directory;
  }

  /**
   * Reads the content of a specified prompt file asynchronously. Assumes UTF-8
   * encoding for the file content.
   *
   * @param filePath The full, absolute or relative, path to the prompt file.
   *
   * @return A promise that resolves with the file content as a string.
   * @private
   */
  private async readPromptFile(filePath: string): Promise<string> {
    return fs.readFile(filePath, 'utf-8');
  }

  /**
   * Calculates a deterministic version identifier for the given content string.
   * This uses the first 8 characters of the SHA1 hash of the content.
   *
   * @param content The string content to hash for versioning.
   *
   * @return A short SHA1 hash (8 hexadecimal characters) representing the
   * content version.
   * @private
   */
  private calculateVersion(content: string): string {
    return createHash('sha1').update(content).digest('hex').substring(0, 8);
  }

  /**
   * Parses a prompt filename (excluding any leading underscore for partials)
   * to extract its base name and optional variant identifier. Expects the
   * filename to end with the `.prompt` extension.
   *
   * @param filename The filename part (e.g., "myPrompt.variant.prompt" or
   * "myPrompt.prompt").
   *
   * @return An object containing the base `name` and optional `variant` string.
   *
   * @throws If the filename does not match the expected format
   * `name[.variant].prompt`.
   * @private
   */
  private parsePromptFilename(filename: string): {
    name: string;
    variant?: string;
  } {
    // Regex breakdown:
    // ^([^.]+)     Capture group 1: One or more chars not a dot (base name)
    // (?:\.([^.]+))? Optional non-capturing group for variant:
    //   \.         Literal dot separator
    //   ([^.]+)    Capture group 2: One or more chars not a dot (variant)
    // \.prompt$    Literal ".prompt" at the end
    const match = filename.match(/^([^.]+)(?:\.([^.]+))?\.prompt$/);
    if (!match) {
      throw new Error(`Invalid prompt filename format: ${filename}`);
    }

    const [, name, variant] = match;
    return { name, variant };
  }

  /**
   * Determines if a given filename represents a partial prompt based on the
   * convention that partial filenames start with an underscore (`_`).
   *
   * @param filename The filename to check.
   *
   * @return `true` if the filename starts with '_', `false` otherwise.
   * @private
   */
  private isPartial(filename: string): boolean {
    return filename.startsWith('_');
  }

  /**
   * Recursively scans a directory (relative to the store's base directory)
   * for files ending with the `.prompt` extension. Builds an array of
   * relative paths for all matching files found.
   *
   * @param dir The subdirectory relative to the base directory to start
   * scanning from. Defaults to the base directory itself ('').
   * @param results An array used internally to accumulate the relative paths
   * of found prompt files during recursion. Defaults to an empty array.
   *
   * @return A promise that resolves with an array containing the relative paths
   * (including subdirectories) of all found `.prompt` files.
   * @private
   */
  private async scanDirectory(
    dir = '',
    results: string[] = []
  ): Promise<string[]> {
    const fullPath = path.join(this.directory, dir);
    const entries = await fs.readdir(fullPath, { withFileTypes: true });

    for (const entry of entries) {
      const relativePath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        // Recurse into subdirectories.
        await this.scanDirectory(relativePath, results);
      } else if (entry.isFile() && entry.name.endsWith('.prompt')) {
        // Add matching files to results.
        results.push(relativePath);
      }
    }

    return results;
  }

  /**
   * Lists available prompts (excluding partials) found within the store's
   * configured directory and its subdirectories. It calculates the version
   * for each prompt based on its content.
   *
   * Note: Pagination options (`cursor`, `limit`) are accepted for interface
   * compatibility but are not currently implemented. This method returns all
   * matching prompts found in a single operation.
   *
   * @param options Listing options (currently unused for pagination).
   * @return A promise resolving to an object containing the list of prompt
   * references (`PromptRef[]`) and no cursor (`undefined`).
   */
  async list(options?: ListPromptsOptions): Promise<PaginatedPrompts> {
    const files = await this.scanDirectory();
    const prompts: PromptRef[] = [];

    for (const file of files) {
      const baseName = path.basename(file);
      // Skip partials (files starting with _).
      if (!this.isPartial(baseName)) {
        try {
          const { name: parsedName, variant } =
            this.parsePromptFilename(baseName);
          const dirPath = path.dirname(file);
          // Construct full name including relative directory path, using /.
          const fullName =
            dirPath !== '.'
              ? `${dirPath.replace(/\\/g, '/')}/${parsedName}`
              : parsedName;
          const content = await this.readPromptFile(
            path.join(this.directory, file)
          );
          const version = this.calculateVersion(content);

          prompts.push({
            name: fullName,
            variant,
            version,
          });
        } catch (error) {
          // Log or handle files with invalid names, skipping them.
          console.warn(
            `Skipping file with invalid name format: ${file}`,
            error
          );
        }
      }
    }
    // DirStore doesn't support pagination, so cursor is always undefined.
    return { prompts };
  }

  /**
   * Lists available partials found within the store's configured directory and
   * its subdirectories. Partials are identified by filenames starting with `_`.
   * It calculates the version for each partial based on its content.
   *
   * Note: Pagination options (`cursor`, `limit`) are accepted for interface
   * compatibility but are not currently implemented. This method returns all
   * matching partials found in a single operation.
   *
   * @param options Listing options (currently unused for pagination).
   * @return A promise resolving to an object containing the list of partial
   * references (`PartialRef[]`) and no cursor (`undefined`).
   */
  async listPartials(
    options?: ListPartialsOptions
  ): Promise<PaginatedPartials> {
    const files = await this.scanDirectory();
    const partials: PartialRef[] = [];

    for (const file of files) {
      const baseName = path.basename(file);
      // Only include partials (files starting with _).
      if (this.isPartial(baseName)) {
        try {
          // Remove the leading underscore before parsing filename structure.
          const actualFilename = baseName.slice(1);
          const { name: parsedName, variant } =
            this.parsePromptFilename(actualFilename);
          const dirPath = path.dirname(file);
          // Construct full name including relative directory path, using /.
          const fullName =
            dirPath !== '.'
              ? `${dirPath.replace(/\\/g, '/')}/${parsedName}`
              : parsedName;
          const content = await this.readPromptFile(
            path.join(this.directory, file)
          );
          const version = this.calculateVersion(content);

          partials.push({
            name: fullName,
            variant,
            version,
          });
        } catch (error) {
          // Log or handle files with invalid names, skipping them.
          console.warn(
            `Skipping partial file with invalid name format: ${file}`,
            error
          );
        }
      }
    }
    // DirStore doesn't support pagination, so cursor is always undefined
    return { partials };
  }

  /**
   * Loads a specific prompt from the store by reading its corresponding file.
   * The prompt `name` can include subdirectory paths relative to the base
   * directory (e.g., "group1/myPrompt"). Handles default prompts and variants.
   * Optionally verifies the content version against a provided hash.
   *
   * @param name The full logical name of the prompt, including any relative
   * path from the base directory.
   * @param options Loading options.
   * @return A promise resolving to the loaded prompt data (`PromptData`),
   * including its source content and calculated version hash.
   *
   * @throws If the prompt file is not found (`ENOENT`), cannot be read, or if a
   * requested `version` does not match the actual calculated version.
   */
  async load(name: string, options?: LoadPromptOptions): Promise<PromptData> {
    const variant = options?.variant;
    const dirName = path.dirname(name); // Relative dir path or ".".
    const baseName = path.basename(name); // The logical name part.

    // Construct the expected filename: baseName[.variant].prompt.
    const fileName = variant
      ? `${baseName}.${variant}.prompt`
      : `${baseName}.prompt`;
    // Construct the full path relative to the store's base directory.
    const filePath = path.join(this.directory, dirName, fileName);

    try {
      const source = await this.readPromptFile(filePath);
      const version = this.calculateVersion(source);

      // If a specific version was requested, verify it matches calculated one.
      if (options?.version && options.version !== version) {
        throw new Error(
          `Version mismatch for prompt '${name}'` +
            `${variant ? ` (variant: ${variant})` : ''}` +
            `: requested ${options.version} but found ${version}`
        );
      }

      return {
        name, // Return the original logical name requested.
        variant,
        version,
        source,
      };
    } catch (error: unknown) {
      // Create more informative error messages.
      const variantInfo = variant ? ` (variant: ${variant})` : '';
      const versionInfo = options?.version
        ? ` (version: ${options.version})`
        : '';
      const message = error instanceof Error ? error.message : String(error);
      // Specifically check for file not found errors.
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new Error(
          `Prompt '${name}'${variantInfo}${versionInfo} ` +
            `not found at path: ${filePath}`
        );
      }
      // General loading failure.
      throw new Error(
        `Failed to load prompt '${name}'${variantInfo}${versionInfo}: ` +
          `${message}`
      );
    }
  }

  /**
   * Loads a specific partial from the store by reading its corresponding file.
   * Partials are identified by filenames starting with an underscore (`_`).
   * The partial `name` should be the logical name (without the underscore) and
   * can include subdirectory paths. Handles default and variant partials.
   * Optionally verifies the content version against a provided hash.
   *
   * @param name The full logical name of the partial (e.g., "common/header").
   * Do not include the leading underscore in this parameter.
   * @param options Loading options.
   * @return A promise resolving to the loaded partial data (as `PromptData`),
   * including its source content and calculated version hash.
   * @throws If the partial file is not found (`ENOENT`), cannot be read, or if
   * a requested `version` doesn't match the actual version.
   */
  async loadPartial(
    name: string,
    options?: LoadPartialOptions
  ): Promise<PromptData> {
    const variant = options?.variant;
    const dirName = path.dirname(name); // Relative dir path or ".".
    const baseName = path.basename(name); // Logical name part.

    // Construct the expected filename: _baseName[.variant].prompt.
    const fileName = variant
      ? `_${baseName}.${variant}.prompt`
      : `_${baseName}.prompt`;
    // Construct the full path relative to the store's base directory.
    const filePath = path.join(this.directory, dirName, fileName);

    try {
      const source = await this.readPromptFile(filePath);
      const version = this.calculateVersion(source);

      // If a specific version was requested, verify it matches.
      if (options?.version && options.version !== version) {
        throw new Error(
          `Version mismatch for partial '${name}'` +
            `${variant ? ` (variant: ${variant})` : ''}` +
            `: requested ${options.version} but found ${version}`
        );
      }

      return {
        name, // Return the original logical name requested.
        variant,
        version,
        source,
      };
    } catch (error: unknown) {
      // Create more informative error messages.
      const variantInfo = variant ? ` (variant: ${variant})` : '';
      const versionInfo = options?.version
        ? ` (version: ${options.version})`
        : '';
      const message = error instanceof Error ? error.message : String(error);
      // Specifically check for file not found errors.
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new Error(
          `Partial '${name}'${variantInfo}${versionInfo} ` +
            `not found at path: ${filePath}`
        );
      }
      // General loading failure.
      throw new Error(
        `Failed to load partial '${name}'${variantInfo}${versionInfo}: ` +
          `${message}`
      );
    }
  }

  /**
   * Saves a prompt to the store by writing its `source` content to a file.  The
   * filename is determined by the `name` and optional `variant` properties of
   * the `prompt` object. It creates necessary subdirectories within the base
   * directory if they don't exist. Overwrites existing files with the same
   * calculated path.
   *
   * Note: To save a partial, the `name` property in the `PromptData` should
   * conventionally start with an underscore (e.g., `_myPartial`), although
   * `loadPartial` expects the name *without* the underscore. Ensure consistent
   * naming. The `version` property in the input `PromptData` is ignored.
   *
   * @param prompt The prompt data to save. Must include at least `name` and
   * `source`. The `variant` property is optional.
   *
   * @return A promise that resolves when the file has been successfully written.
   *
   * @throws If `prompt.name` or `prompt.source` is missing, or if there's an
   * error creating directories or writing the file to the file system.
   */
  async save(prompt: PromptData): Promise<void> {
    if (!prompt.name) {
      throw new Error('Prompt name is required for saving.');
    }
    if (prompt.source === undefined || prompt.source === null) {
      throw new Error('Prompt source content is required for saving.');
    }

    const dirName = path.dirname(prompt.name); // Relative dir path or ".".
    // Name part, potentially with "_".
    const baseName = path.basename(prompt.name);

    // Construct the filename based on basename and variant.
    const fileName = prompt.variant
      ? `${baseName}.${prompt.variant}.prompt`
      : `${baseName}.prompt`;
    const filePath = path.join(this.directory, dirName, fileName);
    const fileDir = path.dirname(filePath); // Full path to directory needed.

    try {
      // Ensure the target directory exists, creating it if necessary.
      await fs.mkdir(fileDir, { recursive: true });
      // Write the prompt source content to the file (UTF-8 assumed).
      await fs.writeFile(filePath, prompt.source, 'utf-8');
    } catch (error: unknown) {
      // Create more informative error messages.
      const variantInfo = prompt.variant ? ` (variant: ${prompt.variant})` : '';
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(
        `Failed to save prompt '${prompt.name}'${variantInfo} ` +
          `to ${filePath}: ${message}`
      );
    }
  }

  /**
   * Deletes a specific prompt or partial file from the store's directory.  It
   * first tries to find and delete the prompt file corresponding to the `name`
   * and `variant`. If not found, it tries to find and delete the corresponding
   * partial file (prefixed with `_`).
   *
   * @param name The full logical name of the prompt or partial (e.g.,
   * "subDir/myPrompt" or "subDir/myPartial"). For partials, use the name
   * *without* the leading underscore.
   * @param options Deletion options.
   * @return A promise that resolves when the deletion is complete.
   * @throws If neither the corresponding prompt nor partial file can be found
   * (`ENOENT`), or if there's another file system error during deletion.
   */
  async delete(
    name: string,
    options?: DeletePromptOrPartialOptions
  ): Promise<void> {
    const variant = options?.variant;
    const dirName = path.dirname(name);
    const baseName = path.basename(name);

    // Determine potential filename for a regular prompt.
    const promptFileName = variant
      ? `${baseName}.${variant}.prompt`
      : `${baseName}.prompt`;
    const promptFilePath = path.join(this.directory, dirName, promptFileName);

    // Determine potential filename for a partial.
    const partialFileName = variant
      ? `_${baseName}.${variant}.prompt`
      : `_${baseName}.prompt`;
    const partialFilePath = path.join(this.directory, dirName, partialFileName);

    let filePathToDelete: string | null = null;
    let fileType = 'item'; // Generic term for error messages.

    // Try to access (check existence of) the prompt file first.
    try {
      await fs.access(promptFilePath);
      filePathToDelete = promptFilePath;
      fileType = 'prompt';
    } catch {
      // If prompt file doesn't exist, try to access the partial file.
      try {
        await fs.access(partialFilePath);
        filePathToDelete = partialFilePath;
        fileType = 'partial';
      } catch (accessError) {
        // If neither the prompt nor the partial file exists, throw an error.
        const variantInfo = variant ? ` (variant: ${variant})` : '';
        // Error indicating neither expected file was found.
        throw new Error(
          `Failed to delete ${fileType} '${name}'${variantInfo}: ` +
            `File not found at expected paths ${promptFilePath} ` +
            `or ${partialFilePath}`
        );
      }
    }

    // If a file path was determined (either prompt or partial), attempt
    // deletion.
    if (filePathToDelete) {
      try {
        await fs.unlink(filePathToDelete);
      } catch (error: unknown) {
        // Handle errors during the actual deletion process.
        const variantInfo = variant ? ` (variant: ${variant})` : '';
        const message = error instanceof Error ? error.message : String(error);
        throw new Error(
          `Failed to delete ${fileType} '${name}'${variantInfo} ` +
            `at ${filePathToDelete}: ${message}`
        );
      }
    }
    // Defensive: This part should theoretically not be reached if logic above
    // is sound but added for robustness. If filePathToDelete is still null,
    // something is wrong.
    if (!filePathToDelete) {
      const variantInfo = variant ? ` (variant: ${variant})` : '';
      throw new Error(
        `Internal error: Could not determine file path to delete for '${name}'${variantInfo}.`
      );
    }
  }
}
