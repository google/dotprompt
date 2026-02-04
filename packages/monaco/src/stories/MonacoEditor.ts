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

import * as monaco from 'monaco-editor';
import { initVimMode } from 'monaco-vim';
import {
  createDotpromptTheme,
  LANGUAGE_ID,
  registerDotpromptLanguage,
} from '../index';

export interface MonacoEditorProps {
  /** Initial content for the editor */
  value: string;
  /** Editor width */
  width: string;
  /** Editor height */
  height: string;
  /** Theme to use */
  theme: 'vs' | 'vs-dark' | 'dotprompt-dark' | 'dotprompt-light';
  /** Enable line numbers */
  lineNumbers: boolean;
  /** Enable minimap */
  minimap: boolean;
  /** Enable word wrap */
  wordWrap: boolean;
  /** Font size in pixels */
  fontSize: number;
  /** Enable completions */
  completions: boolean;
  /** Enable hover */
  hover: boolean;
  /** Enable Vim keybindings */
  vimMode: boolean;
  /** Read-only mode */
  readOnly: boolean;
}

/**
 * Creates a Monaco editor with Dotprompt language support.
 */
export const createMonacoEditor = (props: MonacoEditorProps): HTMLElement => {
  const wrapper = document.createElement('div');
  wrapper.style.width = props.width;
  wrapper.style.display = 'flex';
  wrapper.style.flexDirection = 'column';

  const container = document.createElement('div');
  container.style.width = '100%';
  container.style.height = props.height;
  container.style.border = '1px solid #333';
  container.style.borderRadius = props.vimMode ? '4px 4px 0 0' : '4px';
  container.style.overflow = 'hidden';

  wrapper.appendChild(container);

  // Register Dotprompt language support
  registerDotpromptLanguage(monaco, {
    completions: props.completions,
    hover: props.hover,
  });

  // Register custom themes
  monaco.editor.defineTheme('dotprompt-dark', createDotpromptTheme('vs-dark'));
  monaco.editor.defineTheme('dotprompt-light', createDotpromptTheme('vs'));

  // Create the editor
  const editor = monaco.editor.create(container, {
    value: props.value,
    language: LANGUAGE_ID,
    theme: props.theme,
    lineNumbers: props.lineNumbers ? 'on' : 'off',
    minimap: { enabled: props.minimap },
    wordWrap: props.wordWrap ? 'on' : 'off',
    fontSize: props.fontSize,
    readOnly: props.readOnly,
    automaticLayout: true,
    scrollBeyondLastLine: false,
    padding: { top: 16, bottom: 16 },
  });

  // Enable Vim mode if requested
  if (props.vimMode && !props.readOnly) {
    const statusBarElement = document.createElement('div');
    statusBarElement.style.height = '24px';
    statusBarElement.style.backgroundColor =
      props.theme === 'vs' || props.theme === 'dotprompt-light'
        ? '#f0f0f0'
        : '#1e1e1e';
    statusBarElement.style.color =
      props.theme === 'vs' || props.theme === 'dotprompt-light'
        ? '#333'
        : '#d4d4d4';
    statusBarElement.style.padding = '0 8px';
    statusBarElement.style.fontFamily = 'monospace';
    statusBarElement.style.fontSize = '12px';
    statusBarElement.style.lineHeight = '24px';
    statusBarElement.style.borderRadius = '0 0 4px 4px';
    statusBarElement.style.border = '1px solid #333';
    statusBarElement.style.borderTop = 'none';
    wrapper.appendChild(statusBarElement);

    initVimMode(editor, statusBarElement);
  }

  return wrapper;
};
