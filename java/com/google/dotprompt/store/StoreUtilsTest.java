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

import java.io.IOException;
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
}
