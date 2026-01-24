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

import com.intellij.openapi.fileTypes.LanguageFileType
import javax.swing.Icon

/**
 * File type definition for Dotprompt (.prompt) files.
 */
class DotpromptFileType private constructor() : LanguageFileType(DotpromptLanguage.INSTANCE) {

    override fun getName(): String = "Dotprompt"

    override fun getDescription(): String = "Dotprompt file"

    override fun getDefaultExtension(): String = "prompt"

    override fun getIcon(): Icon? = DotpromptIcons.FILE

    companion object {
        @JvmField
        val INSTANCE = DotpromptFileType()
    }
}
