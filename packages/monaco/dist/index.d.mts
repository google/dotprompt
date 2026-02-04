import * as monaco from 'monaco-editor';

/**
 * Copyright 2026 Google LLC
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

/**
 * Creates a completion provider for Dotprompt files.
 */
declare function createCompletionProvider(monacoInstance: typeof monaco): monaco.languages.CompletionItemProvider;

/**
 * Copyright 2026 Google LLC
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

/**
 * Creates a hover provider for Dotprompt files.
 */
declare function createHoverProvider(monacoInstance: typeof monaco): monaco.languages.HoverProvider;

/**
 * Copyright 2026 Google LLC
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

/**
 * Language ID for Dotprompt files.
 */
declare const LANGUAGE_ID = "dotprompt";
/**
 * Monarch tokenizer for Dotprompt syntax highlighting.
 * Handles YAML frontmatter, Handlebars templates, and Dotprompt markers.
 */
declare const monarchLanguage: monaco.languages.IMonarchLanguage;
/**
 * Language configuration for Dotprompt.
 * Provides bracket matching, auto-closing, and comment toggling.
 */
declare const languageConfiguration: monaco.languages.LanguageConfiguration;

/**
 * Copyright 2026 Google LLC
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
/**
 * Monaco Editor language support for Dotprompt (.prompt) files.
 *
 * Provides syntax highlighting, autocompletion, and hover documentation
 * for Dotprompt files in Monaco-based editors.
 *
 * @example
 * ```typescript
 * import * as monaco from 'monaco-editor';
 * import { registerDotpromptLanguage } from '@dotprompt/monaco';
 *
 * // Register the language
 * registerDotpromptLanguage(monaco);
 *
 * // Create an editor with Dotprompt support
 * const editor = monaco.editor.create(container, {
 *   value: '---\nmodel: gemini-2.0-flash\n---\nHello {{ name }}!',
 *   language: 'dotprompt',
 * });
 * ```
 *
 * @module @dotprompt/monaco
 */

/**
 * Options for registering the Dotprompt language.
 */
interface RegisterOptions {
    /**
     * Enable completion provider.
     * @default true
     */
    completions?: boolean;
    /**
     * Enable hover provider.
     * @default true
     */
    hover?: boolean;
    /**
     * Custom themes to register.
     * Themes are keyed by name and contain token color rules.
     */
    themes?: Record<string, monaco.editor.IStandaloneThemeData>;
}
/**
 * Registers the Dotprompt language with Monaco Editor.
 *
 * This function:
 * 1. Registers the language ID ('dotprompt')
 * 2. Sets up syntax highlighting using the Monarch tokenizer
 * 3. Configures language features (brackets, comments, folding)
 * 4. Optionally registers completion and hover providers
 *
 * @param monacoInstance - The Monaco Editor instance
 * @param options - Optional configuration
 * @returns Disposable to unregister the language
 *
 * @example
 * ```typescript
 * import * as monaco from 'monaco-editor';
 * import { registerDotpromptLanguage } from '@dotprompt/monaco';
 *
 * const disposable = registerDotpromptLanguage(monaco, {
 *   completions: true,
 *   hover: true,
 * });
 *
 * // Later, to unregister:
 * disposable.dispose();
 * ```
 */
declare function registerDotpromptLanguage(monacoInstance: typeof monaco, options?: RegisterOptions): monaco.IDisposable;
/**
 * Default theme rules for Dotprompt syntax highlighting.
 * Can be merged into your existing theme or used standalone.
 */
declare const dotpromptThemeRules: monaco.editor.ITokenThemeRule[];
/**
 * Creates a complete theme with Dotprompt token rules.
 *
 * @param base - Base theme ('vs', 'vs-dark', or 'hc-black')
 * @param name - Theme name
 * @returns Theme data for use with monaco.editor.defineTheme
 */
declare function createDotpromptTheme(base?: 'vs' | 'vs-dark' | 'hc-black', name?: string): monaco.editor.IStandaloneThemeData;

export { LANGUAGE_ID, type RegisterOptions, createCompletionProvider, createDotpromptTheme, createHoverProvider, dotpromptThemeRules, languageConfiguration, monarchLanguage, registerDotpromptLanguage };
