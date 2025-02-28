/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['test/**/*.test.ts', 'src/**/*.test.ts'],
    environment: 'node',
    coverage: {
      enabled: true,
      provider: 'v8',
      reporter: ['text', 'html'],
      thresholds: {
        autoUpdate: true,
        branches: 88.61,
        functions: 95.45,
        lines: 72.25,
        statements: 72.25,
      },
    },
  },
});
