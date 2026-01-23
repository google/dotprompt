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

import static com.google.common.truth.Truth.assertThat;
import static org.junit.Assert.fail;

import java.io.IOException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for {@link StoreUtils}. */
@RunWith(JUnit4.class)
public class StoreUtilsTest {

  @Rule public TemporaryFolder tempFolder = new TemporaryFolder();

  @Test
  public void calculateVersion_shouldReturnConsistentHash() {
    String content = "Hello, World!";
    String version1 = StoreUtils.calculateVersion(content);
    String version2 = StoreUtils.calculateVersion(content);

    assertThat(version1).isEqualTo(version2);
    assertThat(version1).hasLength(8);
  }

  @Test
  public void calculateVersion_shouldReturnDifferentHashForDifferentContent() {
    String version1 = StoreUtils.calculateVersion("Hello");
    String version2 = StoreUtils.calculateVersion("World");

    assertThat(version1).isNotEqualTo(version2);
  }

  @Test
  public void parsePromptFilename_shouldExtractNameWithoutVariant() {
    StoreUtils.ParsedFilename result = StoreUtils.parsePromptFilename("greet.prompt");

    assertThat(result.name()).isEqualTo("greet");
    assertThat(result.variant()).isNull();
  }

  @Test
  public void parsePromptFilename_shouldExtractNameAndVariant() {
    StoreUtils.ParsedFilename result = StoreUtils.parsePromptFilename("greet.formal.prompt");

    assertThat(result.name()).isEqualTo("greet");
    assertThat(result.variant()).isEqualTo("formal");
  }

  @Test
  public void parsePromptFilename_shouldHandlePartialPrefix() {
    StoreUtils.ParsedFilename result = StoreUtils.parsePromptFilename("_header.prompt");

    assertThat(result.name()).isEqualTo("header");
    assertThat(result.variant()).isNull();
  }

  @Test
  public void parsePromptFilename_shouldHandlePartialWithVariant() {
    StoreUtils.ParsedFilename result = StoreUtils.parsePromptFilename("_footer.dark.prompt");

    assertThat(result.name()).isEqualTo("footer");
    assertThat(result.variant()).isEqualTo("dark");
  }

  @Test(expected = IllegalArgumentException.class)
  public void parsePromptFilename_shouldThrowForInvalidExtension() {
    StoreUtils.parsePromptFilename("greet.txt");
  }

  @Test
  public void isPartial_shouldReturnTrueForPartials() {
    assertThat(StoreUtils.isPartial("_header.prompt")).isTrue();
    assertThat(StoreUtils.isPartial("_footer.dark.prompt")).isTrue();
  }

  @Test
  public void isPartial_shouldReturnFalseForPrompts() {
    assertThat(StoreUtils.isPartial("greet.prompt")).isFalse();
    assertThat(StoreUtils.isPartial("greet.formal.prompt")).isFalse();
  }

  @Test
  public void buildFilename_shouldBuildPromptFilename() {
    String result = StoreUtils.buildFilename("greet", null, false);
    assertThat(result).isEqualTo("greet.prompt");
  }

  @Test
  public void buildFilename_shouldBuildPromptFilenameWithVariant() {
    String result = StoreUtils.buildFilename("greet", "formal", false);
    assertThat(result).isEqualTo("greet.formal.prompt");
  }

  @Test
  public void buildFilename_shouldBuildPartialFilename() {
    String result = StoreUtils.buildFilename("header", null, true);
    assertThat(result).isEqualTo("_header.prompt");
  }

  @Test
  public void buildFilename_shouldBuildPartialFilenameWithVariant() {
    String result = StoreUtils.buildFilename("footer", "dark", true);
    assertThat(result).isEqualTo("_footer.dark.prompt");
  }

  @Test
  public void buildFilename_shouldHandleSubdirectory() {
    String result = StoreUtils.buildFilename("group/greet", "formal", false);
    assertThat(result).isEqualTo("group/greet.formal.prompt");
  }

