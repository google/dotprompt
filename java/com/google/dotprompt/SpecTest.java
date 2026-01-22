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

package com.google.dotprompt;

import static com.google.common.truth.Truth.assertThat;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.PromptFunction;
import com.google.dotprompt.models.PromptMetadata;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.TextPart;
import java.io.File;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/**
 * Spec-based tests for Dotprompt.
 *
 * <p>Each test target runs a single YAML spec file specified via the {@code spec.file} system
 * property. This allows Bazel to report pass/fail status for each spec file individually.
 */
@RunWith(JUnit4.class)
public class SpecTest {

  /** Object mapper for parsing YAML spec files. */
  private final ObjectMapper mapper = new ObjectMapper(new YAMLFactory());

  @Test
  public void runSpec() throws Exception {
    String specFilePath = System.getProperty("spec.file");
    if (specFilePath == null || specFilePath.isEmpty()) {
      throw new IllegalStateException(
          "spec.file system property is required. "
              + "Run via Bazel: bazel test //java/com/google/dotprompt:SpecTest_metadata");
    }

    File specFile = new File(specFilePath);
    if (!specFile.exists()) {
      throw new IllegalStateException("Spec file not found: " + specFilePath);
    }

    System.out.println("Running spec: " + specFile.getName());
    List<Map<String, Object>> testGroups = mapper.readValue(specFile, List.class);
    for (Map<String, Object> group : testGroups) {
      runTestGroup(group);
    }
  }

