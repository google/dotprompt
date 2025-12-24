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

import com.github.jknack.handlebars.EscapingStrategy;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

@RunWith(JUnit4.class)
public class HelpersTest {

  private Handlebars handlebars;

  @Before
  public void setUp() {
    handlebars = new Handlebars().with(EscapingStrategy.NOOP);
    Helpers.register(
        new Dotprompt(new PromptLoader()) {
          @Override
          public void registerHelper(String name, com.github.jknack.handlebars.Helper<?> helper) {
            handlebars.registerHelper(name, helper);
          }
        });
  }

  @Test
  public void testDiagnostic() throws IOException {
    handlebars.registerHelper(
        "diag",
        new com.github.jknack.handlebars.Helper<Object>() {
          @Override
          public Object apply(Object context, com.github.jknack.handlebars.Options options)
              throws IOException {
            return "Params: " + options.params.length + ", Context: " + context;
          }
        });
    Template template = handlebars.compileInline("{{diag 123}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("Params: 0, Context: 123");
  }

  @Test
  public void testJsonHelper() throws IOException {
    Map<String, Object> data = new HashMap<>();
    data.put("foo", "bar");
    data.put("num", 123);

    Template template = handlebars.compileInline("{{json data}}");
    Map<String, Object> context = new HashMap<>();
    context.put("data", data);

    String result = template.apply(context);
    assertThat(result).contains("\"foo\":\"bar\"");
    assertThat(result).contains("\"num\":123");
  }

  @Test
  public void testMediaHelper() throws IOException {
    Template template =
        handlebars.compileInline(
            "{{media url=\"http://example.com/img.jpg\" contentType=\"image/jpeg\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:media:url http://example.com/img.jpg image/jpeg>>>");
  }

  @Test
  public void testRoleHelper() throws IOException {
    Template template = handlebars.compileInline("{{role \"model\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:role:model>>>");
  }

  @Test
  public void testRoleHelperEmpty() throws IOException {
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
    Template template = handlebars.compileInline("{{section \"foo\"}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("<<<dotprompt:section foo>>>");
  }

  @Test
  public void testSectionHelperEmpty() throws IOException {
    Template template = handlebars.compileInline("{{section}}");
    String result = template.apply(new HashMap<>());
    assertThat(result).isEqualTo("");
  }

  @Test
  public void testIfEquals() throws IOException {
    Template template =
        handlebars.compileInline("{{#ifEquals a b}}equal{{else}}not equal{{/ifEquals}}");

    Map<String, Object> ctx3 = new HashMap<>();
    ctx3.put("a", 5);
    ctx3.put("b", 5);
    assertThat(template.apply(ctx3)).isEqualTo("equal");
  }

  @Test
  public void testUnlessEquals() throws IOException {
    Template template =
        handlebars.compileInline("{{#unlessEquals a b}}different{{else}}same{{/unlessEquals}}");

    Map<String, Object> ctx1 = new HashMap<>();
    ctx1.put("a", "foo");
    ctx1.put("b", "bar");
    assertThat(template.apply(ctx1)).isEqualTo("different");

    Map<String, Object> ctx2 = new HashMap<>();
    ctx2.put("a", "foo");
    ctx2.put("b", "foo");
    assertThat(template.apply(ctx2)).isEqualTo("same");
  }
}
