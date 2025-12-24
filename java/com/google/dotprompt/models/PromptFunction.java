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
 * A compiled prompt function that can be reused for multiple renders.
 *
 * <p>This interface represents a pre-compiled template that can be rendered multiple times with
 * different data without re-parsing the template source. It matches the JS concept of
 * PromptFunction.
 *
 * <h2>Usage Example</h2>
 *
 * <pre>{@code
 * Dotprompt dotprompt = new Dotprompt(loader);
 * PromptFunction fn = dotprompt.compile("---\nmodel: gemini\n---\nHello {{name}}").get();
 *
 * // Render multiple times with different data
 * RenderedPrompt result1 = fn.render(Map.of("name", "Alice")).get();
 * RenderedPrompt result2 = fn.render(Map.of("name", "Bob")).get();
 * }</pre>
 *
 * @see com.google.dotprompt.Dotprompt#compile(String)
 */
public interface PromptFunction {

  /**
   * Renders the compiled prompt with the provided data.
   *
   * @param data The data to use for rendering the template.
   * @return A future containing the rendered prompt.
   */
  CompletableFuture<RenderedPrompt> render(Map<String, Object> data);

  /**
   * Renders the compiled prompt with the provided data and options.
   *
   * @param data The data to use for rendering the template.
   * @param options Additional options to merge into the render context.
   * @return A future containing the rendered prompt.
   */
  CompletableFuture<RenderedPrompt> render(Map<String, Object> data, Map<String, Object> options);

  /**
   * Gets the parsed prompt metadata from the compiled template.
   *
   * @return The parsed prompt containing the template and configuration.
   */
  Prompt getPrompt();
}
