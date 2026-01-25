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

import {
  Completion,
  CompletionContext,
  CompletionResult,
} from '@codemirror/autocomplete';

/**
 * Handlebars helper completions.
 */
const HANDLEBARS_HELPERS: Completion[] = [
  {
    label: 'if',
    type: 'keyword',
    info: 'Conditionally renders content when the condition is truthy.',
    apply: '{{#if ${condition}}}\n\t\n{{/if}}',
  },
  {
    label: 'unless',
    type: 'keyword',
    info: 'Inverse of if - renders content when the condition is falsy.',
    apply: '{{#unless ${condition}}}\n\t\n{{/unless}}',
  },
  {
    label: 'each',
    type: 'keyword',
    info: 'Iterates over arrays or objects.',
    apply: '{{#each ${items}}}\n\t{{this}}\n{{/each}}',
  },
  {
    label: 'with',
    type: 'keyword',
    info: 'Changes the current context for the enclosed block.',
    apply: '{{#with ${context}}}\n\t\n{{/with}}',
  },
  {
    label: 'else',
    type: 'keyword',
    info: 'Else branch for if/unless blocks.',
    apply: '{{else}}',
  },
  {
    label: 'log',
    type: 'function',
    info: 'Logs a value to the console for debugging.',
    apply: '{{log ${value}}}',
  },
  {
    label: 'lookup',
    type: 'function',
    info: 'Dynamically looks up a value by key from an object.',
    apply: '{{lookup ${object} ${key}}}',
  },
];

/**
 * Dotprompt-specific helper completions.
 */
const DOTPROMPT_HELPERS: Completion[] = [
  {
    label: 'role',
    type: 'keyword',
    info: 'Defines a message with a specific role (system, user, model).',
    apply: '{{#role "${role}"}}\n\t\n{{/role}}',
    boost: 10,
  },
  {
    label: 'json',
    type: 'function',
    info: 'Serializes a value to JSON format.',
    apply: '{{ json ${value} }}',
  },
  {
    label: 'history',
    type: 'function',
    info: 'Inserts the conversation history at this point.',
    apply: '{{history}}',
  },
  {
    label: 'section',
    type: 'keyword',
    info: 'Defines a named section that can be referenced elsewhere.',
    apply: '{{#section "${name}"}}\n\t\n{{/section}}',
  },
  {
    label: 'media',
    type: 'function',
    info: 'Embeds media content (images, audio, video) by URL.',
    apply: '{{media url=${url}}}',
  },
  {
    label: 'ifEquals',
    type: 'keyword',
    info: 'Renders content when two values are equal.',
    apply: '{{#ifEquals ${value1} ${value2}}}\n\t\n{{/ifEquals}}',
  },
  {
    label: 'unlessEquals',
    type: 'keyword',
    info: 'Renders content when two values are NOT equal.',
    apply: '{{#unlessEquals ${value1} ${value2}}}\n\t\n{{/unlessEquals}}',
  },
];

/**
 * Role snippet completions.
 */
const ROLE_SNIPPETS: Completion[] = [
  {
    label: 'system',
    type: 'text',
    info: "System role block - sets the AI's behavior and context.",
    apply: '{{#role "system"}}\n\t\n{{/role}}',
    boost: 5,
  },
  {
    label: 'user',
    type: 'text',
    info: 'User role block - represents user input.',
    apply: '{{#role "user"}}\n\t\n{{/role}}',
    boost: 5,
  },
  {
    label: 'model',
    type: 'text',
    info: 'Model role block - represents AI responses (for few-shot examples).',
    apply: '{{#role "model"}}\n\t\n{{/role}}',
    boost: 5,
  },
];

/**
 * Frontmatter field completions.
 */
const FRONTMATTER_FIELDS: Completion[] = [
  {
    label: 'model',
    type: 'property',
    info: 'The AI model to use for this prompt.',
    apply: 'model: ',
  },
  {
    label: 'config',
    type: 'property',
    info: 'Model configuration options.',
    apply: 'config:\n  temperature: 0.7',
  },
  {
    label: 'input',
    type: 'property',
    info: 'Input schema definition.',
    apply: 'input:\n  schema:\n    name: string',
  },
  {
    label: 'output',
    type: 'property',
    info: 'Output format and schema.',
    apply: 'output:\n  format: json',
  },
  {
    label: 'tools',
    type: 'property',
    info: 'Tools/functions available to the model.',
    apply: 'tools:\n  - ',
  },
  {
    label: 'temperature',
    type: 'property',
    info: 'Controls randomness (0.0-2.0).',
    apply: 'temperature: 0.7',
  },
  {
    label: 'maxOutputTokens',
    type: 'property',
    info: 'Maximum number of tokens in the response.',
    apply: 'maxOutputTokens: 1024',
  },
];

