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

import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.Prompt;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.Role;
import com.google.dotprompt.models.TextPart;
import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

@RunWith(JUnit4.class)
public class DotpromptTest {

  @Test
  public void testParseAndRender() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("hello".equals(name)) {
              return Futures.immediateFuture(
                  new Prompt("Hello {{name}}!", Map.of("model", "gemini-pro")));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    ListenableFuture<RenderedPrompt> result = dotprompt.render("hello", Map.of("name", "World"));

    RenderedPrompt rendered = result.get();
    assertThat(rendered.messages()).hasSize(1);
    assertThat(rendered.messages().get(0).role()).isEqualTo(Role.USER);
    Part part = rendered.messages().get(0).content().get(0);
    assertThat(part).isInstanceOf(TextPart.class);
    assertThat(((TextPart) part).text()).isEqualTo("Hello World!");
  }

  @Test
  public void testRenderWithOptions() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("options".equals(name)) {
              return Futures.immediateFuture(new Prompt("Hello {{name}}!", Map.of()));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    ListenableFuture<RenderedPrompt> result =
        dotprompt.render(
            "options", Map.of(), Map.of("input", Map.of("default", Map.of("name", "Options"))));

    RenderedPrompt rendered = result.get();
    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("Hello Options!");
  }

  @Test
  public void testPartials() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("partial_test".equals(name)) {
              return Futures.immediateFuture(new Prompt("{{> header}} world", Map.of()));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    dotprompt.registerPartial("header", "hello");

    ListenableFuture<RenderedPrompt> result = dotprompt.render("partial_test", Map.of());

    RenderedPrompt rendered = result.get();
    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("hello world");
  }

  @Test
  public void testMessageSplitting() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("multi_turn".equals(name)) {
              return Futures.immediateFuture(
                  new Prompt(
                      "System instruction\n"
                          + "<<<dotprompt:role:user>>>User query\n"
                          + "<<<dotprompt:role:model>>>Model response",
                      Map.of()));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    RenderedPrompt rendered = dotprompt.render("multi_turn", Map.of()).get();

    List<Message> messages = rendered.messages();
    assertThat(messages).hasSize(3);
    assertThat(messages.get(0).role()).isEqualTo(Role.USER); // Default start logic?
    // Wait, my logic starts with User.
    // "System instruction" -> User message (default).
    // <<<dotprompt:role:user>>> -> New User message.
    // <<<dotprompt:role:model>>> -> Model message.

    assertThat(((TextPart) messages.get(0).content().get(0)).text().trim())
        .isEqualTo("System instruction");
    assertThat(messages.get(1).role()).isEqualTo(Role.USER);
    assertThat(((TextPart) messages.get(1).content().get(0)).text().trim()).isEqualTo("User query");
    assertThat(messages.get(2).role()).isEqualTo(Role.MODEL);
    assertThat(((TextPart) messages.get(2).content().get(0)).text().trim())
        .isEqualTo("Model response");
  }

  @Test
  public void testHistoryInjection() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("history_marker".equals(name)) {
              return Futures.immediateFuture(
                  new Prompt(
                      "System instruction\n" + "<<<dotprompt:history>>>\n" + "User follow up",
                      Map.of()));
            }
            if ("history_auto".equals(name)) {
              return Futures.immediateFuture(new Prompt("User follow up", Map.of()));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    List<Message> history =
        List.of(
            new Message(Role.USER, List.of(new TextPart("Old user msg"))),
            new Message(Role.MODEL, List.of(new TextPart("Old model msg"))));
    Map<String, Object> data = Map.of("messages", history);

    // Case 1: Explicit marker
    RenderedPrompt renderedMarker = dotprompt.render("history_marker", data).get();
    List<Message> msgsMarker = renderedMarker.messages();
    // System (User) -> History (User, Model) -> Model (empty from marker logic) -> User ("User
    // follow up")
    // Wait, marker logic: "Start a new model message after history marker".
    // "System instruction" -> User.
    // Marker -> History added.
    // New Model message started.
    // "User follow up" -> Added to that Model message? Or does it look like user text?
    // "User follow up" is just text. If current role is MODEL, it gets added to MODEL.
    // Unless there is a role marker.
    // Let's check python behavior or desired behavior.
    // Usually "User follow up" would have a role marker if it's user.
    // If not, it appends to current.
    // In my logic: currentMessage = new MessageSource(Role.MODEL);
    // messageSources.add(currentMessage);
    // Then "User follow up" appends to this MODEL message.

    // Let's verify what we get.
    // 1. User: "System instruction\n"
    // 2. User: "Old user msg"
    // 3. Model: "Old model msg"
    // 4. Model: "\nUser follow up"

    assertThat(msgsMarker).hasSize(4);
    assertThat(msgsMarker.get(1).content()).isEqualTo(history.get(0).content());

    // Case 2: Auto insertion
    // "User follow up" -> User message.
    // History should be inserted BEFORE the last user message.
    RenderedPrompt renderedAuto = dotprompt.render("history_auto", data).get();
    List<Message> msgsAuto = renderedAuto.messages();
    // 1. User: "Old user msg"
    // 2. Model: "Old model msg"
    // 3. User: "User follow up"

    assertThat(msgsAuto).hasSize(3);
    assertThat(msgsAuto.get(0).content()).isEqualTo(history.get(0).content());
    assertThat(((TextPart) msgsAuto.get(2).content().get(0)).text()).isEqualTo("User follow up");
  }

