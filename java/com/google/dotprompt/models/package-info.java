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
 * Data models for Dotprompt prompts, messages, and content parts.
 *
 * <p>This package contains the core data structures used throughout Dotprompt for representing
 * prompts, rendered messages, and their content. These models are designed to be immutable records
 * for thread-safety and ease of use.
 *
 * <h2>Type Hierarchy</h2>
 *
 * <pre>
 *                        ┌─────────────────────────┐
 *                        │         Part            │ (sealed interface)
 *                        │  Base for all content   │
 *                        └───────────┬─────────────┘
 *                                    │
 *        ┌───────────────┬───────────┼───────────┬─────────────────┐
 *        │               │           │           │                 │
 *        ▼               ▼           ▼           ▼                 ▼
 *  ┌──────────┐   ┌───────────┐ ┌──────────┐ ┌────────────┐ ┌────────────────┐
 *  │ TextPart │   │ MediaPart │ │ DataPart │ │ ToolRequest│ │ ToolResponse   │
 *  │          │   │           │ │          │ │ Part       │ │ Part           │
 *  └──────────┘   └───────────┘ └──────────┘ └────────────┘ └────────────────┘
 *       │               │            │             │               │
 *       │               ▼            │             │               │
 *       │        ┌───────────┐       │             │               │
 *       │        │MediaContent│      │             │               │
 *       │        │ url,      │       │             │               │
 *       │        │ contentType│      │             │               │
 *       │        └───────────┘       │             │               │
 *       │                            │             │               │
 *       └─────────────┬──────────────┴─────────────┴───────────────┘
 *                     │
 *                     ▼
 *               ┌──────────┐
 *               │ Message  │ (role + List&lt;Part&gt; + metadata)
 *               └────┬─────┘
 *                    │
 *                    ▼
 *            ┌───────────────┐
 *            │RenderedPrompt│ (config + List&lt;Message&gt;)
 *            └───────────────┘
 * </pre>
 *
 * <h2>Core Types</h2>
 *
 * <h3>Content Parts</h3>
 *
 * <ul>
 *   <li>{@link com.google.dotprompt.models.TextPart} - Plain text content
 *   <li>{@link com.google.dotprompt.models.MediaPart} - Images, audio, video via URL
 *   <li>{@link com.google.dotprompt.models.DataPart} - Structured data (JSON)
 *   <li>{@link com.google.dotprompt.models.ToolRequestPart} - Tool/function call requests
 *   <li>{@link com.google.dotprompt.models.ToolResponsePart} - Tool/function call responses
 * </ul>
 *
 * <h3>Messages and Prompts</h3>
 *
 * <ul>
 *   <li>{@link com.google.dotprompt.models.Message} - A message with role, parts, and metadata
 *   <li>{@link com.google.dotprompt.models.Prompt} - Parsed template with config
 *   <li>{@link com.google.dotprompt.models.RenderedPrompt} - Fully rendered prompt ready for LLM
 *   <li>{@link com.google.dotprompt.models.PromptFunction} - Compiled prompt for repeated use
 * </ul>
 *
 * <h3>Storage Types</h3>
 *
 * <ul>
 *   <li>{@link com.google.dotprompt.models.PromptData} - Raw prompt data from storage
 *   <li>{@link com.google.dotprompt.models.PromptRef} - Reference to a stored prompt
 *   <li>{@link com.google.dotprompt.models.PartialData} - Raw partial data
 *   <li>{@link com.google.dotprompt.models.PartialRef} - Reference to a stored partial
 * </ul>
 *
 * <h3>Roles</h3>
 *
 * <p>The {@link com.google.dotprompt.models.Role} enum defines message roles:
 *
 * <pre>
 *  ┌────────┬────────────────────────────────────────────┐
 *  │ Role   │ Description                                │
 *  ├────────┼────────────────────────────────────────────┤
 *  │ USER   │ Input from the user                        │
 *  │ MODEL  │ Output from the AI model                   │
 *  │ SYSTEM │ System instructions                        │
 *  │ TOOL   │ Tool/function call responses               │
 *  └────────┴────────────────────────────────────────────┘
 * </pre>
 *
 * <h2>Usage Example</h2>
 *
 * <pre>{@code
 * // Create a message with mixed content
 * Message message = new Message(
 *     Role.USER,
 *     List.of(
 *         new TextPart("Describe this image:"),
 *         new MediaPart(new MediaContent("https://example.com/photo.jpg", "image/jpeg"))
 *     ),
 *     Map.of()
 * );
 *
 * // Work with a rendered prompt
 * RenderedPrompt rendered = promptFn.render(data).get();
 * for (Message msg : rendered.messages()) {
 *     System.out.println(msg.role() + ": " + msg.content());
 * }
 * }</pre>
 *
 * @see com.google.dotprompt.models.Part
 * @see com.google.dotprompt.models.Message
 * @see com.google.dotprompt.models.RenderedPrompt
 */
package com.google.dotprompt.models;
