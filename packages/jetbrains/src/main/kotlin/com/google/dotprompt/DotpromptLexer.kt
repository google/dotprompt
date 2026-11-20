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
 * - Header comments (`#` lines before the first frontmatter delimiter)
 * - YAML frontmatter delimiters (`---`) and top-level YAML keys
 * - Handlebars comments (`{{! ... }}`)
 * - Handlebars expressions in the template body:
 *   - `{{`, `{{{`, `{{~` plus an optional `#`, `/`, `>`, `^` or `&` as HANDLEBARS_OPEN
 *   - the name in helper position (right after the opener or `(`) as
 *     HANDLEBARS_HELPER when it is a Handlebars built-in or Dotprompt helper
 *     (`{{role "system"}}`, `{{#if x}}`, `{{else if y}}`, `{{/each}}`)
 *   - any other identifier or path (`name`, `user.name`, `@root`, `this`,
 *     `../x`) as HANDLEBARS_VARIABLE
 *   - `}}`, `~}}` (and `}}}` for triple-stash) as HANDLEBARS_CLOSE
 *   - string/number/boolean literals, whitespace and punctuation as TEXT
 *
 * Inside frontmatter `{{` is still only HANDLEBARS_OPEN followed by TEXT.
 *
 * Raw `<<<dotprompt:...>>>` text is deliberately lexed as TEXT: runtimes only
 * honor nonce-tagged markers emitted by the helpers ({{role}}, {{history}},
 * {{section}}, {{media}}), so a literal marker in a template is plain text.
 *
 * The highlighter restarts lexing from a token's start offset with the value
 * [getState] reported for that token, so [getState] returns the state at the
 * start of the current token (like FlexAdapter), and everything needed to
 * resume (section of the file, whether we are inside an expression,
 * triple-stash, helper position) lives in that int. See the `STATE_*` /
 * `FLAG_*` constants.
 */
class DotpromptLexer : LexerBase() {
    private var buffer: CharSequence = ""
    private var bufferEnd: Int = 0
    private var tokenStart: Int = 0
    private var tokenEnd: Int = 0
    private var tokenType: IElementType? = null
    /** State the lexer was in when the current token started. */
    private var tokenStartState: Int = STATE_HEADER
    private var state: Int = STATE_HEADER

    companion object {
        // Low bits: which part of the file we are in.
        private const val STATE_HEADER = 0
        private const val STATE_CONTENT = 1
        private const val STATE_FRONTMATTER = 2
        private const val MODE_MASK = 0x3

        // Flags OR-ed on top of the mode while inside `{{ ... }}`.
        private const val FLAG_EXPR = 0x4
        /** Opened with `{{{`, so the closer is `}}}`. */
        private const val FLAG_TRIPLE = 0x8
        /** The next identifier is in helper position (after the opener, `(` or `else`). */
        private const val FLAG_HEAD = 0x10

        /** Handlebars built-ins plus the helpers registered by Dotprompt runtimes. */
        private val KNOWN_HELPERS = setOf(
            "if", "unless", "each", "with", "else", "log", "lookup",
            "role", "history", "section", "media", "json", "ifEquals", "unlessEquals",
        )

        private val LITERALS = setOf("true", "false", "null", "undefined")
        private val NUMBER = Regex("-?[0-9]+(\\.[0-9]+)?")

        /** Characters Handlebars excludes from identifiers (besides whitespace). */
        private const val NON_ID_CHARS = "!\"#%&'()*+,./;<=>@[\\]^`{|}~"

        /** Characters that may follow `{{` (after an optional `~`) to form the opener. */
        private const val OPEN_PREFIXES = "#/>^&"
    }

    override fun start(buffer: CharSequence, startOffset: Int, endOffset: Int, initialState: Int) {
        this.buffer = buffer
        this.bufferEnd = endOffset
        this.tokenStart = startOffset
        this.tokenEnd = startOffset
        this.state = initialState
        advance()
    }

    override fun getState(): Int = tokenStartState

    override fun getTokenType(): IElementType? = tokenType

    override fun getTokenStart(): Int = tokenStart

    override fun getTokenEnd(): Int = tokenEnd

    private val mode: Int
        get() = state and MODE_MASK

    private fun hasFlag(flag: Int): Boolean = (state and flag) != 0