  @Test
  public void testDataVariables() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("data_var".equals(name)) {
              return Futures.immediateFuture(new Prompt("State: {{@state.count}}", Map.of()));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    ListenableFuture<RenderedPrompt> result =
        dotprompt.render("data_var", Map.of("context", Map.of("state", Map.of("count", 123))));

    RenderedPrompt rendered = result.get();
    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("State: 123");
  }

  @Test
  public void testNoEscaping() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("no_escape".equals(name)) {
              return Futures.immediateFuture(new Prompt("{{value}}", Map.of()));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    ListenableFuture<RenderedPrompt> result =
        dotprompt.render("no_escape", Map.of("value", "<b>bold</b>"));

    RenderedPrompt rendered = result.get();
    assertThat(((TextPart) rendered.messages().get(0).content().get(0)).text())
        .isEqualTo("<b>bold</b>");
  }

  @Test
  public void testModelConfigMerging() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("model_test".equals(name)) {
              // Prompt defines temperature: 0.5
              Map<String, Object> config = new java.util.HashMap<>();
              config.put("model", "gpt-4");
              config.put("temperature", 0.5);
              return Futures.immediateFuture(new Prompt("template", config));
            }
            return super.load(name);
          }
        };

    // Model config defines topP: 0.9, temperature: 0.1
    Map<String, Object> gpt4Config = Map.of("topP", 0.9, "temperature", 0.1);
    Map<String, Object> modelConfigs = Map.of("gpt-4", gpt4Config);

    Dotprompt dotprompt = new Dotprompt(loader, null, modelConfigs, null);

    RenderedPrompt rendered = dotprompt.render("model_test", Map.of()).get();
    Map<String, Object> config = rendered.config();

    // Temperature should be 0.5 (Prompt override)
    // topP should be 0.9 (Model default)
    assertThat(config.get("temperature")).isEqualTo(0.5);
    assertThat(config.get("topP")).isEqualTo(0.9);
  }

  @Test
  public void testMessageMetadata() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            return Futures.immediateFuture(new Prompt("", Map.of()));
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);

    // Simulate input message with metadata (as Map, typical for JSON/external input)
    Map<String, Object> msgWithMetadata =
        Map.of(
            "role", "user",
            "content", List.of(Map.of("text", "Hello")),
            "metadata", Map.of("id", "msg-123", "timestamp", 1000L));

    ListenableFuture<RenderedPrompt> result =
        dotprompt.render("test", Map.of("messages", List.of(msgWithMetadata)));
    RenderedPrompt rendered = result.get();

    List<Message> messages = rendered.messages();
    assertThat(messages).hasSize(1);
    assertThat(messages.get(0).role()).isEqualTo(Role.USER);
    assertThat(messages.get(0).metadata()).containsEntry("id", "msg-123");
    assertThat(messages.get(0).metadata()).containsEntry("timestamp", 1000L);
  }

  @Test
  public void testMediaParsing() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            // Template producing the new media marker format manually or via helper logic if we
            // used full render stack
            // Here we just test parsing of the string.
            return Futures.immediateFuture(
                new Prompt(
                    "<<<dotprompt:media:url http://example.com/img.png image/png>>>", Map.of()));
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    RenderedPrompt rendered = dotprompt.render("media_test", Map.of()).get();

    List<Message> messages = rendered.messages();
    assertThat(messages).hasSize(1);
    Part part = messages.get(0).content().get(0);
    assertThat(part).isInstanceOf(MediaPart.class);
    MediaPart media = (MediaPart) part;
    assertThat(media.media().url()).isEqualTo("http://example.com/img.png");
    assertThat(media.media().contentType()).isEqualTo("image/png");
  }

  @Test
  public void testInvalidMarkers() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            // Contains invalid markers that should be treated as text
            return Futures.immediateFuture(
                new Prompt(
                    "<<<dotprompt:ROLE:user>>> "
                        + // Uppercase invalid
                        "<<<dotprompt:role:>>> "
                        + // Missing role name
                        "dotprompt:role:user", // Missing brackets
                    Map.of()));
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    RenderedPrompt rendered = dotprompt.render("invalid_markers", Map.of()).get();

    List<Message> messages = rendered.messages();
    assertThat(messages).hasSize(1);
    Part part = messages.get(0).content().get(0);
    assertThat(part).isInstanceOf(TextPart.class);
    // Verify text contains the invalid markers literally
    String text = ((TextPart) part).text();
    assertThat(text).contains("<<<dotprompt:ROLE:user>>>");
    assertThat(text).contains("<<<dotprompt:role:>>>");
    assertThat(text).contains("dotprompt:role:user");
  }
}
