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
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.Prompt;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.TextPart;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.Parameterized;

@RunWith(Parameterized.class)
public class SpecTest {

  /** Object mapper for parsing YAML spec files. */
  private final ObjectMapper mapper = new ObjectMapper(new YAMLFactory());

  private final File specFile;

  public SpecTest(String name, File specFile) {
    this.specFile = specFile;
  }

  @Parameterized.Parameters(name = "{0}")
  public static Collection<Object[]> data() {
    Path specDir = Paths.get("../../spec");
    if (!Files.exists(specDir)) {
      specDir = Paths.get("spec");
    }
    if (!Files.exists(specDir)) {
      specDir = Paths.get("external/dotprompt/spec");
    }

    if (!Files.exists(specDir)) {
      System.err.println("Could not find spec directory at: " + specDir.toAbsolutePath());
      return List.of();
    }

    try (Stream<Path> stream = Files.walk(specDir)) {
      return stream
          .filter(p -> !Files.isDirectory(p))
          .filter(p -> p.toString().endsWith(".yaml"))
          .map(p -> new Object[] {p.toFile().getName(), p.toFile()})
          .collect(Collectors.toList());
    } catch (IOException e) {
      throw new RuntimeException("Failed to discover spec files", e);
    }
  }

  @Test
  public void runSpec() throws Exception {
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

    PromptLoader parser = new PromptLoader();
    Prompt parsedPrompt = parser.parse(template);

    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String n) {
            if (n.equals("test")) {
              return Futures.immediateFuture(parsedPrompt);
            }
            return super.load(n);
          }
        };

    Map<String, String> resolverPartials = (Map<String, String>) group.get("resolverPartials");
    Map<String, Map<String, Object>> schemas =
        (Map<String, Map<String, Object>>) group.get("schemas");

    Dotprompt dotprompt = new Dotprompt(loader);

    if (schemas != null) {
      for (Map.Entry<String, Map<String, Object>> entry : schemas.entrySet()) {
        dotprompt.registerSchema(entry.getKey(), entry.getValue());
      }
    }

    // Helpers are now registered automatically in Dotprompt constructor via Helpers.register(this)

    if (partials != null) {
      for (Map.Entry<String, String> entry : partials.entrySet()) {
        dotprompt.registerPartial(entry.getKey(), entry.getValue());
      }
    }
    if (resolverPartials != null) {
      for (Map.Entry<String, String> entry : resolverPartials.entrySet()) {
        dotprompt.registerPartial(entry.getKey(), entry.getValue());
      }
    }

    for (Map<String, Object> test : tests) {
      String desc = (String) test.get("desc");
      System.out.println("    Test: " + desc);
      Map<String, Object> testData = (Map<String, Object>) test.get("data");
      Map<String, Object> data = new java.util.HashMap<>();
      if (groupData != null) {
        data.putAll(groupData);
      }
      if (testData != null) {
        data.putAll(testData);
      }

      Map<String, Object> options = (Map<String, Object>) test.get("options");
      Map<String, Object> expect = (Map<String, Object>) test.get("expect");

      Map<String, Object> renderData = data;
      if (data != null && data.containsKey("input")) {
        renderData = (Map<String, Object>) data.get("input");
      }

      try {
        RenderedPrompt result = dotprompt.render("test", renderData, options).get();
        // Verify result matches expect
        // Simple check for now: just check text content of first message
        List<Map<String, Object>> expectedMessages =
            (List<Map<String, Object>>) expect.get("messages");
        if (expectedMessages != null && !expectedMessages.isEmpty()) {
          List<Message> actualMessages = result.messages();
          // The original code had `expectedMessages` defined twice, and `messages` was undefined.
          // Assuming the intent was to use the `expectedMessages` defined above.
          // Also, the `content` and `expectedText` variables were part of a simpler,
          // now-replaced check.

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
          // In SpecTest (SpecTest.java), render(data) is called.
          // But result.config() is the Prompt config merged with options.
          // Wait, result.config() comes from Dotprompt.render() -> mergeConfigs(prompt.config(),
          // options).
          // Does mergeConfigs merge input configurations?
          // Prompt config has input schema.
          // If input schema is parsed, it should be in actualConfig.
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
      } catch (Exception e) {
        throw new RuntimeException("Failed test: " + desc, e);
      }
    }
  }
}
