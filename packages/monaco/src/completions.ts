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
 * Handlebars built-in helpers with documentation.
 */
const HANDLEBARS_HELPERS = [
  {
    label: 'if',
    kind: 1, // Function
    insertText: '{{#if ${1:condition}}}\n\t$0\n{{/if}}',
    insertTextRules: 4, // InsertAsSnippet
    documentation:
      'Conditionally renders content when the condition is truthy.',
  },
  {
    label: 'unless',
    kind: 1,
    insertText: '{{#unless ${1:condition}}}\n\t$0\n{{/unless}}',
    insertTextRules: 4,
    documentation:
      'Inverse of if - renders content when the condition is falsy.',
  },
  {
    label: 'each',
    kind: 1,
    insertText: '{{#each ${1:items}}}\n\t$0\n{{/each}}',
    insertTextRules: 4,
    documentation:
      'Iterates over arrays or objects. Use @index, @first, @last inside.',
  },
  {
    label: 'with',
    kind: 1,
    insertText: '{{#with ${1:context}}}\n\t$0\n{{/with}}',
    insertTextRules: 4,
    documentation: 'Changes the current context for the enclosed block.',
  },
  {
    label: 'else',
    kind: 14, // Keyword
    insertText: '{{else}}',
    documentation: 'Else branch for if/unless blocks.',
  },
  {
    label: 'log',
    kind: 1,
    insertText: '{{log ${1:value}}}',
    insertTextRules: 4,
    documentation: 'Logs a value to the console for debugging.',
  },
  {
    label: 'lookup',
    kind: 1,
    insertText: '{{lookup ${1:object} ${2:key}}}',
    insertTextRules: 4,
    documentation: 'Dynamically looks up a value by key from an object.',
  },
];

/**
 * Dotprompt-specific helpers with documentation.
 */
const DOTPROMPT_HELPERS = [
  {
    label: 'role',
    kind: 1,
    insertText: '{{#role "${1|system,user,model|}"}}}\n\t$0\n{{/role}}',
    insertTextRules: 4,
    documentation:
      'Defines a message with a specific role (system, user, or model).',
  },
  {
    label: 'json',
    kind: 1,
    insertText: '{{ json ${1:value} }}',
    insertTextRules: 4,
    documentation: 'Serializes a value to JSON format.',
  },
  {
    label: 'history',
    kind: 1,
    insertText: '{{history}}',
    documentation: 'Inserts the conversation history at this point.',
  },
  {
    label: 'section',
    kind: 1,
    insertText: '{{#section "${1:name}"}}\n\t$0\n{{/section}}',
    insertTextRules: 4,
    documentation: 'Defines a named section that can be referenced elsewhere.',
  },
  {
    label: 'media',
    kind: 1,
    insertText: '{{media url=${1:url}}}',
    insertTextRules: 4,
    documentation: 'Embeds media content (images, audio, video) by URL.',
  },
  {
    label: 'ifEquals',
    kind: 1,
    insertText: '{{#ifEquals ${1:value1} ${2:value2}}}\n\t$0\n{{/ifEquals}}',
    insertTextRules: 4,
    documentation: 'Renders content when two values are equal.',
  },
  {
    label: 'unlessEquals',
    kind: 1,
    insertText:
      '{{#unlessEquals ${1:value1} ${2:value2}}}\n\t$0\n{{/unlessEquals}}',
    insertTextRules: 4,
    documentation: 'Renders content when two values are NOT equal.',
  },
];

/**
 * Role snippets for quick insertion.
 */
const ROLE_SNIPPETS = [
  {
    label: 'system',
    kind: 15, // Snippet
    insertText: '{{#role "system"}}\n\t$0\n{{/role}}',
    insertTextRules: 4,
    documentation: "System role block - sets the AI's behavior and context.",
  },
  {
    label: 'user',
    kind: 15,
    insertText: '{{#role "user"}}\n\t$0\n{{/role}}',
    insertTextRules: 4,
    documentation: 'User role block - represents user input.',
  },
  {
    label: 'model',
    kind: 15,
    insertText: '{{#role "model"}}\n\t$0\n{{/role}}',
    insertTextRules: 4,
    documentation:
      'Model role block - represents AI responses (for few-shot examples).',
  },
];

/**
 * Frontmatter field completions.
 */
const FRONTMATTER_FIELDS = [
  {
    label: 'model',
    kind: 5, // Field
    insertText: 'model: ${1:gemini-2.0-flash}',
    insertTextRules: 4,
    documentation: 'The AI model to use for this prompt.',
  },
  {
    label: 'config',
    kind: 5,
    insertText: 'config:\n  temperature: ${1:0.7}',
    insertTextRules: 4,
    documentation: 'Model configuration options.',
  },
  {
    label: 'input',
    kind: 5,
    insertText: 'input:\n  schema:\n    ${1:name}: ${2:string}',
    insertTextRules: 4,
    documentation: 'Input schema definition for the prompt.',
  },
  {
    label: 'output',
    kind: 5,
    insertText: 'output:\n  format: ${1|json,text,media|}',
    insertTextRules: 4,
    documentation: 'Output format and schema.',
  },
  {
    label: 'tools',
    kind: 5,
    insertText: 'tools:\n  - ${1:toolName}',
    insertTextRules: 4,
    documentation: 'Tools/functions available to the model.',
  },
  {
    label: 'temperature',
    kind: 5,
    insertText: 'temperature: ${1:0.7}',
    insertTextRules: 4,
    documentation: 'Controls randomness (0.0-2.0). Lower = more deterministic.',
  },
  {
    label: 'maxOutputTokens',
    kind: 5,
    insertText: 'maxOutputTokens: ${1:1024}',
    insertTextRules: 4,
    documentation: 'Maximum number of tokens in the response.',
  },
];

