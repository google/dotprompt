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

/**
 * Synchronous interface for reading prompts and partials from a store.
 *
 * <p>This is the synchronous counterpart to {@link PromptStore}. Use this interface when blocking
 * operations are acceptable and you don't need async handling.
 *
 * @see PromptStore
 * @see PromptStoreWritableSync
 */
public interface PromptStoreSync {

  /**
   * Lists prompts in the store.
   *
   * @param options Options for listing prompts.
   * @return The paginated results.
   */
  PaginatedPrompts list(ListPromptsOptions options);

  /**
   * Lists partials available in the store.
   *
   * @param options Options for listing partials.
   * @return The paginated results.
   */
  PaginatedPartials listPartials(ListPartialsOptions options);

  /**
   * Loads a prompt from the store.
   *
   * @param name The name of the prompt.
   * @param options Options for loading the prompt.
   * @return The prompt data.
   */
  PromptData load(String name, LoadPromptOptions options);

  /**
   * Loads a partial from the store.
   *
   * @param name The name of the partial.
   * @param options Options for loading the partial.
   * @return The prompt data representing the partial.
   */
  PromptData loadPartial(String name, LoadPartialOptions options);
}
