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

import com.google.dotprompt.models.Prompt;
import java.io.IOException;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

@RunWith(JUnit4.class)
public class PromptLoaderTest {

  private final PromptLoader promptLoader = new PromptLoader();

  @Test
  public void parse_withFrontmatter() throws IOException {
    String content = "---\nkey: value\n---\ntemplate body";
    Prompt prompt = promptLoader.parse(content);

    assertThat(prompt.template()).isEqualTo("template body");
    // "key" is not a known key, so it goes to ext (and raw)
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("key", "value");
    Map<String, Object> raw = (Map<String, Object>) prompt.config().get("raw");
    assertThat(raw).containsEntry("key", "value");
  }

  @Test
  public void parse_withoutFrontmatter() throws IOException {
    String content = "just template parsing";
    Prompt prompt = promptLoader.parse(content);

    assertThat(prompt.template()).isEqualTo("just template parsing");
    assertThat(prompt.config()).isEmpty(); // No raw/ext if no frontmatter
  }

  @Test
  public void parse_preservesWhitespaceInTemplate() throws IOException {
    String content = "---\nfoo: bar\n---\n  whitespace  \n  preserved  ";
    Prompt prompt = promptLoader.parse(content);

    assertThat(prompt.template()).isEqualTo("  whitespace  \n  preserved  ");
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void parse_handlesEmptyFrontmatter() throws IOException {
    String content = "---\n\n---\ntemplate";
    Prompt prompt = promptLoader.parse(content);

    assertThat(prompt.template()).isEqualTo("template");
    assertThat(prompt.config()).isEmpty();
  }

  @Test
  public void parse_complexFrontmatter() throws IOException {
    String content =
        """
        ---
        key: value
        nested:
          inner: foo
        list:
          - one
          - two
        ---
        template
        """;
    Prompt prompt = promptLoader.parse(content);

    assertThat(prompt.template()).isEqualTo("template\n");

    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("key", "value");

    @SuppressWarnings("unchecked")
    Map<String, Object> nested = (Map<String, Object>) ext.get("nested");
    assertThat(nested).containsEntry("inner", "foo");
  }

  @Test
  public void parse_knownKeys() throws IOException {
    String content = "---\nname: my-prompt\nmodel: gemini-pro\n---\n";
    Prompt prompt = promptLoader.parse(content);

    assertThat(prompt.config()).containsEntry("name", "my-prompt");
    assertThat(prompt.config()).containsEntry("model", "gemini-pro");
    assertThat(prompt.config()).doesNotContainKey("ext");
  }
}
