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

import com.intellij.psi.tree.IElementType

/**
 * Token types for Dotprompt syntax highlighting.
 */
object DotpromptTokenTypes {
    @JvmField val FRONTMATTER_DELIMITER = IElementType("FRONTMATTER_DELIMITER", DotpromptLanguage.INSTANCE)
    @JvmField val YAML_KEY = IElementType("YAML_KEY", DotpromptLanguage.INSTANCE)
    @JvmField val YAML_VALUE = IElementType("YAML_VALUE", DotpromptLanguage.INSTANCE)
    @JvmField val HANDLEBARS_OPEN = IElementType("HANDLEBARS_OPEN", DotpromptLanguage.INSTANCE)
    @JvmField val HANDLEBARS_CLOSE = IElementType("HANDLEBARS_CLOSE", DotpromptLanguage.INSTANCE)
    @JvmField val HANDLEBARS_HELPER = IElementType("HANDLEBARS_HELPER", DotpromptLanguage.INSTANCE)
    @JvmField val HANDLEBARS_VARIABLE = IElementType("HANDLEBARS_VARIABLE", DotpromptLanguage.INSTANCE)
    @JvmField val MARKER = IElementType("MARKER", DotpromptLanguage.INSTANCE)
    @JvmField val COMMENT = IElementType("COMMENT", DotpromptLanguage.INSTANCE)
    @JvmField val HEADER_COMMENT = IElementType("HEADER_COMMENT", DotpromptLanguage.INSTANCE)
    @JvmField val TEXT = IElementType("TEXT", DotpromptLanguage.INSTANCE)
}
