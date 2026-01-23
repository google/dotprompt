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

import * as path from 'path';

export function validatePromptName(name: string): void {
  if (!name || name.trim() === '') {
    throw new Error('Prompt name cannot be empty');
  }

  // Check for null byte injection (CWE-134)
  // Null bytes can be used to bypass string validation in some systems
  if (name.includes('\x00')) {
    throw new Error(`Null byte not allowed in prompt name: '${name}'`);
  }

  // Check for null byte escape sequence pattern (backslash followed by zero)
  // This catches suspicious escape sequences even if not actual null bytes
  if (name.includes('\\0')) {
    throw new Error(
      `Null byte escape sequence not allowed in prompt name: '${name}'`
    );
  }

  // DECODE URL-ENCODED INPUT BEFORE VALIDATION
  // This prevents bypass attempts using URL-encoded path traversal sequences
  // e.g., "%2e%2e/%2e%2e" would decode to "../.." before validation checks
  // SECURITY: Decode iteratively to catch double-encoding bypasses (%252e%252e)
  let decoded = name;
  const MAX_DECODE_ITERATIONS = 3; // Prevent DoS via infinite decoding loop
  for (let iterations = 0; iterations < MAX_DECODE_ITERATIONS; iterations++) {
    try {
      const newDecoded = decodeURIComponent(decoded);
      if (newDecoded === decoded) {
        break; // No change, fully decoded
      }
      decoded = newDecoded;
    } catch {
      throw new Error(`Invalid URL encoding in prompt name: '${name}'`);
    }
  }
  // Check for remaining encoded characters (potential double-encoding bypass)
  if (decoded.includes('%')) {
    throw new Error(
      `Invalid prompt name: encoded characters not allowed: '${name}'`
    );
  }

  // UNICODE NORMALIZATION TO CATCH HOMOGRAPH ATTACKS
  // This prevents bypass attempts using visually similar characters
  // Note: Normalize AFTER URL decoding to catch URL-encoded Unicode bypasses
  const normalizedDecoded = decoded.normalize('NFC');

  // Unicode homograph attack detection (CWE-156)
  // Block fullwidth and other unicode characters that could be used to bypass validation
  // Only printable ASCII characters (U+0020 to U+007E) are allowed
  // SECURITY: Check 'normalizedDecoded' not 'name' to catch URL-encoded Unicode bypasses
  if (/[^\u0020-\u007E]/u.test(normalizedDecoded)) {
    throw new Error(
      `Non-ASCII characters not allowed in prompt name: '${name}'`
    );
  }

  // Normalize backslashes to forward slashes for consistent validation
  const normalized = normalizedDecoded.replace(/\\/g, '/');

  // Check for Windows drive letter absolute paths (e.g., C:/, D:\, C:)
  // Use normalized to catch URL-encoded variants like %43%3a
  // SECURITY: Also block bare drive letters like "C:" (length 2, letter + colon)
  if (/^[a-zA-Z]:([\/\\]|$)/.test(normalized)) {
    throw new Error(`Absolute paths not allowed: '${name}'`);
  }

  // Check for UNC network paths (e.g., \\server\share)
  // Use normalized to catch URL-encoded variants
  if (normalized.startsWith('//')) {
    throw new Error(`UNC network paths not allowed: '${name}'`);
  }

  // Check for current directory reference patterns (./)
  // While ./ alone doesn't traverse, it's unnecessary in prompt names
  if (normalized.includes('./')) {
    throw new Error(`Current directory reference not allowed: '${name}'`);
  }

  // Check for path traversal using segment-based validation
  // This catches:
  // - Segments that are only dots: "..", "...", "....", etc.
  // - Segments STARTING with "..": "..config", "..hidden" (leading parent reference)
  // - Segments ENDING with ".." when followed by non-alphanumeric: "safe..", "0.."
  // Allows: "a..b", "file..txt", "...test", "test..." (legitimate filename patterns)
  const segments = normalized.split('/');
  for (const segment of segments) {
    // Check if segment is ONLY dots (2 or more)
    if (segment.length >= 2 && /^\.+$/.test(segment)) {
      throw new Error(`Path traversal not allowed: '${name}'`);
    }

    // Check if segment STARTS with ".." (potential bypass: "..config", "..hidden")
    // Allow segments starting with 3+ dots like "...test" which are legitimate filenames
    // Block only if it starts with exactly ".." (2 dots) not "...", "...." etc
    if (
      segment.length > 2 &&
      segment[0] === '.' &&
      segment[1] === '.' &&
      segment[2] !== '.'
    ) {
      // Starts with exactly ".." followed by non-dot - check if valid pattern
      if (!/^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$/.test(segment)) {
        throw new Error(`Path traversal not allowed: '${name}'`);
      }
    }

    // Check if segment ENDS with ".." (potential bypass: "safe..", "0..", "test..")
    // But allow alphanumeric..alphanumeric patterns like "a..b" or "file..txt"
    // Also allow trailing three-or-more dots like "test..." (valid filename pattern)
    if (segment.endsWith('..') && segment.length > 2) {
      // Allow if: alphanumeric..alphanumeric (has chars after ..) OR ends with 3+ dots
      const hasCharsAfterDots = /^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$/.test(segment);
      const hasTrailingTripleDots =
        /\.\.+$/.test(segment) &&
        segment.length >= 3 &&
        segment.slice(-3).startsWith('...');
      if (!hasCharsAfterDots && !hasTrailingTripleDots) {
        throw new Error(`Path traversal not allowed: '${name}'`);
      }
    }
  }

  // Check for trailing slash (could indicate directory traversal attempt)
  if (normalized.endsWith('/')) {
    throw new Error(`Trailing slash not allowed in prompt name: '${name}'`);
  }

  // Check for absolute paths (Unix-style /path or Windows via path.isAbsolute)
  if (normalized.startsWith('/') || path.isAbsolute(name)) {
    throw new Error(`Absolute paths not allowed: '${name}'`);
  }
}

export function removeUndefinedFields(obj: any): any {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map((item) => removeUndefinedFields(item));
  }

  const result: { [key: string]: any } = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value !== undefined) {
      result[key] = removeUndefinedFields(value);
    }
  }
  return result;
}
