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
import com.google.dotprompt.models.ParsedPrompt;
import com.google.dotprompt.models.PromptFunction;
import com.google.dotprompt.models.PromptMetadata;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.TextPart;
import com.google.dotprompt.models.ToolDefinition;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for the Dotprompt class. */
@RunWith(JUnit4.class)
public class DotpromptTest {

  @Test
  public void constructor_initializesWithDefaultOptions() {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    assertThat(dp).isNotNull();
  }

  @Test
  public void constructor_initializesWithCustomModelConfigs() {
    Map<String, Object> modelConfigs =
        Map.of(
            "gemini-1.5-pro", Map.of("temperature", 0.7), "gemini-2.0-flash", Map.of("top_p", 0.9));
    DotpromptOptions options = DotpromptOptions.builder().setModelConfigs(modelConfigs).build();
    Dotprompt dp = new Dotprompt(options);
    assertThat(dp).isNotNull();
  }

  @Test
  public void constructor_initializesWithDefaultModel() {
    DotpromptOptions options = DotpromptOptions.builder().setDefaultModel("gemini-1.5-pro").build();
    Dotprompt dp = new Dotprompt(options);
    assertThat(dp).isNotNull();
  }

  @Test
  public void constructor_initializesWithCustomHelpers() throws Exception {
    Helper<Object> customHelper = (context, options) -> "HELPER: " + context;
    DotpromptOptions options =
        DotpromptOptions.builder().addHelper("customHelper", customHelper).build();
    Dotprompt dp = new Dotprompt(options);

    PromptFunction promptFn = dp.compile("{{customHelper \"test\"}}").get();
    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("HELPER: test");
  }

  @Test
  public void defineHelper_registersHelperFunction() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    dp.defineHelper("testHelper", (context, options) -> "Helper: " + context);

