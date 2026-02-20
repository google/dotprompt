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

import java.util.HashMap;
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
 * @param model The name of the model to use (e.g., "vertexai/gemini-3.0-pro").
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
  public record InputConfig(Map<String, Object> defaultValues, Object schema) {
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
  public record OutputConfig(String format, Object schema) {}

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
    List<ToolDefinition> toolDefs = null;
    Object toolDefsRaw = config.get("toolDefs");
    if (toolDefsRaw instanceof List) {
      toolDefs = (List<ToolDefinition>) toolDefsRaw;
    }
    Map<String, Object> modelConfig = (Map<String, Object>) config.get("config");

    InputConfig input = null;
    Object inputRaw = config.get("input");
    if (inputRaw instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> inputMap = (Map<String, Object>) inputRaw;
      // Schema can be a Map (JSON Schema) or other type (picoschema String)
      Object inputSchema = inputMap.get("schema");
      input = new InputConfig((Map<String, Object>) inputMap.get("default"), inputSchema);
    }

    OutputConfig output = null;
    Object outputRaw = config.get("output");
    if (outputRaw instanceof Map) {
      @SuppressWarnings("unchecked")
      Map<String, Object> outputMap = (Map<String, Object>) outputRaw;
      // Schema can be a Map (JSON Schema) or other type (picoschema String)
      Object outputSchema = outputMap.get("schema");
      output = new OutputConfig((String) outputMap.get("format"), outputSchema);
    }

    Map<String, Object> raw = (Map<String, Object>) config.get("raw");
    Map<String, Map<String, Object>> ext = (Map<String, Map<String, Object>>) config.get("ext");
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

  /**
   * Converts this metadata to a config map (inverse of fromConfig).
   *
   * <p>This is useful when the metadata needs to be passed to methods that accept Map-based
   * configuration, such as the internal renderMetadata implementation.
   *
   * @return A map representation of this metadata.
   */
  public Map<String, Object> toConfig() {
    Map<String, Object> map = new HashMap<>();

    if (name != null) map.put("name", name);
    if (variant != null) map.put("variant", variant);
    if (version != null) map.put("version", version);
    if (description != null) map.put("description", description);
    if (model != null) map.put("model", model);
    if (tools != null) map.put("tools", tools);
    if (toolDefs != null) map.put("toolDefs", toolDefs);
    if (config != null) map.put("config", config);

    if (input != null) {
      Map<String, Object> inputMap = new HashMap<>();
      if (input.defaultValues() != null) inputMap.put("default", input.defaultValues());
      if (input.schema() != null) inputMap.put("schema", input.schema());
      map.put("input", inputMap);
    }

    if (output != null) {
      Map<String, Object> outputMap = new HashMap<>();
      if (output.format() != null) outputMap.put("format", output.format());
      if (output.schema() != null) outputMap.put("schema", output.schema());
      map.put("output", outputMap);
    }

    if (raw != null) map.put("raw", raw);
    if (ext != null) map.put("ext", ext);
    if (metadata != null) map.put("metadata", metadata);

    return map;
  }
}
