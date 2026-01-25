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
 * Documentation for Handlebars helpers.
 */
const HELPER_DOCS: Record<string, { description: string; example?: string }> = {
  if: {
    description: 'Conditionally renders content when the condition is truthy.',
    example: '{{#if isLoggedIn}}\n  Welcome back!\n{{/if}}',
  },
  unless: {
    description:
      'Inverse of `if` - renders content when the condition is falsy.',
    example: '{{#unless isLoggedIn}}\n  Please log in.\n{{/unless}}',
  },
  each: {
    description:
      'Iterates over arrays or objects. Inside the block, `this` refers to the current item. Use `@index`, `@first`, `@last`, `@key` for metadata.',
    example:
      '{{#each items}}\n  - {{this.name}} (index: {{@index}})\n{{/each}}',
  },
  with: {
    description: 'Changes the current context for the enclosed block.',
    example: '{{#with user}}\n  Hello, {{name}}!\n{{/with}}',
  },
  else: {
    description: 'Provides an else branch for `if` or `unless` blocks.',
    example: '{{#if condition}}\n  True\n{{else}}\n  False\n{{/if}}',
  },
  log: {
    description: 'Logs a value to the console for debugging purposes.',
    example: '{{log user.name}}',
  },
  lookup: {
    description: 'Dynamically looks up a value by key from an object.',
    example: '{{lookup user "name"}}',
  },
};

/**
 * Documentation for Dotprompt-specific helpers.
 */
const DOTPROMPT_DOCS: Record<
  string,
  { description: string; example?: string }
> = {
  role: {
    description:
      'Defines a message with a specific role. Valid roles are `system`, `user`, and `model`.',
    example:
      '{{#role "system"}}\nYou are a helpful assistant.\n{{/role}}\n\n{{#role "user"}}\nHello!\n{{/role}}',
  },
  json: {
    description: 'Serializes a value to JSON format for structured output.',
    example: 'Here is the data: {{ json userData }}',
  },
  history: {
    description:
      'Inserts the conversation history at this point. Used for multi-turn conversations.',
    example: '{{history}}',
  },
  section: {
    description:
      'Defines a named section that can be extracted or referenced elsewhere.',
    example: '{{#section "instructions"}}\nFollow these rules...\n{{/section}}',
  },
  media: {
    description:
      'Embeds media content (images, audio, video) by URL. The AI model will process this media.',
    example: '{{media url=imageUrl}}',
  },
  ifEquals: {
    description: 'Renders content when two values are equal.',
    example:
      '{{#ifEquals status "active"}}\n  Account is active\n{{/ifEquals}}',
  },
  unlessEquals: {
    description: 'Renders content when two values are NOT equal.',
    example:
      '{{#unlessEquals role "admin"}}\n  Access denied\n{{/unlessEquals}}',
  },
};

/**
 * Documentation for frontmatter fields.
 */
const FRONTMATTER_DOCS: Record<string, { description: string; type?: string }> =
  {
    model: {
      description: 'The AI model to use for this prompt.',
      type: 'string',
    },
    config: {
      description: 'Model configuration options.',
      type: 'object',
    },
    temperature: {
      description:
        'Controls randomness in output generation (0.0-2.0). Lower values are more deterministic, higher values are more creative.',
      type: 'number',
    },
    maxOutputTokens: {
      description: 'Maximum number of tokens in the response.',
      type: 'number',
    },
    topP: {
      description: 'Nucleus sampling parameter (0.0-1.0).',
      type: 'number',
    },
    topK: {
      description: 'Top-k sampling parameter.',
      type: 'number',
    },
    input: {
      description: 'Input schema definition for the prompt variables.',
      type: 'object',
    },
    output: {
      description: 'Output format and schema specification.',
      type: 'object',
    },
    format: {
      description: 'Output format: `json`, `text`, or `media`.',
      type: 'string',
    },
    schema: {
      description: 'Type schema for input or output.',
      type: 'object',
    },
    tools: {
      description:
        'Tools/functions available to the model for function calling.',
      type: 'array',
    },
    metadata: {
      description: 'Custom metadata for the prompt.',
      type: 'object',
    },
    default: {
      description: 'Default values for input variables.',
      type: 'object',
    },
  };

/**
 * Creates a hover provider for Dotprompt files.
 */
export function createHoverProvider(
  monacoInstance: typeof monaco
): monaco.languages.HoverProvider {
  return {
    provideHover(
      model: monaco.editor.ITextModel,
      position: monaco.Position
    ): monaco.languages.ProviderResult<monaco.languages.Hover> {
      const word = model.getWordAtPosition(position);
      if (!word) {
        return null;
      }

      const wordText = word.word;
      const lineContent = model.getLineContent(position.lineNumber);

      // Check if we're in frontmatter
      const textUntilPosition = model.getValueInRange({
        startLineNumber: 1,
        startColumn: 1,
        endLineNumber: position.lineNumber,
        endColumn: position.column,
      });

      const isInFrontmatter =
        textUntilPosition.split('---').length === 2 &&
        textUntilPosition.startsWith('---');

      if (isInFrontmatter) {
        // Check frontmatter field
        const frontmatterDoc = FRONTMATTER_DOCS[wordText];
        if (frontmatterDoc) {
          const contents: monaco.IMarkdownString[] = [
            {
              value: `**${wordText}**${frontmatterDoc.type ? `: \`${frontmatterDoc.type}\`` : ''}`,
            },
            { value: frontmatterDoc.description },
          ];

          return {
            range: {
              startLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endLineNumber: position.lineNumber,
              endColumn: word.endColumn,
            },
            contents,
          };
        }
      }

      // Check if we're in a Handlebars expression
      const isInHandlebars =
        /\{\{[^}]*$/.test(lineContent.substring(0, position.column)) ||
        /\{\{#\w*$/.test(lineContent.substring(0, position.column)) ||
        /\{\{\/\w*$/.test(lineContent.substring(0, position.column));

      if (isInHandlebars || /\{\{[#/]?\s*\w+/.test(lineContent)) {
        // Check Dotprompt helper
        const dotpromptDoc = DOTPROMPT_DOCS[wordText];
        if (dotpromptDoc) {
          const contents: monaco.IMarkdownString[] = [
            { value: `**${wordText}** (Dotprompt helper)` },
            { value: dotpromptDoc.description },
          ];

          if (dotpromptDoc.example) {
            contents.push({
              value: `\`\`\`handlebars\n${dotpromptDoc.example}\n\`\`\``,
            });
          }

          return {
            range: {
              startLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endLineNumber: position.lineNumber,
              endColumn: word.endColumn,
            },
            contents,
          };
        }

        // Check Handlebars helper
        const helperDoc = HELPER_DOCS[wordText];
        if (helperDoc) {
          const contents: monaco.IMarkdownString[] = [
            { value: `**${wordText}** (Handlebars helper)` },
            { value: helperDoc.description },
          ];

          if (helperDoc.example) {
            contents.push({
              value: `\`\`\`handlebars\n${helperDoc.example}\n\`\`\``,
            });
          }

          return {
            range: {
              startLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endLineNumber: position.lineNumber,
              endColumn: word.endColumn,
            },
            contents,
          };
        }
      }

      return null;
    },
  };
}
