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

// Re-renders conformance_cases.json with Handlebars and checks the recording.
// Usage: node conformance_oracle.js <path-to-handlebars> <path-to-cases.json>

const fs = require('fs');
const Handlebars = require(process.argv[2]);
const cases = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));

function upper(value) {
  if (value == null) return '';
  return String(value).toUpperCase();
}
function add(a, b) {
  const n = (v) => (v == null || v === false ? 0 : v === true ? 1 : Number(v));
  return n(a) + n(b);
}
function ident(value) {
  return value;
}
function wrap(a, b) {
  if (b && typeof b === 'object' && Object.prototype.hasOwnProperty.call(b, 'hash')) {
    const prefix = (b.hash && b.hash.prefix) || '';
    const value = a == null ? '' : a;
    return prefix + '[' + value + ']';
  }
  if (a && typeof a.fn === 'function') return a.fn(this);
  return '[' + (a == null ? '' : a) + ']';
}
function eq(a, b, options) {
  const same = a === b;
  if (options && typeof options.fn === 'function') {
    return same ? options.fn(this) : options.inverse(this);
  }
  return same;
}
const catalog = { upper, add, ident, wrap, eq };
const problems = [];

for (const c of cases) {
  const hb = Handlebars.create();
  for (const name of c.helpers || []) hb.registerHelper(name, catalog[name]);
  for (const [key, value] of Object.entries(c.partials || {})) hb.registerPartial(key, value);
  let rendered;
  let failed = false;
  try {
    rendered = hb.compile(c.template, { strict: !!c.strict })(c.context, { data: c.data || undefined });
  } catch (err) {
    failed = true;
  }
  if (c.raises) {
    if (!failed) problems.push(c.name + ' rendered ' + JSON.stringify(rendered));
    continue;
  }
  if (failed || rendered !== c.text) {
    problems.push(c.name + ' got ' + JSON.stringify(failed ? 'RAISE' : rendered));
  }
}

if (problems.length) {
  console.error(problems.join('\n'));
  process.exit(1);
}
