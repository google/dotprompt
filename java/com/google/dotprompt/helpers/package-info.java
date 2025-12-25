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
 * Handlebars helper functions for Dotprompt templates.
 *
 * <p>This package provides custom Handlebars helpers that enable rich template functionality in
 * Dotprompt. These helpers are automatically registered when creating a {@link
 * com.google.dotprompt.Dotprompt} instance.
 *
 * <h2>Available Helpers</h2>
 *
 * <pre>
 *  ┌──────────────────────────────────────────────────────────────────┐
 *  │                    Dotprompt Handlebars Helpers                  │
 *  ├──────────────┬───────────────────────────────────────────────────┤
 *  │ json         │ Serialize objects to JSON                         │
 *  │ role         │ Switch message role (user, model, system)         │
 *  │ history      │ Insert conversation history                       │
 *  │ section      │ Delineate named sections in output                │
 *  │ media        │ Embed media (images, audio, video)                │
 *  │ ifEquals     │ Conditional block if values are equal             │
 *  │ unlessEquals │ Conditional block unless values are equal         │
 *  └──────────────┴───────────────────────────────────────────────────┘
 * </pre>
 *
 * <h2>Helper Usage Examples</h2>
 *
 * <h3>json</h3>
 *
 * <p>Serializes any object to formatted JSON. Supports an optional {@code indent} parameter.
 *
 * <pre>{@code
 * {{json myObject}}
 * {{json myObject indent=2}}
 * }</pre>
 *
 * <h3>role</h3>
 *
 * <p>Switches the role for subsequent content. Valid roles: user, model, system.
 *
 * <pre>{@code
 * {{role "system"}}You are a helpful assistant.
 * {{role "user"}}Hello!
 * }</pre>
 *
 * <h3>history</h3>
 *
 * <p>Injects conversation history at this position. History messages are passed via the render
 * data.
 *
 * <pre>{@code
 * {{role "system"}}You are a helpful assistant.
 * {{history}}
 * {{role "user"}}{{userMessage}}
 * }</pre>
 *
 * <h3>section</h3>
 *
 * <p>Creates a named section marker for structured output parsing.
 *
 * <pre>{@code
 * {{section "introduction"}}
 * Welcome to the tutorial.
 * {{section "main"}}
 * Main content here.
 * }</pre>
 *
 * <h3>media</h3>
 *
 * <p>Embeds media content with a URL and optional content type.
 *
 * <pre>{@code
 * {{media url="https://example.com/image.png"}}
 * {{media url=imageUrl contentType="image/jpeg"}}
 * }</pre>
 *
 * <h3>ifEquals / unlessEquals</h3>
 *
 * <p>Conditional rendering based on equality comparison.
 *
 * <pre>{@code
 * {{#ifEquals status "active"}}
 *   User is active!
 * {{else}}
 *   User is inactive.
 * {{/ifEquals}}
 *
 * {{#unlessEquals role "guest"}}
 *   Welcome back, {{name}}!
 * {{/unlessEquals}}
 * }</pre>
 *
 * <h2>Implementation</h2>
 *
 * <p>All helpers output special marker strings that are parsed by {@link
 * com.google.dotprompt.parser.Parser} during rendering to produce structured {@link
 * com.google.dotprompt.models.Message} objects.
 *
 * <pre>
 *  Template                   Helpers                    Parser
 *  ┌────────────┐          ┌───────────┐          ┌──────────────────┐
 *  │ {{role     │ ──────▶  │ role()    │ ──────▶  │ Parser.parse()   │
 *  │ "system"}} │          │           │          │                  │
 *  │            │          │ Returns:  │          │ Produces:        │
 *  │            │          │ marker    │          │ Message[role=    │
 *  │            │          │ string    │          │   SYSTEM, ...]   │
 *  └────────────┘          └───────────┘          └──────────────────┘
 * </pre>
 *
 * @see com.google.dotprompt.helpers.Helpers
 * @see com.google.dotprompt.parser.Parser
 */
package com.google.dotprompt.helpers;
