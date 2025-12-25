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

import com.google.dotprompt.models.PaginatedPrompts;
import com.google.dotprompt.models.PromptData;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.ExecutionException;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TemporaryFolder;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for {@link DirStore}. */
@RunWith(JUnit4.class)
public class DirStoreTest {

  @Rule public TemporaryFolder tempFolder = new TemporaryFolder();

  private Path baseDir;
  private DirStore store;

  @Before
  public void setUp() throws IOException {
    baseDir = tempFolder.newFolder("prompts").toPath();
    store = new DirStore(new DirStoreOptions(baseDir));
  }

  @Test
  public void list_shouldReturnFutureWithPrompts()
      throws IOException, ExecutionException, InterruptedException {
    Files.writeString(baseDir.resolve("greet.prompt"), "Hello", StandardCharsets.UTF_8);

    PaginatedPrompts result = store.list(null).get();

    assertThat(result.prompts()).hasSize(1);
    assertThat(result.prompts().get(0).name()).isEqualTo("greet");
  }

  @Test
  public void load_shouldReturnFutureWithPromptData()
      throws IOException, ExecutionException, InterruptedException {
    String content = "Hello {{name}}";
    Files.writeString(baseDir.resolve("greet.prompt"), content, StandardCharsets.UTF_8);

    PromptData result = store.load("greet", null).get();

    assertThat(result.name()).isEqualTo("greet");
    assertThat(result.source()).isEqualTo(content);
  }

  @Test
  public void save_shouldCompleteFutureAfterWriting()
      throws IOException, ExecutionException, InterruptedException {
    PromptData prompt = new PromptData("greet", null, null, "Hello");

    store.save(prompt).get();

    Path file = baseDir.resolve("greet.prompt");
    assertThat(Files.exists(file)).isTrue();
    assertThat(Files.readString(file, StandardCharsets.UTF_8)).isEqualTo("Hello");
  }

  @Test
  public void delete_shouldCompleteFutureAfterDeleting()
      throws IOException, ExecutionException, InterruptedException {
    Path file = baseDir.resolve("greet.prompt");
    Files.writeString(file, "Hello", StandardCharsets.UTF_8);

    store.delete("greet", null).get();

    assertThat(Files.exists(file)).isFalse();
  }

  @Test
  public void operations_shouldBeAsync() throws IOException {
    Files.writeString(baseDir.resolve("greet.prompt"), "Hello", StandardCharsets.UTF_8);

    // These should return immediately with CompletableFutures
    var listFuture = store.list(null);
    var loadFuture = store.load("greet", null);

    assertThat(listFuture).isNotNull();
    assertThat(loadFuture).isNotNull();

    // And the futures should complete with correct data
    assertThat(listFuture.join().prompts()).hasSize(1);
    assertThat(loadFuture.join().source()).isEqualTo("Hello");
  }
}
