/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it, suite } from 'vitest';
import { parse } from 'yaml';
import { Dotprompt } from '../src/dotprompt';
import type { DataArgument, JSONSchema, ToolDefinition } from '../src/types';

const specDir = join('..', 'spec');
const files = readdirSync(specDir, { recursive: true, withFileTypes: true });

interface SpecSuite {
  name: string;
  template: string;
  data?: DataArgument;
  schemas?: Record<string, JSONSchema>;
  tools?: Record<string, ToolDefinition>;
  partials?: Record<string, string>;
  resolverPartials?: Record<string, string>;
  tests: { desc?: string; data: DataArgument; expect: any; options: object }[];
}

// Process each YAML file
files
  .filter((file) => !file.isDirectory() && file.name.endsWith('.yaml'))
  .forEach((file) => {
    const suiteName = join(
      relative(specDir, file.path),
      file.name.replace(/\.yaml$/, '')
    );
    const suites: SpecSuite[] = parse(
      readFileSync(join(file.path, file.name), 'utf-8')
    );

    // Create a describe block for each YAML file
    suite(suiteName, () => {
      // Create a describe block for each suite in the file
      suites.forEach((s) => {
        describe(s.name, () => {
          // Create a test for each test case in the suite
          s.tests.forEach((tc) => {
            it(tc.desc || 'should match expected output', async () => {
              const env = new Dotprompt({
                schemas: s.schemas,
                tools: s.tools,
                partialResolver: (name: string) =>
                  s.resolverPartials?.[name] || null,
              });

              if (s.partials) {
                for (const [name, template] of Object.entries(s.partials)) {
                  env.definePartial(name, template);
                }
              }

              const result = await env.render(
                s.template,
                { ...s.data, ...tc.data },
                tc.options
              );
              const { raw, ...prunedResult } = result;
              const {
                raw: expectRaw,
                input: discardInputForRender,
                ...expected
              } = tc.expect;
              expect(
                prunedResult,
                'render should produce the expected result'
              ).toEqual({
                ...expected,
                ext: expected.ext || {},
                config: expected.config || {},
                metadata: expected.metadata || {},
              });
              // only compare raw if the spec demands it
              if (tc.expect.raw) {
                expect(raw).toEqual(expectRaw);
              }

              const metadataResult = await env.renderMetadata(
                s.template,
                tc.options
              );
              const { raw: metadataResultRaw, ...prunedMetadataResult } =
                metadataResult;
              const {
                messages,
                raw: metadataExpectRaw,
                ...expectedMetadata
              } = tc.expect;
              expect(
                prunedMetadataResult,
                'renderMetadata should produce the expected result'
              ).toEqual({
                ...expectedMetadata,
                ext: expectedMetadata.ext || {},
                config: expectedMetadata.config || {},
                metadata: expectedMetadata.metadata || {},
              });
            });
          });
        });
      });
    });
  });