    override fun advance() {
        tokenStart = tokenEnd
        tokenStartState = state
        if (tokenStart >= bufferEnd) {
            tokenType = null
            return
        }

        if (hasFlag(FLAG_EXPR)) {
            if (lookingAt("{{")) {
                // Unterminated expression: recover by treating this as a new opener.
                state = mode
            } else {
                advanceInExpression()
                return
            }
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
        if (lookingAt("{{!") || lookingAt("{{~!")) {
            val end = findEndOfHandlebars()
            tokenEnd = end
            tokenType = DotpromptTokenTypes.COMMENT
            return
        }

        // Check for Handlebars expression
        if (lookingAt("{{")) {
            if (state == STATE_FRONTMATTER) {
                tokenEnd = tokenStart + 2
            } else {
                lexOpener()
            }
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

    /** Consumes `{{`, an optional `{`, an optional `~` and an optional opener prefix. */
    private fun lexOpener() {
        var pos = tokenStart + 2
        var flags = FLAG_EXPR or FLAG_HEAD
        if (pos < bufferEnd && buffer[pos] == '{') {
            flags = flags or FLAG_TRIPLE
            pos++
        }
        if (pos < bufferEnd && buffer[pos] == '~') pos++
        if (pos < bufferEnd && buffer[pos] in OPEN_PREFIXES) pos++
        tokenEnd = pos
        state = mode or flags
    }

    private fun advanceInExpression() {
        val c = buffer[tokenStart]

        val closeLen = closerLength()
        if (closeLen > 0) {
            tokenEnd = tokenStart + closeLen
            tokenType = DotpromptTokenTypes.HANDLEBARS_CLOSE
            state = mode
            return
        }

        if (c.isWhitespace()) {
            var pos = tokenStart + 1
            while (pos < bufferEnd && buffer[pos].isWhitespace()) pos++
            tokenEnd = pos
            tokenType = DotpromptTokenTypes.TEXT
            return
        }

        if (c == '"' || c == '\'') {
            tokenEnd = findEndOfString(c)
            tokenType = DotpromptTokenTypes.TEXT
            clearFlag(FLAG_HEAD)
            return
        }

        if (c == '(') {
            tokenEnd = tokenStart + 1
            tokenType = DotpromptTokenTypes.TEXT
            state = state or FLAG_HEAD
            return
        }

        if (isPathStart(c)) {
            tokenEnd = findEndOfPath()
            val text = buffer.subSequence(tokenStart, tokenEnd).toString()
            val inHead = hasFlag(FLAG_HEAD)
            tokenType = when {
                text in LITERALS || NUMBER.matches(text) -> DotpromptTokenTypes.TEXT
                inHead && text in KNOWN_HELPERS -> DotpromptTokenTypes.HANDLEBARS_HELPER
                else -> DotpromptTokenTypes.HANDLEBARS_VARIABLE
            }
            // `{{else if x}}`: the name after `else` is still in helper position.
            if (!(inHead && text == "else")) clearFlag(FLAG_HEAD)
            return
        }

        // Anything else (`=`, `|`, `)`, a stray `}` or `~`, ...) is single-char TEXT.
        tokenEnd = tokenStart + 1
        tokenType = DotpromptTokenTypes.TEXT
        clearFlag(FLAG_HEAD)
    }

    private fun clearFlag(flag: Int) {
        state = state and flag.inv()
    }

    /** Length of the expression closer at [tokenStart], or 0 if there is none. */
    private fun closerLength(): Int {
        var pos = tokenStart
        if (pos < bufferEnd && buffer[pos] == '~') pos++
        if (!lookingAtPos(pos, "}}")) return 0
        pos += 2
        if (hasFlag(FLAG_TRIPLE) && pos < bufferEnd && buffer[pos] == '}') pos++
        return pos - tokenStart
    }

    private fun isIdChar(c: Char): Boolean = !c.isWhitespace() && c !in NON_ID_CHARS

    private fun isPathStart(c: Char): Boolean = isIdChar(c) || c == '@' || c == '.' || c == '['

    /** Consumes a path like `@root.user.name`, `../x`, `this` or `items.[0]`. */
    private fun findEndOfPath(): Int {
        var pos = tokenStart
        if (buffer[pos] == '@') pos++
        while (pos < bufferEnd) {
            val c = buffer[pos]
            when {
                isIdChar(c) || c == '.' || c == '/' -> pos++
                c == '[' -> {
                    // Literal segment; stop at `]`, a closer or end of line if unterminated.
                    pos++
                    while (pos < bufferEnd && buffer[pos] != ']' && buffer[pos] != '\n' && !lookingAtPos(pos, "}}")) pos++
                    if (pos < bufferEnd && buffer[pos] == ']') pos++
                }
                else -> return pos
            }
        }
        return pos
    }

    /**
     * Ends after the closing quote. An unterminated string stops before `}}` so
     * the closer still gets its own token; this also means a string literal that
     * itself contains `}}` is split, which is rare enough to accept.
     */
    private fun findEndOfString(quote: Char): Int {
        var pos = tokenStart + 1
        while (pos < bufferEnd) {
            val c = buffer[pos]
            if (c == '\\' && pos + 1 < bufferEnd) {
                pos += 2
                continue
            }
            if (c == quote) return pos + 1
            if (lookingAtPos(pos, "}}")) return pos
            pos++
        }
        return bufferEnd
    }

    private fun lookingAt(s: String): Boolean = lookingAtPos(tokenStart, s)

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