/**
 * Model name completions.
 */
const MODEL_NAMES: Completion[] = [
  {
    label: 'gemini-2.0-flash',
    type: 'constant',
    info: 'Fast Gemini 2.0 model',
  },
  {
    label: 'gemini-2.0-flash-lite',
    type: 'constant',
    info: 'Lightweight Gemini 2.0',
  },
  {
    label: 'gemini-1.5-pro',
    type: 'constant',
    info: 'Gemini 1.5 Pro (2M context)',
  },
  {
    label: 'gemini-1.5-flash',
    type: 'constant',
    info: 'Fast Gemini 1.5 model',
  },
  { label: 'gpt-4o', type: 'constant', info: 'OpenAI GPT-4o' },
  { label: 'gpt-4o-mini', type: 'constant', info: 'OpenAI GPT-4o Mini' },
  {
    label: 'claude-3-5-sonnet',
    type: 'constant',
    info: 'Anthropic Claude 3.5 Sonnet',
  },
  { label: 'claude-3-opus', type: 'constant', info: 'Anthropic Claude 3 Opus' },
];

/**
 * Completion source for Dotprompt files.
 */
export function dotpromptCompletions(
  context: CompletionContext
): CompletionResult | null {
  const { state, pos } = context;
  const doc = state.doc;
  const text = doc.toString();
  const textBefore = text.slice(0, pos);
  const line = doc.lineAt(pos);
  const lineText = line.text;
  const lineBefore = lineText.slice(0, pos - line.from);

  // Check if we're in frontmatter
  const frontmatterMatches = textBefore.split('---');
  const isInFrontmatter = frontmatterMatches.length === 2;

  if (isInFrontmatter) {
    // After "model: " - suggest model names
    if (/model:\s*$/.test(lineBefore)) {
      return {
        from: pos,
        options: MODEL_NAMES,
      };
    }

    // At line start - suggest frontmatter fields
    if (/^\s*$/.test(lineBefore)) {
      return {
        from: pos,
        options: FRONTMATTER_FIELDS,
      };
    }

    // Typing a field name
    const fieldMatch = lineBefore.match(/^\s*(\w*)$/);
    if (fieldMatch) {
      return {
        from: pos - fieldMatch[1].length,
        options: FRONTMATTER_FIELDS,
      };
    }

    return null;
  }

  // Check if we're inside a Handlebars expression
  const handlebarsMatch = lineBefore.match(/\{\{([#/]?)(\w*)$/);
  if (handlebarsMatch) {
    const [, prefix, word] = handlebarsMatch;
    const from = pos - word.length;

    // After {{# - block helpers
    if (prefix === '#') {
      const blockHelpers = [
        ...HANDLEBARS_HELPERS.filter((h) =>
          ['if', 'unless', 'each', 'with'].includes(h.label)
        ),
        ...DOTPROMPT_HELPERS.filter((h) =>
          ['role', 'section', 'ifEquals', 'unlessEquals'].includes(h.label)
        ),
      ].map((h) => ({
        ...h,
        apply: h.label, // Just insert the helper name after {{#
      }));

      return {
        from,
        options: blockHelpers,
      };
    }

    // After {{/ - closing block name
    if (prefix === '/') {
      const blockNames = [
        'if',
        'unless',
        'each',
        'with',
        'role',
        'section',
        'ifEquals',
        'unlessEquals',
      ].map((name) => ({
        label: name,
        type: 'keyword' as const,
        apply: name,
      }));

      return {
        from,
        options: blockNames,
      };
    }

    // After {{ - all helpers
    return {
      from,
      options: [...HANDLEBARS_HELPERS, ...DOTPROMPT_HELPERS],
    };
  }

  // Check for { - suggest starting expressions
  if (lineBefore.endsWith('{')) {
    return {
      from: pos,
      options: [
        {
          label: '{{',
          type: 'text',
          info: 'Start a Handlebars expression',
          apply: '{ }}',
        },
        {
          label: '{{#',
          type: 'text',
          info: 'Start a Handlebars block',
          apply: '{# }}',
        },
        {
          label: '{{>',
          type: 'text',
          info: 'Include a partial',
          apply: '{> }}',
        },
        {
          label: '{{!',
          type: 'text',
          info: 'Add a comment',
          apply: '{!  }}',
        },
      ],
    };
  }

  // General completions - role snippets
  const wordMatch = lineBefore.match(/(\w+)$/);
  if (wordMatch) {
    const from = pos - wordMatch[1].length;
    return {
      from,
      options: ROLE_SNIPPETS,
    };
  }

  return null;
}
