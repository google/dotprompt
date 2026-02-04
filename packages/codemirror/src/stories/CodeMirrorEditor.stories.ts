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

import type { Meta, StoryObj } from '@storybook/html';
import {
  type CodeMirrorEditorProps,
  createCodeMirrorEditor,
} from './CodeMirrorEditor';
import { getSampleContent, getSampleIds, samples } from './samples';

const meta: Meta<CodeMirrorEditorProps & { sample: string }> = {
  title: 'CodeMirror Editor/Dotprompt',
  render: (args) => {
    // Get content from selected sample if sample is specified
    const content =
      args.sample && args.sample !== 'custom'
        ? getSampleContent(args.sample)
        : args.value;
    return createCodeMirrorEditor({ ...args, value: content });
  },
  argTypes: {
    sample: {
      control: 'select',
      options: ['custom', ...getSampleIds()],
      mapping: {
        custom: 'custom',
        ...Object.fromEntries(getSampleIds().map((id) => [id, id])),
      },
      description: 'Load a sample prompt file',
      table: {
        category: 'Sample',
      },
    },
    value: {
      control: 'text',
      description: 'Custom prompt content (used when sample is "custom")',
      table: {
        category: 'Content',
      },
    },
    width: {
      control: 'text',
      table: { category: 'Layout' },
    },
    height: {
      control: 'text',
      table: { category: 'Layout' },
    },
    theme: {
      control: 'select',
      options: ['dark', 'light'],
      table: { category: 'Appearance' },
    },
    lineNumbers: {
      control: 'boolean',
      table: { category: 'Appearance' },
    },
    lineWrapping: {
      control: 'boolean',
      table: { category: 'Appearance' },
    },
    editorMode: {
      control: 'select',
      options: ['standard', 'vim', 'emacs'],
      description: 'Editor keybinding mode',
      table: { category: 'Features' },
    },
    readOnly: {
      control: 'boolean',
      table: { category: 'Features' },
    },
  },
  args: {
    sample: 'basic',
    value: '',
    width: '100%',
    height: 'calc(100vh - 40px)',
    theme: 'dark',
    lineNumbers: true,
    lineWrapping: true,
    editorMode: 'standard',
    readOnly: false,
  },
};

export default meta;
type Story = StoryObj<CodeMirrorEditorProps & { sample: string }>;

/**
 * Basic prompt with minimal frontmatter.
 */
export const Basic: Story = {
  args: {
    sample: 'basic',
  },
};

/**
 * Schema and configuration options with Picoschema and JSON output.
 */
export const SchemaAndConfig: Story = {
  args: {
    sample: 'schema-config',
  },
};

/**
 * Multimodal prompt with media helper for images and audio.
 */
export const MultimodalMedia: Story = {
  args: {
    sample: 'multimodal',
  },
};

/**
 * Tool-enabled prompt with detailed system instructions.
 */
export const ToolCalling: Story = {
  args: {
    sample: 'tools',
  },
};

/**
 * Handlebars helpers demonstration with if/else/each/with.
 */
export const HandlebarsHelpers: Story = {
  args: {
    sample: 'helpers',
  },
};

/**
 * Partials demonstration with inclusion and hash parameters.
 */
export const Partials: Story = {
  args: {
    sample: 'partials',
  },
};

/**
 * Multi-turn conversation with history helper.
 */
export const MultiTurnHistory: Story = {
  args: {
    sample: 'history',
  },
};

/**
 * Sections and Chain-of-Thought reasoning patterns.
 */
export const SectionsAndThinking: Story = {
  args: {
    sample: 'sections',
  },
};

/**
 * Complex nested JSON Schema definitions.
 */
export const ComplexSchema: Story = {
  args: {
    sample: 'complex-schema',
  },
};

/**
 * Kitchen sink example with ALL Dotprompt features.
 */
export const KitchenSink: Story = {
  args: {
    sample: 'kitchen-sink',
  },
};

/**
 * Light theme variant.
 */
export const LightTheme: Story = {
  args: {
    sample: 'basic',
    theme: 'light',
  },
};

/**
 * Vim keybinding mode for power users.
 */
export const VimMode: Story = {
  args: {
    sample: 'basic',
    editorMode: 'vim',
  },
};

/**
 * Emacs keybinding mode for Emacs users.
 */
export const EmacsMode: Story = {
  args: {
    sample: 'basic',
    editorMode: 'emacs',
  },
};

/**
 * Multilingual and Unicode support with CJK, Arabic, Cyrillic, emoji.
 */
export const Multilingual: Story = {
  args: {
    sample: 'multilingual',
  },
};

/**
 * Read-only mode for viewing prompts without editing.
 */
export const ReadOnly: Story = {
  args: {
    sample: 'kitchen-sink',
    readOnly: true,
  },
};

/**
 * Minimal editor without line numbers.
 */
export const Minimal: Story = {
  args: {
    sample: 'basic',
    lineNumbers: false,
  },
};
