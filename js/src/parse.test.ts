/**
 * Copyright 2025 Google LLC
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

import { describe, expect, it } from 'vitest';
import {
  FRONTMATTER_AND_BODY_REGEX,
  MEDIA_AND_SECTION_MARKER_REGEX,
  RESERVED_METADATA_KEYWORDS,
  ROLE_AND_HISTORY_MARKER_REGEX,
  convertNamespacedEntryToNestedObject,
  extractFrontmatterAndBody,
  insertHistory,
  messageSourcesToMessages,
  messagesHaveHistory,
  parseDocument,
  parseMediaPart,
  parsePart,
  parseSectionPart,
  parseTextPart,
  splitByMediaAndSectionMarkers,
  splitByRegex,
  splitByRoleAndHistoryMarkers,
  toMessages,
  transformMessagesToHistory,
} from './parse';
import type { MessageSource } from './parse';
import type { DataArgument, Message } from './types';

describe('ROLE_AND_HISTORY_MARKER_REGEX', () => {
  // NOTE: Currently this doesn't validate the role.
  describe('valid patterns', () => {
    const validPatterns = [
      '<<<dotprompt:role:user>>>',
      '<<<dotprompt:role:model>>>',
      '<<<dotprompt:role:system>>>',
      '<<<dotprompt:history>>>',
      '<<<dotprompt:role:bot>>>',
      '<<<dotprompt:role:human>>>',
      '<<<dotprompt:role:customer>>>',
    ];

    for (const pattern of validPatterns) {
      it(`should match "${pattern}"`, () => {
        expect(pattern).toMatch(ROLE_AND_HISTORY_MARKER_REGEX);
      });
    }
  });

  describe('invalid patterns', () => {
    const invalidPatterns = [
      '<<<dotprompt:role:USER>>>', // uppercase not allowed
      '<<<dotprompt:role:model1>>>', // numbers not allowed
      '<<<dotprompt:role:>>>', // needs at least one letter
      '<<<dotprompt:role>>>', // missing role value
      '<<<dotprompt:history123>>>', // history should be exact
      '<<<dotprompt:HISTORY>>>', // history must be lowercase
      'dotprompt:role:user', // missing brackets
      '<<<dotprompt:role:user', // incomplete closing
      'dotprompt:role:user>>>', // incomplete opening
    ];

    for (const pattern of invalidPatterns) {
      it(`should not match "${pattern}"`, () => {
        expect(pattern).not.toMatch(ROLE_AND_HISTORY_MARKER_REGEX);
      });
    }
  });

  it('should match multiple occurrences in a string', () => {
    const text = `
      <<<dotprompt:role:user>>> Hello
      <<<dotprompt:role:model>>> Hi there
      <<<dotprompt:history>>>
      <<<dotprompt:role:user>>> How are you?
    `;

    const matches = text.match(ROLE_AND_HISTORY_MARKER_REGEX);
    expect(matches).toHaveLength(4);
  });
});

describe('MEDIA_AND_SECTION_MARKER_REGEX', () => {
  describe('valid patterns', () => {
    const validPatterns = [
      '<<<dotprompt:media:url>>>',
      '<<<dotprompt:section>>>',
    ];

    for (const pattern of validPatterns) {
      it(`should match "${pattern}"`, () => {
        expect(pattern).toMatch(MEDIA_AND_SECTION_MARKER_REGEX);
      });
    }
  });

  it('should match media and section markers', () => {
    const text = `
      <<<dotprompt:media:url>>> https://example.com/image.jpg
      <<<dotprompt:section>>> Section 1
      <<<dotprompt:media:url>>> https://example.com/video.mp4
      <<<dotprompt:section>>> Section 2
    `;

    const matches = text.match(MEDIA_AND_SECTION_MARKER_REGEX);
    expect(matches).toHaveLength(4);
  });
});

describe('splitByRoleAndHistoryMarkers', () => {
  it('returns the entire string when no markers are present', () => {
    const input = 'Hello World';
    const output = splitByRoleAndHistoryMarkers(input);
    expect(output).toEqual(['Hello World']);
  });

  it('splits a string with a single marker correctly', () => {
    const input = 'Hello <<<dotprompt:role:model>>> world';
    const output = splitByRoleAndHistoryMarkers(input);
    expect(output).toEqual(['Hello ', '<<<dotprompt:role:model', ' world']);
  });

  it('filters out empty and whitespace-only pieces', () => {
    const input = '  <<<dotprompt:role:system>>>   ';
    const output = splitByRoleAndHistoryMarkers(input);
    expect(output).toEqual(['<<<dotprompt:role:system']);
  });

  it('handles adjacent markers correctly', () => {
    const input = '<<<dotprompt:role:user>>><<<dotprompt:history>>>';
    const output = splitByRoleAndHistoryMarkers(input);
    expect(output).toEqual(['<<<dotprompt:role:user', '<<<dotprompt:history']);
  });

  it('does not split on markers with uppercase letters (invalid format)', () => {
    const input = '<<<dotprompt:ROLE:user>>>';
    // The regex only matches lowercase "role:"; so no split occurs.
    const output = splitByRoleAndHistoryMarkers(input);
    expect(output).toEqual(['<<<dotprompt:ROLE:user>>>']);
  });

  it('handles a string with multiple markers interleaved with text', () => {
    const input =
      'Start <<<dotprompt:role:user>>> middle <<<dotprompt:history>>> end';
    const output = splitByRoleAndHistoryMarkers(input);
    expect(output).toEqual([
      'Start ',
      '<<<dotprompt:role:user',
      ' middle ',
      '<<<dotprompt:history',
      ' end',
    ]);
  });
});

describe('convertNamespacedEntryToNestedObject', () => {
  it('should create nested object structure from namespaced key', () => {
    const result = convertNamespacedEntryToNestedObject('foo.bar', 'hello');
    expect(result).toEqual({
      foo: {
        bar: 'hello',
      },
    });
  });

  it('should add to existing namespace', () => {
    const existing = {
      foo: {
        bar: 'hello',
      },
    };
    const result = convertNamespacedEntryToNestedObject(
      'foo.baz',
      'world',
      existing
    );
    expect(result).toEqual({
      foo: {
        bar: 'hello',
        baz: 'world',
      },
    });
  });

  it('should handle multiple namespaces', () => {
    const result = convertNamespacedEntryToNestedObject('foo.bar', 'hello');
    const finalResult = convertNamespacedEntryToNestedObject(
      'baz.qux',
      'world',
      result
    );
    expect(finalResult).toEqual({
      foo: {
        bar: 'hello',
      },
      baz: {
        qux: 'world',
      },
    });
  });
});

describe('FRONTMATTER_AND_BODY_REGEX', () => {
  it('should match a document with frontmatter and body', () => {
    const source = '---\nfoo: bar\n---\nThis is the body.';
    const match = source.match(FRONTMATTER_AND_BODY_REGEX);
    expect(match).not.toBeNull();
    if (match) {
      const [fullMatch, frontmatter, body] = match;
      expect(fullMatch).toBe(source);
      expect(frontmatter).toBe('foo: bar');
      expect(body).toBe('This is the body.');
    }
  });

  it('should match a document with frontmatter having extra spaces', () => {
    const source = '---   \n   title: Test   \n---   \nContent here.';
    const match = source.match(FRONTMATTER_AND_BODY_REGEX);
    expect(match).not.toBeNull();
    if (match) {
      const [fullMatch, frontmatter, body] = match;
      expect(fullMatch).toBe(source);
      expect(frontmatter.trim()).toBe('title: Test');
      expect(body).toBe('Content here.');
    }
  });

  it('should not match when there is no frontmatter', () => {
    const source = 'No frontmatter here.';
    const match = source.match(FRONTMATTER_AND_BODY_REGEX);
    expect(match).toBeNull();
  });
});

describe('extractFrontmatterAndBody', () => {
  it('should extract frontmatter and body', () => {
    const source = '---\nfoo: bar\n---\nThis is the body.';
    const { frontmatter, body } = extractFrontmatterAndBody(source);
    expect(frontmatter).toBe('foo: bar');
    expect(body).toBe('This is the body.');
  });

  it('should match as empty frontmatter and body when there is no frontmatter', () => {
    // Both the frontmatter and the body match as empty when there is no
    // frontmatter.
    const source = 'No frontmatter here.';
    const { frontmatter, body } = extractFrontmatterAndBody(source);
    expect(frontmatter).toBe('');
    expect(body).toBe('');
  });
});

describe('splitByMediaAndSectionMarkers', () => {
  it('should return entire string in an array if there are no markers', () => {
    const source = 'This is a test string.';
    const parts = splitByMediaAndSectionMarkers(source);
    expect(parts).toEqual(['This is a test string.']);
  });

  it('should split a string containing markers into expected parts', () => {
    const source =
      'Hello <<<dotprompt:media:url>>> World <<<dotprompt:section>>>!';
    const parts = splitByMediaAndSectionMarkers(source);
    expect(parts).toEqual([
      'Hello ',
      '<<<dotprompt:media:url',
      ' World ',
      '<<<dotprompt:section',
      '!',
    ]);
  });
});

describe('splitByRegex', () => {
  it('should split string by regex and filter empty/whitespace pieces', () => {
    const source = '  one  ,  ,  two  ,  three  ';
    const result = splitByRegex(source, /,/g);
    expect(result).toEqual(['  one  ', '  two  ', '  three  ']);
  });

  it('should handle string with no matches', () => {
    const source = 'no matches here';
    const result = splitByRegex(source, /,/g);
    expect(result).toEqual(['no matches here']);
  });

  it('should return empty array for empty string', () => {
    const result = splitByRegex('', /,/g);
    expect(result).toEqual([]);
  });
});

describe('transformMessagesToHistory', () => {
  it('should add history metadata to messages', () => {
    const messages: Message[] = [
      { role: 'user', content: [{ text: 'Hello' }] },
      { role: 'model', content: [{ text: 'Hi there' }] },
    ];

    const result = transformMessagesToHistory(messages);

    expect(result).toHaveLength(2);
    expect(result).toEqual([
      {
        role: 'user',
        content: [{ text: 'Hello' }],
        metadata: { purpose: 'history' },
      },
      {
        role: 'model',
        content: [{ text: 'Hi there' }],
        metadata: { purpose: 'history' },
      },
    ]);
  });

  it('should preserve existing metadata while adding history purpose', () => {
    const messages: Message[] = [
      { role: 'user', content: [{ text: 'Hello' }], metadata: { foo: 'bar' } },
    ];

    const result = transformMessagesToHistory(messages);

    expect(result).toHaveLength(1);
    expect(result).toEqual([
      {
        role: 'user',
        content: [{ text: 'Hello' }],
        metadata: { foo: 'bar', purpose: 'history' },
      },
    ]);
  });

  it('should handle empty array', () => {
    const result = transformMessagesToHistory([]);
    expect(result).toEqual([]);
  });
});

describe('messagesHaveHistory', () => {
  it('should return true if messages have history metadata', () => {
    const messages: Message[] = [
      {
        role: 'user',
        content: [{ text: 'Hello' }],
        metadata: { purpose: 'history' },
      },
    ];

    const result = messagesHaveHistory(messages);

    expect(result).toBe(true);
  });

  it('should return false if messages do not have history metadata', () => {
    const messages: Message[] = [
      { role: 'user', content: [{ text: 'Hello' }] },
    ];

    const result = messagesHaveHistory(messages);

    expect(result).toBe(false);
  });
});

describe('messageSourcesToMessages', () => {
  it('should handle empty array', () => {
    const messageSources: MessageSource[] = [];
    const expected: Message[] = [];
    expect(messageSourcesToMessages(messageSources)).toEqual(expected);
  });

  it('should convert a single message source', () => {
    const messageSources: MessageSource[] = [{ role: 'user', source: 'Hello' }];
    const expected: Message[] = [
      { role: 'user', content: [{ text: 'Hello' }] },
    ];
    expect(messageSourcesToMessages(messageSources)).toEqual(expected);
  });

  it('should handle message source with content', () => {
    const messageSources: MessageSource[] = [
      { role: 'user', content: [{ text: 'Existing content' }] },
    ];
    const expected: Message[] = [
      { role: 'user', content: [{ text: 'Existing content' }] },
    ];
    expect(messageSourcesToMessages(messageSources)).toEqual(expected);
  });

  it('should handle message source with metadata', () => {
    const messageSources: MessageSource[] = [
      { role: 'user', source: 'Hello', metadata: { foo: 'bar' } },
    ];
    const expected: Message[] = [
      {
        role: 'user',
        content: [{ text: 'Hello' }],
        metadata: { foo: 'bar' },
      },
    ];
    expect(messageSourcesToMessages(messageSources)).toEqual(expected);
  });

  it('should filter out message sources with empty source and content', () => {
    const messageSources: MessageSource[] = [
      { role: 'user', source: '' },
      { role: 'model', source: '  ' },
      { role: 'user', source: 'Hello' },
    ];
    const expected: Message[] = [
      { role: 'model', content: [] },
      { role: 'user', content: [{ text: 'Hello' }] },
    ];
    expect(messageSourcesToMessages(messageSources)).toEqual(expected);
  });

  it('should handle multiple message sources', () => {
    const messageSources: MessageSource[] = [
      { role: 'user', source: 'Hello' },
      { role: 'model', source: 'Hi there!' },
      { role: 'user', source: 'How are you?' },
    ];
    const expected: Message[] = [
      { role: 'user', content: [{ text: 'Hello' }] },
      { role: 'model', content: [{ text: 'Hi there!' }] },
      { role: 'user', content: [{ text: 'How are you?' }] },
    ];
    expect(messageSourcesToMessages(messageSources)).toEqual(expected);
  });
});

describe('toMessages', () => {
  it('should handle a simple string with no markers', () => {
    const renderedString = 'Hello world';
    const result = toMessages(renderedString);

    expect(result).toHaveLength(1);
    expect(result[0].role).toBe('user');
    expect(result[0].content).toEqual([{ text: 'Hello world' }]);
  });

  it('should handle a string with a single role marker', () => {
    const renderedString = '<<<dotprompt:role:model>>>Hello world';
    const result = toMessages(renderedString);

    expect(result).toHaveLength(1);
    expect(result[0].role).toBe('model');
    expect(result[0].content).toEqual([{ text: 'Hello world' }]);
  });

  it('should handle a string with multiple role markers', () => {
    const renderedString =
      '<<<dotprompt:role:system>>>System instructions\n' +
      '<<<dotprompt:role:user>>>User query\n' +
      '<<<dotprompt:role:model>>>Model response';
    const result = toMessages(renderedString);

    expect(result).toHaveLength(3);

    expect(result[0].role).toBe('system');
    expect(result[0].content).toEqual([{ text: 'System instructions\n' }]);

    expect(result[1].role).toBe('user');
    expect(result[1].content).toEqual([{ text: 'User query\n' }]);

    expect(result[2].role).toBe('model');
    expect(result[2].content).toEqual([{ text: 'Model response' }]);
  });

  it('should update the role of an empty message instead of creating a new one', () => {
    const renderedString =
      '<<<dotprompt:role:user>>><<<dotprompt:role:model>>>Response';
    const result = toMessages(renderedString);

    // Should only have one message since the first role marker doesn't have content
    expect(result).toHaveLength(1);
    expect(result[0].role).toBe('model');
    expect(result[0].content).toEqual([{ text: 'Response' }]);
  });

  it('should handle history markers and add metadata', () => {
    const renderedString =
      '<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up';
    const historyMessages: Message[] = [
      { role: 'user', content: [{ text: 'Previous question' }] },
      { role: 'model', content: [{ text: 'Previous answer' }] },
    ];

    const data: DataArgument = { messages: historyMessages };
    const result = toMessages(renderedString, data);

    expect(result).toHaveLength(4);

    // First message is the user query
    expect(result[0].role).toBe('user');
    expect(result[0].content).toEqual([{ text: 'Query' }]);

    // Next two messages should be history messages with appropriate metadata
    expect(result[1].role).toBe('user');
    expect(result[1].content).toEqual([{ text: 'Previous question' }]);
    expect(result[1].metadata).toEqual({ purpose: 'history' });

    expect(result[2].role).toBe('model');
    expect(result[2].content).toEqual([{ text: 'Previous answer' }]);
    expect(result[2].metadata).toEqual({ purpose: 'history' });

    // Last message is the follow-up
    expect(result[3].role).toBe('model');
    expect(result[3].content).toEqual([{ text: 'Follow-up' }]);
  });

  it('should handle empty history gracefully', () => {
    const renderedString =
      '<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up';
    const result = toMessages(renderedString, { messages: [] });

    expect(result).toHaveLength(2);
    expect(result[0].role).toBe('user');
    expect(result[0].content).toEqual([{ text: 'Query' }]);
    expect(result[1].role).toBe('model');
    expect(result[1].content).toEqual([{ text: 'Follow-up' }]);
  });

  it('should handle undefined data gracefully', () => {
    const renderedString =
      '<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up';
    const result = toMessages(renderedString, undefined);

    expect(result).toHaveLength(2);
    expect(result[0].role).toBe('user');
    expect(result[0].content).toEqual([{ text: 'Query' }]);
    expect(result[1].role).toBe('model');
    expect(result[1].content).toEqual([{ text: 'Follow-up' }]);
  });

  it('should filter out empty messages', () => {
    const renderedString =
      '<<<dotprompt:role:user>>> ' +
      '<<<dotprompt:role:system>>> ' +
      '<<<dotprompt:role:model>>>Response';
    const result = toMessages(renderedString);

    expect(result).toHaveLength(1);
    expect(result[0].role).toBe('model');
    expect(result[0].content).toEqual([{ text: 'Response' }]);
  });

  it('should handle multiple history markers by treating each as a separate insertion point', () => {
    const renderedString =
      '<<<dotprompt:history>>>First<<<dotprompt:history>>>Second';
    const historyMessages: Message[] = [
      { role: 'user', content: [{ text: 'Previous' }] },
    ];

    const data: DataArgument = { messages: historyMessages };
    const result = toMessages(renderedString, data);

    expect(result).toHaveLength(4);

    expect(result[0].metadata).toEqual({ purpose: 'history' });
    expect(result[1].content).toEqual([{ text: 'First' }]);
    expect(result[2].metadata).toEqual({ purpose: 'history' });
    expect(result[3].content).toEqual([{ text: 'Second' }]);
  });

  it('should support complex interleaving of role and history markers', () => {
    const renderedString =
      '<<<dotprompt:role:system>>>Instructions\n' +
      '<<<dotprompt:role:user>>>Initial Query\n' +
      '<<<dotprompt:history>>>\n' +
      '<<<dotprompt:role:user>>>Follow-up Question\n' +
      '<<<dotprompt:role:model>>>Final Response';

    const historyMessages: Message[] = [
      { role: 'user', content: [{ text: 'Previous question' }] },
      { role: 'model', content: [{ text: 'Previous answer' }] },
    ];

    const data: DataArgument = { messages: historyMessages };
    const result = toMessages(renderedString, data);

    expect(result).toHaveLength(6);

    expect(result[0].role).toBe('system');
    expect(result[0].content).toEqual([{ text: 'Instructions\n' }]);

    expect(result[1].role).toBe('user');
    expect(result[1].content).toEqual([{ text: 'Initial Query\n' }]);

    expect(result[2].role).toBe('user');
    expect(result[2].metadata).toEqual({ purpose: 'history' });

    expect(result[3].role).toBe('model');
    expect(result[3].metadata).toEqual({ purpose: 'history' });

    expect(result[4].role).toBe('user');
    expect(result[4].content).toEqual([{ text: 'Follow-up Question\n' }]);

    expect(result[5].role).toBe('model');
    expect(result[5].content).toEqual([{ text: 'Final Response' }]);
  });

  it('should handle an empty input string', () => {
    const result = toMessages('');
    expect(result).toHaveLength(0);
  });

  it('should properly call insertHistory with data.messages', () => {
    const renderedString = '<<<dotprompt:role:user>>>Question';
    const historyMessages: Message[] = [
      { role: 'user', content: [{ text: 'Previous' }] },
    ];

    const data: DataArgument = { messages: historyMessages };
    const result = toMessages(renderedString, data);

    // The resulting messages should have the history message inserted
    // before the user message by the insertHistory function
    expect(result).toHaveLength(2);
    expect(result[0].role).toBe('user');
    expect(result[0].content).toEqual([{ text: 'Previous' }]);
    expect(result[0].metadata).toBeUndefined(); // insertHistory shouldn't add history metadata

    expect(result[1].role).toBe('user');
    expect(result[1].content).toEqual([{ text: 'Question' }]);
  });
});

describe('insertHistory', () => {
  it('should return original messages if history is undefined', () => {
    const messages: Message[] = [
      { role: 'user', content: [{ text: 'Hello' }] },
    ];

    const result = insertHistory(messages, []);

    expect(result).toEqual(messages);
  });

  it('should return original messages if history purpose already exists', () => {
    const messages: Message[] = [
      {
        role: 'user',
        content: [{ text: 'Hello' }],
        metadata: { purpose: 'history' },
      },
    ];

    const history: Message[] = [
      {
        role: 'model',
        content: [{ text: 'Previous' }],
        metadata: { purpose: 'history' },
      },
    ];

    const result = insertHistory(messages, history);

    expect(result).toEqual(messages);
  });

  it('should insert history before the last user message', () => {
    const messages: Message[] = [
      { role: 'system', content: [{ text: 'System prompt' }] },
      { role: 'user', content: [{ text: 'Current question' }] },
    ];

    const history: Message[] = [
      {
        role: 'model',
        content: [{ text: 'Previous' }],
        metadata: { purpose: 'history' },
      },
    ];

    const result = insertHistory(messages, history);

    expect(result).toHaveLength(3);
    expect(result).toEqual([
      { role: 'system', content: [{ text: 'System prompt' }] },
      {
        role: 'model',
        content: [{ text: 'Previous' }],
        metadata: { purpose: 'history' },
      },
      { role: 'user', content: [{ text: 'Current question' }] },
    ]);
  });

  it('should append history at the end if no user message is last', () => {
    const messages: Message[] = [
      { role: 'system', content: [{ text: 'System prompt' }] },
      { role: 'model', content: [{ text: 'Model message' }] },
    ];
    const history: Message[] = [
      {
        role: 'model',
        content: [{ text: 'Previous' }],
        metadata: { purpose: 'history' },
      },
    ];

    const result = insertHistory(messages, history);

    expect(result).toHaveLength(3);
    expect(result).toEqual([
      { role: 'system', content: [{ text: 'System prompt' }] },
      { role: 'model', content: [{ text: 'Model message' }] },
      {
        role: 'model',
        content: [{ text: 'Previous' }],
        metadata: { purpose: 'history' },
      },
    ]);
  });
});

describe('parsePart', () => {
  it('should parse a media part', () => {
    const source = '<<<dotprompt:media:url>>> https://example.com/image.jpg';
    const result = parsePart(source);
    expect(result).toEqual({ media: { url: 'https://example.com/image.jpg' } });
  });

  it('should parse a section piece', () => {
    const source = '<<<dotprompt:section>>> code';
    const result = parsePart(source);
    expect(result).toEqual({ metadata: { purpose: 'code', pending: true } });
  });

  it('should parse a text piece', () => {
    const source = 'Hello World';
    const result = parsePart(source);
    expect(result).toEqual({ text: 'Hello World' });
  });
});

describe('parseMediaPart', () => {
  it('should parse a media part', () => {
    const source = '<<<dotprompt:media:url>>> https://example.com/image.jpg';
    const result = parseMediaPart(source);
    expect(result).toEqual({ media: { url: 'https://example.com/image.jpg' } });
  });

  it('should parse a media piece with content type', () => {
    const source =
      '<<<dotprompt:media:url>>> https://example.com/image.jpg image/jpeg';
    const result = parseMediaPart(source);
    expect(result).toEqual({
      media: {
        url: 'https://example.com/image.jpg',
        contentType: 'image/jpeg',
      },
    });
  });

  it('should throw an error if the media piece is invalid', () => {
    const source = 'https://example.com/image.jpg';
    expect(() => parseMediaPart(source)).toThrow();
  });
});

describe('parseSectionPart', () => {
  it('should parse a section part', () => {
    const source = '<<<dotprompt:section>>> code';
    const result = parseSectionPart(source);
    expect(result).toEqual({ metadata: { purpose: 'code', pending: true } });
  });

  it('should throw an error if the section piece is invalid', () => {
    const source = 'https://example.com/image.jpg';
    expect(() => parseSectionPart(source)).toThrow();
  });
});

describe('parseTextPart', () => {
  it('should parse a text part', () => {
    const source = 'Hello World';
    const result = parseTextPart(source);
    expect(result).toEqual({ text: 'Hello World' });
  });
});

describe('parseDocument', () => {
  it('should parse document with frontmatter and template', () => {
    const source = `---
name: test
description: test description
foo.bar: value
---
Template content`;

    const result = parseDocument(source);
    expect(result).toMatchObject({
      name: 'test',
      description: 'test description',
      ext: {
        foo: {
          bar: 'value',
        },
      },
      template: 'Template content',
    });
  });

  it('should handle document with empty frontmatter', () => {
    // TODO: Check whether this is the correct behavior.
    const source = '---\n\n---\nJust template content';
    const result = parseDocument(source);
    expect(result).toMatchObject({
      ext: {},
      template: source.trim(),
    });
  });

  it('should handle document without frontmatter', () => {
    const source = 'Just template content';
    const result = parseDocument(source);
    expect(result).toMatchObject({
      ext: {},
      template: 'Just template content',
    });
  });

  it('should handle invalid YAML frontmatter', () => {
    const source = `---
invalid: : yaml
---
Template content`;

    const result = parseDocument(source);
    expect(result).toMatchObject({
      ext: {},
      template: source.trim(),
    });
  });

  it('should handle reserved keywords in frontmatter', () => {
    const frontmatter_parts = [];
    for (const keyword of RESERVED_METADATA_KEYWORDS) {
      frontmatter_parts.push(`${keyword}: value`);
    }
    const source = `---
${frontmatter_parts.join('\n')}
---
Template content`;

    const result = parseDocument(source);
    expect(result).toMatchObject({
      ext: {},
      template: 'Template content',
    });
  });
});
