/*
 * Copyright 2025 Google LLC
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

package com.google.dotprompt.store;

import java.io.IOException;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

/**
 * Utility methods for directory-based prompt stores.
 *
 * <p>This class provides common functionality for parsing prompt filenames, calculating versions,
 * and scanning directories for prompt files.
 */
public final class StoreUtils {

  /** The file extension for prompt files. */
  public static final String PROMPT_EXTENSION = ".prompt";

  /** Private constructor to prevent instantiation. */
  private StoreUtils() {}

  /**
   * Calculates a version hash for the given content.
   *
   * <p>Uses SHA-1 and returns the first 8 characters of the hex-encoded hash. This matches the
   * version calculation in the JavaScript and Python implementations for cross-language
   * compatibility.
   *
   * @param content The content to hash.
   * @return An 8-character hex string representing the version.
   */
  public static String calculateVersion(String content) {
    try {
      MessageDigest digest = MessageDigest.getInstance("SHA-1");
      byte[] hash = digest.digest(content.getBytes(StandardCharsets.UTF_8));
      StringBuilder hexString = new StringBuilder();
      for (int i = 0; i < 4; i++) { // 4 bytes = 8 hex chars
        String hex = Integer.toHexString(0xff & hash[i]);
        if (hex.length() == 1) {
          hexString.append('0');
        }
        hexString.append(hex);
      }
      return hexString.toString();
    } catch (NoSuchAlgorithmException e) {
      throw new RuntimeException("SHA-1 not available", e);
    }
  }

  /**
   * Parses a prompt filename to extract name and optional variant.
   *
   * <p>Expected format: {@code name[.variant].prompt} or {@code _name[.variant].prompt} for
   * partials.
   *
   * @param filename The filename to parse (without any directory prefix).
   * @return A ParsedFilename containing the name and variant.
   * @throws IllegalArgumentException If the filename doesn't match expected format.
   */
  public static ParsedFilename parsePromptFilename(String filename) {
    if (!filename.endsWith(PROMPT_EXTENSION)) {
      throw new IllegalArgumentException("Filename must end with " + PROMPT_EXTENSION);
    }

    // Remove the leading underscore for partials
    String baseName = filename;
    if (baseName.startsWith("_")) {
      baseName = baseName.substring(1);
    }

    // Remove the .prompt extension
    baseName = baseName.substring(0, baseName.length() - PROMPT_EXTENSION.length());

    // Check for variant (format: name.variant)
    int lastDot = baseName.lastIndexOf('.');
    if (lastDot > 0) {
      String name = baseName.substring(0, lastDot);
      String variant = baseName.substring(lastDot + 1);
      return new ParsedFilename(name, variant);
    }

    return new ParsedFilename(baseName, null);
  }

  /**
   * Checks if a filename represents a partial prompt.
   *
   * <p>Partials are identified by a leading underscore in the filename.
   *
   * @param filename The filename to check.
   * @return true if the filename starts with '_', false otherwise.
   */
  public static boolean isPartial(String filename) {
    return filename.startsWith("_");
  }

  /**
   * Scans a directory for prompt files.
   *
   * @param baseDir The base directory to scan.
   * @return A list of relative paths to all .prompt files found.
   * @throws IOException If an error occurs while scanning.
   */
  public static List<String> scanDirectory(Path baseDir) throws IOException {
    List<String> results = new ArrayList<>();
    if (!Files.exists(baseDir) || !Files.isDirectory(baseDir)) {
      return results;
    }

    try (Stream<Path> paths = Files.walk(baseDir)) {
      paths
          .filter(Files::isRegularFile)
          .filter(p -> p.getFileName().toString().endsWith(PROMPT_EXTENSION))
          .forEach(
              p -> {
                Path relativePath = baseDir.relativize(p);
                results.add(relativePath.toString());
              });
    }
    return results;
  }

