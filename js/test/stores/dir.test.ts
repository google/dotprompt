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
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { DirStore } from '../../src/stores/dir';
import type { PromptData } from '../../src/types';

describe('DirStore', () => {
  const tempDir = path.join(process.cwd(), 'test-prompts');
  let store: DirStore;

  beforeEach(async () => {
    await fs.mkdir(tempDir, { recursive: true });
    store = new DirStore({ directory: tempDir });
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  function calculateVersion(content: string): string {
    return createHash('sha1').update(content).digest('hex').substring(0, 8);
  }

  async function createPromptFile(name: string, content = 'test source') {
    const filePath = path.join(tempDir, name);
    await fs.mkdir(path.dirname(filePath), { recursive: true });
    await fs.writeFile(filePath, content);
  }

  describe('list', () => {
    it('should list prompts in root directory with versions', async () => {
      const content1 = 'test source 1';
      const content2 = 'test source 2';
      await createPromptFile('test.prompt', content1);
      await createPromptFile('other.prompt', content2);

      const result = await store.list();
      expect(result.prompts).toHaveLength(2);
      const prompts = result.prompts.sort((a, b) =>
        a.name.localeCompare(b.name)
      );

      expect(prompts[0].name).toBe('other');
      expect(prompts[0].version).toBe(calculateVersion(content2));
      expect(prompts[1].name).toBe('test');
      expect(prompts[1].version).toBe(calculateVersion(content1));
    });

    it('should handle prompts with variants', async () => {
      const content = 'test variant source';
      await createPromptFile('test.v1.prompt', content);

      const result = await store.list();
      expect(result.prompts).toHaveLength(1);
      expect(result.prompts[0].name).toBe('test');
      expect(result.prompts[0].variant).toBe('v1');
      expect(result.prompts[0].version).toBe(calculateVersion(content));
    });

    it('should handle prompts in subdirectories', async () => {
      const content = 'test subdir source';
      await createPromptFile('subdir/test.prompt', content);

      const result = await store.list();
      expect(result.prompts).toHaveLength(1);
      expect(result.prompts[0].name).toBe('subdir/test');
      expect(result.prompts[0].version).toBe(calculateVersion(content));
    });
  });

  describe('listPartials', () => {
    it('should list partial prompts with versions', async () => {
      const content1 = 'partial source 1';
      const content2 = 'partial source 2';
      await createPromptFile('_partial.prompt', content1);
      await createPromptFile('_other.prompt', content2);

      const result = await store.listPartials();
      expect(result.partials).toHaveLength(2);
      const partials = result.partials.sort((a, b) =>
        a.name.localeCompare(b.name)
      );

      expect(partials[0].name).toBe('other');
      expect(partials[0].version).toBe(calculateVersion(content2));
      expect(partials[1].name).toBe('partial');
      expect(partials[1].version).toBe(calculateVersion(content1));
    });

    it('should handle partial prompts with variants', async () => {
      const content = 'test partial variant source';
      await createPromptFile('_test.v1.prompt', content);

      const result = await store.listPartials();
      expect(result.partials).toHaveLength(1);
      expect(result.partials[0].name).toBe('test');
      expect(result.partials[0].variant).toBe('v1');
      expect(result.partials[0].version).toBe(calculateVersion(content));
    });
  });

  describe('load', () => {
    it('should load a prompt with version', async () => {
      const source = 'test source content';
      await createPromptFile('test.prompt', source);

      const result = await store.load('test');
      expect(result.name).toBe('test');
      expect(result.source).toBe(source);
      expect(result.version).toBe(calculateVersion(source));
    });

    it('should load a specific version of a prompt', async () => {
      const source = 'test source content';
      await createPromptFile('test.prompt', source);
      const version = calculateVersion(source);

      const result = await store.load('test', { version });
      expect(result.version).toBe(version);
    });

    it('should throw error when requested version does not match', async () => {
      const source = 'test source content';
      await createPromptFile('test.prompt', source);

      await expect(
        store.load('test', { version: 'wrongversion' })
      ).rejects.toThrow(/Version mismatch/);
    });
  });

  describe('loadPartial', () => {
    it('should load a partial prompt with version', async () => {
      const source = 'partial source content';
      await createPromptFile('_test.prompt', source);

      const result = await store.loadPartial('test');
      expect(result.name).toBe('test');
      expect(result.source).toBe(source);
      expect(result.version).toBe(calculateVersion(source));
    });

    it('should load a specific version of a partial', async () => {
      const source = 'partial source content';
      await createPromptFile('_test.prompt', source);
      const version = calculateVersion(source);

      const result = await store.loadPartial('test', { version });
      expect(result.version).toBe(version);
    });

    it('should throw error when requested partial version does not match', async () => {
      const source = 'partial source content';
      await createPromptFile('_test.prompt', source);

      await expect(
        store.loadPartial('test', { version: 'wrongversion' })
      ).rejects.toThrow(/Version mismatch/);
    });
  });

  describe('save', () => {
    it('should save a prompt and generate correct version', async () => {
      const source = 'new source content';
      const prompt: PromptData = {
        name: 'test',
        source,
        version: calculateVersion(source),
      };

      await store.save(prompt);
      const saved = await fs.readFile(
        path.join(tempDir, 'test.prompt'),
        'utf-8'
      );
      expect(saved).toBe(source);

      // Verify version is correct after loading
      const loaded = await store.load('test');
      expect(loaded.version).toBe(prompt.version);
    });

    it('should save a prompt with variant and generate correct version', async () => {
      const source = 'new variant source content';
      const prompt: PromptData = {
        name: 'test',
        variant: 'v1',
        source,
        version: calculateVersion(source),
      };

      await store.save(prompt);
      const saved = await fs.readFile(
        path.join(tempDir, 'test.v1.prompt'),
        'utf-8'
      );
      expect(saved).toBe(source);

      // Verify version is correct after loading
      const loaded = await store.load('test', { variant: 'v1' });
      expect(loaded.version).toBe(prompt.version);
    });

    it('should save a prompt in subdirectory and generate correct version', async () => {
      const source = 'new subdirectory source content';
      const prompt: PromptData = {
        name: 'subdir/test',
        source,
        version: calculateVersion(source),
      };

      await store.save(prompt);
      const saved = await fs.readFile(
        path.join(tempDir, 'subdir/test.prompt'),
        'utf-8'
      );
      expect(saved).toBe(source);

      // Verify version is correct after loading
      const loaded = await store.load('subdir/test');
      expect(loaded.version).toBe(prompt.version);
    });

    it('should throw error when name is missing', async () => {
      const prompt = { source: 'test', version: 'abc123' } as PromptData;
      await expect(store.save(prompt)).rejects.toThrow();
    });
  });

  describe('delete', () => {
    it('should delete a prompt', async () => {
      await createPromptFile('test.prompt');
      await store.delete('test');

      await expect(
        fs.access(path.join(tempDir, 'test.prompt'))
      ).rejects.toThrow();
    });

    it('should delete a prompt with variant', async () => {
      await createPromptFile('test.v1.prompt');
      await store.delete('test', { variant: 'v1' });

      await expect(
        fs.access(path.join(tempDir, 'test.v1.prompt'))
      ).rejects.toThrow();
    });

    it('should throw error for non-existent prompt', async () => {
      await expect(store.delete('nonexistent')).rejects.toThrow();
    });
  });
});
