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

package com.google.dotprompt.smoke;

import static com.google.common.base.Strings.isNullOrEmpty;
import static com.google.common.truth.Truth.assertThat;

import com.google.dotprompt.smoke.Smoke;
import com.github.jknack.handlebars.Context;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;
import java.io.IOException;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for {@link Smoke}. */
@RunWith(JUnit4.class)
public final class SmokeTest {

  @Test
  public void square_calculatesSquare() {
    assertThat(Smoke.square(0)).isEqualTo(0);
    assertThat(Smoke.square(1)).isEqualTo(1);
    assertThat(Smoke.square(2)).isEqualTo(4);
    assertThat(Smoke.square(3)).isEqualTo(9);
    assertThat(Smoke.square(-4)).isEqualTo(16);
  }

  @Test
  public void guava_isNullOrEmpty() {
    assertThat(isNullOrEmpty(null)).isTrue();
    assertThat(isNullOrEmpty("")).isTrue();
    assertThat(isNullOrEmpty("hello")).isFalse();
  }

  @Test
  public void handlebars_rendersTemplate() throws IOException {
    Handlebars handlebars = new Handlebars();
    Template template = handlebars.compileInline("Hello {{name}}!");
    Context context = Context.newContext(
        Map.of("name", "World")
    );
    String result = template.apply(context);
    assertThat(result).isEqualTo("Hello World!");
  }
}