  /**
   * Validates that a prompt name doesn't contain path traversal sequences.
   *
   * @param name the prompt name to validate.
   * @throws IllegalArgumentException if name contains path traversal attempts.
   */
  public static void validatePromptName(String name) {
    if (name == null || name.isEmpty() || name.trim().isEmpty()) {
      throw new IllegalArgumentException("Invalid prompt name: name cannot be empty or whitespace");
    }

    // DECODE URL-ENCODED INPUT BEFORE VALIDATION
    // This prevents bypass attempts using URL-encoded path traversal sequences
    // e.g., "%2e%2e/%2e%2e" would decode to "../.." before validation checks
    // SECURITY: Decode iteratively to catch double-encoding bypasses (%252e%252e)
    String decoded = name;
    int iterations = 0;
    final int MAX_DECODE_ITERATIONS = 3; // Prevent DoS via infinite decoding loop
    while (iterations < MAX_DECODE_ITERATIONS) {
      try {
        String newDecoded = URLDecoder.decode(decoded, StandardCharsets.UTF_8.name());
        if (newDecoded.equals(decoded)) {
          break; // No change, fully decoded
        }
        decoded = newDecoded;
        iterations++;
      } catch (Exception e) {
        throw new IllegalArgumentException("Invalid URL encoding in prompt name");
      }
    }
    // Check for remaining encoded characters (potential double-encoding bypass)
    if (decoded.contains("%")) {
      throw new IllegalArgumentException("Invalid prompt name: encoded characters not allowed: '" + name + "'");
    }
    name = decoded;

    // NORMALIZE UNICODE TO CATCH HOMOGRAPH ATTACKS
    // This prevents bypass attempts using visually similar characters
    // Note: NFC doesn't convert all Unicode dots (U+FF0E, U+2024, U+2025), so we check for those
    name = Normalizer.normalize(name, Normalizer.Form.NFC);

    // BLOCK UNC NETWORK PATHS - Prevent Windows network path access
    if (name.startsWith("\\\\")) {
      throw new IllegalArgumentException("Invalid path: UNC network paths not allowed: '" + name + "'");
    }

    // Check for current directory reference patterns
    if (name.contains("./") || name.contains(".\\")) {
      throw new IllegalArgumentException("Invalid path: current directory reference not allowed: '" + name + "'");
    }

    // Check for path traversal - block segments with ".." patterns
    // This catches:
    // - Segments that are only dots: "..", "...", "....", etc.
    // - Segments STARTING with "..": "..config", "..hidden" (leading parent reference)
    // - Segments ENDING with ".." when followed by non-alphanumeric: "safe..", "0.."
    // Allows: "a..b", "file..txt", "...test", "test..." (legitimate filename patterns)
    String normalized = name.replace('\\', '/');
    String[] segments = normalized.split("/");
    for (String segment : segments) {
      // Check if segment is ONLY dots (2 or more)
      if (segment.length() >= 2 && segment.matches("^\\.+$")) {
        throw new IllegalArgumentException("Path traversal not allowed: '" + name + "'");
      }

      // Check if segment STARTS with ".." (potential bypass: "..config", "..hidden")
      // Allow segments starting with 3+ dots like "...test" which are legitimate filenames
      // Block only if it starts with exactly ".." (2 dots) not "...", "...." etc
      if (segment.length() > 2 && segment.charAt(0) == '.' && segment.charAt(1) == '.' && segment.charAt(2) != '.') {
        // Starts with exactly ".." followed by non-dot - check if valid pattern
        if (!segment.matches("^[a-zA-Z0-9]+\\.\\.[a-zA-Z0-9]+$")) {
          throw new IllegalArgumentException("Path traversal not allowed: '" + name + "'");
        }
      }

      // Check if segment ENDS with ".." (potential bypass: "safe..", "0..", "test..")
      // But allow alphanumeric..alphanumeric patterns like "a..b" or "file..txt"
      // Also allow trailing three-or-more dots like "test..." (valid filename pattern)
      if (segment.endsWith("..") && segment.length() > 2) {
        // Allow if: alphanumeric..alphanumeric (has chars after ..) OR ends with 3+ dots
        boolean hasCharsAfterDots = segment.matches("^[a-zA-Z0-9]+\\.\\.[a-zA-Z0-9]+$");
        boolean hasTrailingTripleDots = segment.matches(".*\\.\\.\\.+$");
        if (!hasCharsAfterDots && !hasTrailingTripleDots) {
          throw new IllegalArgumentException("Path traversal not allowed: '" + name + "'");
        }
      }
    }

    // BLOCK NULL BYTES - Check after path traversal to catch null bytes in any form
    if (name.indexOf('\0') >= 0) {
      throw new IllegalArgumentException(
          "Invalid prompt name: null bytes not allowed for security");
    }

    // BLOCK NULL BYTE ESCAPE SEQUENCE PATTERN
    // Check for the literal "\0" pattern (backslash followed by zero)
    // This catches suspicious escape sequences even if not actual null bytes
    if (name.contains("\\0")) {
      throw new IllegalArgumentException("Invalid prompt name: null byte escape sequence not allowed: '" + name + "'");
    }

    // Check for absolute paths - Unix-style leading slash
    if (name.startsWith("/")) {
      throw new IllegalArgumentException("Invalid path: absolute paths not allowed: '" + name + "'");
    }

    // Block trailing slashes - prevents directory access ambiguity
    if (name.endsWith("/") || name.endsWith("\\")) {
      throw new IllegalArgumentException(
          "Invalid path: trailing slash not allowed: '" + name + "'");
    }

    // Check for Windows absolute paths - single letter followed by colon (e.g., C:, D:)
    // This specifically targets Windows drive letter patterns, not general colons in names
    if (name.length() == 2 || (name.length() > 2 && !Character.isLetterOrDigit(name.charAt(2)))) {
      if (name.charAt(1) == ':' && Character.isLetter(name.charAt(0))) {
        throw new IllegalArgumentException("Invalid path: Windows drive paths not allowed: '" + name + "'");
      }
    }
  }

  /**
   * Builds the filename for a prompt.
   *
   * @param name The prompt name (can include subdirectory paths).
   * @param variant The optional variant.
   * @param isPartial Whether this is a partial.
   * @return The constructed filename.
   */
  public static String buildFilename(String name, String variant, boolean isPartial) {
    StringBuilder sb = new StringBuilder();

    // Handle subdirectories in the name
    int lastSlash = Math.max(name.lastIndexOf('/'), name.lastIndexOf('\\'));
    String dir = "";
    String baseName = name;
    if (lastSlash >= 0) {
      dir = name.substring(0, lastSlash + 1);
      baseName = name.substring(lastSlash + 1);
    }

    sb.append(dir);
    if (isPartial) {
      sb.append("_");
    }
    sb.append(baseName);
    if (variant != null && !variant.isEmpty()) {
      sb.append(".").append(variant);
    }
    sb.append(PROMPT_EXTENSION);
    return sb.toString();
  }

  /** Result of parsing a prompt filename. */
  public record ParsedFilename(String name, String variant) {}
}
