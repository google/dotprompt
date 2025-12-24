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

package com.google.dotprompt.parser;

import static com.google.common.truth.Truth.assertThat;

import com.google.dotprompt.models.Prompt;
import java.io.IOException;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

@RunWith(JUnit4.class)
public class ParserTest {

  @Test
  public void testParseWithFrontmatter() throws IOException {
    String content =
        "---\n"
            + "input:\n"
            + "  schema:\n"
            + "    type: object\n"
            + "---\n"
            + "Start of the template.";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Start of the template.");
    assertThat(prompt.config()).containsKey("input");
  }

  @Test
  public void testParseWithoutFrontmatter() throws IOException {
    String content = "Just a template.";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Just a template.");
    assertThat(prompt.config()).isEmpty();
  }

  @Test
  public void testParseEmptyFrontmatter() throws IOException {
    String content = "---\n---\nTemplate";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Template");
    assertThat(prompt.config()).isEmpty();
  }

  @Test
  public void testParseWhitespacePreservation() throws IOException {
    String content = "---\nfoo: bar\n---\n  Indented.\n";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("  Indented.\n");
  }

  @Test
  public void testParseCRLF() throws IOException {
    String content = "---\r\nfoo: bar\r\n---\r\nBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseMultilineFrontmatter() throws IOException {
    String content = "---\nfoo: bar\nbaz: qux\n---\nBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
    assertThat(ext).containsEntry("baz", "qux");
  }

  @Test
  public void testParseExtraMarkers() throws IOException {
    String content = "---\nfoo: bar\n---\nBody\n---\nExtra";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body\n---\nExtra");
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseWithCR() throws IOException {
    String content = "---\rfoo: bar\r---\rBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseFrontmatterWithExtraSpaces() throws IOException {
    String content = "---   \nfoo: bar\n---   \nBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseNamespacedKeys() throws IOException {
    String content = "---\na.b.c: val\n---\nBody";
    Prompt prompt = Parser.parse(content);
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");

    // Expect: { "a.b": { "c": "val" } }
    // Flattens to last dot logic.
    assertThat(ext).containsKey("a.b");
    Map<String, Object> ab = (Map<String, Object>) ext.get("a.b");
    assertThat(ab).containsEntry("c", "val");
  }

  @Test
  public void testParseIncompleteFrontmatter() throws IOException {
    String content = "---\nfoo: bar\nBody"; // Missing second marker
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo(content);
    assertThat(prompt.config()).isEmpty();
  }
}
