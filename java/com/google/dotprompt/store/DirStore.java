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

import com.google.dotprompt.models.DeletePromptOrPartialOptions;
import com.google.dotprompt.models.ListPartialsOptions;
import com.google.dotprompt.models.ListPromptsOptions;
import com.google.dotprompt.models.LoadPartialOptions;
import com.google.dotprompt.models.LoadPromptOptions;
import com.google.dotprompt.models.PaginatedPartials;
import com.google.dotprompt.models.PaginatedPrompts;
import com.google.dotprompt.models.PromptData;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.ForkJoinPool;

/**
 * Asynchronous filesystem-based prompt store implementation.
 *
 * <p>Reads and writes prompts and partials from/to the local file system within a specified
 * directory using asynchronous operations backed by {@link CompletableFuture}.
 *
 * <h2>File Naming Conventions</h2>
 *
 * <ul>
 *   <li>Prompts: {@code [name][.variant].prompt}
 *   <li>Partials: {@code _[name][.variant].prompt}
 * </ul>
 *
 * <h2>Usage Example</h2>
 *
 * <pre>{@code
 * DirStore store = new DirStore(DirStoreOptions.of("/path/to/prompts"));
 *
 * // List prompts asynchronously
 * store.list(null).thenAccept(prompts -> {
 *     prompts.prompts().forEach(p -> System.out.println(p.name()));
 * });
 *
 * // Load a specific prompt
 * PromptData data = store.load("my_prompt", null).join();
 * }</pre>
 *
 * <p>This class wraps {@link DirStoreSync} to provide async operations. All operations are executed
 * on a configurable {@link Executor}.
 */
public class DirStore implements PromptStoreWritable {

  private final DirStoreSync syncStore;
  private final Executor executor;

  /**
   * Creates a new DirStore instance using the common ForkJoinPool.
   *
   * @param options Configuration options including the base directory.
   */
  public DirStore(DirStoreOptions options) {
    this(options, ForkJoinPool.commonPool());
  }

  /**
   * Creates a new DirStore instance with a custom executor.
   *
   * @param options Configuration options including the base directory.
   * @param executor The executor to use for async operations.
   */
  public DirStore(DirStoreOptions options, Executor executor) {
    this.syncStore = new DirStoreSync(options);
    this.executor = executor;
  }

  @Override
  public CompletableFuture<PaginatedPrompts> list(ListPromptsOptions options) {
    return CompletableFuture.supplyAsync(() -> syncStore.list(options), executor);
  }

  @Override
  public CompletableFuture<PaginatedPartials> listPartials(ListPartialsOptions options) {
    return CompletableFuture.supplyAsync(() -> syncStore.listPartials(options), executor);
  }

  @Override
  public CompletableFuture<PromptData> load(String name, LoadPromptOptions options) {
    return CompletableFuture.supplyAsync(() -> syncStore.load(name, options), executor);
  }

  @Override
  public CompletableFuture<PromptData> loadPartial(String name, LoadPartialOptions options) {
    return CompletableFuture.supplyAsync(() -> syncStore.loadPartial(name, options), executor);
  }

  @Override
  public CompletableFuture<Void> save(PromptData prompt) {
    return CompletableFuture.runAsync(() -> syncStore.save(prompt), executor);
  }

  @Override
  public CompletableFuture<Void> delete(String name, DeletePromptOrPartialOptions options) {
    return CompletableFuture.runAsync(() -> syncStore.delete(name, options), executor);
  }
}
