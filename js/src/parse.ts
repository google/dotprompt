/**
 * Copyright 2024 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { parse } from 'yaml';
import type {
  DataArgument,
  MediaPart,
  Message,
  ParsedPrompt,
  Part,
  PromptMetadata,
} from './types';

/**
 * Regular expression to match YAML frontmatter delineated by `---` markers at
 * the start of a .prompt content block.
 */
export const FRONTMATTER_AND_BODY_REGEX =
  /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;

/**
 * List of reserved keywords that are handled specially in the metadata.
 * These keys are processed differently from extension metadata.
 */
const RESERVED_METADATA_KEYWORDS: (keyof PromptMetadata)[] = [
  // NOTE: KEEP SORTED
  'config',
  'description',
  'ext',
  'input',
  'model',
  'name',
  'output',
  'raw',
  'toolDefs',
  'tools',
  'variant',
  'version',
];

/**
 * Regular expression to match <<<dotprompt:role:xxx>>> and
 * <<<dotprompt:history>>> markers in the template.
 *
 * Examples of matching patterns:
 * - <<<dotprompt:role:user>>>
 * - <<<dotprompt:role:assistant>>>
 * - <<<dotprompt:role:system>>>
 * - <<<dotprompt:history>>>
 *
 * Note: Only lowercase letters are allowed after 'role:'.
 */
export const ROLE_AND_HISTORY_MARKER_REGEX =
  /(<<<dotprompt:(?:role:[a-z]+|history))>>>/g;

/**
 * Regular expression to match <<<dotprompt:media:url>>> and
 * <<<dotprompt:section>>> markers in the template.
 *
 * Examples of matching patterns:
 * - <<<dotprompt:media:url>>>
 * - <<<dotprompt:section>>>
 */
export const MEDIA_AND_SECTION_MARKER_REGEX =
  /(<<<dotprompt:(?:media:url|section).*?)>>>/g;

/**
 * Default metadata structure with empty extension and configuration objects.
 */
const BASE_METADATA: PromptMetadata<any> = {
  ext: {},
  metadata: {},
  config: {},
};

/**
 * Splits a string by a regular expression while filtering out
 * empty/whitespace-only pieces.
 *
 * @param source The source string to split into parts.
 * @param regex The regular expression to use for splitting.
 * @return An array of non-empty string pieces.
 */
export function splitByRegex(source: string, regex: RegExp): string[] {
  return source.split(regex).filter((s) => s.trim() !== '');
}

/**
 * Splits a rendered template string into pieces based on role and history
 * markers while filtering out empty/whitespace-only pieces.
 *
 * @param renderedString The template string to split.
 * @return Array of non-empty string pieces.
 */
export function splitByRoleAndHistoryMarkers(renderedString: string): string[] {
  return splitByRegex(renderedString, ROLE_AND_HISTORY_MARKER_REGEX);
}

/**
 * Split the source into pieces based on media and section markers while
 * filtering out empty/whitespace-only pieces.
 *
 * @param source The source string to split into parts
 * @return An array of string parts
 */
export function splitByMediaAndSectionMarkers(source: string): string[] {
  return splitByRegex(source, MEDIA_AND_SECTION_MARKER_REGEX);
}

/**
 * Processes a namespaced key-value pair into a nested object structure.
 * For example, 'foo.bar': 'value' becomes { foo: { bar: 'value' } }
 *
 * @param key The dotted namespace key (e.g., 'foo.bar')
 * @param value The value to assign
 * @param obj The object to add the namespaced value to
 * @returns The updated target object
 */
export function convertNamespacedEntryToNestedObject(
  key: string,
  value: unknown,
  obj: Record<string, Record<string, unknown>> = {}
): Record<string, Record<string, unknown>> {
  const lastDotIndex = key.lastIndexOf('.');
  const ns = key.substring(0, lastDotIndex);
  const field = key.substring(lastDotIndex + 1);
  obj[ns] = obj[ns] || {};
  obj[ns][field] = value;
  return obj;
}

/**
 * Extracts the YAML frontmatter and body from a document.
 *
 * @param source The source document containing frontmatter and template
 * @returns An object containing the frontmatter and body
 */
export function extractFrontmatterAndBody(source: string) {
  const match = source.match(FRONTMATTER_AND_BODY_REGEX);
  if (match) {
    const [, frontmatter, body] = match;
    return { frontmatter, body };
  }
  return { frontmatter: '', body: '' };
}

/**
 * Parses a document containing YAML frontmatter and a template content section.
 * The frontmatter contains metadata and configuration for the prompt.
 *
 * @template ModelConfig Type for model-specific configuration
 * @param source The source document containing frontmatter and template
 * @return Parsed prompt with metadata and template content
 */
