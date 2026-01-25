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

import type * as monaco from 'monaco-editor';

/**
 * Language ID for Dotprompt files.
 */
export const LANGUAGE_ID = 'dotprompt';

/**
 * Monarch tokenizer for Dotprompt syntax highlighting.
 * Handles YAML frontmatter, Handlebars templates, and Dotprompt markers.
 */
export const monarchLanguage: monaco.languages.IMonarchLanguage = {
  defaultToken: '',
  tokenPostfix: '.dotprompt',

  // Handlebars keywords
  keywords: ['if', 'unless', 'each', 'with', 'else', 'log', 'lookup'],

  // Dotprompt-specific helpers
  dotpromptHelpers: [
    'json',
    'role',
    'history',
    'section',
    'media',
    'ifEquals',
    'unlessEquals',
  ],

  // YAML frontmatter keys
  yamlKeys: [
    'model',
    'config',
    'input',
    'output',
    'tools',
    'metadata',
    'default',
    'schema',
    'format',
    'temperature',
    'maxOutputTokens',
    'topP',
    'topK',
  ],

  // Operators and brackets
  brackets: [
    { open: '{{', close: '}}', token: 'delimiter.handlebars' },
    { open: '{{#', close: '}}', token: 'delimiter.handlebars.block' },
    { open: '{{/', close: '}}', token: 'delimiter.handlebars.block' },
    { open: '{', close: '}', token: 'delimiter.curly' },
    { open: '[', close: ']', token: 'delimiter.square' },
  ],

  tokenizer: {
    root: [
      // License header comments (lines starting with #)
      [/^#.*$/, 'comment.line'],

      // Frontmatter delimiter
      [/^---\s*$/, { token: 'delimiter.frontmatter', next: '@frontmatter' }],

      // Dotprompt markers <<<dotprompt:...>>>
      [/<<<dotprompt:[^>]+>>>/, 'keyword.marker'],

      // Include template tokens
      { include: '@template' },
    ],

    frontmatter: [
      // End of frontmatter
      [/^---\s*$/, { token: 'delimiter.frontmatter', next: '@root' }],

      // YAML comments
      [/#.*$/, 'comment.yaml'],

      // YAML keys
      [
        /([a-zA-Z_][a-zA-Z0-9_-]*)(\s*)(:)/,
        [
          {
            cases: {
              '@yamlKeys': 'keyword.yaml',
              '@default': 'variable.yaml',
            },
          },
          '',
          'delimiter.colon',
        ],
      ],

      // YAML strings
      [/"([^"\\]|\\.)*$/, 'string.invalid'], // non-terminated string
      [/"/, { token: 'string.quote', next: '@yamlDoubleString' }],
      [/'/, { token: 'string.quote', next: '@yamlSingleString' }],

      // YAML numbers
      [/\d+(\.\d+)?/, 'number'],

      // YAML booleans
      [/\b(true|false|null)\b/, 'constant.language'],

      // Everything else in frontmatter
      [/./, 'source.yaml'],
    ],

    yamlDoubleString: [
      [/[^\\"]+/, 'string'],
      [/\\./, 'string.escape'],
      [/"/, { token: 'string.quote', next: '@pop' }],
    ],

    yamlSingleString: [
      [/[^\\']+/, 'string'],
      [/\\./, 'string.escape'],
      [/'/, { token: 'string.quote', next: '@pop' }],
    ],

    template: [
      // Handlebars comments {{! ... }}
      [/\{\{!--/, { token: 'comment.block', next: '@handlebarsBlockComment' }],
      [/\{\{!/, { token: 'comment.block', next: '@handlebarsComment' }],

      // Handlebars block start {{#helper ...}}
      [
        /(\{\{#)(\s*)(\w+)/,
        [
          'delimiter.handlebars.block',
          '',
          {
            cases: {
              '@keywords': 'keyword.handlebars',
              '@dotpromptHelpers': 'keyword.dotprompt',
              '@default': 'variable.handlebars',
            },
          },
        ],
      ],

      // Handlebars block end {{/helper}}
      [
        /(\{\{\/)(\s*)(\w+)(\s*)(\}\})/,
        [
          'delimiter.handlebars.block',
          '',
          {
            cases: {
              '@keywords': 'keyword.handlebars',
              '@dotpromptHelpers': 'keyword.dotprompt',
              '@default': 'variable.handlebars',
            },
          },
          '',
          'delimiter.handlebars.block',
        ],
      ],

      // Handlebars else {{else}}
      [/\{\{else\}\}/, 'keyword.handlebars'],

      // Partials {{> partialName}}
      [
        /(\{\{>)(\s*)([a-zA-Z_][a-zA-Z0-9_-]*)(\s*)(\}\})/,
        [
          'delimiter.handlebars',
          '',
          'variable.partial',
          '',
          'delimiter.handlebars',
        ],
      ],

      // Handlebars expressions {{ ... }}
      [
        /\{\{/,
        { token: 'delimiter.handlebars', next: '@handlebarsExpression' },
      ],

      // Plain text
      [/[^{<]+/, ''],
      [/./, ''],
    ],

    handlebarsExpression: [
      // Close expression
      [/\}\}/, { token: 'delimiter.handlebars', next: '@pop' }],

      // Helpers
      [
        /\b(\w+)\b/,
        {
          cases: {
            '@keywords': 'keyword.handlebars',
            '@dotpromptHelpers': 'keyword.dotprompt',
            '@default': 'variable',
          },
        },
      ],

      // Strings in expressions
      [/"([^"\\]|\\.)*"/, 'string'],
      [/'([^'\\]|\\.)*'/, 'string'],

      // Numbers
      [/\d+/, 'number'],

      // Operators
      [/[=]/, 'operator'],

      // Dotted paths
      [/\./, 'delimiter.dot'],

      // @ variables (@index, @first, etc.)
      [/@\w+/, 'variable.special'],

      // Whitespace
      [/\s+/, ''],
    ],

    handlebarsComment: [
      [/\}\}/, { token: 'comment.block', next: '@pop' }],
      [/./, 'comment.block'],
    ],

    handlebarsBlockComment: [
      [/--\}\}/, { token: 'comment.block', next: '@pop' }],
      [/./, 'comment.block'],
    ],
  },
};

/**
 * Language configuration for Dotprompt.
 * Provides bracket matching, auto-closing, and comment toggling.
 */
export const languageConfiguration: monaco.languages.LanguageConfiguration = {
  comments: {
    blockComment: ['{{!', '}}'],
  },
  brackets: [
    ['{{', '}}'],
    ['{{#', '}}'],
    ['{{/', '}}'],
    ['{', '}'],
    ['[', ']'],
    ['(', ')'],
  ],
  autoClosingPairs: [
    { open: '{{', close: '}}' },
    { open: '{', close: '}' },
    { open: '[', close: ']' },
    { open: '(', close: ')' },
    { open: '"', close: '"' },
    { open: "'", close: "'" },
  ],
  surroundingPairs: [
    { open: '{{', close: '}}' },
    { open: '{', close: '}' },
    { open: '[', close: ']' },
    { open: '(', close: ')' },
    { open: '"', close: '"' },
    { open: "'", close: "'" },
  ],
  folding: {
    markers: {
      start: /^\s*\{\{#/,
      end: /^\s*\{\{\//,
    },
  },
  indentationRules: {
    increaseIndentPattern: /^\s*\{\{#(if|unless|each|with|role|section)/,
    decreaseIndentPattern: /^\s*\{\{\/(if|unless|each|with|role|section)/,
  },
};
