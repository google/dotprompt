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
 * In-band markers used to turn a rendered template string into messages.
 *
 * The `role`, `history`, `section` and `media` helpers emit markers into the
 * rendered string, which is then split back apart by `toMessages`. Because the
 * rendered string also contains user-supplied variable values verbatim, every
 * marker carries a random per-render nonce and the splitter only honors markers
 * with that nonce. Anything else that merely looks like a marker (e.g. typed by
 * an end user) stays plain text.
 *
 * Marker format: `<<<dotprompt:{nonce}:{body}>>>`, where body is one of
 * `role:{name}`, `history`, `section {name}`, `media:url {url} [{contentType}]`.
 */

/**
 * Key under which the per-render nonce is stored in the Handlebars data frame.
 * Written last when building the frame so `data.context` can't override it.
 */
export const MARKER_NONCE_DATA_KEY = '__dotpromptMarkerNonce';

const NONCE_PATTERN = /^[0-9a-f]{32}$/;

/** Generates a fresh 128-bit hex nonce. Call once per render. */
export function generateMarkerNonce(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
}

function assertNonce(nonce: string): void {
  // The nonce is interpolated into a RegExp, so keep it strictly hex.
  if (!NONCE_PATTERN.test(nonce)) {
    throw new Error('dotprompt: invalid marker nonce');
  }
}

/** Formats a marker with the given nonce and body. */
export function formatMarker(nonce: string, body: string): string {
  assertNonce(nonce);
  return `<<<dotprompt:${nonce}:${body}>>>`;
}

/**
 * Matches role and history markers for the given nonce. The single capture
 * group is the marker body (`role:user`, `history`).
 *
 * Only lowercase letters are allowed in role names.
 */
export function roleAndHistoryMarkerRegex(nonce: string): RegExp {
  assertNonce(nonce);
  return new RegExp(`<<<dotprompt:${nonce}:(role:[a-z]+|history)>>>`, 'g');
}

/**
 * Matches media and section markers for the given nonce. The single capture
 * group is the marker body (`media:url https://... image/png`, `section code`).
 */
export function mediaAndSectionMarkerRegex(nonce: string): RegExp {
  assertNonce(nonce);
  return new RegExp(
    `<<<dotprompt:${nonce}:((?:media:url|section) .*?)>>>`,
    'g'
  );
}

/** A piece of a rendered string: either literal text or a trusted marker. */
export type MarkerPiece =
  | { type: 'text'; text: string }
  | { type: 'marker'; body: string };

/**
 * Splits `source` on markers matched by `regex`, which must have exactly one
 * capture group (the marker body).
 *
 * Pieces are classified by position rather than content: `String.split` with
 * one capture group puts text at even indices and captures at odd ones. This
 * matters because a text piece could itself start with something that looks
 * like a marker. Whitespace-only text pieces are dropped.
 */
export function splitByMarkers(source: string, regex: RegExp): MarkerPiece[] {
  const pieces: MarkerPiece[] = [];
  source.split(regex).forEach((s, i) => {
    if (i % 2 === 1) {
      pieces.push({ type: 'marker', body: s });
    } else if (s.trim() !== '') {
      pieces.push({ type: 'text', text: s });
    }
  });
  return pieces;
}
