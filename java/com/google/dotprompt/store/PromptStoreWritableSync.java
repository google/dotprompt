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
import com.google.dotprompt.models.PromptData;

/**
 * Synchronous interface for reading, writing, and deleting prompts and partials.
 *
 * <p>This is the synchronous counterpart to {@link PromptStoreWritable}. Use this interface when
 * blocking operations are acceptable and you don't need async handling.
 *
 * @see PromptStoreWritable
 * @see PromptStoreSync
 */
public interface PromptStoreWritableSync extends PromptStoreSync {

  /**
   * Saves a prompt in the store.
   *
   * @param prompt The prompt data to save.
   */
  void save(PromptData prompt);

  /**
   * Deletes a prompt from the store.
   *
   * @param name The name of the prompt to delete.
   * @param options Options for deleting the prompt.
   */
  void delete(String name, DeletePromptOrPartialOptions options);
}
