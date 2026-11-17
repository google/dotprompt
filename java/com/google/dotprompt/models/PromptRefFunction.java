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

package com.google.dotprompt.models;

import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * A function that renders a prompt after loading it via a PromptRef.
 *
 * <p>This interface represents a prompt that is loaded dynamically from a store or registry using a
 * reference (name, variant, version) rather than being compiled from source directly.
 *
 * <h2>Usage Example</h2>
 *
 * <pre>{@code
 * // Create a reference function
 * PromptRef ref = new PromptRef("greeting", "formal", null);
 * PromptRefFunction fn = dotprompt.loadRef(ref);
 *
 * // Render the prompt
 * RenderedPrompt result = fn.render(new DataArgument(Map.of("name", "Alice"))).get();
 *
 * // Access the reference
 * PromptRef loadedRef = fn.getPromptRef();
 * }</pre>
 *
 * @see PromptRef
 * @see PromptFunction
 */
public interface PromptRefFunction {

  /**
   * Renders the referenced prompt with the provided data.
   *
   * <p>Template variables come only from {@link DataArgument#input()}, {@code @} data only from
   * {@link DataArgument#context()} and history only from {@link DataArgument#messages()}.
   *
   * @param data The data to use for rendering the template.
   * @return A future containing the rendered prompt.
   */
  CompletableFuture<RenderedPrompt> render(DataArgument data);

  /**
   * Renders the referenced prompt with the provided data and options.
   *
   * @param data The data to use for rendering the template.
   * @param options Additional options to merge into the render context.
   * @return A future containing the rendered prompt.
   */
  CompletableFuture<RenderedPrompt> render(DataArgument data, Map<String, Object> options);

  /**
   * Renders the referenced prompt with a single map of template variables.
   *
   * @param data Template variables. The reserved keys {@code "context"} and {@code "messages"} are
   *     also read as {@code @} data and conversation history.
   * @return A future containing the rendered prompt.
   * @deprecated Every key of {@code data} is a template variable, and the {@code "context"} and
   *     {@code "messages"} keys additionally set {@code @} data and history. If {@code data}
   *     contains user-controlled input, a user can inject a system turn, arbitrary media URLs or
   *     {@code @} data. Use {@link #render(DataArgument)}, which keeps these in separate fields.
   */
  @Deprecated
  CompletableFuture<RenderedPrompt> render(Map<String, Object> data);

  /**
   * Renders the referenced prompt with a single map of template variables and options.
   *
   * @param data Template variables. The reserved keys {@code "context"} and {@code "messages"} are
   *     also read as {@code @} data and conversation history.
   * @param options Additional options to merge into the render context.
   * @return A future containing the rendered prompt.
   * @deprecated See {@link #render(Map)}. Use {@link #render(DataArgument, Map)}.
   */
  @Deprecated
  CompletableFuture<RenderedPrompt> render(Map<String, Object> data, Map<String, Object> options);

  /**
   * Gets the prompt reference used to load this function.
   *
   * @return The PromptRef containing name, variant, and version.
   */
  PromptRef getPromptRef();
}
