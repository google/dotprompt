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

/// Security utilities for prompt name validation.
///
/// Provides validation to prevent path traversal (CWE-22), null byte
/// injection (CWE-134), and Unicode homograph attacks (CWE-156).
library;

/// Validates a prompt name for security issues.
///
/// Prevents:
/// - Path traversal attacks (CWE-22): `../../etc/passwd`
/// - Null byte injection (CWE-134): `file\x00.txt`
/// - UNC path attacks: `\\server\share`
/// - Unicode homograph attacks (CWE-156): visually similar characters
/// - URL-encoded bypass attempts: `%2e%2e/`
/// - Absolute path references: `/etc/passwd`, `C:\`
///
/// Throws [ArgumentError] if the name is invalid.
///
/// ## Example
///
/// ```dart
/// validatePromptName('my-prompt');      // OK
/// validatePromptName('org/my-prompt');  // OK (namespaced)
/// validatePromptName('../../secret');   // Throws ArgumentError
/// validatePromptName('/etc/passwd');    // Throws ArgumentError
/// ```
void validatePromptName(String name) {
  if (name.isEmpty || name.trim().isEmpty) {
    throw ArgumentError.value(name, "name", "Prompt name cannot be empty");
  }

  // Check for null byte injection (CWE-134)
  if (name.contains("\x00")) {
    throw ArgumentError.value(
      name,
      "name",
      "Null byte not allowed in prompt name",
    );
  }

  // Check for null byte escape sequence pattern
  if (name.contains(r"\0")) {
    throw ArgumentError.value(
      name,
      "name",
      "Null byte escape sequence not allowed in prompt name",
    );
  }

  // Decode URL-encoded input before validation.
  // This prevents bypass attempts using URL-encoded path traversal sequences
  // e.g., "%2e%2e/%2e%2e" would decode to "../.." before validation checks.
  // Decode iteratively to catch double-encoding bypasses (%252e%252e).
  var decoded = name;
  const maxDecodeIterations = 3; // Prevent DoS via infinite decoding loop
  for (var i = 0; i < maxDecodeIterations; i++) {
    final newDecoded = _tryDecodeUri(decoded);
    if (newDecoded == null) {
      throw ArgumentError.value(
        name,
        "name",
        "Invalid URL encoding in prompt name",
      );
    }
    if (newDecoded == decoded) break; // No change, fully decoded
    decoded = newDecoded;
  }

  // Check for remaining encoded characters (potential double-encoding bypass)
  if (decoded.contains("%")) {
    throw ArgumentError.value(
      name,
      "name",
      "Invalid prompt name: encoded characters not allowed",
    );
  }

  // Unicode homograph attack detection (CWE-156)
  // Only printable ASCII characters (U+0020 to U+007E) are allowed.
  // Check decoded value to catch URL-encoded Unicode bypasses.
  if (_containsNonAscii(decoded)) {
    throw ArgumentError.value(
      name,
      "name",
      "Non-ASCII characters not allowed in prompt name",
    );
  }

  // Normalize backslashes to forward slashes for consistent validation
  final normalized = decoded.replaceAll(r"\", "/");

  // Check for Windows drive letter absolute paths (e.g., C:/, D:\, C:)
  if (RegExp(r"^[a-zA-Z]:([/\\]|$)").hasMatch(normalized)) {
    throw ArgumentError.value(name, "name", "Absolute paths not allowed");
  }

  // Check for UNC network paths (e.g., \\server\share)
  if (normalized.startsWith("//")) {
    throw ArgumentError.value(
      name,
      "name",
      "UNC network paths not allowed",
    );
  }

  // Check for current directory reference patterns (./)
  if (normalized.contains("./")) {
    throw ArgumentError.value(
      name,
      "name",
      "Current directory reference not allowed",
    );
  }

  // Check for path traversal using segment-based validation
  final segments = normalized.split("/");
  for (final segment in segments) {
    // Check if segment is ONLY dots (2 or more)
    if (segment.length >= 2 && RegExp(r"^\.+$").hasMatch(segment)) {
      throw ArgumentError.value(name, "name", "Path traversal not allowed");
    }

    // Check if segment STARTS with ".." (potential bypass: "..config")
    // Allow segments starting with 3+ dots like "...test"
    if (segment.length > 2 && segment[0] == "." && segment[1] == "." && segment[2] != ".") {
      if (!RegExp(r"^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$").hasMatch(segment)) {
        throw ArgumentError.value(name, "name", "Path traversal not allowed");
      }
    }

    // Check if segment ENDS with ".." (potential bypass: "safe..", "0..")
    // Allow alphanumeric..alphanumeric patterns like "a..b" or "file..txt"
    if (segment.endsWith("..") && segment.length > 2) {
      final hasCharsAfterDots = RegExp(r"^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$").hasMatch(segment);
      final hasTrailingTripleDots = RegExp(r"\.\.+$").hasMatch(segment) &&
          segment.length >= 3 &&
          segment.substring(segment.length - 3).startsWith("...");
      if (!hasCharsAfterDots && !hasTrailingTripleDots) {
        throw ArgumentError.value(name, "name", "Path traversal not allowed");
      }
    }
  }

  // Check for trailing slash
  if (normalized.endsWith("/")) {
    throw ArgumentError.value(
      name,
      "name",
      "Trailing slash not allowed in prompt name",
    );
  }

  // Check for absolute paths (Unix-style)
  if (normalized.startsWith("/")) {
    throw ArgumentError.value(name, "name", "Absolute paths not allowed");
  }
}

/// Attempts to decode a URI component string.
/// Returns null if decoding fails (invalid encoding).
String? _tryDecodeUri(String input) {
  try {
    return Uri.decodeComponent(input);
  } on ArgumentError {
    return null;
  } on FormatException {
    return null;
  }
}

/// Checks if a string contains any non-ASCII characters.
/// Only printable ASCII (U+0020 to U+007E) is allowed.
bool _containsNonAscii(String input) {
  for (var i = 0; i < input.length; i++) {
    final code = input.codeUnitAt(i);
    if (code < 0x20 || code > 0x7E) {
      return true;
    }
  }
  return false;
}
