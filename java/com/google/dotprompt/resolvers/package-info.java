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
 * Resolver interfaces for dynamic content loading in Dotprompt.
 *
 * <p>This package defines functional interfaces for resolving external resources during prompt
 * compilation and rendering. Resolvers enable dynamic loading of partials, schemas, and tools from
 * various sources such as databases, file systems, or remote APIs.
 *
 * <h2>Resolver Architecture</h2>
 *
 * <pre>
 *                           ┌─────────────────────┐
 *                           │     Dotprompt       │
 *                           │                     │
 *                           │  - partialResolver  │
 *                           │  - schemaResolver   │
 *                           │  - toolResolver     │
 *                           └─────────┬───────────┘
 *                                     │
 *          ┌──────────────────────────┼──────────────────────────┐
 *          │                          │                          │
 *          ▼                          ▼                          ▼
 *  ┌───────────────┐        ┌─────────────────┐        ┌─────────────────┐
 *  │PartialResolver│        │ SchemaResolver  │        │  ToolResolver   │
 *  │               │        │                 │        │                 │
 *  │ name ─▶ source│        │ name ─▶ schema  │        │ name ─▶ tool    │
 *  └───────┬───────┘        └────────┬────────┘        └────────┬────────┘
 *          │                         │                          │
 *          ▼                         ▼                          ▼
 *  ┌───────────────┐        ┌─────────────────┐        ┌─────────────────┐
 *  │  File System  │        │  Schema Store   │        │  Tool Registry  │
 *  │  Database     │        │  Database       │        │  API Gateway    │
 *  │  Remote API   │        │  Remote API     │        │  etc.           │
 *  └───────────────┘        └─────────────────┘        └─────────────────┘
 * </pre>
 *
 * <h2>Available Resolvers</h2>
 *
 * <pre>
 *  ┌────────────────────┬────────────────────────────────────────────────┐
 *  │ Resolver           │ Purpose                                        │
 *  ├────────────────────┼────────────────────────────────────────────────┤
 *  │ PartialResolver    │ Resolve partial templates by name              │
 *  │ SchemaResolver     │ Resolve JSON schemas by name                   │
 *  │ ToolResolver       │ Resolve tool definitions by name               │
 *  └────────────────────┴────────────────────────────────────────────────┘
 * </pre>
 *
 * <h2>PartialResolver</h2>
 *
 * <p>{@link com.google.dotprompt.resolvers.PartialResolver} resolves Handlebars partials by name.
 * When a template uses {@code {{> partialName}}}, the resolver fetches the partial source.
 *
 * <pre>{@code
 * PartialResolver resolver = name -> {
 *     // Load from database, file, etc.
 *     return loadPartialFromDatabase(name);
 * };
 * dotprompt.setPartialResolver(resolver);
 * }</pre>
 *
 * <h2>SchemaResolver</h2>
 *
 * <p>{@link com.google.dotprompt.resolvers.SchemaResolver} resolves JSON schema definitions by
 * name. Used when templates reference schemas like {@code input.schema: MySchema}.
 *
 * <pre>{@code
 * SchemaResolver resolver = name -> {
 *     return schemaRegistry.get(name);
 * };
 * dotprompt.setSchemaResolver(resolver);
 * }</pre>
 *
 * <h2>ToolResolver</h2>
 *
 * <p>{@link com.google.dotprompt.resolvers.ToolResolver} resolves tool definitions by name. Used
 * when templates specify tools for function calling.
 *
 * <pre>{@code
 * ToolResolver resolver = name -> {
 *     return toolRegistry.getDefinition(name);
 * };
 * dotprompt.setToolResolver(resolver);
 * }</pre>
 *
 * <h2>Async Support</h2>
 *
 * <p>All resolvers return {@link java.util.concurrent.CompletableFuture} to support asynchronous
 * loading from remote sources without blocking the rendering pipeline.
 *
 * @see com.google.dotprompt.resolvers.PartialResolver
 * @see com.google.dotprompt.resolvers.SchemaResolver
 * @see com.google.dotprompt.resolvers.ToolResolver
 */
package com.google.dotprompt.resolvers;
