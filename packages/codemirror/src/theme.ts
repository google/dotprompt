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

import { HighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { tags } from '@lezer/highlight';

/**
 * Dark theme highlighting for Dotprompt.
 * Uses colors similar to VS Code's dark theme.
 */
export const dotpromptDarkHighlighting = HighlightStyle.define([
  // Comments
  { tag: tags.comment, color: '#6A9955', fontStyle: 'italic' },

  // Keywords (if, each, etc.)
  { tag: tags.keyword, color: '#C586C0' },

  // Dotprompt helpers (role, json, etc.) - variable-2
  { tag: tags.special(tags.variableName), color: '#4EC9B0' },

  // Variables
  { tag: tags.variableName, color: '#9CDCFE' },

  // @ variables - variable-3
  { tag: tags.local(tags.variableName), color: '#4FC1FF' },

  // Strings
  { tag: tags.string, color: '#CE9178' },

  // Numbers
  { tag: tags.number, color: '#B5CEA8' },

  // Booleans and null
  { tag: tags.atom, color: '#569CD6' },

  // Property names (YAML keys)
  { tag: tags.propertyName, color: '#569CD6' },

  // Operators
  { tag: tags.operator, color: '#D4D4D4' },

  // Brackets/delimiters
  { tag: tags.bracket, color: '#DCDCAA' },

  // Meta (frontmatter delimiters)
  { tag: tags.meta, color: '#6A9955' },
]);

/**
 * Light theme highlighting for Dotprompt.
 */
export const dotpromptLightHighlighting = HighlightStyle.define([
  // Comments
  { tag: tags.comment, color: '#008000', fontStyle: 'italic' },

  // Keywords
  { tag: tags.keyword, color: '#AF00DB' },

  // Dotprompt helpers
  { tag: tags.special(tags.variableName), color: '#267F99' },

  // Variables
  { tag: tags.variableName, color: '#001080' },

  // @ variables
  { tag: tags.local(tags.variableName), color: '#0070C1' },

  // Strings
  { tag: tags.string, color: '#A31515' },

  // Numbers
  { tag: tags.number, color: '#098658' },

  // Booleans and null
  { tag: tags.atom, color: '#0000FF' },

  // Property names
  { tag: tags.propertyName, color: '#0000FF' },

  // Operators
  { tag: tags.operator, color: '#000000' },

  // Brackets
  { tag: tags.bracket, color: '#795E26' },

  // Meta
  { tag: tags.meta, color: '#008000' },
]);

/**
 * Dark theme extension for Dotprompt.
 */
export const dotpromptDarkTheme = syntaxHighlighting(dotpromptDarkHighlighting);

/**
 * Light theme extension for Dotprompt.
 */
export const dotpromptLightTheme = syntaxHighlighting(
  dotpromptLightHighlighting
);
