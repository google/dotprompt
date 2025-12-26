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

import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.PromptFunction;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.Role;
import com.google.dotprompt.models.TextPart;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for the Dotprompt class. */
@RunWith(JUnit4.class)
public class DotpromptTest {

  @Test
  public void testParseAndRender() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn =
        dotprompt.compile("---\nmodel: gemini-pro\n---\nHello {{name}}!").get();

    RenderedPrompt rendered = promptFn.render(Map.of("name", "World")).get();

    assertThat(rendered.messages()).hasSize(1);
    assertThat(rendered.messages().get(0).role()).isEqualTo(Role.USER);
    Part part = rendered.messages().get(0).content().get(0);
    assertThat(part).isInstanceOf(TextPart.class);
    assertThat(((TextPart) part).text()).isEqualTo("Hello World!");
  }

  @Test
  public void testRenderWithOptions() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn = dotprompt.compile("Hello {{name}}!").get();

    RenderedPrompt rendered =
        promptFn
            .render(Map.of(), Map.of("input", Map.of("default", Map.of("name", "Options"))))
            .get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Hello Options!");
  }

  @Test
  public void testPartials() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    dotprompt.definePartial("header", "Hello");

    PromptFunction promptFn = dotprompt.compile("{{> header}} world").get();
    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Hello world");
  }

  @Test
  public void testDefaultRoleIsUser() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn = dotprompt.compile("Just some text").get();

    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(rendered.messages()).hasSize(1);
    assertThat(rendered.messages().get(0).role()).isEqualTo(Role.USER);
  }

  @Test
  public void testHistoryHelperRendersWithoutError() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn = dotprompt.compile("Before\n{{history}}\nAfter").get();

    Message historyMsg = new Message(Role.USER, List.of(new TextPart("History message")), Map.of());
    Map<String, Object> data = new HashMap<>();
    data.put("history", List.of(historyMsg));

    // Just verify that rendering with history data doesn't throw an error
    RenderedPrompt rendered = promptFn.render(data).get();
    assertThat(rendered.messages()).isNotEmpty();
  }

  @Test
  public void testRoleSystem() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn = dotprompt.compile("{{role \"system\"}}System message").get();

    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(rendered.messages().get(0).role()).isEqualTo(Role.SYSTEM);
  }

  @Test
  public void testRoleModel() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn = dotprompt.compile("{{role \"model\"}}Model message").get();

    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(rendered.messages().get(0).role()).isEqualTo(Role.MODEL);
  }

  @Test
  public void testMediaUrl() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn =
        dotprompt.compile("{{media url=\"https://example.com/image.png\"}}").get();

    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    Part part = rendered.messages().get(0).content().get(0);
    assertThat(part).isInstanceOf(MediaPart.class);
    assertThat(((MediaPart) part).media().url()).isEqualTo("https://example.com/image.png");
  }

  @Test
  public void testModelConfigMerge() throws Exception {
    Map<String, Object> gptConfig = Map.of("temperature", 0.7);
    DotpromptOptions options =
        DotpromptOptions.builder().addModelConfig("gpt-4", gptConfig).build();
    Dotprompt dotprompt = new Dotprompt(options);

    PromptFunction promptFn = dotprompt.compile("---\nmodel: gpt-4\n---\nHello").get();
    RenderedPrompt rendered = promptFn.render(Map.of()).get();

    assertThat(rendered.config().get("temperature")).isEqualTo(0.7);
  }

  @Test
  public void testIfEqualsHelper() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn =
        dotprompt
            .compile("Status: {{#ifEquals status \"active\"}}active{{else}}inactive{{/ifEquals}}")
            .get();

    RenderedPrompt rendered = promptFn.render(Map.of("status", "active")).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Status: active");
  }

  @Test
  public void testUnlessEqualsHelper() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn =
        dotprompt.compile("{{#unlessEquals status \"inactive\"}}Show this{{/unlessEquals}}").get();

    RenderedPrompt rendered = promptFn.render(Map.of("status", "active")).get();

    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Show this");
  }

  @Test
  public void testJsonHelper() throws Exception {
    Dotprompt dotprompt = new Dotprompt(DotpromptOptions.builder().build());
    PromptFunction promptFn = dotprompt.compile("Data: {{json data}}").get();

    RenderedPrompt rendered =
        promptFn.render(Map.of("data", Map.of("key", "value", "count", 42))).get();

    String text = ((TextPart) rendered.messages().get(0).content().get(0)).text();
    assertThat(text).contains("\"key\"");
    assertThat(text).contains("\"value\"");
  }
}