  @Test
  public void scanDirectory_shouldFindPromptFiles() throws IOException {
    Path baseDir = tempFolder.newFolder("prompts").toPath();
    Files.writeString(baseDir.resolve("greet.prompt"), "content", StandardCharsets.UTF_8);
    Files.writeString(baseDir.resolve("_header.prompt"), "partial", StandardCharsets.UTF_8);
    Files.writeString(baseDir.resolve("other.txt"), "text", StandardCharsets.UTF_8);

    List<String> results = StoreUtils.scanDirectory(baseDir);

    assertThat(results).hasSize(2);
    assertThat(results).contains("greet.prompt");
    assertThat(results).contains("_header.prompt");
  }

  @Test
  public void scanDirectory_shouldFindFilesInSubdirectories() throws IOException {
    Path baseDir = tempFolder.newFolder("prompts").toPath();
    Path subDir = baseDir.resolve("group");
    Files.createDirectories(subDir);
    Files.writeString(subDir.resolve("greet.prompt"), "content", StandardCharsets.UTF_8);

    List<String> results = StoreUtils.scanDirectory(baseDir);

    assertThat(results).hasSize(1);
    assertThat(results.get(0)).contains("greet.prompt");
    assertThat(results.get(0)).contains("group");
  }

  @Test
  public void scanDirectory_shouldReturnEmptyForNonexistentDir() throws IOException {
    Path baseDir = Path.of(tempFolder.getRoot().getPath(), "nonexistent");

    List<String> results = StoreUtils.scanDirectory(baseDir);

    assertThat(results).isEmpty();
  }

  // ========== PATH VALIDATION TESTS ==========

  @Test
  public void validatePromptName_rejectsDoubleDotTraversal() {
    assertValidationThrows("../../../etc/passwd");
  }

  @Test
  public void validatePromptName_rejectsDoubleDotOnly() {
    assertValidationThrows("..");
  }

  @Test
  public void validatePromptName_rejectsTripleDots() {
    assertValidationThrows(".../...");
  }

  @Test
  public void validatePromptName_rejectsAbsolutePaths() {
    assertValidationThrows("/absolute/path.attack");
  }

  @Test
  public void validatePromptName_rejectsWindowsAbsolutePaths() {
    assertValidationThrows("C:/Windows/System32");
  }

  @Test
  public void validatePromptName_rejectsNetworkPaths() {
    assertValidationThrows("\\\\network\\share");
  }

  @Test
  public void validatePromptName_rejectsEmbeddedTraversal() {
    assertValidationThrows("subdir/../../../escape");
  }

  @Test
  public void validatePromptName_rejectsWindowsStyleTraversal() {
    assertValidationThrows("..\\windows\\system32");
  }

  @Test
  public void validatePromptName_rejectsMixedSlashTraversal() {
    assertValidationThrows("..\\../etc/passwd");
  }

  @Test
  public void validatePromptName_rejectsUrlEncodedDots() {
    assertValidationThrows("%2e%2e/%2e%2e");
  }

  @Test
  public void validatePromptName_rejectsEmptyString() {
    assertValidationThrows("");
  }

  @Test
  public void validatePromptName_rejectsWhitespaceOnly() {
    assertValidationThrows("   ");
  }

  @Test
  public void validatePromptName_rejectsNullByteInjection() {
    // Null byte injection - attacker tries to truncate validation
    assertValidationThrows("safe..\\0../etc/passwd");
    assertValidationThrows("prompt\\0.trigger");
    assertValidationThrows("a\\0../escape");
  }

  @Test
  public void validatePromptName_rejectsUncNetworkPaths() {
    // UNC network paths for Windows
    assertValidationThrows("\\\\network\\share");
    assertValidationThrows("\\\\?\\C:\\Windows");
    assertValidationThrows("\\\\192.168.1.1\\share");
  }

  @Test
  public void validatePromptName_allowsColonNotFollowedByDriveLetter() {
    // Names with colons that are NOT Windows drive letters should be allowed
    // The old implementation would reject "a:b" incorrectly
    assertValidationPasses("a:b");
    assertValidationPasses("time:12:30");
    assertValidationPasses("label:value");
  }

  @Test
  public void validatePromptName_rejectsTrailingSlash() {
    assertValidationThrows("prompt/");
  }

  @Test
  public void validatePromptName_rejectsLeadingSlashInSubdir() {
    assertValidationThrows("/subdir/prompt");
  }

