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
 *   value: '---\nmodel: gemini-2.5-flash\n---\nHello {{ name }}!',
 *   language: 'dotprompt',
 * });
 * ```
 *
 * @module @dotprompt/monaco
 */

import type * as monaco from 'monaco-editor';
import { createCompletionProvider } from './completions';
import { createHoverProvider } from './hover';
import {
  LANGUAGE_ID,
  languageConfiguration,
  monarchLanguage,
} from './language';

export { createCompletionProvider } from './completions';
export { createHoverProvider } from './hover';
export {
  LANGUAGE_ID,
  languageConfiguration,
  monarchLanguage,
} from './language';

/**
 * Options for registering the Dotprompt language.
 */
export interface RegisterOptions {
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
export function registerDotpromptLanguage(
  monacoInstance: typeof monaco,
  options: RegisterOptions = {}
): monaco.IDisposable {
  const { completions = true, hover = true, themes } = options;

  const disposables: monaco.IDisposable[] = [];

  // Register the language
  monacoInstance.languages.register({
    id: LANGUAGE_ID,
    extensions: ['.prompt'],
    aliases: ['Dotprompt', 'dotprompt'],
    mimetypes: ['text/x-dotprompt'],
  });

  // Register the Monarch tokenizer
  monacoInstance.languages.setMonarchTokensProvider(
    LANGUAGE_ID,
    monarchLanguage
  );

  // Register the language configuration
  monacoInstance.languages.setLanguageConfiguration(
    LANGUAGE_ID,
    languageConfiguration
  );

  // Register completion provider
  if (completions) {
    disposables.push(
      monacoInstance.languages.registerCompletionItemProvider(
        LANGUAGE_ID,
        createCompletionProvider(monacoInstance)
      )
    );
  }

  // Register hover provider
  if (hover) {
    disposables.push(
      monacoInstance.languages.registerHoverProvider(
        LANGUAGE_ID,
        createHoverProvider(monacoInstance)
      )
    );
  }

  // Register custom themes if provided
  if (themes) {
    for (const [themeName, themeData] of Object.entries(themes)) {
      monacoInstance.editor.defineTheme(themeName, themeData);
    }
  }

  // Return a disposable that cleans up all registered providers
  return {
    dispose() {
      for (const disposable of disposables) {
        disposable.dispose();
      }
    },
  };
}

/**
 * Default theme rules for Dotprompt syntax highlighting.
 * Can be merged into your existing theme or used standalone.
 */
export const dotpromptThemeRules: monaco.editor.ITokenThemeRule[] = [
  // Frontmatter
  { token: 'delimiter.frontmatter', foreground: '6A9955' },
  { token: 'keyword.yaml', foreground: '569CD6' },
  { token: 'variable.yaml', foreground: '9CDCFE' },
  { token: 'source.yaml', foreground: 'D4D4D4' },

  // Handlebars
  { token: 'delimiter.handlebars', foreground: 'DCDCAA' },
  { token: 'delimiter.handlebars.block', foreground: 'DCDCAA' },
  { token: 'keyword.handlebars', foreground: 'C586C0' },
  { token: 'keyword.dotprompt', foreground: '4EC9B0' },
  { token: 'variable', foreground: '9CDCFE' },
  { token: 'variable.partial', foreground: 'CE9178' },
  { token: 'variable.special', foreground: '4FC1FF' },

  // Markers
  { token: 'keyword.marker', foreground: '569CD6', fontStyle: 'bold' },

  // Comments
  { token: 'comment.block', foreground: '6A9955', fontStyle: 'italic' },
  { token: 'comment.line', foreground: '6A9955', fontStyle: 'italic' },
  { token: 'comment.yaml', foreground: '6A9955', fontStyle: 'italic' },

  // Literals
  { token: 'string', foreground: 'CE9178' },
  { token: 'string.quote', foreground: 'CE9178' },
  { token: 'string.escape', foreground: 'D7BA7D' },
  { token: 'number', foreground: 'B5CEA8' },
  { token: 'constant.language', foreground: '569CD6' },
];

/**
 * Creates a complete theme with Dotprompt token rules.
 *
 * @param base - Base theme ('vs', 'vs-dark', or 'hc-black')
 * @param name - Theme name
 * @returns Theme data for use with monaco.editor.defineTheme
 */
export function createDotpromptTheme(
  base: 'vs' | 'vs-dark' | 'hc-black' = 'vs-dark',
  name: string = 'dotprompt-dark'
): monaco.editor.IStandaloneThemeData {
  return {
    base,
    inherit: true,
    rules: dotpromptThemeRules,
    colors: {},
  };
}
