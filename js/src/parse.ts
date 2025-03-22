/**
 * Copyright 2024 Google LLC
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

import { parse } from 'yaml';
import type {
  DataArgument,
  MediaPart,
  Message,
  ParsedPrompt,
  Part,
  PendingPart,
  PromptMetadata,
  Role,
  TextPart,
} from './types';

/**
 * A message source is a message with a source string and optional content and
 * metadata.
 */
export type MessageSource = {
  role: Role;
  source?: string;
  content?: Message['content'];
  metadata?: Record<string, unknown>;
};

/**
 * Prefixes for the role markers in the template.
 */
export const ROLE_MARKER_PREFIX = '<<<dotprompt:role:';

/**
 * Prefixes for the history markers in the template.
 */
export const HISTORY_MARKER_PREFIX = '<<<dotprompt:history';

/**
 * Prefixes for the media markers in the template.
 */
export const MEDIA_MARKER_PREFIX = '<<<dotprompt:media:';

/**
 * Prefixes for the section markers in the template.
 */
export const SECTION_MARKER_PREFIX = '<<<dotprompt:section';

/**
 * Regular expression to match YAML frontmatter delineated by `---` markers at
 * the start of a .prompt content block.
 */
export const FRONTMATTER_AND_BODY_REGEX =
  /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;

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
 * List of reserved keywords that are handled specially in the metadata.
 * These keys are processed differently from extension metadata.
 */
export const RESERVED_METADATA_KEYWORDS: (keyof PromptMetadata)[] = [
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
  // NOTE: Goes only a single level deep.
  const result = obj || {};

  const lastDotIndex = key.lastIndexOf('.');
  const ns = key.substring(0, lastDotIndex);
  const field = key.substring(lastDotIndex + 1);

  // Ensure the namespace exists.
  result[ns] = result[ns] || {};
  result[ns][field] = value;

  return result;
}

/**
 * Extracts the YAML frontmatter and body from a document.
 *
 * @param source The source document containing frontmatter and template
 * @returns An object containing the frontmatter and body If the pattern does
 *   not match, both the values returned will be empty.
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

  // No frontmatter, return a basic ParsedPrompt with just the template
  return { ...BASE_METADATA, template: source };
}

/**
 * Processes an array of message sources into an array of messages.
 *
 * @param messageSources Array of message sources
 * @returns Array of structured messages
 */
export function messageSourcesToMessages(
  messageSources: MessageSource[]
): Message[] {
  return messageSources
    .filter((ms) => ms.content || ms.source)
    .map((m) => {
      const out: Message = {
        role: m.role as Role,
        content: m.content || toParts(m.source || ''),
      };
      if (m.metadata) {
        out.metadata = m.metadata;
      }
      return out;
    });
}

/**
 * Transforms an array of messages by adding history metadata to each message.
 *
 * @param messages Array of messages to transform
 * @returns Array of messages with history metadata added
 */
export function transformMessagesToHistory(
  messages: Array<Message>
): Array<Message> {
  return messages.map((m) => ({
    ...m,
    metadata: { ...m.metadata, purpose: 'history' },
  }));
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
export function toMessages<ModelConfig = Record<string, unknown>>(
  renderedString: string,
  data?: DataArgument
): Message[] {
  let currentMessage: MessageSource = { role: 'user', source: '' };
  const messageSources: MessageSource[] = [currentMessage];

  for (const piece of splitByRoleAndHistoryMarkers(renderedString)) {
    if (piece.startsWith(ROLE_MARKER_PREFIX)) {
      const role = piece.substring(ROLE_MARKER_PREFIX.length) as Role;

      if (currentMessage.source?.trim()) {
        // If the current message has a source, reset it.
        currentMessage = { role, source: '' };
        messageSources.push(currentMessage);
      } else {
        // Otherwise, update the role of the current message.
        currentMessage.role = role;
      }
    } else if (piece.startsWith(HISTORY_MARKER_PREFIX)) {
      // Add the history messages to the message sources.
      const historyMessages = transformMessagesToHistory(data?.messages ?? []);
      if (historyMessages) {
        messageSources.push(...historyMessages);
      }

      // Add a new message source for the model.
      currentMessage = { role: 'model', source: '' };
      messageSources.push(currentMessage);
    } else {
      // Otherwise, add the piece to the current message source.
      currentMessage.source += piece;
    }
  }

  const messages: Message[] = messageSourcesToMessages(messageSources);
  return insertHistory(messages, data?.messages);
}

/**
 * Checks if the messages have history metadata.
 *
 * @param messages The messages to check
 * @return True if the messages have history metadata, false otherwise
 */
export function messagesHaveHistory(messages: Message[]): boolean {
  return messages.some((m) => m.metadata?.purpose === 'history');
}

/**
 * Inserts historical messages into the conversation at appropriate positions.
 *
 * The history is inserted at:
 * - Before the last user message if there is a user message.
 * - The end of the conversation if there is no history or no user message.
 *
 * The history is not inserted:
 * - If it already exists in the messages.
 * - If there is no user message.
 *
 * @param messages Current array of messages
 * @param history Historical messages to insert
 * @return Messages with history inserted
 */
export function insertHistory(
  messages: Message[],
  history: Message[] = []
): Message[] {
  // If we have no history or find an existing instance of history, return the
  // original messages unmodified.
  if (!history || messagesHaveHistory(messages)) {
    return messages;
  }

  // If there are no messages, return the history.
  if (messages.length === 0) {
    return history;
  }

  const lastMessage = messages.at(-1);
  if (lastMessage?.role === 'user') {
    // If the last message is a user message, insert the history before it.
    const messagesWithoutLast = messages.slice(0, -1);
    return [...messagesWithoutLast, ...history, lastMessage];
  }

  // Otherwise, append the history to the end of the messages.
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
  return splitByMediaAndSectionMarkers(source).map(parsePart);
}

/**
 * Parses a part from a string.
 *
 * @param piece The piece to parse
 * @return Parsed part
 */
export function parsePart(piece: string): Part {
  if (piece.startsWith(MEDIA_MARKER_PREFIX)) {
    return parseMediaPart(piece);
  } else if (piece.startsWith(SECTION_MARKER_PREFIX)) {
    return parseSectionPart(piece);
  }
  return parseTextPart(piece);
}

/**
 * Parses a media part from a string.
 *
 * @param piece The piece to parse
 * @return Parsed media part
 */
export function parseMediaPart(piece: string): MediaPart {
  if (!piece.startsWith(MEDIA_MARKER_PREFIX)) {
    throw new Error('Invalid media piece');
  }
  const [_, url, contentType] = piece.split(' ');
  const part: MediaPart = { media: { url } };
  if (contentType) {
    part.media.contentType = contentType;
  }
  return part;
}

/**
 * Parses a section part from a string.
 *
 * @param piece The piece to parse
 * @return Parsed section part
 */
export function parseSectionPart(piece: string): PendingPart {
  if (!piece.startsWith(SECTION_MARKER_PREFIX)) {
    throw new Error('Invalid section piece');
  }
  const [_, sectionType] = piece.split(' ');
  return { metadata: { purpose: sectionType, pending: true } };
}

/**
 * Parses a text part from a string.
 *
 * @param piece The piece to parse
 * @return Parsed text part
 */
export function parseTextPart(piece: string): TextPart {
  return { text: piece };
}
