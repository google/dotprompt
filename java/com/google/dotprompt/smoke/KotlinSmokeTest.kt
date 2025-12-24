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
import com.google.dotprompt.PromptLoader
import com.google.dotprompt.models.RenderedPrompt
import com.google.dotprompt.models.TextPart
import com.google.dotprompt.models.Prompt
import com.google.common.truth.Truth.assertThat
import com.google.common.util.concurrent.Futures
import com.google.common.util.concurrent.ListenableFuture
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.JUnit4

@RunWith(JUnit4::class)
class KotlinSmokeTest {

    @Test
    fun testBasicRender() {
        val loader = object : PromptLoader() {
            override fun load(name: String): ListenableFuture<Prompt> {
                if (name == "test") {
                    try {
                        return Futures.immediateFuture(parse("{{> greeting}}"))
                    } catch (e: Exception) {
                        return Futures.immediateFailedFuture(e)
                    }
                }
                return super.load(name)
            }
        }
        
        val dotprompt = Dotprompt(loader)
        dotprompt.registerPartial("greeting", "Hello, {{name}}!")

        val rendered: RenderedPrompt = dotprompt.render(
            "test",
            mapOf("name" to "Kotlin")
        ).get()

        assertThat(rendered.messages()).hasSize(1)
        val firstPart = rendered.messages()[0].content()[0]
        assertThat(firstPart).isInstanceOf(TextPart::class.java)
        assertThat((firstPart as TextPart).text()).isEqualTo("Hello, Kotlin!")
    }

    @Test
    fun testModelConfig() {
        val loader = object : PromptLoader() {
            override fun load(name: String): ListenableFuture<Prompt> {
                if (name == "configured") {
                    return Futures.immediateFuture(parse("---\nmodel: test-model\n---\nBody"))
                }
                return super.load(name)
            }
        }

        val dotprompt = Dotprompt(loader)
        dotprompt.defineModelConfig("test-model", mapOf("temperature" to 0.7))

        val rendered = dotprompt.render("configured", emptyMap()).get()
        assertThat(rendered.config()).containsEntry("model", "test-model")
        assertThat(rendered.config()).containsEntry("temperature", 0.7)
    }
}