  @Test
  public void validatePromptName_rejectsNormalizedTraversal() {
    assertValidationThrows("./..");
    assertValidationThrows("subdir/./../escape");
  }

  @Test
  public void validatePromptName_allowsSimpleName() {
    assertValidationPasses("simple");
  }

  @Test
  public void validatePromptName_allowsHyphenatedName() {
    assertValidationPasses("my-prompt");
  }

  @Test
  public void validatePromptName_allowsUnderscoredName() {
    assertValidationPasses("my_prompt");
  }

  @Test
  public void validatePromptName_allowsDotsInMiddleOfName() {
    // Key distinction: 'a..b' has dots in the middle, not at path segment start
    assertValidationPasses("a..b");
  }

  @Test
  public void validatePromptName_allowsVersionWithDots() {
    assertValidationPasses("version..2");
  }

  @Test
  public void validatePromptName_allowsSubdirectoryPaths() {
    assertValidationPasses("subdir/nested");
  }

  @Test
  public void validatePromptName_allowsDeepNesting() {
    assertValidationPasses("subdir/deeply/nested/prompt");
  }

  @Test
  public void validatePromptName_allowsMultipleDotsInName() {
    assertValidationPasses("a.b.c");
  }

  @Test
  public void validatePromptName_allowsComplexLegitimateNames() {
    String[] legitimateNames = {
      "simple",
      "my-prompt",
      "my_prompt",
      "a..b",
      "subdir/nested",
      "version..2",
      "a.b.c",
      "subdir/deeply/nested/prompt",
      "prompt-with-multiple.dots.v2",
      "underscore_name",
      "kebab-case-name",
      "CamelCase",
      "123numeric",
      "sub.dir/file.name",
      "a:b", // Colon NOT followed by drive letter pattern - should be allowed
      "time:12:30",
      "label:value",
    };

    for (String name : legitimateNames) {
      assertValidationPasses(name);
    }
  }

  @Test
  public void validatePromptName_rejectsAllMaliciousPatterns() {
    String[] maliciousNames = {
      "../../../etc/passwd",
      "/absolute/path.attack",
      "subdir/../../../escape",
      "..",
      ".../...",
      "./../../etc/passwd",
      "normal/../../../escape",
      "../sibling",
      "....//etc/passwd",
      "..\\windows\\system32",
      "%2e%2e/%2e%2e",
      "..\\../etc",
      "/etc/passwd",
      "C:/Windows/System32",
      "\\\\network\\share",
      "./..",
      // Null byte injection attacks
      "safe..\\0../etc/passwd",
      "prompt\\0.trigger",
      "a\\0../escape",
    };

    for (String name : maliciousNames) {
      assertValidationThrows(name);
    }
  }

  // ========== HELPER METHODS ==========

  /** Helper method to call validatePromptName via reflection. */
  private void validatePromptName(String name) {
    try {
      Method method = StoreUtils.class.getMethod("validatePromptName", String.class);
      method.invoke(null, name);
    } catch (NoSuchMethodException e) {
      fail(
          "validatePromptName method not found in StoreUtils. "
              + "This method must be implemented to prevent path traversal attacks.");
    } catch (ReflectiveOperationException e) {
      Throwable cause = e.getCause();
      if (cause instanceof IllegalArgumentException) {
        throw (IllegalArgumentException) cause;
      }
      throw new RuntimeException("Unexpected error calling validatePromptName", e);
    }
  }

  /** Assert that validation passes for the given name. */
  private void assertValidationPasses(String name) {
    try {
      validatePromptName(name);
    } catch (IllegalArgumentException e) {
      fail("Expected validation to pass for '" + name + "' but got: " + e.getMessage());
    }
  }

  /** Assert that validation throws for the given name. */
  private void assertValidationThrows(String name) {
    try {
      validatePromptName(name);
      fail("Expected validation to throw for '" + name + "'");
    } catch (IllegalArgumentException expected) {
      // Expected - validation worked
      String message = expected.getMessage().toLowerCase();
      boolean hasRelevantKeyword =
          message.contains("path")
              || message.contains("traversal")
              || message.contains("invalid")
              || message.contains("security")
              || message.contains("..");
      // Error message should mention path, traversal, or security
      assertThat(hasRelevantKeyword).isTrue();
    }
  }
}
