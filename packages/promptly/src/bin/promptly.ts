#!/usr/bin/env node

// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview Wrapper script that executes the native promptly binary.
 */

import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);

type Platform = 'darwin' | 'linux' | 'win32';
type Arch = 'arm64' | 'x64';

interface PlatformConfig {
  package: string;
  binaryName: string;
}

const PLATFORM_MAP: Record<string, PlatformConfig> = {
  'darwin-arm64': {
    package: '@dotprompt/promptly-darwin-arm64',
    binaryName: 'promptly',
  },
  'darwin-x64': {
    package: '@dotprompt/promptly-darwin-x64',
    binaryName: 'promptly',
  },
  'linux-arm64': {
    package: '@dotprompt/promptly-linux-arm64',
    binaryName: 'promptly',
  },
  'linux-x64': {
    package: '@dotprompt/promptly-linux-x64',
    binaryName: 'promptly',
  },
  'win32-x64': {
    package: '@dotprompt/promptly-win32-x64',
    binaryName: 'promptly.exe',
  },
};

/**
 * Returns the platform key for the current system.
 */
function getPlatformKey(): string {
  const platform = process.platform as Platform;
  const arch = process.arch as Arch;
  return `${platform}-${arch}`;
}

/**
 * Returns the configuration for the current platform.
 */
function getPlatformConfig(): PlatformConfig | undefined {
  const key = getPlatformKey();
  return PLATFORM_MAP[key];
}

/**
 * Resolves the path to the native binary.
 */
function getBinaryPath(): string {
  const config = getPlatformConfig();

  if (!config) {
    const supported = Object.keys(PLATFORM_MAP).join(', ');
    console.error(`Unsupported platform: ${getPlatformKey()}`);
    console.error(`Supported platforms: ${supported}`);
    process.exit(1);
  }

  try {
    const pkgPath = require.resolve(`${config.package}/package.json`);
    const pkgDir = path.dirname(pkgPath);
    return path.join(pkgDir, 'bin', config.binaryName);
  } catch {
    console.error(`Failed to find promptly binary for your platform.`);
    console.error(`Package ${config.package} is not installed.`);
    console.error('');
    console.error('Try reinstalling @dotprompt/promptly:');
    console.error('  npm install @dotprompt/promptly');
    process.exit(1);
  }
}

// Execute the binary with all arguments
const binaryPath = getBinaryPath();
const args = process.argv.slice(2);

const child = spawn(binaryPath, args, {
  stdio: 'inherit',
  windowsHide: true,
});

child.on('error', (err: Error) => {
  console.error(`Failed to execute promptly: ${err.message}`);
  process.exit(1);
});

child.on('close', (code: number | null) => {
  process.exit(code ?? 0);
});
