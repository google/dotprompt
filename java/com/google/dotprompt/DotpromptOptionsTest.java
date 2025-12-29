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

import com.github.jknack.handlebars.Helper;
import com.github.jknack.handlebars.Options;
import com.google.dotprompt.models.ToolDefinition;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Unit tests for the DotpromptOptions builder. */
@RunWith(JUnit4.class)
public class DotpromptOptionsTest {

  @Test
  public void testBuilder_emptyOptions() {
    DotpromptOptions options = DotpromptOptions.builder().build();

    assertThat(options.getDefaultModel()).isNull();
    assertThat(options.getModelConfigs()).isEmpty();
    assertThat(options.getHelpers()).isEmpty();
    assertThat(options.getPartials()).isEmpty();
    assertThat(options.getTools()).isEmpty();
    assertThat(options.getSchemas()).isEmpty();
    assertThat(options.getToolResolver()).isNull();
    assertThat(options.getSchemaResolver()).isNull();
    assertThat(options.getPartialResolver()).isNull();
    assertThat(options.getStore()).isNull();
  }

  @Test
  public void testBuilder_setDefaultModel() {
    DotpromptOptions options = DotpromptOptions.builder().setDefaultModel("gemini-1.5-pro").build();

    assertThat(options.getDefaultModel()).isEqualTo("gemini-1.5-pro");
  }

  @Test
  public void testBuilder_addModelConfig() {
    Map<String, Object> gptConfig = Map.of("temperature", 0.7);
    DotpromptOptions options =
        DotpromptOptions.builder().addModelConfig("gpt-4", gptConfig).build();

    assertThat(options.getModelConfigs()).containsKey("gpt-4");
    assertThat(options.getModelConfigs().get("gpt-4")).isEqualTo(gptConfig);
  }

  @Test
  public void testBuilder_setModelConfigs() {
    Map<String, Object> configs =
        Map.of("gemini", Map.of("temperature", 0.5), "gpt-4", Map.of("temperature", 0.8));
    DotpromptOptions options = DotpromptOptions.builder().setModelConfigs(configs).build();

    assertThat(options.getModelConfigs()).hasSize(2);
    assertThat(options.getModelConfigs()).containsKey("gemini");
    assertThat(options.getModelConfigs()).containsKey("gpt-4");
  }

  @Test
  public void testBuilder_addHelper() {
    Helper<Object> customHelper =
        new Helper<Object>() {
          @Override
          public Object apply(Object context, Options options) {
            return "custom";
          }
        };

    DotpromptOptions options = DotpromptOptions.builder().addHelper("custom", customHelper).build();

    assertThat(options.getHelpers()).containsKey("custom");
    assertThat(options.getHelpers().get("custom")).isEqualTo(customHelper);
  }

  @Test
  public void testBuilder_setHelpers() {
    Map<String, Helper<?>> helpers = new HashMap<>();
    helpers.put("helper1", (context, options) -> "result1");
    helpers.put("helper2", (context, options) -> "result2");

    DotpromptOptions options = DotpromptOptions.builder().setHelpers(helpers).build();

    assertThat(options.getHelpers()).hasSize(2);
    assertThat(options.getHelpers()).containsKey("helper1");
    assertThat(options.getHelpers()).containsKey("helper2");
  }

  @Test
  public void testBuilder_addPartial() {
    DotpromptOptions options =
        DotpromptOptions.builder().addPartial("greeting", "Hello, {{name}}!").build();

    assertThat(options.getPartials()).containsKey("greeting");
    assertThat(options.getPartials().get("greeting")).isEqualTo("Hello, {{name}}!");
  }

  @Test
  public void testBuilder_setPartials() {
    Map<String, String> partials = Map.of("header", "# Title", "footer", "---End---");
    DotpromptOptions options = DotpromptOptions.builder().setPartials(partials).build();

    assertThat(options.getPartials()).hasSize(2);
    assertThat(options.getPartials().get("header")).isEqualTo("# Title");
    assertThat(options.getPartials().get("footer")).isEqualTo("---End---");
  }

  @Test
  public void testBuilder_addTool() {
    ToolDefinition tool =
        new ToolDefinition(
            "calculator", "Performs math calculations", Map.of("type", "object"), null);

    DotpromptOptions options = DotpromptOptions.builder().addTool(tool).build();

    assertThat(options.getTools()).containsKey("calculator");
    assertThat(options.getTools().get("calculator")).isEqualTo(tool);
  }

  @Test
  public void testBuilder_setTools() {
    ToolDefinition tool1 =
        new ToolDefinition("tool1", "First tool", Map.of("type", "object"), null);
    ToolDefinition tool2 =
        new ToolDefinition("tool2", "Second tool", Map.of("type", "object"), null);
    Map<String, ToolDefinition> tools = Map.of("tool1", tool1, "tool2", tool2);

    DotpromptOptions options = DotpromptOptions.builder().setTools(tools).build();

    assertThat(options.getTools()).hasSize(2);
  }

  @Test
  public void testBuilder_setToolResolver() {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .setToolResolver(name -> CompletableFuture.completedFuture(null))
            .build();

    assertThat(options.getToolResolver()).isNotNull();
  }

  @Test
  public void testBuilder_addSchema() {
    Map<String, Object> userSchema = Map.of("type", "object", "properties", Map.of());
    DotpromptOptions options = DotpromptOptions.builder().addSchema("User", userSchema).build();

    assertThat(options.getSchemas()).containsKey("User");
    assertThat(options.getSchemas().get("User")).isEqualTo(userSchema);
  }

  @Test
  public void testBuilder_setSchemas() {
    Map<String, Map<String, Object>> schemas =
        Map.of("User", Map.of("type", "object"), "Product", Map.of("type", "object"));

    DotpromptOptions options = DotpromptOptions.builder().setSchemas(schemas).build();

    assertThat(options.getSchemas()).hasSize(2);
  }

  @Test
  public void testBuilder_setSchemaResolver() {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .setSchemaResolver(name -> CompletableFuture.completedFuture(Map.of("type", "object")))
            .build();

    assertThat(options.getSchemaResolver()).isNotNull();
  }

  @Test
  public void testBuilder_setPartialResolver() {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .setPartialResolver(name -> CompletableFuture.completedFuture("partial content"))
            .build();

    assertThat(options.getPartialResolver()).isNotNull();
  }

  @Test
  public void testBuilder_methodChaining() {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .setDefaultModel("gemini-1.5-pro")
            .addModelConfig("gpt-4", Map.of("temp", 0.5))
            .addPartial("intro", "Hello")
            .addSchema("User", Map.of("type", "object"))
            .build();

    assertThat(options.getDefaultModel()).isEqualTo("gemini-1.5-pro");
    assertThat(options.getModelConfigs()).hasSize(1);
    assertThat(options.getPartials()).hasSize(1);
    assertThat(options.getSchemas()).hasSize(1);
  }
}
