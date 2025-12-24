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
 * Metadata associated with a prompt definition.
 *
 * <p>This record contains all the configuration and metadata fields that can be specified in a
 * prompt's YAML frontmatter. It corresponds to the JS PromptMetadata interface.
 *
 * @param name The name of the prompt.
 * @param variant The variant name for the prompt.
 * @param version The version of the prompt.
 * @param description A description of the prompt.
 * @param model The name of the model to use (e.g., "vertexai/gemini-1.0-pro").
 * @param tools Names of tools (registered separately) to allow use of in this prompt.
 * @param toolDefs Definitions of tools to allow use of in this prompt.
 * @param config Model configuration. Not all models support all options.
 * @param input Configuration for input variables including defaults and schema.
 * @param output Defines the expected model output format and schema.
 * @param raw The raw frontmatter as parsed with no additional processing.
 * @param ext Extension fields gathered by namespace (fields containing a period).
 * @param metadata Arbitrary metadata for tooling or informational purposes.
 */
public record PromptMetadata(
    String name,
    String variant,
    String version,
    String description,
    String model,
    List<String> tools,
    List<ToolDefinition> toolDefs,
    Map<String, Object> config,
    InputConfig input,
    OutputConfig output,
    Map<String, Object> raw,
    Map<String, Map<String, Object>> ext,
    Map<String, Object> metadata) {

  /**
   * Configuration for input variables.
   *
   * @param defaultValues Default input variable values to use if none are provided.
   * @param schema Schema definition for input variables.
   */
  public record InputConfig(Map<String, Object> defaultValues, Map<String, Object> schema) {
    /** Alias for defaultValues to match JS naming. */
    public Map<String, Object> getDefault() {
      return defaultValues;
    }
  }

  /**
   * Configuration for output format.
   *
   * @param format Desired output format ("json", "text", or custom).
   * @param schema Schema defining the output structure.
   */
  public record OutputConfig(String format, Map<String, Object> schema) {}

  /** Creates empty metadata. */
  public PromptMetadata() {
    this(null, null, null, null, null, null, null, null, null, null, null, null, null);
  }

  /**
   * Creates metadata from a config map (typically from parsed frontmatter).
   *
   * @param config The configuration map.
   * @return A PromptMetadata instance.
   */
  @SuppressWarnings("unchecked")
  public static PromptMetadata fromConfig(Map<String, Object> config) {
    if (config == null || config.isEmpty()) {
      return new PromptMetadata();
    }

    String name = (String) config.get("name");
    String variant = (String) config.get("variant");
    String version = (String) config.get("version");
    String description = (String) config.get("description");
    String model = (String) config.get("model");
    List<String> tools = (List<String>) config.get("tools");
    List<ToolDefinition> toolDefs = null; // Would need conversion
    Map<String, Object> modelConfig = (Map<String, Object>) config.get("config");

    InputConfig input = null;
    Map<String, Object> inputMap = (Map<String, Object>) config.get("input");
    if (inputMap != null) {
      input =
          new InputConfig(
              (Map<String, Object>) inputMap.get("default"),
              (Map<String, Object>) inputMap.get("schema"));
    }

    OutputConfig output = null;
    Map<String, Object> outputMap = (Map<String, Object>) config.get("output");
    if (outputMap != null) {
      output =
          new OutputConfig(
              (String) outputMap.get("format"), (Map<String, Object>) outputMap.get("schema"));
    }

    Map<String, Object> raw = (Map<String, Object>) config.get("raw");
    Map<String, Map<String, Object>> ext =
        (Map<String, Map<String, Object>>) config.get("ext");
    Map<String, Object> metadata = (Map<String, Object>) config.get("metadata");

    return new PromptMetadata(
        name,
        variant,
        version,
        description,
        model,
        tools,
        toolDefs,
        modelConfig,
        input,
        output,
        raw,
        ext,
        metadata);
  }
}
