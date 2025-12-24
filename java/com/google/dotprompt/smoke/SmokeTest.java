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

import static com.google.common.truth.Truth.assertThat;

import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.dotprompt.Dotprompt;
import com.google.dotprompt.PromptLoader;
import com.google.dotprompt.models.Prompt;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.TextPart;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for {@link Smoke}. */
@RunWith(JUnit4.class)
public final class SmokeTest {

  @Test
  public void dotprompt_rendersSimpleTemplate() throws Exception {
    PromptLoader loader =
        new PromptLoader() {
          @Override
          public ListenableFuture<Prompt> load(String name) {
            if ("hello".equals(name)) {
              return Futures.immediateFuture(new Prompt("Hello {{name}}!", Map.of()));
            }
            return super.load(name);
          }
        };

    Dotprompt dotprompt = new Dotprompt(loader);
    RenderedPrompt result = dotprompt.render("hello", Map.of("name", "World")).get();

    assertThat(result.messages()).hasSize(1);
    assertThat(((TextPart) result.messages().get(0).content().get(0)).text())
        .isEqualTo("Hello World!");
  }
}
