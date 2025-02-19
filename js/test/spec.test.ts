/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { readFileSync, readdirSync } from 'node:fs';
import { join, relative } from 'node:path';
import { afterAll, describe, expect, it, suite } from 'vitest';
import { parse } from 'yaml';
import { Dotprompt } from '../src/dotprompt';
import type { DataArgument, JSONSchema, ToolDefinition } from '../src/types';

// Define supported runtimes
enum Runtime {
  Go = 'go',
  Python = 'python',
  JavaScript = 'js',
}

interface TestCase {
  id?: string;
  desc?: string;
  skip?: boolean;
  runtimes?: Runtime[];
  data: DataArgument;
  expect: any;
  options: object;
}

interface SpecSuite {
  name: string;
  template: string;
  skip?: boolean;
  runtimes?: Runtime[];
  data?: DataArgument;
  schemas?: Record<string, JSONSchema>;
  tools?: Record<string, ToolDefinition>;
  partials?: Record<string, string>;
  resolverPartials?: Record<string, string>;
  tests: TestCase[];
}

const specDir = join('..', 'spec');
const files = readdirSync(specDir, { recursive: true, withFileTypes: true });

/**
 * Determines whether a test should be skipped.
 *
 * @param test The test to check
 * @param currentRuntime The current runtime in use; default 'js' for
 *   this one.
 * @return boolean indicating whether the test should be skipped.
 */
function shouldSkipTest(
  test: Partial<TestCase> & { data: DataArgument },
  currentRuntime: Runtime = Runtime.JavaScript
): boolean {
  if (test.skip) {
    return true;
  }
  if (test.runtimes && !test.runtimes.includes(currentRuntime)) {
    return true;
  }
  return false;
}

/**
 * Determines whether a test suite should be skipped.
 *
 * @param suite The test suite to check
 * @param currentRuntime The current runtime in use; default 'js' for
 *   this one.
 * @return boolean indicating whether the test suite should be skipped.
 */
function shouldSkipTestSuite(
  suite: Partial<SpecSuite> & { tests: TestCase[] },
  currentRuntime: Runtime = Runtime.JavaScript
): boolean {
  if (suite.skip) {
    return true;
  }
  if (suite.runtimes && !suite.runtimes.includes(currentRuntime)) {
    return true;
  }
  return false;
}

// Self-testing for harness.
describe('harness', () => {
  describe('shouldSkipTest', () => {
    const baseTest: TestCase = {
      desc: 'test',
      data: {},
      expect: { messages: [] },
    };

    it('returns true for explicitly skipped tests', () => {
      expect(shouldSkipTest({ ...baseTest, skip: true })).toBe(true);
    });

    it('returns false for non-skipped tests without runtime constraints', () => {
      expect(shouldSkipTest(baseTest)).toBe(false);
    });

    it('returns true when test requires different runtime', () => {
      expect(shouldSkipTest({ ...baseTest, runtimes: [Runtime.Go] })).toBe(
        true
      );
    });

    it('returns false when test supports current runtime', () => {
      expect(
        shouldSkipTest({ ...baseTest, runtimes: [Runtime.JavaScript] })
      ).toBe(false);
    });

    it('returns false when test supports multiple runtimes including current', () => {
      expect(
        shouldSkipTest({
          ...baseTest,
          runtimes: [Runtime.Go, Runtime.JavaScript],
        })
      ).toBe(false);
    });

    it('handles custom runtime parameter', () => {
      expect(
        shouldSkipTest(
          { ...baseTest, runtimes: [Runtime.Python] },
          Runtime.Python
        )
      ).toBe(false);
      expect(
        shouldSkipTest(
          { ...baseTest, runtimes: [Runtime.JavaScript] },
          Runtime.Python
        )
      ).toBe(true);
    });
  });

  describe('shouldSkipTestSuite', () => {
    const baseSuite = {
      tests: [],
      skip: false,
    };

    it('returns true for explicitly skipped suites', () => {
      expect(shouldSkipTestSuite({ ...baseSuite, skip: true })).toBe(true);
    });

    it('returns false for non-skipped suites without runtime constraints', () => {
      expect(shouldSkipTestSuite(baseSuite)).toBe(false);
    });

    it('returns true when suite requires different runtime', () => {
      expect(
        shouldSkipTestSuite({ ...baseSuite, runtimes: [Runtime.Go] })
      ).toBe(true);
    });

    it('returns false when suite requires current runtime', () => {
      expect(
        shouldSkipTestSuite({ ...baseSuite, runtimes: [Runtime.JavaScript] })
      ).toBe(false);
    });

    it('returns false when suite supports multiple runtimes including current', () => {
      expect(
        shouldSkipTestSuite({
          ...baseSuite,
          runtimes: [Runtime.Go, Runtime.JavaScript, Runtime.Python],
        })
      ).toBe(false);
    });

    it('handles custom runtime parameter', () => {
      expect(
        shouldSkipTestSuite(
          { ...baseSuite, runtimes: [Runtime.Python] },
          Runtime.Python
        )
      ).toBe(false);

      expect(
        shouldSkipTestSuite(
          { ...baseSuite, runtimes: [Runtime.JavaScript] },
          Runtime.Python
        )
      ).toBe(true);
    });
  });
});

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
      // Process each suite in the YAML file
      suites
        .filter((s) => !shouldSkipTestSuite(s))
        .forEach((s) => {
          describe(s.name, () => {
            s.tests.forEach((test) => {
              // Create test title
              const testTitle = [
                test.id && `[${test.id}]`,
                test.desc || 'unnamed test',
                test.runtimes && `(runtimes: ${test.runtimes.join(', ')})`,
              ]
                .filter(Boolean)
                .join(' ');

              // Skip test if explicitly marked or if runtime is not supported
              const shouldSkip = shouldSkipTest(test, Runtime.JavaScript);
              if (shouldSkip) {
                it.skip(testTitle, () => {
                  // Test body is not executed when skipped
                });
                return;
              }

              it(testTitle, async () => {
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
                  { ...s.data, ...test.data },
                  test.options
                );
                const { raw, ...prunedResult } = result;
                const {
                  raw: expectRaw,
                  input: discardInputForRender,
                  ...expected
                } = test.expect;
                expect(
                  prunedResult,
                  'render should produce the expected result'
                ).toEqual({
                  ...expected,
                  ext: expected.ext || {},
                  config: expected.config || {},
                  metadata: expected.metadata || {},
                });
                if (test.expect.raw) {
                  expect(raw).toEqual(expectRaw);
                }

                const metadataResult = await env.renderMetadata(
                  s.template,
                  test.options
                );
                const { raw: metadataResultRaw, ...prunedMetadataResult } =
                  metadataResult;
                const {
                  messages,
                  raw: metadataExpectRaw,
                  ...expectedMetadata
                } = test.expect;
                expect(
                  prunedMetadataResult,
                  'renderMetadata should produce the expected result'
                ).toEqual({
                  ...expectedMetadata,
                  ext: expectedMetadata.ext || {},
                  config: expectedMetadata.config || {},
                  metadata: expectedMetadata.metadata || {},
                });
                if (metadataExpectRaw) {
                  expect(metadataResultRaw).toEqual(metadataExpectRaw);
                }
              });
            });
          });
        });
    });
  });
