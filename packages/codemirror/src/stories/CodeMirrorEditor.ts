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

import { defaultKeymap } from '@codemirror/commands';
import { EditorState, Extension } from '@codemirror/state';
import { EditorView, keymap, lineNumbers } from '@codemirror/view';
import { emacs } from '@replit/codemirror-emacs';
import { vim } from '@replit/codemirror-vim';
import { dotprompt, dotpromptDarkTheme, dotpromptLightTheme } from '../index';

/** Editor keybinding mode */
export type EditorMode = 'standard' | 'vim' | 'emacs';

export interface CodeMirrorEditorProps {
  /** Initial content for the editor */
  value: string;
  /** Editor width */
  width: string;
  /** Editor height */
  height: string;
  /** Theme to use */
  theme: 'dark' | 'light';
  /** Enable line numbers */
  lineNumbers: boolean;
  /** Enable line wrapping */
  lineWrapping: boolean;
  /** Editor keybinding mode */
  editorMode: EditorMode;
  /** Read-only mode */
  readOnly: boolean;
}

/**
 * Creates a CodeMirror editor with Dotprompt language support.
 */
export const createCodeMirrorEditor = (
  props: CodeMirrorEditorProps
): HTMLElement => {
  const container = document.createElement('div');
  container.style.width = props.width;
  container.style.height = props.height;
  container.style.border = '1px solid #333';
  container.style.borderRadius = '4px';
  container.style.overflow = 'hidden';

  // Build extensions array
  const extensions: Extension[] = [
    // Dotprompt language support with completions
    dotprompt(),
    // Theme
    props.theme === 'dark' ? dotpromptDarkTheme : dotpromptLightTheme,
    // Basic keymap
    keymap.of(defaultKeymap),
  ];

  // Editor mode keybindings
  if (props.editorMode === 'vim') {
    extensions.push(vim());
  } else if (props.editorMode === 'emacs') {
    extensions.push(emacs());
  }

  if (props.lineNumbers) {
    extensions.push(lineNumbers());
  }

  if (props.lineWrapping) {
    extensions.push(EditorView.lineWrapping);
  }

  if (props.readOnly) {
    extensions.push(EditorState.readOnly.of(true));
  }

  // Apply base styling
  extensions.push(
    EditorView.theme({
      '&': {
        height: '100%',
        fontSize: '14px',
      },
      '.cm-scroller': {
        fontFamily:
          '"JetBrains Mono", "Fira Code", "Consolas", "Monaco", monospace',
        padding: '16px 0',
      },
      '.cm-content': {
        padding: '0 16px',
      },
      '&.cm-focused': {
        outline: 'none',
      },
    })
  );

  // Dark/light background
  if (props.theme === 'dark') {
    extensions.push(
      EditorView.theme({
        '&': {
          backgroundColor: '#1e1e1e',
          color: '#d4d4d4',
        },
        '.cm-gutters': {
          backgroundColor: '#1e1e1e',
          color: '#858585',
          border: 'none',
        },
        '.cm-activeLineGutter': {
          backgroundColor: '#282828',
        },
        '.cm-activeLine': {
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
        },
      })
    );
  } else {
    extensions.push(
      EditorView.theme({
        '&': {
          backgroundColor: '#ffffff',
          color: '#000000',
        },
        '.cm-gutters': {
          backgroundColor: '#f5f5f5',
          color: '#999',
          border: 'none',
        },
        '.cm-activeLineGutter': {
          backgroundColor: '#e8e8e8',
        },
        '.cm-activeLine': {
          backgroundColor: 'rgba(0, 0, 0, 0.03)',
        },
      })
    );
  }

  // Create editor state
  const state = EditorState.create({
    doc: props.value,
    extensions,
  });

  // Create editor view
  new EditorView({
    state,
    parent: container,
  });

  return container;
};
