/**
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, expect, it } from 'vitest';
import {
  FRONTMATTER_AND_BODY_REGEX,
  MEDIA_AND_SECTION_MARKER_REGEX,
  ROLE_AND_HISTORY_MARKER_REGEX,
  convertNamespacedEntryToNestedObject,
  extractFrontmatterAndBody,
  insertHistory,
  parseDocument,
  splitByMediaAndSectionMarkers,
  splitByRegex,
  splitByRoleAndHistoryMarkers,
  toParts,
  transformMessagesToHistory,
} from './parse';
import type { Message } from './types';

describe('ROLE_AND_HISTORY_MARKER_REGEX', () => {
  describe('valid patterns', () => {
    const validPatterns = [
      '<<<dotprompt:role:user>>>',
      '<<<dotprompt:role:assistant>>>',
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
      '<<<dotprompt:role:assistant1>>>', // numbers not allowed
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
      <<<dotprompt:role:assistant>>> Hi there
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
    const input = 'Hello <<<dotprompt:role:assistant>>> world';
    const output = splitByRoleAndHistoryMarkers(input);
    expect(output).toEqual(['Hello ', '<<<dotprompt:role:assistant', ' world']);
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

  it('should not extract frontmatter when there is no frontmatter', () => {
    // The frontmatter is not optional.
    const source = 'No frontmatter here.';
    const { frontmatter, body } = extractFrontmatterAndBody(source);
    expect(frontmatter).toBe('');
    expect(body).toBe('');
  });
});

describe('splitIntoParts', () => {
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

  it('should remove parts that are only whitespace', () => {
    const source = '  <<<dotprompt:media:url>>>   ';
    const result = toParts(source);
    expect(result).toEqual([{ media: { url: undefined } }]);
  });
});

describe('transformMessagesToHistory', () => {
  it('should add history purpose to messages without metadata', () => {
    const messages: Message[] = [{ content: 'Hello' }, { content: 'World' }];
    const result = transformMessagesToHistory(messages);
    expect(result).toEqual([
      { content: 'Hello', metadata: { purpose: 'history' } },
      { content: 'World', metadata: { purpose: 'history' } },
    ]);
  });

  it('should preserve existing metadata while adding history purpose', () => {
    const messages = [{ content: 'Test', metadata: { foo: 'bar' } }];
    const result = transformMessagesToHistory(messages);
    expect(result).toEqual([
      { content: 'Test', metadata: { foo: 'bar', purpose: 'history' } },
    ]);
  });

  it('should handle empty array', () => {
    const result = transformMessagesToHistory([]);
    expect(result).toEqual([]);
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

describe('insertHistory', () => {
  it('should insert history messages at the correct position', () => {
    const messages: Message[] = [
      { role: 'user', content: 'first' },
      { role: 'model', content: 'second', metadata: { purpose: 'history' } },
      { role: 'user', content: 'third' },
    ];
    const history: Message[] = [
      { role: 'user', content: 'past1' },
      { role: 'assistant', content: 'past2' },
    ];
    const result = insertHistory(messages, history);
    // Since there's already a history marker, the original messages should be
    // returned unchanged.
    expect(result).toEqual(messages);
  });

  it('should handle empty history', () => {
    const messages = [
      { role: 'user', content: 'first' },
      { role: 'user', content: 'second' },
    ];
    const result = insertHistory(messages);
    expect(result).toEqual(messages);
  });

  it('should append history if no history marker and no trailing user message', () => {
    const messages = [
      { role: 'user', content: 'first' },
      { role: 'assistant', content: 'second' },
    ];
    const history = [
      { role: 'user', content: 'past1' },
      { role: 'assistant', content: 'past2' },
    ];
    const result = insertHistory(messages, history);
    expect(result).toEqual([...messages, ...history]);
  });

  it('should insert history before last user message if no history marker', () => {
    const messages = [
      { role: 'user', content: 'first' },
      { role: 'assistant', content: 'second' },
      { role: 'user', content: 'third' },
    ];
    const history = [
      { role: 'user', content: 'past1' },
      { role: 'assistant', content: 'past2' },
    ];
    const result = insertHistory(messages, history);
    expect(result).toEqual([
      { role: 'user', content: 'first' },
      { role: 'assistant', content: 'second' },
      ...history,
      { role: 'user', content: 'third' },
    ]);
  });
});

describe('toParts', () => {
  it('should convert text content to parts', () => {
    const source = 'Hello World';
    const result = toParts(source);
    expect(result).toEqual([{ text: 'Hello World' }]);
  });

  it('should handle media markers', () => {
    const source = '<<<dotprompt:media:url>>> https://example.com/image.jpg';
    const result = toParts(source);
    expect(result).toEqual([
      { media: { url: undefined } },
      { text: ' https://example.com/image.jpg' },
    ]);
  });

  it('should handle section markers', () => {
    const source = '<<<dotprompt:section>>> code';
    const result = toParts(source);
    expect(result).toEqual([
      { metadata: { purpose: undefined, pending: true } },
      { text: ' code' },
    ]);
  });

  it('should handle mixed content', () => {
    const source =
      'Text before <<<dotprompt:media:url>>> https://example.com/image.jpg Text after';
    const result = toParts(source);
    expect(result).toEqual([
      { text: 'Text before ' },
      { media: { url: undefined } },
      { text: ' https://example.com/image.jpg Text after' },
    ]);
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
});
