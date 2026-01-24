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

import com.intellij.lexer.Lexer
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors
import com.intellij.openapi.editor.HighlighterColors
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.fileTypes.SyntaxHighlighter
import com.intellij.openapi.fileTypes.SyntaxHighlighterBase
import com.intellij.openapi.fileTypes.SyntaxHighlighterFactory
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.psi.tree.IElementType

/**
 * Syntax highlighter factory for Dotprompt files.
 */
class DotpromptSyntaxHighlighterFactory : SyntaxHighlighterFactory() {
    override fun getSyntaxHighlighter(project: Project?, virtualFile: VirtualFile?): SyntaxHighlighter {
        return DotpromptSyntaxHighlighter()
    }
}

/**
 * Syntax highlighter for Dotprompt files.
 * 
 * Note: This is a simplified highlighter. For production, you'd want a proper
 * lexer that handles YAML frontmatter and Handlebars syntax distinctly.
 */
class DotpromptSyntaxHighlighter : SyntaxHighlighterBase() {

    override fun getHighlightingLexer(): Lexer = DotpromptLexer()

    override fun getTokenHighlights(tokenType: IElementType): Array<TextAttributesKey> {
        return when (tokenType) {
            DotpromptTokenTypes.FRONTMATTER_DELIMITER -> FRONTMATTER_DELIMITER_KEYS
            DotpromptTokenTypes.YAML_KEY -> YAML_KEY_KEYS
            DotpromptTokenTypes.YAML_VALUE -> YAML_VALUE_KEYS
            DotpromptTokenTypes.HANDLEBARS_OPEN -> HANDLEBARS_BRACE_KEYS
            DotpromptTokenTypes.HANDLEBARS_CLOSE -> HANDLEBARS_BRACE_KEYS
            DotpromptTokenTypes.HANDLEBARS_HELPER -> HANDLEBARS_HELPER_KEYS
            DotpromptTokenTypes.HANDLEBARS_VARIABLE -> HANDLEBARS_VARIABLE_KEYS
            DotpromptTokenTypes.MARKER -> MARKER_KEYS
            DotpromptTokenTypes.COMMENT -> COMMENT_KEYS
            DotpromptTokenTypes.HEADER_COMMENT -> COMMENT_KEYS
            else -> EMPTY_KEYS
        }
    }

    companion object {
        private val EMPTY_KEYS = arrayOf<TextAttributesKey>()

        private val FRONTMATTER_DELIMITER = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_FRONTMATTER_DELIMITER",
            DefaultLanguageHighlighterColors.MARKUP_TAG
        )
        private val YAML_KEY = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_YAML_KEY",
            DefaultLanguageHighlighterColors.KEYWORD
        )
        private val YAML_VALUE = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_YAML_VALUE",
            DefaultLanguageHighlighterColors.STRING
        )
        private val HANDLEBARS_BRACE = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_HANDLEBARS_BRACE",
            DefaultLanguageHighlighterColors.BRACES
        )
        private val HANDLEBARS_HELPER = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_HANDLEBARS_HELPER",
            DefaultLanguageHighlighterColors.FUNCTION_CALL
        )
        private val HANDLEBARS_VARIABLE = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_HANDLEBARS_VARIABLE",
            DefaultLanguageHighlighterColors.IDENTIFIER
        )
        private val MARKER = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_MARKER",
            DefaultLanguageHighlighterColors.METADATA
        )
        private val COMMENT = TextAttributesKey.createTextAttributesKey(
            "DOTPROMPT_COMMENT",
            DefaultLanguageHighlighterColors.LINE_COMMENT
        )

        private val FRONTMATTER_DELIMITER_KEYS = arrayOf(FRONTMATTER_DELIMITER)
        private val YAML_KEY_KEYS = arrayOf(YAML_KEY)
        private val YAML_VALUE_KEYS = arrayOf(YAML_VALUE)
        private val HANDLEBARS_BRACE_KEYS = arrayOf(HANDLEBARS_BRACE)
        private val HANDLEBARS_HELPER_KEYS = arrayOf(HANDLEBARS_HELPER)
        private val HANDLEBARS_VARIABLE_KEYS = arrayOf(HANDLEBARS_VARIABLE)
        private val MARKER_KEYS = arrayOf(MARKER)
        private val COMMENT_KEYS = arrayOf(COMMENT)
    }
}
