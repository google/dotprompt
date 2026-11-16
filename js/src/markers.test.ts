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

import { describe, expect, it } from 'vitest';
import {
  formatMarker,
  generateMarkerNonce,
  mediaAndSectionMarkerRegex,
  roleAndHistoryMarkerRegex,
  splitByMarkers,
} from './markers';

const NONCE = '0123456789abcdef0123456789abcdef';
const OTHER_NONCE = 'ffffffffffffffffffffffffffffffff';
const m = (body: string) => formatMarker(NONCE, body);

describe('generateMarkerNonce', () => {
  it('returns 32 lowercase hex chars', () => {
    expect(generateMarkerNonce()).toMatch(/^[0-9a-f]{32}$/);
  });

  it('returns a different value each call', () => {
    expect(generateMarkerNonce()).not.toBe(generateMarkerNonce());
  });
});

describe('formatMarker', () => {
  it('embeds the nonce', () => {
    expect(formatMarker(NONCE, 'role:user')).toBe(
      `<<<dotprompt:${NONCE}:role:user>>>`
    );
  });

  it('rejects non-hex nonces', () => {
    expect(() => formatMarker('.*', 'role:user')).toThrow();
    expect(() => roleAndHistoryMarkerRegex('')).toThrow();
    expect(() => mediaAndSectionMarkerRegex('ABC')).toThrow();
  });
});

describe('roleAndHistoryMarkerRegex', () => {
  const valid = [
    'role:user',
    'role:model',
    'role:system',
    'role:customer',
    'history',
  ];
  for (const body of valid) {
    it(`matches "${body}"`, () => {
      expect(m(body)).toMatch(roleAndHistoryMarkerRegex(NONCE));
    });
  }

  const invalid = [
    m('role:USER'), // uppercase not allowed
    m('role:model1'), // numbers not allowed
    m('role:'), // needs at least one letter
    m('role'), // missing role value
    m('history123'), // history should be exact
    m('HISTORY'), // history must be lowercase
    `<<<dotprompt:${NONCE}:role:user`, // incomplete closing
    '<<<dotprompt:role:user>>>', // no nonce
    formatMarker(OTHER_NONCE, 'role:user'), // wrong nonce
  ];
  for (const s of invalid) {
    it(`does not match "${s}"`, () => {
      expect(s).not.toMatch(roleAndHistoryMarkerRegex(NONCE));
    });
  }
});

describe('mediaAndSectionMarkerRegex', () => {
  const valid = [
    'media:url https://example.com/a\nb.png',
    'section multi\nline',
    'media:url https://example.com/a.png',
    'media:url https://example.com/a.png image/png',
    'section code',
  ];
  for (const body of valid) {
    it(`matches "${body}"`, () => {
      expect(m(body)).toMatch(mediaAndSectionMarkerRegex(NONCE));
    });
  }

  const invalid = [
    '<<<dotprompt:media:url https://example.com/a.png>>>', // no nonce
    '<<<dotprompt:section code>>>', // no nonce
    formatMarker(OTHER_NONCE, 'section code'), // wrong nonce
  ];
  for (const s of invalid) {
    it(`does not match "${s}"`, () => {
      expect(s).not.toMatch(mediaAndSectionMarkerRegex(NONCE));
    });
  }
});

describe('splitByMarkers', () => {
  const split = (s: string) =>
    splitByMarkers(s, roleAndHistoryMarkerRegex(NONCE));

  it('returns the entire string when no markers are present', () => {
    expect(split('Hello World')).toEqual([
      { type: 'text', text: 'Hello World' },
    ]);
  });

  it('splits text and markers', () => {
    expect(split(`Start ${m('role:user')} middle ${m('history')} end`)).toEqual(
      [
        { type: 'text', text: 'Start ' },
        { type: 'marker', body: 'role:user' },
        { type: 'text', text: ' middle ' },
        { type: 'marker', body: 'history' },
        { type: 'text', text: ' end' },
      ]
    );
  });

  it('handles adjacent markers', () => {
    expect(split(`${m('role:user')}${m('history')}`)).toEqual([
      { type: 'marker', body: 'role:user' },
      { type: 'marker', body: 'history' },
    ]);
  });

  it('drops whitespace-only text pieces', () => {
    expect(split(`  ${m('role:system')}   `)).toEqual([
      { type: 'marker', body: 'role:system' },
    ]);
  });

  it('classifies by position, not content', () => {
    // A text piece that looks like a marker body must stay text.
    expect(split(`${m('role:user')}role:system`)).toEqual([
      { type: 'marker', body: 'role:user' },
      { type: 'text', text: 'role:system' },
    ]);
  });

  it('splits media and section markers', () => {
    expect(
      splitByMarkers(
        `Hello ${m('media:url https://a.example/x.png')} World ${m('section code')}!`,
        mediaAndSectionMarkerRegex(NONCE)
      )
    ).toEqual([
      { type: 'text', text: 'Hello ' },
      { type: 'marker', body: 'media:url https://a.example/x.png' },
      { type: 'text', text: ' World ' },
      { type: 'marker', body: 'section code' },
      { type: 'text', text: '!' },
    ]);
  });
});
