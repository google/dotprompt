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
 * @fileoverview Postinstall script that validates the binary is available.
 */

import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';

const require = createRequire(import.meta.url);

type Platform = 'darwin' | 'linux' | 'win32';
type Arch = 'arm64' | 'x64';

const PLATFORM_MAP: Record<string, { package: string; binaryName: string }> = {
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
 * Checks if the binary is available for the current platform.
 */
function checkBinary(): void {
  const platform = process.platform as Platform;
  const arch = process.arch as Arch;
  const key = `${platform}-${arch}`;
  const config = PLATFORM_MAP[key];

  if (!config) {
    console.warn(`⚠️  Unsupported platform: ${key}`);
    console.warn('   promptly may not work on this platform.');
    return;
  }

  try {
    const pkgPath = require.resolve(`${config.package}/package.json`);
    const pkgDir = path.dirname(pkgPath);
    const binaryPath = path.join(pkgDir, 'bin', config.binaryName);

    if (existsSync(binaryPath)) {
      console.log(`✓ promptly binary installed for ${key}`);
    } else {
      console.warn(`⚠️  Binary not found at ${binaryPath}`);
    }
  } catch {
    // Optional dependency not installed - this is fine during development
    console.warn(`⚠️  Platform package ${config.package} not installed.`);
    console.warn("   This is expected if you're building from source.");
  }
}

checkBinary();
