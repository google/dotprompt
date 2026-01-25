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

import { StreamLanguage, StringStream } from '@codemirror/language';

/**
 * Token types for Dotprompt syntax.
 */
type TokenType =
  | 'comment'
  | 'keyword'
  | 'string'
  | 'number'
  | 'atom'
  | 'variable'
  | 'variable-2'
  | 'variable-3'
  | 'meta'
  | 'bracket'
  | 'tag'
  | 'attribute'
  | 'property'
  | 'operator'
  | null;

/**
 * Parser state for the Dotprompt StreamLanguage.
 */
interface DotpromptState {
  /** Current parsing context */
  context: 'root' | 'frontmatter' | 'template' | 'handlebars';
  /** Whether we're in a block comment */
  inBlockComment: boolean;
  /** Depth of nested handlebars blocks */
  blockDepth: number;
}

/**
 * StreamLanguage mode for Dotprompt.
 */
export const dotpromptStreamParser = {
  name: 'dotprompt',
  startState(): DotpromptState {
    return {
      context: 'root',
      inBlockComment: false,
      blockDepth: 0,
    };
  },

  token(stream: StringStream, state: DotpromptState): TokenType {
    // Handle block comments
    if (state.inBlockComment) {
      if (stream.match('--}}') || stream.match('}}')) {
        state.inBlockComment = false;
        return 'comment';
      }
      stream.next();
      return 'comment';
    }

    // Root state - looking for frontmatter or template content
    if (state.context === 'root') {
      // License header comments
      if (stream.sol() && stream.match(/^#.*/)) {
        return 'comment';
      }

      // Frontmatter delimiter
      if (stream.sol() && stream.match(/^---\s*$/)) {
        state.context = 'frontmatter';
        return 'meta';
      }

      state.context = 'template';
    }

    // Frontmatter parsing (YAML-like)
    if (state.context === 'frontmatter') {
      // End of frontmatter
      if (stream.sol() && stream.match(/^---\s*$/)) {
        state.context = 'template';
        return 'meta';
      }

      // YAML comments
      if (stream.match(/#.*/)) {
        return 'comment';
      }

      // YAML key
      if (stream.sol() && stream.match(/[a-zA-Z_][a-zA-Z0-9_-]*(?=\s*:)/)) {
        return 'property';
      }

      // Colon
      if (stream.match(':')) {
        return 'operator';
      }

      // Strings
      if (stream.match(/"([^"\\]|\\.)*"/)) {
        return 'string';
      }
      if (stream.match(/'([^'\\]|\\.)*'/)) {
        return 'string';
      }

      // Numbers
      if (stream.match(/\d+(\.\d+)?/)) {
        return 'number';
      }

      // Booleans and null
      if (stream.match(/\b(true|false|null)\b/)) {
        return 'atom';
      }

      // Indented keys
      if (stream.match(/[a-zA-Z_][a-zA-Z0-9_-]*(?=\s*:)/)) {
        return 'property';
      }

      stream.next();
      return null;
    }

    // Template parsing
    if (state.context === 'template') {
      // Block comment start {{!-- or {{!
      if (stream.match('{{!--')) {
        state.inBlockComment = true;
        return 'comment';
      }
      if (stream.match('{{!')) {
        if (stream.match(/.*?\}\}/)) {
          return 'comment';
        }
        state.inBlockComment = true;
        return 'comment';
      }

      // Dotprompt markers
      if (stream.match(/<<<dotprompt:[^>]+>>>/)) {
        return 'keyword';
      }

      // Handlebars block start {{#helper
      if (stream.match(/\{\{#/)) {
        state.context = 'handlebars';
        state.blockDepth++;
        return 'bracket';
      }

      // Handlebars block end {{/helper}}
      if (stream.match(/\{\{\//)) {
        state.context = 'handlebars';
        state.blockDepth = Math.max(0, state.blockDepth - 1);
        return 'bracket';
      }

      // Handlebars partials {{>
      if (stream.match(/\{\{>/)) {
        state.context = 'handlebars';
        return 'bracket';
      }

      // Handlebars expression start {{
      if (stream.match('{{')) {
        state.context = 'handlebars';
        return 'bracket';
      }

      // Plain text
      stream.next();
      return null;
    }

    // Handlebars expression parsing
    if (state.context === 'handlebars') {
      stream.eatSpace();

      // Close expression }}
      if (stream.match('}}')) {
        state.context = 'template';
        return 'bracket';
      }

      // Handlebars keywords
      if (stream.match(/\b(if|unless|each|with|else|log|lookup)\b/)) {
        return 'keyword';
      }

      // Dotprompt helpers
      if (
        stream.match(
          /\b(json|role|history|section|media|ifEquals|unlessEquals)\b/
        )
      ) {
        return 'variable-2';
      }

      // @ variables
      if (stream.match(/@[a-zA-Z_][a-zA-Z0-9_]*/)) {
        return 'variable-3';
      }

      // Strings
      if (stream.match(/"([^"\\]|\\.)*"/)) {
        return 'string';
      }
      if (stream.match(/'([^'\\]|\\.)*'/)) {
        return 'string';
      }

      // Numbers
      if (stream.match(/\d+/)) {
        return 'number';
      }

      // Operators
      if (stream.match(/[=]/)) {
        return 'operator';
      }

      // Variable/path
      if (stream.match(/[a-zA-Z_][a-zA-Z0-9_.]*/)) {
        return 'variable';
      }

      stream.next();
      return null;
    }

    stream.next();
    return null;
  },
};

/**
 * CodeMirror StreamLanguage instance for Dotprompt.
 */
export const dotpromptLanguage = StreamLanguage.define(dotpromptStreamParser);