/**
 * Model name completions.
 */
const MODEL_NAMES = [
  {
    label: 'gemini-2.0-flash',
    documentation: 'Fast Gemini 2.0 model (1M context)',
  },
  {
    label: 'gemini-2.0-flash-lite',
    documentation: 'Lightweight Gemini 2.0 model',
  },
  { label: 'gemini-1.5-pro', documentation: 'Gemini 1.5 Pro (2M context)' },
  { label: 'gemini-1.5-flash', documentation: 'Fast Gemini 1.5 model' },
  { label: 'gpt-4o', documentation: 'OpenAI GPT-4o (128K context)' },
  { label: 'gpt-4o-mini', documentation: 'OpenAI GPT-4o Mini' },
  { label: 'gpt-4-turbo', documentation: 'OpenAI GPT-4 Turbo' },
  { label: 'claude-3-5-sonnet', documentation: 'Anthropic Claude 3.5 Sonnet' },
  { label: 'claude-3-opus', documentation: 'Anthropic Claude 3 Opus' },
].map((m) => ({
  ...m,
  kind: 12, // Value
  insertText: m.label,
}));

/**
 * Creates a completion provider for Dotprompt files.
 */
export function createCompletionProvider(
  monacoInstance: typeof monaco
): monaco.languages.CompletionItemProvider {
  return {
    triggerCharacters: ['{', ':', ' ', '"'],

    provideCompletionItems(
      model: monaco.editor.ITextModel,
      position: monaco.Position
    ): monaco.languages.ProviderResult<monaco.languages.CompletionList> {
      const textUntilPosition = model.getValueInRange({
        startLineNumber: 1,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column,
      });

      const lineContent = model.getLineContent(position.lineNumber);
      const linePrefix = lineContent.substring(0, position.column - 1);

      const range = {
        startLineNumber: position.lineNumber,
        startColumn: position.column,
        endLineNumber: position.lineNumber,
        endColumn: position.column,
      };

      // Check if we're in frontmatter
      const frontmatterMatch = textUntilPosition.match(/^---\n[\s\S]*?(?!---)/);
      const isInFrontmatter =
        frontmatterMatch && !textUntilPosition.includes('---\n---');

      if (isInFrontmatter) {
        // Model name completion after "model:"
        if (/model:\s*$/.test(linePrefix)) {
          return {
            suggestions: MODEL_NAMES.map((item) => ({
              ...item,
              range,
            })),
          };
        }

        // Frontmatter field completion at line start
        if (/^\s*$/.test(linePrefix) || /^\s+$/.test(linePrefix)) {
          return {
            suggestions: FRONTMATTER_FIELDS.map((item) => ({
              ...item,
              range,
            })),
          };
        }

        return { suggestions: [] };
      }

      // Check if we're inside a Handlebars expression
      const isInHandlebars = /\{\{[^}]*$/.test(linePrefix);

      if (isInHandlebars) {
        // After {{# - block helpers
        if (/\{\{#\s*$/.test(linePrefix)) {
          const blockHelpers = [
            ...HANDLEBARS_HELPERS.filter((h) =>
              ['if', 'unless', 'each', 'with'].includes(h.label)
            ),
            ...DOTPROMPT_HELPERS.filter((h) =>
              ['role', 'section', 'ifEquals', 'unlessEquals'].includes(h.label)
            ),
          ].map((item) => ({
            ...item,
            insertText: item.label,
            range,
          }));

          return { suggestions: blockHelpers };
        }

        // After {{> - partials
        if (/\{\{>\s*$/.test(linePrefix)) {
          return {
            suggestions: [
              {
                label: 'partial',
                kind: 15,
                insertText: '${1:partialName}',
                insertTextRules: 4,
                documentation: 'Reference a partial template',
                range,
              },
            ],
          };
        }

        // General helpers after {{ or {{
        return {
          suggestions: [...HANDLEBARS_HELPERS, ...DOTPROMPT_HELPERS].map(
            (item) => ({ ...item, range })
          ),
        };
      }

      // At start of expression - suggest opening {{
      if (linePrefix.endsWith('{')) {
        return {
          suggestions: [
            {
              label: '{{',
              kind: 15,
              insertText: '{$0}}',
              insertTextRules: 4,
              documentation: 'Start a Handlebars expression',
              range,
            },
            {
              label: '{{#',
              kind: 15,
              insertText: '{#$0}}',
              insertTextRules: 4,
              documentation: 'Start a Handlebars block',
              range,
            },
            {
              label: '{{>',
              kind: 15,
              insertText: '{> $0}}',
              insertTextRules: 4,
              documentation: 'Include a partial',
              range,
            },
            {
              label: '{{!',
              kind: 15,
              insertText: '{! $0 }}',
              insertTextRules: 4,
              documentation: 'Add a comment',
              range,
            },
          ],
        };
      }

      // Role snippets as general completions
      return {
        suggestions: [...ROLE_SNIPPETS].map((item) => ({ ...item, range })),
      };
    },
  };
}
