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

package com.google.dotprompt.resolvers;

import java.util.concurrent.CompletableFuture;

/**
 * Resolves a partial name to its template content.
 *
 * <p>This is a functional interface that enables dynamic partial loading during template
 * compilation. Implementations can resolve partials from various sources such as file systems,
 * databases, or remote APIs.
 *
 * <p>The resolver is designed to be asynchronous to support non-blocking I/O when fetching partial
 * content from external sources.
 *
 * <h2>Usage Examples</h2>
 *
 * <h3>Synchronous resolver (wrapped):</h3>
 *
 * <pre>{@code
 * Map<String, String> partials = Map.of(
 *     "header", "# Welcome {{name}}"
 * );
 * PartialResolver resolver = PartialResolver.fromSync(partials::get);
 * }</pre>
 *
 * <h3>Asynchronous resolver:</h3>
 *
 * <pre>{@code
 * PartialResolver resolver = partialName ->
 *     CompletableFuture.supplyAsync(() -> loadPartialFromFile(partialName));
 * }</pre>
 *
 * @see com.google.dotprompt.Dotprompt#setPartialResolver(PartialResolver)
 */
@FunctionalInterface
public interface PartialResolver {

  /**
   * Resolves a partial name asynchronously to its template content.
   *
   * <p>Implementations should return a completed future containing the partial template content if
   * found, or {@code null} if the partial is not available.
   *
   * @param partialName The name of the partial to resolve.
   * @return A {@link CompletableFuture} containing the template content as a String, or {@code
   *     null} if the partial could not be found.
   */
  CompletableFuture<String> resolve(String partialName);

  /**
   * Creates an asynchronous resolver from a synchronous lookup function.
   *
   * <p>This factory method wraps a synchronous resolver function (such as a {@code Map::get} method
   * reference) into an asynchronous {@link PartialResolver}. The result is immediately completed,
   * making this suitable for in-memory partial registries.
   *
   * <p>Example:
   *
   * <pre>{@code
   * Map<String, String> partials = new HashMap<>();
   * partials.put("header", "# Welcome {{name}}");
   * PartialResolver resolver = PartialResolver.fromSync(partials::get);
   * }</pre>
   *
   * @param syncResolver A synchronous function that takes a partial name and returns the
   *     corresponding template content, or {@code null}.
   * @return An async {@link PartialResolver} wrapping the synchronous function.
   */
  static PartialResolver fromSync(java.util.function.Function<String, String> syncResolver) {
    return partialName -> CompletableFuture.completedFuture(syncResolver.apply(partialName));
  }
}
