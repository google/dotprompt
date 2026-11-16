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

import handlebars from 'handlebars/dist/cjs/handlebars.js';

import { formatMarker, MARKER_NONCE_DATA_KEY } from './markers';

const { SafeString } = handlebars;

// NOTE: every export of this module is registered as a template helper.

/**
 * Reads the per-render marker nonce from the Handlebars data frame. Data frames
 * are inherited by blocks (`#each`, `#if`, ...) and partials, so this only
 * fails if the helper runs outside `Dotprompt` rendering or a custom block
 * helper replaces `data` wholesale instead of using `createFrame`.
 */
function markerNonce(options: Handlebars.HelperOptions): string {
  const nonce: unknown = options.data?.[MARKER_NONCE_DATA_KEY];
  if (typeof nonce !== 'string') {
    throw new Error(
      'dotprompt: marker helpers (role, history, section, media) must be rendered via Dotprompt'
    );
  }
  return nonce;
}

export function json(
  serializable: any,
  options: { hash: { indent?: number } }
) {
  return new SafeString(
    JSON.stringify(serializable, null, options.hash.indent || 0)
  );
}

export function role(role: string, options: Handlebars.HelperOptions) {
  return new SafeString(formatMarker(markerNonce(options), `role:${role}`));
}

export function history(options: Handlebars.HelperOptions) {
  return new SafeString(formatMarker(markerNonce(options), 'history'));
}

export function section(name: string, options: Handlebars.HelperOptions) {
  return new SafeString(formatMarker(markerNonce(options), `section ${name}`));
}

export function media(options: Handlebars.HelperOptions) {
  const { url, contentType } = options.hash;
  return new SafeString(
    formatMarker(
      markerNonce(options),
      `media:url ${url}${contentType ? ` ${contentType}` : ''}`
    )
  );
}

export function ifEquals(
  this: any,
  arg1: any,
  arg2: any,
  options: Handlebars.HelperOptions
) {
  return arg1 === arg2 ? options.fn(this) : options.inverse(this);
}

export function unlessEquals(
  this: any,
  arg1: any,
  arg2: any,
  options: Handlebars.HelperOptions
) {
  return arg1 !== arg2 ? options.fn(this) : options.inverse(this);
}
