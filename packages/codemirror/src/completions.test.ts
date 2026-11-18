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

import {
  CompletionContext,
  insertCompletionText,
} from '@codemirror/autocomplete';
import { EditorState, type Transaction } from '@codemirror/state';
import type { EditorView } from '@codemirror/view';
import { describe, expect, it } from 'vitest';
import { dotpromptCompletions } from './completions';

/**
 * Runs the completion source on `docWithCursor` (`|` marks the cursor), accepts
 * the option labelled `label` and returns the resulting doc plus the selected
 * text (the active snippet field, if any).
 */
function accept(
  docWithCursor: string,
  label: string
): { doc: string; selected: string } {
  const pos = docWithCursor.indexOf('|');
  const doc = docWithCursor.slice(0, pos) + docWithCursor.slice(pos + 1);
  let state = EditorState.create({ doc, selection: { anchor: pos } });

  const result = dotpromptCompletions(new CompletionContext(state, pos, true));
  const option = result?.options.find((o) => o.label === label);
  if (!result || !option) {
    throw new Error(
      `no "${label}" completion for ${JSON.stringify(docWithCursor)}`
    );
  }
  const to = result.to ?? pos;

  if (typeof option.apply === 'function') {
    // A real EditorView needs a DOM. Snippet apply functions only read `state`
    // and call `dispatch`, so a minimal stand-in is enough here.
    const editor = {
      get state(): EditorState {
        return state;
      },
      dispatch(tr: Transaction): void {
        state = tr.state;
      },
    };
    option.apply(editor as unknown as EditorView, option, result.from, to);
  } else {
    const text = option.apply ?? option.label;
    state = state.update(
      insertCompletionText(state, text, result.from, to)
    ).state;
  }

  const sel = state.selection.main;
  return {
    doc: state.doc.toString(),
    selected: state.sliceDoc(sel.from, sel.to),
  };
}

describe('helper completions after {{', () => {
  it.each([
    ['{{ro|', 'role', '{{role "system"}}\n', 'system'],
    ['{{sec|', 'section', '{{section "name"}}\n', 'name'],
    ['{{i|', 'if', '{{#if condition}}\n  \n{{/if}}', 'condition'],
    ['{{ea|', 'each', '{{#each items}}\n  {{this}}\n{{/each}}', 'items'],
    [
      '{{ifE|',
      'ifEquals',
      '{{#ifEquals value1 value2}}\n  \n{{/ifEquals}}',
      'value1',
    ],
    ['{{js|', 'json', '{{json value}}', 'value'],
    ['{{me|', 'media', '{{media url=url}}', 'url'],
    ['{{loo|', 'lookup', '{{lookup object key}}', 'object'],
    ['{{hi|', 'history', '{{history}}', ''],
    ['{{el|', 'else', '{{else}}', ''],
  ])('%s + %s', (input, label, doc, selected) => {
    expect(accept(input, label)).toEqual({ doc, selected });
  });

  it('replaces an auto-closed }} instead of doubling it', () => {
    expect(accept('{{ro|}}', 'role')).toEqual({
      doc: '{{role "system"}}\n',
      selected: 'system',
    });
    expect(accept('a {{hi|}} b', 'history').doc).toBe('a {{history}} b');
  });

  it('indents block bodies relative to the current line', () => {
    expect(accept('  {{w|', 'with').doc).toBe(
      '  {{#with context}}\n    \n  {{/with}}'
    );
  });
});

describe('block open/close completions', () => {
  it('inserts only the helper name after {{#', () => {
    expect(accept('{{#i|', 'if').doc).toBe('{{#if');
    expect(accept('{{#unlessE|}}', 'unlessEquals').doc).toBe(
      '{{#unlessEquals}}'
    );
  });

  it('inserts only the block name after {{/', () => {
    expect(accept('{{/ea|', 'each').doc).toBe('{{/each');
  });
});

describe('role snippets for a bare word', () => {
  it('replaces the word with an inline role helper', () => {
    expect(accept('Intro\nsys|', 'system').doc).toBe(
      'Intro\n{{role "system"}}\n'
    );
  });
});
