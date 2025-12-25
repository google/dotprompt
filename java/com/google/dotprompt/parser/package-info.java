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
 * Parsing utilities for Dotprompt templates and Picoschema definitions.
 *
 * <p>This package provides the core parsing functionality for Dotprompt, including YAML frontmatter
 * extraction, template body parsing, Picoschema-to-JSON-Schema conversion, and rendered string
 * processing into structured messages.
 *
 * <h2>Parsing Pipeline</h2>
 *
 * <pre>
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │                      PROMPT SOURCE FILE                             │
 *  │  ---                                                                │
 *  │  model: gemini-pro                                                  │
 *  │  input:                                                             │
 *  │    schema:                                                          │
 *  │      name: string                                                   │
 *  │  ---                                                                │
 *  │  Hello {{name}}!                                                    │
 *  └─────────────────────────────────────────────────────────────────────┘
 *                                    │
 *                                    ▼
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │                   Parser.parse(source)                              │
 *  │                                                                     │
 *  │   1. Extract YAML frontmatter  ───▶  config map                     │
 *  │   2. Extract template body     ───▶  template string                │
 *  │   3. Convert Picoschema        ───▶  JSON Schema (if present)       │
 *  └─────────────────────────────────────────────────────────────────────┘
 *                                    │
 *                                    ▼
 *  ┌─────────────────────────────────────────────────────────────────────┐
 *  │                        Prompt                                       │
 *  │   template: "Hello {{name}}!"                                       │
 *  │   config: {model: "gemini-pro", input: {schema: {...}}}             │
 *  └─────────────────────────────────────────────────────────────────────┘
 * </pre>
 *
 * <h2>Key Components</h2>
 *
 * <h3>Parser</h3>
 *
 * <p>The {@link com.google.dotprompt.parser.Parser} class provides:
 *
 * <ul>
 *   <li>{@code parse(source)} - Parse a prompt source into a {@link
 *       com.google.dotprompt.models.Prompt}
 *   <li>{@code toMessages(rendered, data)} - Convert rendered template to messages
 *   <li>{@code transformMessagesToHistory(messages)} - Add history metadata to messages
 * </ul>
 *
 * <h3>Picoschema</h3>
 *
 * <p>The {@link com.google.dotprompt.parser.Picoschema} class converts the compact Picoschema
 * format to full JSON Schema:
 *
 * <pre>
 *  Picoschema (compact)              JSON Schema (expanded)
 *  ─────────────────────             ─────────────────────────────
 *  name: string                 ───▶  {"type": "object",
 *  age?: integer                       "properties": {
 *  tags(array): string                   "name": {"type": "string"},
 *                                        "age": {"type": "integer"},
 *                                        "tags": {"type": "array",
 *                                                 "items": {"type": "string"}}
 *                                      },
 *                                      "required": ["name", "tags"]}
 * </pre>
 *
 * <h3>Marker Processing</h3>
 *
 * <p>Helpers emit special marker strings that the parser processes:
 *
 * <pre>
 *  ┌───────────────────────────┬────────────────────────────────────┐
 *  │ Marker                    │ Effect                             │
 *  ├───────────────────────────┼────────────────────────────────────┤
 *  │ &lt;&lt;&lt;dotprompt:role:X&gt;&gt;&gt;   │ Start new message with role X      │
 *  │ &lt;&lt;&lt;dotprompt:history&gt;&gt;&gt;  │ Insert history messages            │
 *  │ &lt;&lt;&lt;dotprompt:media:url X&gt;&gt;&gt; │ Insert media part                │
 *  │ &lt;&lt;&lt;dotprompt:section X&gt;&gt;&gt;│ Create named section               │
 *  └───────────────────────────┴────────────────────────────────────┘
 * </pre>
 *
 * <h2>Usage Example</h2>
 *
 * <pre>{@code
 * // Parse a prompt from source
 * String source = "---\nmodel: gemini-pro\n---\nHello {{name}}!";
 * Prompt prompt = Parser.parse(source);
 *
 * // Convert Picoschema to JSON Schema
 * Map<String, Object> picoschema = Map.of("name", "string", "age?", "integer");
 * Map<String, Object> jsonSchema = Picoschema.picoschemaToJsonSchema(picoschema, null);
 * }</pre>
 *
 * @see com.google.dotprompt.parser.Parser
 * @see com.google.dotprompt.parser.Picoschema
 */
package com.google.dotprompt.parser;
