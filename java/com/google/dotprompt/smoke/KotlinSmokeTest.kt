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

package com.google.dotprompt.smoke

import com.google.dotprompt.Dotprompt
import com.google.dotprompt.DotpromptOptions
import com.google.dotprompt.models.RenderedPrompt
import com.google.dotprompt.models.TextPart
import com.google.common.truth.Truth.assertThat
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.JUnit4

@RunWith(JUnit4::class)
class KotlinSmokeTest {

    @Test
    fun testBasicRender() {
        val dotprompt = Dotprompt(DotpromptOptions.builder().build())
        dotprompt.definePartial("greeting", "Hello, {{name}}!")

        val promptFn = dotprompt.compile("{{> greeting}}").get()
        val rendered: RenderedPrompt = promptFn.render(mapOf("name" to "Kotlin")).get()

        assertThat(rendered.messages()).hasSize(1)
        val firstPart = rendered.messages()[0].content()[0]
        assertThat(firstPart).isInstanceOf(TextPart::class.java)
        assertThat((firstPart as TextPart).text()).isEqualTo("Hello, Kotlin!")
    }

    @Test
    fun testModelConfig() {
        val options = DotpromptOptions.builder()
            .addModelConfig("test-model", mapOf("temperature" to 0.7))
            .build()
        val dotprompt = Dotprompt(options)

        val promptFn = dotprompt.compile("---\nmodel: test-model\n---\nBody").get()
        val rendered = promptFn.render(emptyMap<String, Any>()).get()

        assertThat(rendered.config()).containsEntry("model", "test-model")
        assertThat(rendered.config()).containsEntry("temperature", 0.7)
    }
}
