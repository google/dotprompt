// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

package com.google.dotprompt

import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.runners.JUnit4

@RunWith(JUnit4::class)
class DotpromptLexerTest {

    private data class Token(val type: String, val text: String, val start: Int, val state: Int)

    private fun lex(text: String, startOffset: Int = 0, initialState: Int = 0): List<Token> {
        val lexer = DotpromptLexer()
        lexer.start(text, startOffset, text.length, initialState)
        val tokens = mutableListOf<Token>()
        while (lexer.tokenType != null) {
            tokens +=
                Token(
                    lexer.tokenType.toString(),
                    text.substring(lexer.tokenStart, lexer.tokenEnd),
                    lexer.tokenStart,
                    lexer.state,
                )
            lexer.advance()
        }
        return tokens
    }

    /** Tokens as `TYPE:text`, dropping whitespace-only TEXT to keep expectations readable. */
    private fun render(text: String): List<String> =
        lex(text).filter { !(it.type == "TEXT" && it.text.isBlank()) }.map { "${it.type}:${it.text}" }

    @Test
    fun helperCall() {
        assertEquals(
            listOf(
                "HANDLEBARS_OPEN:{{",
                "HANDLEBARS_HELPER:role",
                "TEXT:\"system\"",
                "HANDLEBARS_CLOSE:}}",
            ),
            render("{{role \"system\"}}"),
        )
    }

    @Test
    fun variablesAndPaths() {
        assertEquals(
            listOf(
                "TEXT:Hi ",
                "HANDLEBARS_OPEN:{{",
                "HANDLEBARS_VARIABLE:user.name",
                "HANDLEBARS_CLOSE:}}",
                "TEXT:, ",
                "HANDLEBARS_OPEN:{{{",
                "HANDLEBARS_VARIABLE:@root.raw",
                "HANDLEBARS_CLOSE:}}}",
                "TEXT:!",
            ),
            render("Hi {{user.name}}, {{{@root.raw}}}!"),
        )
    }

    @Test
    fun helperNamesOnlyInHelperPosition() {
        // `history` as an argument is a variable; `role` inside a subexpression is a helper.
        assertEquals(
            listOf(
                "HANDLEBARS_OPEN:{{#",
                "HANDLEBARS_HELPER:each",
                "HANDLEBARS_VARIABLE:history",
                "HANDLEBARS_CLOSE:}}",
                "HANDLEBARS_OPEN:{{",
                "HANDLEBARS_HELPER:json",
                "TEXT:(",
                "HANDLEBARS_HELPER:lookup",
                "HANDLEBARS_VARIABLE:this",
                "TEXT:'role'",
                "TEXT:)",
                "HANDLEBARS_CLOSE:}}",
                "HANDLEBARS_OPEN:{{/",
                "HANDLEBARS_HELPER:each",
                "HANDLEBARS_CLOSE:}}",
            ),
            render("{{#each history}}{{json (lookup this 'role')}}{{/each}}"),
        )
    }

    @Test
    fun elseIfAndWhitespaceControl() {
        assertEquals(
            listOf(
                "HANDLEBARS_OPEN:{{~",
                "HANDLEBARS_HELPER:else",
                "HANDLEBARS_HELPER:if",
                "HANDLEBARS_VARIABLE:ready",
                "HANDLEBARS_CLOSE:~}}",
            ),
            render("{{~else if ready~}}"),
        )
    }

    @Test
    fun literalsAndHashArgs() {
        assertEquals(
            listOf(
                "HANDLEBARS_OPEN:{{",
                "HANDLEBARS_HELPER:media",
                "HANDLEBARS_VARIABLE:url",
                "TEXT:=",
                "HANDLEBARS_VARIABLE:photo",
                "HANDLEBARS_VARIABLE:n",
                "TEXT:=",
                "TEXT:42",
                "HANDLEBARS_VARIABLE:ok",
                "TEXT:=",
                "TEXT:true",
                "HANDLEBARS_CLOSE:}}",
            ),
            render("{{media url=photo n=42 ok=true}}"),
        )
    }

    @Test
    fun commentsAndRawMarkers() {
        assertEquals(
            listOf("COMMENT:{{! role }}", "TEXT:<<<dotprompt:role:system>>>"),
            render("{{! role }}<<<dotprompt:role:system>>>"),
        )
    }

    @Test
    fun unterminatedStringStopsAtCloser() {
        assertEquals(
            listOf(
                "HANDLEBARS_OPEN:{{",
                "HANDLEBARS_HELPER:section",
                "TEXT:\"x",
                "HANDLEBARS_CLOSE:}}",
                "TEXT: tail",
            ),
            render("{{section \"x}} tail"),
        )
    }

    @Test
    fun frontmatterIsUnchanged() {
        // Inside frontmatter `{{` is only an opener; the rest of the line stays TEXT.
        assertEquals(
            listOf(
                "HEADER_COMMENT:# header\n",
                "FRONTMATTER_DELIMITER:---",
                "TEXT:\nmodel: x\n",
                "YAML_KEY:note",
                "TEXT:: ",
                "HANDLEBARS_OPEN:{{",
                "TEXT:role}}\n",
                "FRONTMATTER_DELIMITER:---",
                "HANDLEBARS_OPEN:{{",
                "HANDLEBARS_HELPER:role",
                "TEXT:\"user\"",
                "HANDLEBARS_CLOSE:}}",
            ),
            render("# header\n---\nmodel: x\nnote: {{role}}\n---\n{{role \"user\"}}"),
        )
    }

    @Test
    fun restartFromAnyTokenBoundaryMatchesFullLex() {
        // The highlighter relexes from a token's start offset using the state reported for
        // that token, so resuming at every token must reproduce the rest of the full lex.
        val text =
            "---\nmodel: x\n---\n{{role \"system\"}}\nHi {{#if user.name}}{{{user.name}}}{{else}}?{{/if}}\n" +
                "{{~json (lookup this 'k') n=1~}}{{! c }}{{history}}"
        val full = lex(text)
        for (i in full.indices) {
            val resumed = lex(text, full[i].start, full[i].state)
            assertEquals("resume at offset ${full[i].start}", full.subList(i, full.size), resumed)
        }
    }
}