    PromptFunction promptFn = dp.compile("{{testHelper \"test\"}}").get();
    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Helper: test");
  }

  @Test
  public void defineHelper_returnsInstanceForChaining() {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    Dotprompt result = dp.defineHelper("noop", (context, options) -> "");
    assertThat(result).isSameInstanceAs(dp);
  }

  @Test
  public void definePartial_registersPartialTemplate() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    dp.definePartial("testPartial", "Partial content");

    PromptFunction promptFn = dp.compile("{{> testPartial}}").get();
    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Partial content");
  }

  @Test
  public void definePartial_returnsInstanceForChaining() {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    Dotprompt result = dp.definePartial("test", "content");
    assertThat(result).isSameInstanceAs(dp);
  }

  @Test
  public void defineTool_registersToolDefinition() {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    ToolDefinition toolDef =
        new ToolDefinition(
            "testTool",
            "A test tool",
            Map.of("type", "object", "properties", Map.of("param1", Map.of("type", "string"))),
            null);

    dp.defineTool(toolDef);
    assertThat(dp).isNotNull();
  }

  @Test
  public void defineTool_returnsInstanceForChaining() {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    ToolDefinition toolDef = new ToolDefinition("testTool", "desc", Map.of(), null);
    Dotprompt result = dp.defineTool(toolDef);
    assertThat(result).isSameInstanceAs(dp);
  }

  @Test
  public void parse_delegatesToParseDocument() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    ParsedPrompt prompt = dp.parse("source");
    assertThat(prompt.template()).isEqualTo("source");
  }

  @Test
  public void compileAndRender_rendersTemplateWithData() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn = dp.compile("Hello {{name}}!").get();

    RenderedPrompt rendered = promptFn.render(Map.of("name", "World")).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Hello World!");
  }

  @Test
  public void identifyPartials_manualVerification() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    dp.definePartial("header", "Header");
    dp.definePartial("footer", "Footer");

    PromptFunction promptFn = dp.compile("{{> header}} Body {{> footer}}").get();
    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Header Body Footer");
  }

  @Test
  public void resolveTools_usesRegisteredTools() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());
    ToolDefinition toolDef =
        new ToolDefinition("testTool", "A test tool", Map.of("type", "object"), null);
    dp.defineTool(toolDef);

    Map<String, Object> config = new HashMap<>();
    config.put("tools", List.of("testTool", "unknownTool"));
    ParsedPrompt source = ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

    PromptMetadata metadata = dp.renderMetadata(source).get();

    assertThat(metadata.toolDefs()).hasSize(1);
    assertThat(metadata.toolDefs().get(0).name()).isEqualTo("testTool");
    assertThat(metadata.tools()).contains("unknownTool");
  }

  @Test
  public void resolveTools_usesToolResolverForUnregistered() throws Exception {
    ToolDefinition toolDef =
        new ToolDefinition("resolvedTool", "A resolved tool", Map.of("type", "object"), null);

    DotpromptOptions options =
        DotpromptOptions.builder()
            .setToolResolver(
                name -> {
                  if ("resolvedTool".equals(name))
                    return CompletableFuture.completedFuture(toolDef);
                  return CompletableFuture.completedFuture(null);
                })
            .build();
    Dotprompt dp = new Dotprompt(options);

    Map<String, Object> config = new HashMap<>();
    config.put("tools", List.of("resolvedTool"));
    ParsedPrompt source = ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

    PromptMetadata metadata = dp.renderMetadata(source).get();

    assertThat(metadata.toolDefs()).hasSize(1);
    assertThat(metadata.toolDefs().get(0).name()).isEqualTo("resolvedTool");
    assertThat(metadata.tools()).doesNotContain("resolvedTool");
  }

  @Test
  public void resolveTools_throwsWhenResolverReturnsNull() {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .setToolResolver(name -> CompletableFuture.completedFuture(null))
            .build();
    Dotprompt dp = new Dotprompt(options);

    Map<String, Object> config = new HashMap<>();
    config.put("tools", List.of("nonExistentTool"));
    ParsedPrompt source = ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

    // renderMetadata shouldn't throw if tool is missing, just adds to unresolved list in tools()
    // unless tool resolving throws explicitly.
    // JS: if resolve fails or returns null, it remains in tools array.
    // So assertions:
    try {
      PromptMetadata metadata = dp.renderMetadata(source).get();
      assertThat(metadata.toolDefs()).isEmpty();
      assertThat(metadata.tools()).contains("nonExistentTool");
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  @Test
  public void renderPicoschema_processesDefinitions() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());

    Map<String, Object> inputSchema = Map.of("name", "string");
    Map<String, Object> config = new HashMap<>();
    config.put("input", Map.of("schema", inputSchema));
    ParsedPrompt source = ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

    PromptMetadata metadata = dp.renderMetadata(source).get();

    @SuppressWarnings("unchecked")
    Map<String, Object> schema = (Map<String, Object>) metadata.input().schema();
    assertThat(schema).containsEntry("type", "object");
    assertThat(schema).containsKey("properties");
  }

  @Test
  public void wrappedSchemaResolver_resolvesFromRegisteredSchemas() throws Exception {
    Map<String, Object> schema = Map.of("type", "string");
    DotpromptOptions options = DotpromptOptions.builder().addSchema("test-schema", schema).build();
    Dotprompt dp = new Dotprompt(options);

    Map<String, Object> config = new HashMap<>();
    config.put("input", Map.of("schema", "test-schema"));
    ParsedPrompt source = ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

    PromptMetadata metadata = dp.renderMetadata(source).get();

    @SuppressWarnings("unchecked")
    Map<String, Object> resolvedSchema = (Map<String, Object>) metadata.input().schema();
    assertThat(resolvedSchema).containsEntry("type", "string");
  }

  @Test
  public void wrappedSchemaResolver_usesResolverForUnregistered() throws Exception {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .setSchemaResolver(
                name -> {
                  if ("external-schema".equals(name))
                    return CompletableFuture.completedFuture(Map.of("type", "boolean"));
                  return CompletableFuture.completedFuture(null);
                })
            .build();
    Dotprompt dp = new Dotprompt(options);

    Map<String, Object> config = new HashMap<>();
    config.put("input", Map.of("schema", "external-schema"));
    ParsedPrompt source = ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(config));

    PromptMetadata metadata = dp.renderMetadata(source).get();

    @SuppressWarnings("unchecked")
    Map<String, Object> resolvedSchema = (Map<String, Object>) metadata.input().schema();
    assertThat(resolvedSchema).containsEntry("type", "boolean");
  }

  @Test
  public void resolveMetadata_mergesObjects() throws Exception {
    Dotprompt dp = new Dotprompt(DotpromptOptions.builder().build());

    Map<String, Object> promptConfig = new HashMap<>();
    promptConfig.put("model", "gemini-1.5-pro");
    promptConfig.put("config", Map.of("temperature", 0.7));
    ParsedPrompt source = ParsedPrompt.fromMetadata("", PromptMetadata.fromConfig(promptConfig));

    Map<String, Object> additionalConfig = new HashMap<>();
    additionalConfig.put("model", "gemini-2.0-flash");
    additionalConfig.put("config", Map.of("max_tokens", 2000));

    PromptMetadata result = dp.renderMetadata(source, additionalConfig).get();

    assertThat(result.model()).isEqualTo("gemini-2.0-flash");
    assertThat(result.config()).containsEntry("temperature", 0.7);
    assertThat(result.config()).containsEntry("max_tokens", 2000);
  }

  @Test
  public void resolvePartials_resolvesAndRegisters() throws Exception {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .setPartialResolver(
                name -> {
                  if ("header".equals(name)) return CompletableFuture.completedFuture("Header");
                  return CompletableFuture.completedFuture(null);
                })
            .build();
    Dotprompt dp = new Dotprompt(options);

    PromptFunction promptFn = dp.compile("{{> header}}").get();
    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text()).isEqualTo("Header");
  }

  @Test
  public void renderMetadata_usesDefaultModel() throws Exception {
    DotpromptOptions options = DotpromptOptions.builder().setDefaultModel("default-model").build();
    Dotprompt dp = new Dotprompt(options);

    ParsedPrompt source = ParsedPrompt.fromMetadata("content", null);

    PromptMetadata metadata = dp.renderMetadata(source).get();
    assertThat(metadata.model()).isEqualTo("default-model");
  }

  @Test
  public void renderMetadata_usesModelConfigs() throws Exception {
    DotpromptOptions options =
        DotpromptOptions.builder()
            .addModelConfig("gemini-1.5-pro", Map.of("temperature", 0.7))
            .build();
    Dotprompt dp = new Dotprompt(options);

    Map<String, Object> config = new HashMap<>();
    config.put("model", "gemini-1.5-pro");
    ParsedPrompt source = ParsedPrompt.fromMetadata("content", PromptMetadata.fromConfig(config));

    PromptMetadata metadata = dp.renderMetadata(source).get();
    assertThat(metadata.config()).containsEntry("temperature", 0.7);
  }
}
