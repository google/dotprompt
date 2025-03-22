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

import { SafeString } from 'handlebars';

export function json(
  serializable: any,
  options: { hash: { indent?: number } }
) {
  return new SafeString(
    JSON.stringify(serializable, null, options.hash.indent || 0)
  );
}

export function role(role: string) {
  return new SafeString(`<<<dotprompt:role:${role}>>>`);
}

export function history() {
  return new SafeString('<<<dotprompt:history>>>');
}

export function section(name: string) {
  return new SafeString(`<<<dotprompt:section ${name}>>>`);
}

export function media(options: Handlebars.HelperOptions) {
  return new SafeString(
    `<<<dotprompt:media:url ${options.hash.url}${
      options.hash.contentType ? ` ${options.hash.contentType}` : ''
    }>>>`
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
