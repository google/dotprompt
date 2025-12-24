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

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for type parity and serialization of new models. */
@RunWith(JUnit4.class)
public class TypeParityTest {

  private final ObjectMapper mapper = new ObjectMapper();

  @Test
  public void testPromptRefSerialization() throws Exception {
    PromptRef ref = new PromptRef("test", "base", "v1");
    String json = mapper.writeValueAsString(ref);
    assertThat(json).contains("\"name\":\"test\"");
    assertThat(json).contains("\"variant\":\"base\"");
    assertThat(json).contains("\"version\":\"v1\"");

    PromptRef deserialized = mapper.readValue(json, PromptRef.class);
    assertThat(deserialized).isEqualTo(ref);
  }

  @Test
  public void testPromptDataSerialization() throws Exception {
    PromptData data = new PromptData("test", "base", "v1", "source code");
    String json = mapper.writeValueAsString(data);
    assertThat(json).contains("\"source\":\"source code\"");

    PromptData deserialized = mapper.readValue(json, PromptData.class);
    assertThat(deserialized).isEqualTo(data);
  }

  @Test
  public void testDataArgumentInstantiation() {
    DataArgument arg =
        new DataArgument(
            Map.of("var", "val"),
            List.of(new Document(List.of(new TextPart("doc")), Map.of())),
            List.of(new Message(Role.USER, List.of(new TextPart("msg")))),
            Map.of("state", "active"));
    assertThat(arg.input()).containsEntry("var", "val");
    assertThat(arg.context()).containsEntry("state", "active");
  }

  @Test
  public void testPaginationSerialization() throws Exception {
    PaginatedPrompts paginated = new PaginatedPrompts(List.of(new PromptRef("p1")), "next-token");
    String json = mapper.writeValueAsString(paginated);
    assertThat(json).contains("\"cursor\":\"next-token\"");
    assertThat(json).contains("\"prompts\":[{\"name\":\"p1\"");
  }
}
