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

import com.google.dotprompt.models.ListPartialsOptions;
import com.google.dotprompt.models.ListPromptsOptions;
import com.google.dotprompt.models.LoadPartialOptions;
import com.google.dotprompt.models.LoadPromptOptions;
import com.google.dotprompt.models.PaginatedPartials;
import com.google.dotprompt.models.PaginatedPrompts;
import com.google.dotprompt.models.PromptData;
import java.util.concurrent.CompletableFuture;

/**
 * Asynchronous interface for reading prompts and partials from a store.
 *
 * <p>A prompt store provides methods for listing and loading prompt templates and partials. Prompts
 * are template files containing prompt definitions with optional frontmatter configuration, while
 * partials are reusable fragments that can be included in prompts using Handlebars syntax.
 *
 * <p>All methods return {@link CompletableFuture} for non-blocking operations. For synchronous
 * access, use {@link PromptStoreSync} instead.
 *
 * <h2>Core Operations</h2>
 *
 * <ul>
 *   <li>{@link #list} - List all available prompts with their versions
 *   <li>{@link #listPartials} - List all available partials
 *   <li>{@link #load} - Load a specific prompt by name
 *   <li>{@link #loadPartial} - Load a specific partial by name
 * </ul>
 *
 * <h2>Implementations</h2>
 *
 * <ul>
 *   <li>{@link DirStore} - Filesystem-based implementation
 * </ul>
 *
 * @see PromptStoreSync for synchronous operations
 * @see PromptStoreWritable for write operations (save, delete)
 */
public interface PromptStore {
  /**
   * Lists prompts in the store.
   *
   * @param options Options for listing prompts.
   * @return A future containing the paginated results.
   */
  CompletableFuture<PaginatedPrompts> list(ListPromptsOptions options);

  /**
   * Lists partials available in the store.
   *
   * @param options Options for listing partials.
   * @return A future containing the paginated results.
   */
  CompletableFuture<PaginatedPartials> listPartials(ListPartialsOptions options);

  /**
   * Loads a prompt from the store.
   *
   * @param name The name of the prompt.
   * @param options Options for loading the prompt.
   * @return A future containing the prompt data.
   */
  CompletableFuture<PromptData> load(String name, LoadPromptOptions options);

  /**
   * Loads a partial from the store.
   *
   * @param name The name of the partial.
   * @param options Options for loading the partial.
   * @return A future containing the prompt data representing the partial.
   */
  CompletableFuture<PromptData> loadPartial(String name, LoadPartialOptions options);
}
