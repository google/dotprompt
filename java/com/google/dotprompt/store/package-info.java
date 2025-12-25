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

/**
 * Prompt storage and retrieval implementations for Dotprompt.
 *
 * <p>This package provides interfaces and implementations for storing, retrieving, and managing
 * prompt templates and partials. A prompt store is responsible for persisting prompts and their
 * associated metadata, enabling prompt reuse across applications.
 *
 * <h2>Key Concepts</h2>
 *
 * <ul>
 *   <li><b>Prompts</b>: Template files containing prompt definitions with optional frontmatter
 *       configuration
 *   <li><b>Partials</b>: Reusable prompt fragments that can be included in other prompts using
 *       Handlebars partial syntax ({@code {{> partialName}}})
 *   <li><b>Variants</b>: Alternative versions of the same prompt (e.g., {@code greeting.formal} vs
 *       {@code greeting.casual})
 *   <li><b>Versions</b>: Content-based hashes (SHA-1) for tracking prompt changes
 * </ul>
 *
 * <h2>Architecture</h2>
 *
 * <p>The package follows a layered interface design:
 *
 * <pre>
 *                    ┌─────────────────────────────────────┐
 *                    │      PromptStoreWritable            │
 *                    │  (async: save, delete + read ops)   │
 *                    └─────────────────┬───────────────────┘
 *                                      │ extends
 *                    ┌─────────────────▼───────────────────┐
 *                    │         PromptStore                 │
 *                    │  (async: list, listPartials,        │
 *                    │          load, loadPartial)         │
 *                    └─────────────────────────────────────┘
 *
 *                    ┌─────────────────────────────────────┐
 *                    │    PromptStoreWritableSync          │
 *                    │  (sync: save, delete + read ops)    │
 *                    └─────────────────┬───────────────────┘
 *                                      │ extends
 *                    ┌─────────────────▼───────────────────┐
 *                    │       PromptStoreSync               │
 *                    │  (sync: list, listPartials,         │
 *                    │         load, loadPartial)          │
 *                    └─────────────────────────────────────┘
 * </pre>
 *
 * <h2>Available Implementations</h2>
 *
 * <ul>
 *   <li>{@link com.google.dotprompt.store.DirStore}: Asynchronous filesystem-based store using
 *       {@link java.util.concurrent.CompletableFuture}
 *   <li>{@link com.google.dotprompt.store.DirStoreSync}: Synchronous filesystem-based store for
 *       blocking operations
 * </ul>
 *
 * <h2>File Naming Conventions</h2>
 *
 * <p>Directory-based stores organize prompts using the following conventions:
 *
 * <ul>
 *   <li>Prompts: {@code [name].prompt} or {@code [name].[variant].prompt}
 *   <li>Partials: {@code _[name].prompt} or {@code _[name].[variant].prompt}
 *   <li>Directory structure forms part of the prompt/partial name (e.g., {@code group/greeting})
 * </ul>
 *
 * <h2>Usage Examples</h2>
 *
 * <h3>Async Usage (DirStore)</h3>
 *
 * <pre>{@code
 * // Create a store
 * DirStore store = new DirStore(DirStoreOptions.of("/path/to/prompts"));
 *
 * // List all prompts
 * store.list(null).thenAccept(result -> {
 *     result.prompts().forEach(p ->
 *         System.out.println(p.name() + " v" + p.version())
 *     );
 * });
 *
 * // Load a prompt
 * PromptData data = store.load("greeting", null).join();
 * System.out.println(data.source());
 *
 * // Load a variant
 * PromptData formal = store.load("greeting",
 *     new LoadPromptOptions("formal", null)).join();
 *
 * // Save a new prompt
 * store.save(new PromptData("welcome", null, null,
 *     "---\nmodel: gemini\n---\nHello {{name}}!")).join();
 *
 * // Delete a prompt
 * store.delete("old_prompt", null).join();
 * }</pre>
 *
 * <h3>Sync Usage (DirStoreSync)</h3>
 *
 * <pre>{@code
 * // Create a sync store
 * DirStoreSync store = new DirStoreSync(DirStoreOptions.of("/path/to/prompts"));
 *
 * // List all prompts
 * PaginatedPrompts result = store.list(null);
 * result.prompts().forEach(p -> System.out.println(p.name()));
 *
 * // Load a prompt
 * PromptData data = store.load("greeting", null);
 *
 * // Save a prompt
 * store.save(new PromptData("welcome", null, null, "Hello!"));
 * }</pre>
 *
 * <h2>Version Calculation</h2>
 *
 * <p>Versions are calculated as the first 8 characters of the SHA-1 hash of the prompt content.
 * This provides:
 *
 * <ul>
 *   <li>Deterministic versioning across all language implementations (Java, JS, Python)
 *   <li>Content-based change detection
 *   <li>Version verification on load to ensure content integrity
 * </ul>
 *
 * @see com.google.dotprompt.store.PromptStore
 * @see com.google.dotprompt.store.DirStore
 * @see com.google.dotprompt.store.DirStoreSync
 */
package com.google.dotprompt.store;
