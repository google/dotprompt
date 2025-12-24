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

package com.google.dotprompt.helpers;

import static com.google.common.truth.Truth.assertThat;

import com.github.jknack.handlebars.EscapingStrategy;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;
import java.io.IOException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/**
 * Tests for the Helpers class.
 *
 * <p>These tests verify that all Handlebars helpers produce the expected output markers and handle
 * edge cases correctly. Test coverage matches the Python implementation for full parity.
 */
@RunWith(JUnit4.class)
public class HelpersTest {

  private Handlebars handlebars;

  @Before
  public void setUp() {
    handlebars = new Handlebars().with(EscapingStrategy.NOOP);
    Helpers.register(handlebars);
  }

  @Test
  public void testJsonHelper_basicObject() throws IOException {
    Map<String, Object> data = new HashMap<>();
    data.put("name", "John");
    data.put("age", 30);

    Template template = handlebars.compileInline("{{json data}}");
    Map<String, Object> context = new HashMap<>();
    context.put("data", data);

    String result = template.apply(context);
    assertThat(result).contains("\"name\":\"John\"");
    assertThat(result).contains("\"age\":30");
  }

  @Test
  public void testJsonHelper_withIndent() throws IOException {
    Map<String, Object> data = new HashMap<>();
    data.put("name", "John");
    data.put("age", 30);

    Template template = handlebars.compileInline("{{json data indent=2}}");
    Map<String, Object> context = new HashMap<>();
    context.put("data", data);

    // With indentation, the result should contain newlines
    String result = template.apply(context);
    assertThat(result).contains("\n");
    assertThat(result).contains("\"name\"");
    assertThat(result).contains("\"John\"");
  }

  @Test
  public void testJsonHelper_withArray() throws IOException {
    Template template = handlebars.compileInline("{{json data}}");
    Map<String, Object> context = new HashMap<>();
    context.put("data", Arrays.asList(1, 2, 3));

    String result = template.apply(context);
    assertThat(result).isEqualTo("[1,2,3]");
  }

  @Test
  public void testRoleHelper_system() throws IOException {
    Template template = handlebars.compileInline("{{role \"system\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:role:system>>>");
  }

  @Test
  public void testRoleHelper_user() throws IOException {
    Template template = handlebars.compileInline("{{role \"user\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:role:user>>>");
  }

  @Test
  public void testRoleHelper_model() throws IOException {
    Template template = handlebars.compileInline("{{role \"model\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:role:model>>>");
  }

  @Test
  public void testRoleHelper_empty() throws IOException {
    Template template = handlebars.compileInline("{{role}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("");
  }

  @Test
  public void testHistoryHelper() throws IOException {
    Template template = handlebars.compileInline("{{history}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:history>>>");
  }

  @Test
  public void testSectionHelper() throws IOException {
    Template template = handlebars.compileInline("{{section \"example\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:section example>>>");
  }

  @Test
  public void testSectionHelper_empty() throws IOException {
    Template template = handlebars.compileInline("{{section}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("");
  }

  @Test
  public void testMediaHelper_withUrl() throws IOException {
    Template template = handlebars.compileInline("{{media url=\"https://example.com/img.png\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:media:url https://example.com/img.png>>>");
  }

  @Test
  public void testMediaHelper_withUrlAndContentType() throws IOException {
    Template template =
        handlebars.compileInline(
            "{{media url=\"https://example.com/img.png\" contentType=\"image/png\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:media:url https://example.com/img.png image/png>>>");
  }

  @Test
  public void testIfEquals_equalIntValues() throws IOException {
    Template template = handlebars.compileInline("{{#ifEquals a b}}yes{{else}}no{{/ifEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", 1);
    context.put("b", 1);
    assertThat(template.apply(context)).isEqualTo("yes");
  }

  @Test
  public void testIfEquals_unequalIntValues() throws IOException {
    Template template = handlebars.compileInline("{{#ifEquals a b}}yes{{else}}no{{/ifEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", 1);
    context.put("b", 2);
    assertThat(template.apply(context)).isEqualTo("no");
  }

  @Test
  public void testIfEquals_equalStringValues() throws IOException {
    Template template = handlebars.compileInline("{{#ifEquals a b}}yes{{else}}no{{/ifEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", "test");
    context.put("b", "test");
    assertThat(template.apply(context)).isEqualTo("yes");
  }

  @Test
  public void testIfEquals_unequalStringValues() throws IOException {
    Template template = handlebars.compileInline("{{#ifEquals a b}}yes{{else}}no{{/ifEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", "test");
    context.put("b", "diff");
    assertThat(template.apply(context)).isEqualTo("no");
  }

  @Test
  public void testUnlessEquals_unequalIntValues() throws IOException {
    Template template =
        handlebars.compileInline("{{#unlessEquals a b}}yes{{else}}no{{/unlessEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", 1);
    context.put("b", 2);
    assertThat(template.apply(context)).isEqualTo("yes");
  }

  @Test
  public void testUnlessEquals_equalIntValues() throws IOException {
    Template template =
        handlebars.compileInline("{{#unlessEquals a b}}yes{{else}}no{{/unlessEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", 1);
    context.put("b", 1);
    assertThat(template.apply(context)).isEqualTo("no");
  }

  @Test
  public void testUnlessEquals_unequalStringValues() throws IOException {
    Template template =
        handlebars.compileInline("{{#unlessEquals a b}}yes{{else}}no{{/unlessEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", "test");
    context.put("b", "diff");
    assertThat(template.apply(context)).isEqualTo("yes");
  }

  @Test
  public void testUnlessEquals_equalStringValues() throws IOException {
    Template template =
        handlebars.compileInline("{{#unlessEquals a b}}yes{{else}}no{{/unlessEquals}}");

    Map<String, Object> context = new HashMap<>();
    context.put("a", "test");
    context.put("b", "test");
    assertThat(template.apply(context)).isEqualTo("no");
  }
}
