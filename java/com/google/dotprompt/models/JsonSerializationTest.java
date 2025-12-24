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

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

@RunWith(JUnit4.class)
public class JsonSerializationTest {

  private final ObjectMapper mapper =
      new ObjectMapper().setSerializationInclusion(Include.NON_NULL);

  @Test
  public void testMediaPartSerialization() throws Exception {
    MediaPart part = new MediaPart(new MediaContent("http://example.com/image.png", "image/png"));
    String json = mapper.writeValueAsString(part);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    // Structure: { "media": { "url": "...", "contentType": "..." } }
    assertThat(map).containsKey("media");
    Map<String, Object> media = (Map<String, Object>) map.get("media");
    assertThat(media).containsEntry("url", "http://example.com/image.png");
    assertThat(media).containsEntry("contentType", "image/png");
  }

  @Test
  public void testToolRequestPartSerialization() throws Exception {
    ToolRequestPart part =
        new ToolRequestPart(new ToolRequestContent("myTool", Map.of("arg", "val"), "ref-123"));
    String json = mapper.writeValueAsString(part);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    // Structure: { "toolRequest": { "name": "...", "input": {...}, "ref": "..." } }
    assertThat(map).containsKey("toolRequest");
    Map<String, Object> req = (Map<String, Object>) map.get("toolRequest");
    assertThat(req).containsEntry("name", "myTool");
    assertThat(req).containsEntry("ref", "ref-123");
    assertThat((Map) req.get("input")).containsEntry("arg", "val");
  }

  @Test
  public void testToolResponsePartSerialization() throws Exception {
    ToolResponsePart part =
        new ToolResponsePart(new ToolResponseContent("myTool", Map.of("result", "ok"), "ref-123"));
    String json = mapper.writeValueAsString(part);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    assertThat(map).containsKey("toolResponse");
    Map<String, Object> resp = (Map<String, Object>) map.get("toolResponse");
    assertThat(resp).containsEntry("name", "myTool");
    assertThat(resp).containsEntry("ref", "ref-123");
    assertThat((Map) resp.get("output")).containsEntry("result", "ok");
  }

  @Test
  public void testTextPartSerialization() throws Exception {
    TextPart part = new TextPart("hello");
    String json = mapper.writeValueAsString(part);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    assertThat(map).containsEntry("text", "hello");
  }

  @Test
  public void testDataPartSerialization() throws Exception {
    DataPart part = new DataPart(Map.of("key", "value"));
    String json = mapper.writeValueAsString(part);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    assertThat(map).containsKey("data");
    assertThat((Map) map.get("data")).containsEntry("key", "value");
  }

  @Test
  public void testPendingPartSerialization() throws Exception {
    PendingPart part = new PendingPart();
    String json = mapper.writeValueAsString(part);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    assertThat(map).containsKey("metadata");
    assertThat((Map) map.get("metadata")).containsEntry("pending", true);
  }

  @Test
  public void testToolDefinitionSerialization() throws Exception {
    ToolDefinition tool =
        new ToolDefinition(
            "myTool", "A test tool", Map.of("type", "object"), Map.of("type", "string"));
    String json = mapper.writeValueAsString(tool);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    assertThat(map).containsEntry("name", "myTool");
    assertThat(map).containsEntry("description", "A test tool");
    assertThat(map).containsKey("inputSchema");
    assertThat(map).containsKey("outputSchema");
  }

  @Test
  public void testPartDeserialization() throws Exception {
    String json = "{\"text\": \"hello\"}";
    Part part = mapper.readValue(json, Part.class);
    assertThat(part).isInstanceOf(TextPart.class);
    assertThat(((TextPart) part).text()).isEqualTo("hello");

    json = "{\"media\": {\"url\": \"http://example.com\", \"contentType\": \"image/png\"}}";
    part = mapper.readValue(json, Part.class);
    assertThat(part).isInstanceOf(MediaPart.class);
    assertThat(((MediaPart) part).media().url()).isEqualTo("http://example.com");

    json = "{\"toolRequest\": {\"name\": \"t\", \"input\": {}}}";
    part = mapper.readValue(json, Part.class);
    assertThat(part).isInstanceOf(ToolRequestPart.class);
    assertThat(((ToolRequestPart) part).toolRequest().name()).isEqualTo("t");
  }

  @Test
  public void testMessageSerialization() throws Exception {
    Message msg = new Message(Role.USER, List.of(new TextPart("hi")), Map.of("key", "val"));
    String json = mapper.writeValueAsString(msg);
    Map<String, Object> map = mapper.readValue(json, Map.class);

    assertThat(map).containsEntry("role", "user");
    assertThat(map).containsKey("content");
    assertThat(map).containsKey("metadata");
    assertThat((Map) map.get("metadata")).containsEntry("key", "val");
  }
}
