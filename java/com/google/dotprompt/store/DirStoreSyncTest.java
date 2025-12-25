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

import com.google.dotprompt.models.DeletePromptOrPartialOptions;
import com.google.dotprompt.models.LoadPromptOptions;
import com.google.dotprompt.models.PaginatedPartials;
import com.google.dotprompt.models.PaginatedPrompts;
import com.google.dotprompt.models.PromptData;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for {@link DirStoreSync}. */
@RunWith(JUnit4.class)
public class DirStoreSyncTest {

  @Rule public TemporaryFolder tempFolder = new TemporaryFolder();

  private Path baseDir;
  private DirStoreSync store;

  @Before
  public void setUp() throws IOException {
    baseDir = tempFolder.newFolder("prompts").toPath();
    store = new DirStoreSync(new DirStoreOptions(baseDir));
  }

  @Test
  public void list_shouldReturnEmptyForEmptyDirectory() {
    PaginatedPrompts result = store.list(null);

    assertThat(result.prompts()).isEmpty();
    assertThat(result.cursor()).isNull();
  }

  @Test
  public void list_shouldReturnPromptsExcludingPartials() throws IOException {
    Files.writeString(baseDir.resolve("greet.prompt"), "Hello", StandardCharsets.UTF_8);
    Files.writeString(baseDir.resolve("goodbye.prompt"), "Bye", StandardCharsets.UTF_8);
    Files.writeString(baseDir.resolve("_header.prompt"), "Partial", StandardCharsets.UTF_8);

    PaginatedPrompts result = store.list(null);

    assertThat(result.prompts()).hasSize(2);
    assertThat(result.prompts().stream().map(p -> p.name())).containsExactly("greet", "goodbye");
  }

  @Test
  public void list_shouldIncludeVersions() throws IOException {
    Files.writeString(baseDir.resolve("greet.prompt"), "Hello", StandardCharsets.UTF_8);

    PaginatedPrompts result = store.list(null);

    assertThat(result.prompts().get(0).version()).isNotNull();
    assertThat(result.prompts().get(0).version()).hasLength(8);
  }

  @Test
  public void list_shouldHandleVariants() throws IOException {
    Files.writeString(
        baseDir.resolve("greet.formal.prompt"), "Formal greeting", StandardCharsets.UTF_8);

    PaginatedPrompts result = store.list(null);

    assertThat(result.prompts()).hasSize(1);
    assertThat(result.prompts().get(0).name()).isEqualTo("greet");
    assertThat(result.prompts().get(0).variant()).isEqualTo("formal");
  }

  @Test
  public void listPartials_shouldReturnOnlyPartials() throws IOException {
    Files.writeString(baseDir.resolve("greet.prompt"), "Hello", StandardCharsets.UTF_8);
    Files.writeString(baseDir.resolve("_header.prompt"), "Header", StandardCharsets.UTF_8);
    Files.writeString(
        baseDir.resolve("_footer.dark.prompt"), "Dark Footer", StandardCharsets.UTF_8);

    PaginatedPartials result = store.listPartials(null);

    assertThat(result.partials()).hasSize(2);
    assertThat(result.partials().stream().map(p -> p.name())).containsExactly("header", "footer");
  }

  @Test
  public void load_shouldLoadPromptContent() throws IOException {
    String content = "---\nmodel: gemini\n---\nHello {{name}}";
    Files.writeString(baseDir.resolve("greet.prompt"), content, StandardCharsets.UTF_8);

    PromptData result = store.load("greet", null);

    assertThat(result.name()).isEqualTo("greet");
    assertThat(result.source()).isEqualTo(content);
    assertThat(result.variant()).isNull();
    assertThat(result.version()).isNotNull();
  }

  @Test
  public void load_shouldLoadPromptWithVariant() throws IOException {
    String content = "Formal greeting";
    Files.writeString(baseDir.resolve("greet.formal.prompt"), content, StandardCharsets.UTF_8);

    PromptData result = store.load("greet", new LoadPromptOptions("formal", null));

    assertThat(result.name()).isEqualTo("greet");
    assertThat(result.variant()).isEqualTo("formal");
    assertThat(result.source()).isEqualTo(content);
  }

