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

import com.google.dotprompt.models.ToolDefinition;
import java.util.concurrent.CompletableFuture;

/**
 * Resolves a provided tool name to an underlying {@link ToolDefinition}.
 *
 * <p>This is a functional interface that enables tool lookup during prompt rendering.
 * Implementations can resolve tools from various sources such as in-memory registries, plugin
 * systems, or remote service catalogs.
 *
 * <p>The resolver is designed to be asynchronous to support non-blocking I/O when fetching tool
 * definitions from external sources.
 *
 * <h2>Usage Examples</h2>
 *
 * <h3>Synchronous resolver (wrapped):</h3>
 *
 * <pre>{@code
 * Map<String, ToolDefinition> tools = Map.of(
 *     "search", new ToolDefinition("search", "Search the web", inputSchema, null)
 * );
 * ToolResolver resolver = ToolResolver.fromSync(tools::get);
 * }</pre>
 *
 * <h3>Asynchronous resolver:</h3>
 *
 * <pre>{@code
 * ToolResolver resolver = toolName ->
 *     CompletableFuture.supplyAsync(() -> fetchToolFromRegistry(toolName));
 * }</pre>
 *
 * @see ToolDefinition
 * @see com.google.dotprompt.Dotprompt
 */
@FunctionalInterface
public interface ToolResolver {

  /**
   * Resolves a tool name asynchronously to its {@link ToolDefinition}.
   *
   * <p>Implementations should return a completed future containing the tool definition if found, or
   * {@code null} if the tool is not available.
   *
   * @param toolName The name of the tool to resolve (e.g., "search", "calculator").
   * @return A {@link CompletableFuture} containing the {@link ToolDefinition}, or {@code null} if
   *     the tool could not be found.
   */
  CompletableFuture<ToolDefinition> resolve(String toolName);

  /**
   * Creates an asynchronous resolver from a synchronous lookup function.
   *
   * <p>This factory method wraps a synchronous resolver function (such as a {@code Map::get} method
   * reference) into an asynchronous {@link ToolResolver}. The result is immediately completed,
   * making this suitable for in-memory tool registries.
   *
   * <p>Example:
   *
   * <pre>{@code
   * Map<String, ToolDefinition> tools = new HashMap<>();
   * tools.put("search", new ToolDefinition("search", "Search the web", ...));
   * ToolResolver resolver = ToolResolver.fromSync(tools::get);
   * }</pre>
   *
   * @param syncResolver A synchronous function that takes a tool name and returns the corresponding
   *     {@link ToolDefinition}, or {@code null}.
   * @return An async {@link ToolResolver} wrapping the synchronous function.
   */
  static ToolResolver fromSync(java.util.function.Function<String, ToolDefinition> syncResolver) {
    return toolName -> CompletableFuture.completedFuture(syncResolver.apply(toolName));
  }
}
