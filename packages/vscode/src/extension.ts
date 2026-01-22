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

import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  const provider = vscode.languages.registerCompletionItemProvider(
    'dotprompt',
    {
      provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position
      ) {
        const linePrefix = document
          .lineAt(position)
          .text.slice(0, position.character);

        // Check if we are inside a Handlebars expression {{...}}
        // This is a simple check; for production, a real parser or regex is better.
        // But for now, check if the last opening brace is {{
        if (!linePrefix.includes('{{')) {
          return undefined;
        }

        // Handlebars built-ins
        const handlebarsHelpers = [
          'if',
          'unless',
          'each',
          'with',
          'log',
          'lookup',
        ].map((item) => {
          const completion = new vscode.CompletionItem(
            item,
            vscode.CompletionItemKind.Function
          );
          completion.detail = `Handlebars ${item} helper`;
          return completion;
        });

        // Dotprompt built-ins
        const dotpromptHelpers = [
          'json',
          'role',
          'history',
          'section',
          'media',
          'ifEquals',
          'unlessEquals',
        ].map((item) => {
          const completion = new vscode.CompletionItem(
            item,
            vscode.CompletionItemKind.Function
          );
          completion.detail = `Dotprompt ${item} helper`;
          return completion;
        });

        return [...handlebarsHelpers, ...dotpromptHelpers];
      },
    },
    '{' // Trigger on '{'
  );

  context.subscriptions.push(provider);
}

export function deactivate() {}
