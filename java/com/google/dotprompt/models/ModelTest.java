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

import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

@RunWith(JUnit4.class)
public class ModelTest {

  @Test
  public void message_creation() {
    Message message = new Message(Role.USER, List.of(new TextPart("hello")));
    assertThat(message.role()).isEqualTo(Role.USER);
    assertThat(message.content()).hasSize(1);
    assertThat(((TextPart) message.content().get(0)).text()).isEqualTo("hello");
  }

  @Test
  public void prompt_creation() {
    Prompt prompt = new Prompt("template", Map.of("key", "value"));
    assertThat(prompt.template()).isEqualTo("template");
    assertThat(prompt.config()).containsEntry("key", "value");
  }

  @Test
  public void renderedPrompt_creation() {
    RenderedPrompt rendered =
        new RenderedPrompt(
            Map.of("cfg", "val"),
            List.of(new Message(Role.MODEL, List.of(new TextPart("response")))));
    assertThat(rendered.config()).containsEntry("cfg", "val");
    assertThat(rendered.messages()).hasSize(1);
    assertThat(rendered.messages().get(0).role()).isEqualTo(Role.MODEL);
  }

  @Test
  public void textPart_creation() {
    TextPart part = new TextPart("content");
    assertThat(part.text()).isEqualTo("content");
  }
}
