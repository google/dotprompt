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
 * Dotprompt: A templating library for AI prompts.
 *
 * <p>Dotprompt provides a powerful, cross-language templating system for defining and rendering AI
 * prompts. It combines Handlebars templating with YAML frontmatter for configuration, enabling
 * structured, maintainable prompt definitions.
 *
 * <h2>Architecture Overview</h2>
 *
 * <pre>
 *                              ┌────────────────────────────────────────┐
 *                              │            Dotprompt                   │
 *                              │  Main entry point for the library      │
 *                              └─────────────────┬──────────────────────┘
 *                                                │
 *         ┌──────────────────┬───────────────────┼───────────────────┬──────────────────┐
 *         │                  │                   │                   │                  │
 *         ▼                  ▼                   ▼                   ▼                  ▼
 *  ┌─────────────┐   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐    ┌────────────┐
 *  │   parser    │   │   helpers   │     │   models    │     │  resolvers  │    │   store    │
 *  │             │   │             │     │             │     │             │    │            │
 *  │ Parser      │   │ Helpers     │     │ Message     │     │ Partial     │    │ DirStore   │
 *  │ Picoschema  │   │ (json,role, │     │ Part        │     │ Schema      │    │ PromptStore│
 *  │             │   │  media...)  │     │ Prompt      │     │ Tool        │    │            │
 *  └─────────────┘   └─────────────┘     │ Rendered    │     │ Resolver    │    └────────────┘
 *                                        │ Prompt      │     └─────────────┘
 *                                        └─────────────┘
 * </pre>
 *
 * <h2>Core Workflow</h2>
 *
 * <pre>
 *  1. DEFINE                 2. COMPILE                3. RENDER
 *  ┌──────────────┐         ┌──────────────┐          ┌──────────────┐
 *  │ ---          │         │ Dotprompt    │          │ PromptFn     │
 *  │ model: gemini│   ───▶  │   .compile() │   ───▶   │   .render()  │ ───▶ RenderedPrompt
 *  │ ---          │         │              │          │              │
 *  │ Hello {{x}}! │         └──────────────┘          └──────────────┘
 *  └──────────────┘
 * </pre>
 *
 * <h2>Quick Start</h2>
 *
 * <pre>{@code
 * // Create a Dotprompt instance
 * Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
 *
 * // Define a prompt template
 * String template = """
 *     ---
 *     model: gemini-2.5-pro
 *     ---
 *     Hello, {{name}}! How can I help you today?
 *     """;
 *
 * // Compile and render
 * PromptFunction promptFn = dotprompt.compile(template).get();
 * RenderedPrompt rendered = promptFn.render(Map.of("name", "World")).get();
 *
 * // Access rendered messages
 * for (Message message : rendered.messages()) {
 *     System.out.println(message.role() + ": " + message.content());
 * }
 * }</pre>
 *
 * <h2>Key Features</h2>
 *
 * <ul>
 *   <li><b>Handlebars templating</b> - Variables, partials, helpers, conditionals
 *   <li><b>YAML frontmatter</b> - Model configuration, input/output schemas
 *   <li><b>Picoschema</b> - Compact schema definitions that expand to JSON Schema
 *   <li><b>Built-in helpers</b> - json, role, history, section, media, ifEquals, unlessEquals
 *   <li><b>Cross-language parity</b> - Consistent API across JavaScript, Python, and Java
 * </ul>
 *
 * <h2>Packages</h2>
 *
 * <ul>
 *   <li>{@link com.google.dotprompt.helpers} - Handlebars helper functions
 *   <li>{@link com.google.dotprompt.models} - Data models for prompts and messages
 *   <li>{@link com.google.dotprompt.parser} - Template parsing and Picoschema conversion
 *   <li>{@link com.google.dotprompt.resolvers} - Dynamic content resolution interfaces
 *   <li>{@link com.google.dotprompt.store} - Prompt storage and loading
 * </ul>
 *
 * @see com.google.dotprompt.Dotprompt
 * @see com.google.dotprompt.models.PromptFunction
 * @see com.google.dotprompt.models.RenderedPrompt
 */
package com.google.dotprompt;