  private void runTestGroup(Map<String, Object> group) throws Exception {
    String name = (String) group.get("name");
    String template = (String) group.get("template");
    Map<String, String> partials = (Map<String, String>) group.get("partials");
    Map<String, Object> groupData = (Map<String, Object>) group.get("data");
    List<Map<String, Object>> tests = (List<Map<String, Object>>) group.get("tests");

    System.out.println("  Group: " + name);

    Map<String, String> resolverPartials = (Map<String, String>) group.get("resolverPartials");
    Map<String, Map<String, Object>> schemas =
        (Map<String, Map<String, Object>>) group.get("schemas");
    Map<String, Map<String, Object>> tools = (Map<String, Map<String, Object>>) group.get("tools");

    // Build options with schemas, tools, and partialResolver from the spec
    DotpromptOptions.Builder optionsBuilder = DotpromptOptions.builder();

    // Add schemas from spec
    if (schemas != null) {
      for (Map.Entry<String, Map<String, Object>> entry : schemas.entrySet()) {
        optionsBuilder.addSchema(entry.getKey(), entry.getValue());
      }
    }

    // Add tools from spec (matching JS spec.test.ts)
    if (tools != null) {
      for (Map.Entry<String, Map<String, Object>> entry : tools.entrySet()) {
        String toolName = entry.getKey();
        Map<String, Object> toolSpec = entry.getValue();
        com.google.dotprompt.models.ToolDefinition toolDef =
            new com.google.dotprompt.models.ToolDefinition(
                toolName,
                (String) toolSpec.get("description"),
                (Map<String, Object>) toolSpec.get("inputSchema"),
                (Map<String, Object>) toolSpec.get("outputSchema"));
        optionsBuilder.addTool(toolDef);
      }
    }

    // Use partialResolver for resolverPartials (matching JS spec.test.ts)
    if (resolverPartials != null) {
      optionsBuilder.setPartialResolver(
          com.google.dotprompt.resolvers.PartialResolver.fromSync(resolverPartials::get));
    }

    Dotprompt dotprompt = new Dotprompt(optionsBuilder.build());

    // Register static partials via definePartial (matching JS spec.test.ts)
    if (partials != null) {
      for (Map.Entry<String, String> entry : partials.entrySet()) {
        dotprompt.definePartial(entry.getKey(), entry.getValue());
      }
    }

    // Compile the template once per group
    PromptFunction promptFn = dotprompt.compile(template).get();

    for (Map<String, Object> test : tests) {
      String desc = (String) test.get("desc");
      System.out.println("    Test: " + desc);
      Map<String, Object> testData = (Map<String, Object>) test.get("data");
      Map<String, Object> data = new HashMap<>();
      if (groupData != null) {
        data.putAll(groupData);
      }
      if (testData != null) {
        data.putAll(testData);
      }

      Map<String, Object> options = (Map<String, Object>) test.get("options");
      Map<String, Object> expect = (Map<String, Object>) test.get("expect");

      // Build render data: merge input values into top-level, but also preserve context
      // for @-prefixed variable access and messages for history helper
      Map<String, Object> renderData = new HashMap<>();
      if (data != null && data.containsKey("input")) {
        @SuppressWarnings("unchecked")
        Map<String, Object> inputData = (Map<String, Object>) data.get("input");
        if (inputData != null) {
          renderData.putAll(inputData);
        }
      }
      // Preserve context for @-prefixed variables (e.g., @auth, @state, @user)
      if (data != null && data.containsKey("context")) {
        renderData.put("context", data.get("context"));
      }
      // Preserve messages for {{history}} helper
      if (data != null && data.containsKey("messages")) {
        renderData.put("messages", data.get("messages"));
      }

      try {
        RenderedPrompt result = promptFn.render(renderData, options).get();
        // Verify result matches expect
        List<Map<String, Object>> expectedMessages =
            (List<Map<String, Object>>) expect.get("messages");
        if (expectedMessages != null && !expectedMessages.isEmpty()) {
          List<Message> actualMessages = result.messages();

          assertThat(actualMessages).hasSize(expectedMessages.size());

          for (int i = 0; i < expectedMessages.size(); i++) {
            Message actualMsg = actualMessages.get(i);
            Map<String, Object> expectedMsg = expectedMessages.get(i);

            String expectedRole = (String) expectedMsg.get("role");
            if (expectedRole != null) {
              assertThat(actualMsg.role().toString().toLowerCase())
                  .isEqualTo(expectedRole.toLowerCase());
            }

            Object expectedMsgContent = expectedMsg.get("content");
            if (expectedMsgContent instanceof List) {
              List<Map<String, Object>> expectedParts =
                  (List<Map<String, Object>>) expectedMsgContent;
              assertThat(actualMsg.content()).hasSize(expectedParts.size());

              for (int j = 0; j < expectedParts.size(); j++) {
                Part actualPart = actualMsg.content().get(j);
                Map<String, Object> expectedPartMap = expectedParts.get(j);

                if (expectedPartMap.containsKey("text")) {
                  assertThat(actualPart).isInstanceOf(TextPart.class);
                  String textVal = (String) expectedPartMap.get("text");
                  if (textVal != null) {
                    assertThat(((TextPart) actualPart).text().trim()).isEqualTo(textVal.trim());
                  }
                } else if (expectedPartMap.containsKey("media")) {
                  assertThat(actualPart).isInstanceOf(MediaPart.class);
                  Map<String, String> expectedMedia =
                      (Map<String, String>) expectedPartMap.get("media");
                  MediaPart actualMedia = (MediaPart) actualPart;
                  if (expectedMedia.containsKey("url")) {
                    assertThat(actualMedia.media().url()).isEqualTo(expectedMedia.get("url"));
                  }
                  if (expectedMedia.containsKey("contentType")) {
                    assertThat(actualMedia.media().contentType())
                        .isEqualTo(expectedMedia.get("contentType"));
                  }
                }
              }
            } else if (expectedMsgContent instanceof String) {
              String textVal = (String) expectedMsgContent;
              if (!actualMsg.content().isEmpty()) {
                Part actualPart = actualMsg.content().get(0);
                if (actualPart instanceof TextPart) {
                  assertThat(((TextPart) actualPart).text().trim()).isEqualTo(textVal.trim());
                }
              }
            }
          }
        }

        // Check "output" expectation (config check)
        Map<String, Object> expectedOutput = (Map<String, Object>) expect.get("output");
        if (expectedOutput != null) {
          Map<String, Object> actualConfig = result.config();
          Map<String, Object> actualOutput = (Map<String, Object>) actualConfig.get("output");
          if (actualOutput == null) {
            if (!expectedOutput.isEmpty()) {
              assertThat(actualOutput).isNotNull();
            }
          } else {
            assertThat(actualOutput).isEqualTo(expectedOutput);
          }
        }

        // Check "input" expectation
        Map<String, Object> expectedInput = (Map<String, Object>) expect.get("input");
        if (expectedInput != null) {
          Map<String, Object> actualConfig = result.config();
          Map<String, Object> actualInput = (Map<String, Object>) actualConfig.get("input");
          if (actualInput == null) {
            if (!expectedInput.isEmpty()) {
              assertThat(actualInput).isNotNull();
            }
          } else {
            assertThat(actualInput).isEqualTo(expectedInput);
          }
        }

        // Check "ext" expectation
        Map<String, Object> expectedExt = (Map<String, Object>) expect.get("ext");
        if (expectedExt != null) {
          Map<String, Object> actualConfig = result.config();
          Map<String, Object> actualExt = (Map<String, Object>) actualConfig.get("ext");
          if (actualExt == null) {
            if (!expectedExt.isEmpty()) {
              assertThat(actualExt).isNotNull();
            }
          } else {
            assertThat(actualExt).isEqualTo(expectedExt);
          }
        }

        // Test renderMetadata (matching JS spec.test.ts)
        PromptMetadata metadataResult = dotprompt.renderMetadata(template, options).get();

        if (expectedOutput != null && metadataResult.output() != null) {
          com.google.dotprompt.models.PromptMetadata.OutputConfig output = metadataResult.output();
          if (expectedOutput.containsKey("format")) {
            assertThat(output.format()).isEqualTo(expectedOutput.get("format"));
          }
          if (expectedOutput.containsKey("schema")) {
            assertThat(output.schema()).isEqualTo(expectedOutput.get("schema"));
          }
        }

        if (expectedInput != null && metadataResult.input() != null) {
          com.google.dotprompt.models.PromptMetadata.InputConfig input = metadataResult.input();
          if (expectedInput.containsKey("default")) {
            assertThat(input.defaultValues()).isEqualTo(expectedInput.get("default"));
          }
          if (expectedInput.containsKey("schema")) {
            assertThat(input.schema()).isEqualTo(expectedInput.get("schema"));
          }
        }
      } catch (Exception e) {
        throw new RuntimeException("Failed test: " + desc, e);
      }
    }
  }
}