export function parseDocument<ModelConfig = Record<string, any>>(
  source: string
): ParsedPrompt<ModelConfig> {
  const { frontmatter, body } = extractFrontmatterAndBody(source);
  if (frontmatter) {
    try {
      const parsedMetadata = parse(frontmatter) as PromptMetadata<ModelConfig>;
      const raw = { ...parsedMetadata };
      const pruned: PromptMetadata<ModelConfig> = { ...BASE_METADATA };
      const ext: PromptMetadata['ext'] = {};

      for (const k in raw) {
        const key = k as keyof PromptMetadata;
        if (RESERVED_METADATA_KEYWORDS.includes(key)) {
          pruned[key] = raw[key] as any;
        } else if (key.includes('.')) {
          convertNamespacedEntryToNestedObject(key, raw[key], ext);
        }
      }
      return { ...pruned, raw, ext, template: body.trim() };
    } catch (error) {
      console.error('Dotprompt: Error parsing YAML frontmatter:', error);
      return { ...BASE_METADATA, template: source.trim() };
    }
  }

  return { ...BASE_METADATA, template: source };
}

/**
 * Converts a rendered template string into an array of messages.  Processes
 * role markers and history placeholders to structure the conversation.
 *
 * @template ModelConfig Type for model-specific configuration
 * @param renderedString The rendered template string to convert
 * @param data Optional data containing message history
 * @return Array of structured messages
 */
export function toMessages<ModelConfig = Record<string, any>>(
  renderedString: string,
  data?: DataArgument
): Message[] {
  let currentMessage: { role: string; source: string } = {
    role: 'user',
    source: '',
  };
  const messageSources: {
    role: string;
    source?: string;
    content?: Message['content'];
    metadata?: Record<string, unknown>;
  }[] = [currentMessage];

  for (const piece of splitByRoleAndHistoryMarkers(renderedString)) {
    if (piece.startsWith('<<<dotprompt:role:')) {
      const role = piece.substring(18);
      if (currentMessage.source.trim()) {
        currentMessage = { role, source: '' };
        messageSources.push(currentMessage);
      } else {
        currentMessage.role = role;
      }
    } else if (piece.startsWith('<<<dotprompt:history')) {
      messageSources.push(
        ...(data?.messages ? transformMessagesToHistory(data.messages) : [])
      );
      currentMessage = { role: 'model', source: '' };
      messageSources.push(currentMessage);
    } else {
      currentMessage.source += piece;
    }
  }

  const messages: Message[] = messageSources
    .filter((ms) => ms.content || ms.source)
    .map((m) => {
      const out: Message = {
        role: m.role as Message['role'],
        content: m.content || toParts(m.source!),
      };
      if (m.metadata) out.metadata = m.metadata;
      return out;
    });

  return insertHistory(messages, data?.messages);
}

/**
 * Transforms an array of messages by adding history metadata to each message.
 *
 * @param messages Array of messages to transform
 * @returns Array of messages with history metadata added
 */
export function transformMessagesToHistory(
  messages: Array<{ metadata?: Record<string, unknown> }>
): Array<{ metadata: Record<string, unknown> }> {
  return messages.map((m) => ({
    ...m,
    metadata: { ...m.metadata, purpose: 'history' },
  }));
}

/**
 * Inserts historical messages into the conversation at the appropriate
 * position.
 *
 * @param messages Current array of messages
 * @param history Historical messages to insert
 * @return Messages with history inserted
 */
export function insertHistory(
  messages: Message[],
  history: Message[] = []
): Message[] {
  if (!history || messages.find((m) => m.metadata?.purpose === 'history'))
    return messages;
  if (messages.at(-1)?.role === 'user') {
    return [...messages.slice(0, -1)!, ...history!, messages.at(-1)!];
  }
  return [...messages, ...history];
}

/**
 * Converts a source string into an array of parts, processing media and section
 * markers.
 *
 * @param source The source string to convert into parts
 * @return Array of structured parts (text, media, or metadata)
 */
export function toParts(source: string): Part[] {
  const parts: Part[] = [];
  const pieces = splitByMediaAndSectionMarkers(source);
  for (let i = 0; i < pieces.length; i++) {
    const piece = pieces[i];
    if (piece.startsWith('<<<dotprompt:media:')) {
      // Extract URL and content type if present.
      const [_, url, contentType] = piece.split(' ');
      const part: MediaPart = { media: { url } };
      if (contentType) {
        part.media.contentType = contentType;
      }
      parts.push(part);
    } else if (piece.startsWith('<<<dotprompt:section')) {
      // Extract section type if present.
      const [_, sectionType] = piece.split(' ');
      parts.push({ metadata: { purpose: sectionType, pending: true } });
    } else {
      parts.push({ text: piece });
    }
  }

  return parts;
}
