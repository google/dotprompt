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
import { createMonacoEditor, type MonacoEditorProps } from './MonacoEditor';
import { getSampleContent, getSampleIds, samples } from './samples';

// Build sample options for the dropdown
const sampleOptions = samples.reduce(
  (acc, sample) => {
    acc[`${sample.name} - ${sample.description}`] = sample.id;
    return acc;
  },
  {} as Record<string, string>
);

const meta: Meta<MonacoEditorProps & { sample: string }> = {
  title: 'Monaco Editor/Dotprompt',
  render: (args) => {
    // Get content from selected sample if sample is specified
    const content =
      args.sample && args.sample !== 'custom'
        ? getSampleContent(args.sample)
        : args.value;
    return createMonacoEditor({ ...args, value: content });
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
      options: ['vs', 'vs-dark', 'dotprompt-dark', 'dotprompt-light'],
      table: { category: 'Appearance' },
    },
    lineNumbers: {
      control: 'boolean',
      table: { category: 'Appearance' },
    },
    minimap: {
      control: 'boolean',
      table: { category: 'Appearance' },
    },
    wordWrap: {
      control: 'boolean',
      table: { category: 'Appearance' },
    },
    fontSize: {
      control: { type: 'range', min: 10, max: 24, step: 1 },
      table: { category: 'Appearance' },
    },
    completions: {
      control: 'boolean',
      table: { category: 'Features' },
    },
    hover: {
      control: 'boolean',
      table: { category: 'Features' },
    },
    vimMode: {
      control: 'boolean',
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
    height: '500px',
    theme: 'vs-dark',
    lineNumbers: true,
    minimap: false,
    wordWrap: true,
    fontSize: 14,
    completions: true,
    hover: true,
    vimMode: false,
    readOnly: false,
  },
};

export default meta;
type Story = StoryObj<MonacoEditorProps & { sample: string }>;

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
    height: '600px',
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
    height: '600px',
  },
};

/**
 * Handlebars helpers demonstration with if/else/each/with.
 */
export const HandlebarsHelpers: Story = {
  args: {
    sample: 'helpers',
    height: '700px',
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
    height: '800px',
  },
};

/**
 * Kitchen sink example with ALL Dotprompt features.
 */
export const KitchenSink: Story = {
  args: {
    sample: 'kitchen-sink',
    height: '900px',
  },
};

/**
 * Light theme variant using the standard VS light theme.
 */
export const LightTheme: Story = {
  args: {
    sample: 'basic',
    theme: 'vs',
  },
};

/**
 * Custom Dotprompt dark theme optimized for syntax visibility.
 */
export const DotpromptDarkTheme: Story = {
  args: {
    sample: 'kitchen-sink',
    theme: 'dotprompt-dark',
    height: '900px',
  },
};

/**
 * Vim keybinding mode for power users.
 */
export const VimMode: Story = {
  args: {
    sample: 'basic',
    vimMode: true,
  },
};

/**
 * Multilingual and Unicode support with CJK, Arabic, Cyrillic, emoji.
 */
export const Multilingual: Story = {
  args: {
    sample: 'multilingual',
    height: '700px',
  },
};

/**
 * Read-only mode for viewing prompts without editing.
 */
export const ReadOnly: Story = {
  args: {
    sample: 'kitchen-sink',
    readOnly: true,
    vimMode: false,
    height: '900px',
  },
};

/**
 * Large font size for presentations and demos.
 */
export const LargeFont: Story = {
  args: {
    sample: 'basic',
    fontSize: 20,
    height: '500px',
  },
};

/**
 * Minimal editor without line numbers or minimap.
 */
export const Minimal: Story = {
  args: {
    sample: 'basic',
    lineNumbers: false,
    minimap: false,
    theme: 'dotprompt-dark',
    vimMode: false,
  },
};
