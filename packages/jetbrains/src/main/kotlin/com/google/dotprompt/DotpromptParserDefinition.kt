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

import com.intellij.extapi.psi.PsiFileBase
import com.intellij.lang.ASTNode
import com.intellij.lang.ParserDefinition
import com.intellij.lang.PsiParser
import com.intellij.lexer.Lexer
import com.intellij.openapi.fileTypes.FileType
import com.intellij.openapi.project.Project
import com.intellij.psi.FileViewProvider
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFile
import com.intellij.psi.tree.IFileElementType
import com.intellij.psi.tree.TokenSet

/**
 * Parser definition for Dotprompt files.
 * 
 * Note: This is a minimal implementation. The actual parsing is handled by the LSP.
 */
class DotpromptParserDefinition : ParserDefinition {

    override fun createLexer(project: Project?): Lexer = DotpromptLexer()

    override fun createParser(project: Project?): PsiParser {
        return PsiParser { root, builder ->
            val marker = builder.mark()
            while (!builder.eof()) {
                builder.advanceLexer()
            }
            marker.done(root)
            builder.treeBuilt
        }
    }

    override fun getFileNodeType(): IFileElementType = FILE

    override fun getCommentTokens(): TokenSet = COMMENTS

    override fun getStringLiteralElements(): TokenSet = TokenSet.EMPTY

    override fun createElement(node: ASTNode): PsiElement {
        throw UnsupportedOperationException("Not implemented")
    }

    override fun createFile(viewProvider: FileViewProvider): PsiFile = DotpromptFile(viewProvider)

    companion object {
        val FILE = IFileElementType(DotpromptLanguage.INSTANCE)
        val COMMENTS = TokenSet.create(DotpromptTokenTypes.COMMENT)
    }
}

/**
 * PSI file for Dotprompt.
 */
class DotpromptFile(viewProvider: FileViewProvider) : PsiFileBase(viewProvider, DotpromptLanguage.INSTANCE) {
    override fun getFileType(): FileType = DotpromptFileType.INSTANCE
}
