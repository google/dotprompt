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
 * Sample Dotprompt files for Storybook demonstrations.
 *
 * These samples are loaded at build time using Vite's ?raw import.
 * Each sample demonstrates different Dotprompt features.
 */

import basic from '../../samples/01-basic.prompt?raw';
import schemaAndConfig from '../../samples/02-schema-and-config.prompt?raw';
import multimodalMedia from '../../samples/03-multimodal-media.prompt?raw';
import tools from '../../samples/04-tools.prompt?raw';
import handlebarsHelpers from '../../samples/05-handlebars-helpers.prompt?raw';
import partials from '../../samples/06-partials.prompt?raw';
import multiTurnHistory from '../../samples/07-multi-turn-history.prompt?raw';
import sectionsThinking from '../../samples/08-sections-thinking.prompt?raw';
import complexSchema from '../../samples/09-complex-schema.prompt?raw';
import kitchenSink from '../../samples/10-kitchen-sink.prompt?raw';

export interface Sample {
  /** Sample identifier for selection */
  id: string;
  /** Human-readable name */
  name: string;
  /** Brief description of what the sample demonstrates */
  description: string;
  /** The actual prompt content */
  content: string;
}

/**
 * All available sample prompts, organized by feature.
 */
export const samples: Sample[] = [
  {
    id: 'basic',
    name: 'Basic Prompt',
    description: 'Minimal frontmatter with model and simple conditionals',
    content: basic,
  },
  {
    id: 'schema-config',
    name: 'Schema & Config',
    description:
      'Advanced config options, Picoschema with optional fields and enums, JSON output',
    content: schemaAndConfig,
  },
  {
    id: 'multimodal',
    name: 'Multimodal Media',
    description: 'Media helper for images and audio with array iteration',
    content: multimodalMedia,
  },
  {
    id: 'tools',
    name: 'Tool Calling',
    description:
      'Tools array with detailed system instructions and documentation',
    content: tools,
  },
  {
    id: 'helpers',
    name: 'Handlebars Helpers',
    description:
      'if/else/unless, each with @index/@first/@last, with, nested conditionals',
    content: handlebarsHelpers,
  },
  {
    id: 'partials',
    name: 'Partials',
    description: 'Partial inclusion, hash parameters, and partial blocks',
    content: partials,
  },
  {
    id: 'history',
    name: 'Multi-turn History',
    description: 'History helper for conversation memory and context',
    content: multiTurnHistory,
  },
  {
    id: 'sections',
    name: 'Sections & Thinking',
    description: 'Section helper for structured output and Chain-of-Thought',
    content: sectionsThinking,
  },
  {
    id: 'complex-schema',
    name: 'Complex Nested Schema',
    description: 'Deeply nested JSON Schema definitions and property access',
    content: complexSchema,
  },
  {
    id: 'kitchen-sink',
    name: 'Kitchen Sink',
    description:
      'Comprehensive example with ALL major Dotprompt features combined',
    content: kitchenSink,
  },
];

/**
 * Get a sample by its ID.
 */
export function getSample(id: string): Sample | undefined {
  return samples.find((s) => s.id === id);
}

/**
 * Get sample IDs for use in Storybook controls.
 */
export function getSampleIds(): string[] {
  return samples.map((s) => s.id);
}

/**
 * Get sample content by ID, with fallback to first sample.
 */
export function getSampleContent(id: string): string {
  const sample = getSample(id);
  return sample?.content ?? samples[0].content;
}
