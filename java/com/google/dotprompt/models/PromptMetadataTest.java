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

import static com.google.common.truth.Truth.assertThat;
import static org.junit.Assert.fail;

import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for PromptMetadata, particularly the validation layer in fromConfig(). */
@RunWith(JUnit4.class)
public class PromptMetadataTest {

  // === Happy Path Tests ===

  @Test
  public void fromConfig_emptyConfig_returnsEmptyMetadata() {
    Map<String, Object> config = Map.of();

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.name()).isNull();
    assertThat(result.variant()).isNull();
    assertThat(result.version()).isNull();
    assertThat(result.description()).isNull();
    assertThat(result.model()).isNull();
    assertThat(result.tools()).isNull();
    assertThat(result.toolDefs()).isNull();
    assertThat(result.config()).isNull();
    assertThat(result.input()).isNull();
    assertThat(result.output()).isNull();
    assertThat(result.raw()).isNull();
    assertThat(result.ext()).isNull();
    assertThat(result.metadata()).isNull();
  }

  @Test
  public void fromConfig_nullConfig_returnsEmptyMetadata() {
    PromptMetadata result = PromptMetadata.fromConfig(null);

    assertThat(result.name()).isNull();
    assertThat(result.variant()).isNull();
  }

  @Test
  public void fromConfig_allStringFields_succeeds() {
    Map<String, Object> config =
        Map.of(
            "name", "test-prompt",
            "variant", "v2",
            "version", "1.0.0",
            "description", "A test prompt",
            "model", "gemini-1.5-pro");

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.name()).isEqualTo("test-prompt");
    assertThat(result.variant()).isEqualTo("v2");
    assertThat(result.version()).isEqualTo("1.0.0");
    assertThat(result.description()).isEqualTo("A test prompt");
    assertThat(result.model()).isEqualTo("gemini-1.5-pro");
  }

  @Test
  public void fromConfig_withToolsList_succeeds() {
    Map<String, Object> config = Map.of("tools", List.of("tool1", "tool2"));

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.tools()).containsExactly("tool1", "tool2");
  }

  @Test
  public void fromConfig_withToolDefsList_succeeds() {
    ToolDefinition toolDef = new ToolDefinition("test_tool", "description", null, null);
    Map<String, Object> config = Map.of("toolDefs", List.of(toolDef));

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.toolDefs()).hasSize(1);
    assertThat(result.toolDefs().get(0).name()).isEqualTo("test_tool");
  }

  @Test
  public void fromConfig_withConfigMap_succeeds() {
    Map<String, Object> modelConfig = Map.of("temperature", 0.7, "maxTokens", 100);
    Map<String, Object> config = Map.of("config", modelConfig);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.config()).containsEntry("temperature", 0.7);
    assertThat(result.config()).containsEntry("maxTokens", 100);
  }

  @Test
  public void fromConfig_withInputConfig_succeeds() {
    Map<String, Object> defaultValues = Map.of("foo", "bar");
    Map<String, Object> inputConfig = Map.of("default", defaultValues, "schema", "string");
    Map<String, Object> config = Map.of("input", inputConfig);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.input()).isNotNull();
    assertThat(result.input().defaultValues()).containsEntry("foo", "bar");
    assertThat(result.input().schema()).isEqualTo("string");
  }

  @Test
  public void fromConfig_withOutputConfig_succeeds() {
    Map<String, Object> outputConfig = Map.of("format", "json", "schema", "object");
    Map<String, Object> config = Map.of("output", outputConfig);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.output()).isNotNull();
    assertThat(result.output().format()).isEqualTo("json");
    assertThat(result.output().schema()).isEqualTo("object");
  }

  @Test
  public void fromConfig_withExtMap_succeeds() {
    Map<String, Object> nsMap = Map.of("key", "value");
    Map<String, Map<String, Object>> extMap = Map.of("vendor.namespace", nsMap);
    Map<String, Object> config = Map.of("ext", extMap);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.ext()).isNotNull();
    assertThat(result.ext()).containsKey("vendor.namespace");
  }

  @Test
  public void fromConfig_withMetadataMap_succeeds() {
    Map<String, Object> metadata = Map.of("author", "test", "tags", List.of("ai", "prod"));
    Map<String, Object> config = Map.of("metadata", metadata);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.metadata()).containsEntry("author", "test");
    assertThat(result.metadata()).containsEntry("tags", List.of("ai", "prod"));
  }

  @Test
  public void fromConfig_withRawMap_succeeds() {
    Map<String, Object> raw = Map.of("original", "value");
    Map<String, Object> config = Map.of("raw", raw);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.raw()).containsEntry("original", "value");
  }

  @Test
  public void inputConfig_getDefault_matchesDefaultValues() {
    Map<String, Object> defaultValues = Map.of("key", "value");
    PromptMetadata.InputConfig inputConfig = new PromptMetadata.InputConfig(defaultValues, null);

    assertThat(inputConfig.getDefault()).isSameAs(inputConfig.defaultValues());
    assertThat(inputConfig.getDefault()).containsEntry("key", "value");
  }

  @Test
  public void toConfig_convertsAllFieldsCorrectly() {
    PromptMetadata metadata =
        new PromptMetadata(
            "test-name",
            "variant",
            "1.0",
            "desc",
            "model",
            List.of("tool1"),
            null,
            Map.of("temp", 0.5),
            new PromptMetadata.InputConfig(Map.of("def", "val"), "schema"),
            new PromptMetadata.OutputConfig("json", null),
            Map.of("raw", "data"),
            Map.of("ext", Map.of("key", "val")),
            Map.of("meta", "data"));

    Map<String, Object> result = metadata.toConfig();

    assertThat(result).containsEntry("name", "test-name");
    assertThat(result).containsEntry("variant", "variant");
    assertThat(result).containsEntry("version", "1.0");
    assertThat(result).containsEntry("description", "desc");
    assertThat(result).containsEntry("model", "model");
    assertThat(result).containsEntry("tools", List.of("tool1"));
    assertThat(result).containsEntry("config", Map.of("temp", 0.5));
    assertThat(result).containsEntry("raw", Map.of("raw", "data"));
    assertThat(result).containsEntry("ext", Map.of("ext", Map.of("key", "val")));
    assertThat(result).containsEntry("metadata", Map.of("meta", "data"));
  }

  // === Type Validation Error Tests ===

  @Test
  public void fromConfig_nameIsInteger_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("name", 123);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'name' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("name");
      assertThat(e.getMessage()).contains("String");
      assertThat(e.getMessage()).contains("Integer");
    }
  }

  @Test
  public void fromConfig_variantIsList_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("variant", List.of("v1", "v2"));

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'variant' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("variant");
      assertThat(e.getMessage()).contains("String");
      assertThat(e.getMessage()).contains("List");
    }
  }

  @Test
  public void fromConfig_versionIsMap_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("version", Map.of("major", 1));

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'version' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("version");
      assertThat(e.getMessage()).contains("String");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  @Test
  public void fromConfig_descriptionIsBoolean_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("description", true);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'description' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("description");
      assertThat(e.getMessage()).contains("String");
      assertThat(e.getMessage()).contains("Boolean");
    }
  }

  @Test
  public void fromConfig_modelIsStringArray_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("model", new String[] {"gemini", "gpt"});

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'model' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("model");
      assertThat(e.getMessage()).contains("String");
    }
  }

  @Test
  public void fromConfig_toolsIsString_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("tools", "not-a-list");

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'tools' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("tools");
      assertThat(e.getMessage()).contains("List");
      assertThat(e.getMessage()).contains("String");
    }
  }

  @Test
  public void fromConfig_toolDefsIsString_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("toolDefs", "not-a-list");

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'toolDefs' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("toolDefs");
      assertThat(e.getMessage()).contains("List");
      assertThat(e.getMessage()).contains("String");
    }
  }

  @Test
  public void fromConfig_configIsString_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("config", "not-a-map");

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'config' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("config");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  @Test
  public void fromConfig_rawIsList_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("raw", List.of("item1", "item2"));

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'raw' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("raw");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  @Test
  public void fromConfig_metadataIsInteger_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("metadata", 42);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'metadata' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("metadata");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  @Test
  public void fromConfig_extIsString_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("ext", "not-a-map");

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'ext' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("ext");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  // === Nested Input Config Validation Tests ===

  @Test
  public void fromConfig_inputIsString_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("input", "not-a-map");

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'input' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("input");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  @Test
  public void fromConfig_inputDefaultIsString_throwsIllegalArgumentException() {
    Map<String, Object> inputConfig = Map.of("default", "not-a-map");
    Map<String, Object> config = Map.of("input", inputConfig);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'input.default' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("input.default");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  @Test
  public void fromConfig_inputDefaultIsList_throwsIllegalArgumentException() {
    Map<String, Object> inputConfig = Map.of("default", List.of("item1", "item2"));
    Map<String, Object> config = Map.of("input", inputConfig);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'input.default' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("input.default");
    }
  }

  @Test
  public void fromConfig_inputSchemaCanBeString() {
    Map<String, Object> inputConfig = Map.of("schema", "string");
    Map<String, Object> config = Map.of("input", inputConfig);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.input().schema()).isEqualTo("string");
  }

  @Test
  public void fromConfig_inputSchemaCanBeMap() {
    Map<String, Object> jsonSchema = Map.of("type", "object", "properties", Map.of());
    Map<String, Object> inputConfig = Map.of("schema", jsonSchema);
    Map<String, Object> config = Map.of("input", inputConfig);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.input().schema()).isInstanceOf(Map.class);
  }

  // === Nested Output Config Validation Tests ===

  @Test
  public void fromConfig_outputIsInteger_throwsIllegalArgumentException() {
    Map<String, Object> config = Map.of("output", 123);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'output' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("output");
      assertThat(e.getMessage()).contains("Map");
    }
  }

  @Test
  public void fromConfig_outputFormatIsInteger_throwsIllegalArgumentException() {
    Map<String, Object> outputConfig = Map.of("format", 123);
    Map<String, Object> config = Map.of("output", outputConfig);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'output.format' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("output.format");
      assertThat(e.getMessage()).contains("String");
    }
  }

  @Test
  public void fromConfig_outputFormatIsList_throwsIllegalArgumentException() {
    Map<String, Object> outputConfig = Map.of("format", List.of("json", "text"));
    Map<String, Object> config = Map.of("output", outputConfig);

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException for incorrect 'output.format' type");
    } catch (IllegalArgumentException e) {
      assertThat(e.getMessage()).contains("output.format");
    }
  }

  @Test
  public void fromConfig_outputSchemaCanBeString() {
    Map<String, Object> outputConfig = Map.of("schema", "string");
    Map<String, Object> config = Map.of("output", outputConfig);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.output().schema()).isEqualTo("string");
  }

  @Test
  public void fromConfig_outputSchemaCanBeMap() {
    Map<String, Object> jsonSchema = Map.of("type", "array", "items", Map.of("type", "string"));
    Map<String, Object> outputConfig = Map.of("schema", jsonSchema);
    Map<String, Object> config = Map.of("output", outputConfig);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.output().schema()).isInstanceOf(Map.class);
  }

  // === Edge Case Tests ===

  @Test
  public void fromConfig_nullFieldValues_succeeds() {
    Map<String, Object> config =
        Map.of(
            "name", null,
            "variant", null,
            "tools", null,
            "config", null);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.name()).isNull();
    assertThat(result.variant()).isNull();
    assertThat(result.tools()).isNull();
    assertThat(result.config()).isNull();
  }

  @Test
  public void fromConfig_emptyListsAndMaps_succeeds() {
    Map<String, Object> config =
        Map.of(
            "tools", List.of(),
            "config", Map.of(),
            "metadata", Map.of());

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.tools()).isEmpty();
    assertThat(result.config()).isEmpty();
    assertThat(result.metadata()).isEmpty();
  }

  @Test
  public void fromConfig_complexNestedStructure_succeeds() {
    Map<String, Object> inputDefault =
        Map.of("field1", "value1", "field2", Map.of("nested", "value2"));
    Map<String, Object> inputConfig =
        Map.of("default", inputDefault, "schema", Map.of("type", "object"));
    Map<String, Object> outputConfig =
        Map.of("format", "json", "schema", Map.of("type", "array"));
    Map<String, Object> modelConfig =
        Map.of("temperature", 0.7, "maxTokens", 1000, "topP", 0.9);
    Map<String, Object> extMap = Map.of("vendor.ext", Map.of("key", "value"));

    Map<String, Object> config =
        Map.of(
            "name",
            "complex-prompt",
            "model",
            "gemini-1.5-pro",
            "input",
            inputConfig,
            "output",
            outputConfig,
            "config",
            modelConfig,
            "ext",
            extMap);

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.name()).isEqualTo("complex-prompt");
    assertThat(result.input().defaultValues()).containsEntry("field1", "value1");
    assertThat(result.output().format()).isEqualTo("json");
    assertThat(result.config().get("temperature")).isEqualTo(0.7);
    assertThat(result.ext()).containsKey("vendor.ext");
  }

  @Test
  public void fromConfig_multipleErrors_reportsFirstError() {
    Map<String, Object> config =
        Map.of(
            "name", 123, // Wrong type
            "variant", List.of("v1"), // Wrong type
            "model", true // Wrong type
            );

    try {
      PromptMetadata.fromConfig(config);
      fail("Expected IllegalArgumentException");
    } catch (IllegalArgumentException e) {
      // Should report the first encountered error (name)
      assertThat(e.getMessage()).contains("name");
    }
  }

  @Test
  public void fromConfig_allowsEmptyStrings() {
    Map<String, Object> config =
        Map.of(
            "name", "",
            "description",
            "",
            "model",
            "");

    PromptMetadata result = PromptMetadata.fromConfig(config);

    assertThat(result.name()).isEmpty();
    assertThat(result.description()).isEmpty();
    assertThat(result.model()).isEmpty();
  }

  @Test
  public void noArgConstructor_createsEmptyMetadata() {
    PromptMetadata metadata = new PromptMetadata();

    assertThat(metadata.name()).isNull();
    assertThat(metadata.variant()).isNull();
    assertThat(metadata.version()).isNull();
    assertThat(metadata.description()).isNull();
    assertThat(metadata.model()).isNull();
    assertThat(metadata.tools()).isNull();
    assertThat(metadata.toolDefs()).isNull();
    assertThat(metadata.config()).isNull();
    assertThat(metadata.input()).isNull();
    assertThat(metadata.output()).isNull();
    assertThat(metadata.raw()).isNull();
    assertThat(metadata.ext()).isNull();
    assertThat(metadata.metadata()).isNull();
  }

  @Test
  public void inputConfig_noArgConstructor_createsNullFields() {
    PromptMetadata.InputConfig inputConfig = new PromptMetadata.InputConfig(null, null);

    assertThat(inputConfig.defaultValues()).isNull();
    assertThat(inputConfig.schema()).isNull();
  }

  @Test
  public void outputConfig_recordMethods_work() {
    PromptMetadata.OutputConfig outputConfig =
        new PromptMetadata.OutputConfig("json", Map.of("type", "object"));

    assertThat(outputConfig.format()).isEqualTo("json");
    assertThat(outputConfig.schema()).isInstanceOf(Map.class);
  }
}
