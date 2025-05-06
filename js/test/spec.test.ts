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

import { readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it, suite } from 'vitest';
import { parse } from 'yaml';
import { Dotprompt } from '../src/dotprompt';
import type { DataArgument, JSONSchema, ToolDefinition } from '../src/types';

/**
 * The directory containing the spec files.
 */
const SPEC_DIR = join('..', 'spec');

/** An expectation for the spec. */
interface Expect {
  config: boolean;
  ext: boolean;
  input: boolean;
  messages: boolean;
  metadata: boolean;
  raw: boolean;
}

/**
 * A test case for a YAML spec.
 */
interface SpecTest {
  desc?: string;
  data: DataArgument;
  expect: Expect;
  options: object;
}

/**
 * A suite of test cases for a YAML spec.
 */
interface SpecSuite {
  name: string;
  template: string;
  data?: DataArgument;
  schemas?: Record<string, JSONSchema>;
  tools?: Record<string, ToolDefinition>;
  partials?: Record<string, string>;
  resolverPartials?: Record<string, string>;
  tests: SpecTest[];
}

/**
 * Creates test cases for a YAML spec.
 *
 * @param s The suite
 * @param tc The test case
 * @param dotpromptFactory The dotprompt factory
 */
async function createTestCases(
  s: SpecSuite,
  tc: SpecTest,
  dotpromptFactory: (suite: SpecSuite) => Dotprompt
) {
  it(tc.desc || 'should match expected output', async () => {
    const env = dotpromptFactory(s);

    // Define partials if they exist.
    if (s.partials) {
      for (const [name, template] of Object.entries(s.partials)) {
        env.definePartial(name, template);
      }
    }

    // Render the template.
    const result = await env.render(
      s.template,
      { ...s.data, ...tc.data },
      tc.options
    );

    // Prune the result and compare to the expected output.
    const { raw, ...prunedResult } = result;
    const {
      raw: expectRaw,
      input: discardInputForRender,
      ...expected
    } = tc.expect;

    // Compare the pruned result to the expected output.
    expect(prunedResult, 'render should produce the expected result').toEqual({
      ...expected,
      ext: expected.ext || {},
      config: expected.config || {},
      metadata: expected.metadata || {},
    });

    // Only compare raw if the spec demands it.
    if (tc.expect.raw) {
      expect(raw).toEqual(expectRaw);
    }

    // Render the metadata.
    const metadataResult = await env.renderMetadata(s.template, tc.options);
    const { raw: metadataResultRaw, ...prunedMetadataResult } = metadataResult;
    const { messages, raw: metadataExpectRaw, ...expectedMetadata } = tc.expect;

    // Compare the pruned metadata result to the expected output.
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
}

/**
 * Creates a test suite for a YAML spec.
 *
 * @param suiteName The name of the suite
 * @param suites The suites to create
 * @param dotpromptFactory The dotprompt factory
 */
function createTestSuite(
  suiteName: string,
  suites: SpecSuite[],
  dotpromptFactory: (suite: SpecSuite) => Dotprompt
) {
  suite(suiteName, () => {
    for (const s of suites) {
      describe(s.name, () => {
        for (const tc of s.tests) {
          createTestCases(s, tc, dotpromptFactory);
        }
      });
    }
  });
}

/**
 * Processes a single spec file.  Takes the file reading function as a dependency.
 *
 * @param file The file to process
 * @param readFileSyncFn The file reading function
 * @param dotpromptFactory The dotprompt factory
 */
function processSpecFile(
  file: { path: string; name: string },
  readFileSyncFn: (path: string, encoding: BufferEncoding) => string,
  dotpromptFactory: (suite: SpecSuite) => Dotprompt
) {
  const suiteName = join(
    relative(SPEC_DIR, file.path),
    file.name.replace(/\.yaml$/, '')
  );
  const suites: SpecSuite[] = parse(
    readFileSyncFn(join(file.path, file.name), 'utf-8')
  );
  createTestSuite(suiteName, suites, dotpromptFactory);
}

/**
 * Top level processing, orchestrates the other functions.
 */
function processSpecFiles(dotpromptFactory: (suite: SpecSuite) => Dotprompt) {
  const files = readdirSync(SPEC_DIR, { recursive: true, withFileTypes: true });
  for (const file of files.filter(
    (file) => !file.isDirectory() && file.name.endsWith('.yaml')
  )) {
    processSpecFile(file, readFileSync, dotpromptFactory);
  }
}

const dotpromptFactory = (s: SpecSuite) => {
  return new Dotprompt({
    schemas: s.schemas,
    tools: s.tools,
    partialResolver: (name: string) => s.resolverPartials?.[name] || null,
  });
};
processSpecFiles(dotpromptFactory);
