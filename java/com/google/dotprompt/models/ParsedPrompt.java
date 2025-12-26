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

import java.util.List;
import java.util.Map;

/**
 * Represents a prompt after parsing its metadata and template.
 *
 * <p>This record extends the concept of {@link PromptMetadata} by adding the template string with
 * frontmatter removed. It corresponds to the TypeScript {@code ParsedPrompt} interface.
 *
 * <p>Example:
 *
 * <pre>{@code
 * String source = """
 *     ---
 *     model: gemini-1.5-pro
 *     config:
 *       temperature: 0.7
 *     ---
 *     Hello {{name}}!
 *     """;
 * ParsedPrompt parsed = Parser.parseDocument(source);
 * // parsed.template() -> "Hello {{name}}!"
 * // parsed.model() -> "gemini-1.5-pro"
 * }</pre>
 *
 * @param template The source of the template with metadata/frontmatter already removed.
 * @param name The name of the prompt.
 * @param variant The variant name for the prompt.
 * @param version The version of the prompt.
 * @param description A description of the prompt.
 * @param model The name of the model to use.
 * @param tools Names of tools to allow use of in this prompt.
 * @param toolDefs Definitions of tools to allow use of in this prompt.
 * @param config Model configuration.
 * @param input Configuration for input variables.
 * @param output Configuration for output format.
 * @param raw The raw frontmatter as parsed.
 * @param ext Extension fields gathered by namespace.
 * @param metadata Arbitrary metadata.
 */
public record ParsedPrompt(
    String template,
    String name,
    String variant,
    String version,
    String description,
    String model,
    List<String> tools,
    List<ToolDefinition> toolDefs,
    Map<String, Object> config,
    PromptMetadata.InputConfig input,
    PromptMetadata.OutputConfig output,
    Map<String, Object> raw,
    Map<String, Map<String, Object>> ext,
    Map<String, Object> metadata) {

  /**
   * Creates a ParsedPrompt with just a template and no metadata.
   *
   * @param template The template string.
   */
  public ParsedPrompt(String template) {
    this(template, null, null, null, null, null, null, null, null, null, null, null, null, null);
  }

  /**
   * Creates a ParsedPrompt from a template and PromptMetadata.
   *
   * @param template The template string (frontmatter removed).
   * @param metadata The parsed metadata.
   * @return A new ParsedPrompt instance.
   */
  public static ParsedPrompt fromMetadata(String template, PromptMetadata metadata) {
    if (metadata == null) {
      return new ParsedPrompt(template);
    }
    return new ParsedPrompt(
        template,
        metadata.name(),
        metadata.variant(),
        metadata.version(),
        metadata.description(),
        metadata.model(),
        metadata.tools(),
        metadata.toolDefs(),
        metadata.config(),
        metadata.input(),
        metadata.output(),
        metadata.raw(),
        metadata.ext(),
        metadata.metadata());
  }

  /**
   * Converts this ParsedPrompt to a PromptMetadata (without the template).
   *
   * @return A PromptMetadata instance with the same metadata fields.
   */
  public PromptMetadata toMetadata() {
    return new PromptMetadata(
        name,
        variant,
        version,
        description,
        model,
        tools,
        toolDefs,
        config,
        input,
        output,
        raw,
        ext,
        metadata);
  }
}
