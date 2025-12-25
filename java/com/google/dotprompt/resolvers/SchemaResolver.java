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

import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.function.Function;

/**
 * Resolves a provided schema name to an underlying JSON schema.
 *
 * <p>This is a functional interface that enables schema lookup during Picoschema parsing.
 * Implementations can resolve schemas from various sources such as in-memory registries, remote
 * APIs, or databases.
 *
 * <p>The resolver is designed to be asynchronous to support non-blocking I/O when fetching schemas
 * from external sources.
 *
 * <h2>Usage Examples</h2>
 *
 * <h3>Synchronous resolver (wrapped):</h3>
 *
 * <pre>{@code
 * Map<String, Map<String, Object>> registry = Map.of(
 *     "User", Map.of("type", "object", "properties", Map.of(...))
 * );
 * SchemaResolver resolver = SchemaResolver.fromSync(registry::get);
 * }</pre>
 *
 * <h3>Asynchronous resolver:</h3>
 *
 * <pre>{@code
 * SchemaResolver resolver = schemaName ->
 *     CompletableFuture.supplyAsync(() -> fetchSchemaFromApi(schemaName));
 * }</pre>
 *
 * @see com.google.dotprompt.parser.Picoschema#parse(Object, SchemaResolver)
 */
@FunctionalInterface
public interface SchemaResolver {

  /**
   * Resolves a schema name asynchronously to its JSON Schema representation.
   *
   * <p>Implementations should return a completed future containing the schema if found, or {@code
   * null} if the schema is not available. The returned schema should be a valid JSON Schema
   * represented as a nested Map structure.
   *
   * @param schemaName The name of the schema to resolve (e.g., "User", "Address").
   * @return A {@link CompletableFuture} containing the JSON Schema as a Map, or {@code null} if the
   *     schema could not be found.
   */
  CompletableFuture<Map<String, Object>> resolve(String schemaName);

  /**
   * Creates an asynchronous resolver from a synchronous lookup function.
   *
   * <p>This factory method wraps a synchronous resolver function (such as a {@code Map::get} method
   * reference) into an asynchronous {@link SchemaResolver}. The result is immediately completed,
   * making this suitable for in-memory schema registries.
   *
   * <p>Example:
   *
   * <pre>{@code
   * Map<String, Map<String, Object>> schemas = new HashMap<>();
   * schemas.put("User", Map.of("type", "object", ...));
   * SchemaResolver resolver = SchemaResolver.fromSync(schemas::get);
   * }</pre>
   *
   * @param syncResolver A synchronous function that takes a schema name and returns the
   *     corresponding JSON Schema, or {@code null}.
   * @return An async {@link SchemaResolver} wrapping the synchronous function.
   */
  static SchemaResolver fromSync(Function<String, Map<String, Object>> syncResolver) {
    return schemaName -> CompletableFuture.completedFuture(syncResolver.apply(schemaName));
  }
}
