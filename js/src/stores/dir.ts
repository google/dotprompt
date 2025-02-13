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
 */

import { promises as fs } from 'fs';
import path from 'path';
import { createHash } from 'crypto';
import {
  PromptData,
  PromptRef,
  PromptStoreWritable,
  PartialRef,
} from '../types';

interface DirStoreOptions {
  /** Base directory to read prompts from */
  directory: string;
}

export class DirStore implements PromptStoreWritable {
  private directory: string;

  constructor(options: DirStoreOptions) {
    this.directory = options.directory;
  }

  private async readPromptFile(filePath: string): Promise<string> {
    return fs.readFile(filePath, 'utf-8');
  }

  private calculateVersion(content: string): string {
    return createHash('sha1').update(content).digest('hex').substring(0, 8);
  }

  private parsePromptFilename(filename: string): {
    name: string;
    variant?: string;
  } {
    const match = filename.match(/^([^.]+)(?:\.([^.]+))?\.prompt$/);
    if (!match) throw new Error(`Invalid prompt filename: ${filename}`);

    const [, name, variant] = match;
    return { name, variant };
  }

  private isPartial(filename: string): boolean {
    return filename.startsWith('_');
  }

  private async scanDirectory(
    dir: string = '',
    results: string[] = []
  ): Promise<string[]> {
    const fullPath = path.join(this.directory, dir);
    const entries = await fs.readdir(fullPath, { withFileTypes: true });

    for (const entry of entries) {
      const relativePath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        await this.scanDirectory(relativePath, results);
      } else if (entry.isFile() && entry.name.endsWith('.prompt')) {
        results.push(relativePath);
      }
    }

    return results;
  }

  async list(options?: {
    cursor?: string;
    limit?: number;
  }): Promise<{ prompts: PromptRef[]; cursor?: string }> {
    const files = await this.scanDirectory();
    const prompts: PromptRef[] = [];

    for (const file of files) {
      if (!this.isPartial(path.basename(file))) {
        const { name, variant } = this.parsePromptFilename(path.basename(file));
        const dirPath = path.dirname(file);
        const fullName =
          dirPath !== '.' ? `${dirPath.replace(/\\/g, '/')}/${name}` : name;
        const content = await this.readPromptFile(
          path.join(this.directory, file)
        );
        const version = this.calculateVersion(content);

        prompts.push({
          name: fullName,
          variant,
          version,
        });
      }
    }

    return { prompts };
  }

  async listPartials(options?: {
    cursor?: string;
    limit?: number;
  }): Promise<{ partials: PartialRef[]; cursor?: string }> {
    const files = await this.scanDirectory();
    const partials: PartialRef[] = [];

    for (const file of files) {
      if (this.isPartial(path.basename(file))) {
        const { name, variant } = this.parsePromptFilename(
          path.basename(file).slice(1)
        );
        const dirPath = path.dirname(file);
        const fullName =
          dirPath !== '.' ? `${dirPath.replace(/\\/g, '/')}/${name}` : name;
        const content = await this.readPromptFile(
          path.join(this.directory, file)
        );
        const version = this.calculateVersion(content);

        partials.push({
          name: fullName,
          variant,
          version,
        });
      }
    }

    return { partials };
  }

  async load(
    name: string,
    options?: { variant?: string; version?: string }
  ): Promise<PromptData> {
    const variant = options?.variant;
    const dirName = path.dirname(name);
    const baseName = path.basename(name);
    const fileName = variant
      ? `${baseName}.${variant}.prompt`
      : `${baseName}.prompt`;
    const filePath = path.join(this.directory, dirName, fileName);

    try {
      const source = await this.readPromptFile(filePath);
      const version = this.calculateVersion(source);

      // If a specific version was requested, verify it matches
      if (options?.version && options.version !== version) {
        throw new Error(
          `Version mismatch for prompt '${name}': requested ${options.version} but found ${version}`
        );
      }

      return {
        name,
        variant,
        version,
        source,
      };
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to load prompt ${name}: ${message}`);
    }
  }

  async loadPartial(
    name: string,
    options?: { variant?: string; version?: string }
  ): Promise<PromptData> {
    const variant = options?.variant;
    const dirName = path.dirname(name);
    const baseName = path.basename(name);
    const fileName = variant
      ? `_${baseName}.${variant}.prompt`
      : `_${baseName}.prompt`;
    const filePath = path.join(this.directory, dirName, fileName);

    try {
      const source = await this.readPromptFile(filePath);
      const version = this.calculateVersion(source);

      // If a specific version was requested, verify it matches
      if (options?.version && options.version !== version) {
        throw new Error(
          `Version mismatch: requested ${options.version} but found ${version}`
        );
      }

      return {
        name,
        variant,
        version,
        source,
      };
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to load partial ${name}: ${message}`);
    }
  }

  async save(prompt: PromptData): Promise<void> {
    if (!prompt.name) throw new Error('Prompt name is required');

    const dirName = path.dirname(prompt.name);
    const baseName = path.basename(prompt.name);
    const fileName = prompt.variant
      ? `${baseName}.${prompt.variant}.prompt`
      : `${baseName}.prompt`;
    const filePath = path.join(this.directory, dirName, fileName);

    try {
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, prompt.source, 'utf-8');
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to save prompt ${prompt.name}: ${message}`);
    }
  }

  async delete(name: string, options?: { variant?: string }): Promise<void> {
    const variant = options?.variant;
    const dirName = path.dirname(name);
    const baseName = path.basename(name);
    const fileName = variant
      ? `${baseName}.${variant}.prompt`
      : `${baseName}.prompt`;
    const filePath = path.join(this.directory, dirName, fileName);

    try {
      await fs.unlink(filePath);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to delete prompt ${name}: ${message}`);
    }
  }
}
