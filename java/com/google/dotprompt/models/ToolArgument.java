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

/**
 * Represents a tool argument which can be either a tool name (String) or a full ToolDefinition.
 *
 * <p>This sealed interface allows for flexible tool specification in prompts, where tools can be
 * referenced by name (for tools registered elsewhere) or defined inline.
 *
 * <h2>Usage Examples</h2>
 *
 * <pre>{@code
 * // Reference a tool by name
 * ToolArgument byName = new ToolArgument.ByName("search");
 *
 * // Define a tool inline
 * ToolArgument byDef = new ToolArgument.ByDefinition(
 *     new ToolDefinition("calculator", "Performs math", inputSchema, null)
 * );
 * }</pre>
 */
public sealed interface ToolArgument permits ToolArgument.ByName, ToolArgument.ByDefinition {

  /**
   * A tool argument specified by name only.
   *
   * @param name The name of the tool to reference.
   */
  record ByName(String name) implements ToolArgument {}

  /**
   * A tool argument specified with a full definition.
   *
   * @param definition The complete tool definition.
   */
  record ByDefinition(ToolDefinition definition) implements ToolArgument {}

  /**
   * Creates a ToolArgument from a tool name.
   *
   * @param name The name of the tool.
   * @return A ByName tool argument.
   */
  static ToolArgument of(String name) {
    return new ByName(name);
  }

  /**
   * Creates a ToolArgument from a tool definition.
   *
   * @param definition The tool definition.
   * @return A ByDefinition tool argument.
   */
  static ToolArgument of(ToolDefinition definition) {
    return new ByDefinition(definition);
  }
}