  @Test
  public void load_shouldVerifyVersionIfProvided() throws IOException {
    String content = "Hello";
    Files.writeString(baseDir.resolve("greet.prompt"), content, StandardCharsets.UTF_8);
    String expectedVersion = StoreUtils.calculateVersion(content);

    PromptData result = store.load("greet", new LoadPromptOptions(null, expectedVersion));

    assertThat(result.version()).isEqualTo(expectedVersion);
  }

  @Test(expected = IllegalArgumentException.class)
  public void load_shouldThrowOnVersionMismatch() throws IOException {
    Files.writeString(baseDir.resolve("greet.prompt"), "Hello", StandardCharsets.UTF_8);

    store.load("greet", new LoadPromptOptions(null, "badversion"));
  }

  @Test(expected = UncheckedIOException.class)
  public void load_shouldThrowForNonexistentPrompt() {
    store.load("nonexistent", null);
  }

  @Test
  public void loadPartial_shouldLoadPartialContent() throws IOException {
    String content = "Header content";
    Files.writeString(baseDir.resolve("_header.prompt"), content, StandardCharsets.UTF_8);

    PromptData result = store.loadPartial("header", null);

    assertThat(result.name()).isEqualTo("header");
    assertThat(result.source()).isEqualTo(content);
  }

  @Test
  public void save_shouldWritePromptToFile() throws IOException {
    PromptData prompt = new PromptData("greet", null, null, "Hello {{name}}");

    store.save(prompt);

    Path file = baseDir.resolve("greet.prompt");
    assertThat(Files.exists(file)).isTrue();
    assertThat(Files.readString(file, StandardCharsets.UTF_8)).isEqualTo("Hello {{name}}");
  }

  @Test
  public void save_shouldWritePromptWithVariant() throws IOException {
    PromptData prompt = new PromptData("greet", "formal", null, "Formal greeting");

    store.save(prompt);

    Path file = baseDir.resolve("greet.formal.prompt");
    assertThat(Files.exists(file)).isTrue();
    assertThat(Files.readString(file, StandardCharsets.UTF_8)).isEqualTo("Formal greeting");
  }

  @Test
  public void save_shouldWritePartial() throws IOException {
    PromptData prompt = new PromptData("_header", null, null, "Header content");

    store.save(prompt);

    Path file = baseDir.resolve("_header.prompt");
    assertThat(Files.exists(file)).isTrue();
  }

  @Test
  public void save_shouldCreateSubdirectories() throws IOException {
    PromptData prompt = new PromptData("group/greet", null, null, "Hello");

    store.save(prompt);

    Path file = baseDir.resolve("group/greet.prompt");
    assertThat(Files.exists(file)).isTrue();
  }

  @Test(expected = IllegalArgumentException.class)
  public void save_shouldThrowForMissingName() {
    store.save(new PromptData(null, null, null, "content"));
  }

  @Test(expected = IllegalArgumentException.class)
  public void save_shouldThrowForMissingSource() {
    store.save(new PromptData("greet", null, null, null));
  }

  @Test
  public void delete_shouldDeletePromptFile() throws IOException {
    Path file = baseDir.resolve("greet.prompt");
    Files.writeString(file, "Hello", StandardCharsets.UTF_8);
    assertThat(Files.exists(file)).isTrue();

    store.delete("greet", null);

    assertThat(Files.exists(file)).isFalse();
  }

  @Test
  public void delete_shouldDeletePromptWithVariant() throws IOException {
    Path file = baseDir.resolve("greet.formal.prompt");
    Files.writeString(file, "Formal", StandardCharsets.UTF_8);

    store.delete("greet", new DeletePromptOrPartialOptions("formal"));

    assertThat(Files.exists(file)).isFalse();
  }

  @Test
  public void delete_shouldDeletePartialIfPromptNotFound() throws IOException {
    Path file = baseDir.resolve("_header.prompt");
    Files.writeString(file, "Header", StandardCharsets.UTF_8);

    store.delete("header", null);

    assertThat(Files.exists(file)).isFalse();
  }

  @Test(expected = UncheckedIOException.class)
  public void delete_shouldThrowForNonexistentFile() {
    store.delete("nonexistent", null);
  }
}
