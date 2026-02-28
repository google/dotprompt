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

import com.intellij.lexer.LexerBase
import com.intellij.psi.tree.IElementType

/**
 * Simple lexer for Dotprompt files.
 * 
 * This lexer recognizes:
 * - YAML frontmatter delimiters (---)
 * - Handlebars expressions ({{ ... }})
 * - Dotprompt markers (<<<dotprompt:...>>>)
 * - Comments ({{! ... }})
 */
class DotpromptLexer : LexerBase() {
    private var buffer: CharSequence = ""
    private var bufferEnd: Int = 0
    private var tokenStart: Int = 0
    private var tokenEnd: Int = 0
    private var tokenType: IElementType? = null
    private var state: Int = STATE_HEADER

    companion object {
        private const val STATE_HEADER = 0
        private const val STATE_CONTENT = 1
        private const val STATE_FRONTMATTER = 2
    }

    override fun start(buffer: CharSequence, startOffset: Int, endOffset: Int, initialState: Int) {
        this.buffer = buffer
        this.bufferEnd = endOffset
        this.tokenStart = startOffset
        this.tokenEnd = startOffset
        this.state = initialState
        advance()
    }

    override fun getState(): Int = state

    override fun getTokenType(): IElementType? = tokenType

    override fun getTokenStart(): Int = tokenStart

    override fun getTokenEnd(): Int = tokenEnd

    override fun advance() {
        tokenStart = tokenEnd
        if (tokenStart >= bufferEnd) {
            tokenType = null
            return
        }

        // Check for header comments (lines starting with # before first frontmatter)
        if (state == STATE_HEADER && (tokenStart == 0 || buffer[tokenStart - 1] == '\n') && buffer[tokenStart] == '#') {
            tokenEnd = findEndOfLine()
            tokenType = DotpromptTokenTypes.HEADER_COMMENT
            return
        }

        // Check for frontmatter delimiter
        if (lookingAt("---") && (tokenStart == 0 || buffer[tokenStart - 1] == '\n')) {
            tokenEnd = tokenStart + 3
            tokenType = DotpromptTokenTypes.FRONTMATTER_DELIMITER
            state = when (state) {
                STATE_HEADER -> STATE_FRONTMATTER
                STATE_FRONTMATTER -> STATE_CONTENT
                else -> STATE_FRONTMATTER
            }
            return
        }

        // Check for Handlebars comment
        if (lookingAt("{{!")) {
            val end = findEndOfHandlebars()
            tokenEnd = end
            tokenType = DotpromptTokenTypes.COMMENT
            return
        }

        // Check for Handlebars expression
        if (lookingAt("{{")) {
            tokenEnd = tokenStart + 2
            tokenType = DotpromptTokenTypes.HANDLEBARS_OPEN
            return
        }

        if (lookingAt("}}")) {
            tokenEnd = tokenStart + 2
            tokenType = DotpromptTokenTypes.HANDLEBARS_CLOSE
            return
        }

        // In frontmatter, look for YAML keys
        if (state == STATE_FRONTMATTER) {
            val colonPos = findColon()
            if (colonPos > tokenStart && buffer[tokenStart].isLetter()) {
                tokenEnd = colonPos
                tokenType = DotpromptTokenTypes.YAML_KEY
                return
            }
        }

        // Default: consume as text until next interesting token
        tokenEnd = findNextToken()
        tokenType = DotpromptTokenTypes.TEXT
    }

    override fun getBufferSequence(): CharSequence = buffer

    override fun getBufferEnd(): Int = bufferEnd

    private fun lookingAt(s: String): Boolean {
        if (tokenStart + s.length > bufferEnd) return false
        for (i in s.indices) {
            if (buffer[tokenStart + i] != s[i]) return false
        }
        return true
    }

    private fun findEndOfHandlebars(): Int {
        var pos = tokenStart
        while (pos < bufferEnd - 1) {
            if (buffer[pos] == '}' && buffer[pos + 1] == '}') {
                return pos + 2
            }
            pos++
        }
        return bufferEnd
    }

    private fun findColon(): Int {
        var pos = tokenStart
        while (pos < bufferEnd && buffer[pos] != ':' && buffer[pos] != '\n') {
            pos++
        }
        return if (pos < bufferEnd && buffer[pos] == ':') pos else tokenStart
    }

    private fun findNextToken(): Int {
        var pos = tokenStart + 1
        while (pos < bufferEnd) {
            if (lookingAtPos(pos, "---") || 
                lookingAtPos(pos, "{{")) {
                return pos
            }
            if (buffer[pos] == '\n' && state == STATE_FRONTMATTER) {
                return pos + 1
            }
            // In header state, also watch for # comments
            if (buffer[pos] == '\n' && state == STATE_HEADER) {
                return pos + 1
            }
            pos++
        }
        return bufferEnd
    }

    private fun findEndOfLine(): Int {
        var pos = tokenStart
        while (pos < bufferEnd && buffer[pos] != '\n') {
            pos++
        }
        return if (pos < bufferEnd) pos + 1 else pos
    }

    private fun lookingAtPos(pos: Int, s: String): Boolean {
        if (pos + s.length > bufferEnd) return false
        for (i in s.indices) {
            if (buffer[pos + i] != s[i]) return false
        }
        return true
    }
}
