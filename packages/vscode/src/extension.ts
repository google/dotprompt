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

import * as path from 'path';
import * as vscode from 'vscode';
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from 'vscode-languageclient/node';

let client: LanguageClient | undefined;
let outputChannel: vscode.OutputChannel;

export async function activate(context: vscode.ExtensionContext) {
  // Create output channel early for debugging
  outputChannel = vscode.window.createOutputChannel('Dotprompt LSP');
  context.subscriptions.push(outputChannel);

  outputChannel.appendLine('Dotprompt: Extension activated!');
  outputChannel.appendLine(
    `Dotprompt: Extension path: ${context.extensionPath}`
  );

  // Register completions (existing functionality)
  const completionProvider = registerCompletionProvider();
  context.subscriptions.push(completionProvider);

  // Start LSP client if promptly is available
  await startLspClient(context, outputChannel);
}

/**
 * Registers the completion provider for Handlebars helpers.
 */
function registerCompletionProvider(): vscode.Disposable {
  return vscode.languages.registerCompletionItemProvider(
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
        if (!linePrefix.includes('{{')) {
          return undefined;
        }

        // Handlebars built-ins
        const handlebarsHelpers = [
          { name: 'if', doc: 'Conditionally renders content' },
          { name: 'unless', doc: 'Inverse of if - renders when falsy' },
          { name: 'each', doc: 'Iterates over arrays or objects' },
          { name: 'with', doc: 'Changes context for enclosed block' },
          { name: 'log', doc: 'Logs a value to the console' },
          { name: 'lookup', doc: 'Looks up a value by key' },
        ].map((item) => {
          const completion = new vscode.CompletionItem(
            item.name,
            vscode.CompletionItemKind.Function
          );
          completion.detail = `Handlebars ${item.name} helper`;
          completion.documentation = item.doc;
          return completion;
        });

        // Dotprompt built-ins
        const dotpromptHelpers = [
          { name: 'json', doc: 'Serializes a value to JSON format' },
          { name: 'role', doc: 'Defines a message with a specific role' },
          { name: 'history', doc: 'Inserts conversation history' },
          { name: 'section', doc: 'Defines a named section' },
          { name: 'media', doc: 'Embeds media content' },
          { name: 'ifEquals', doc: 'Compares two values for equality' },
          { name: 'unlessEquals', doc: 'Inverse of ifEquals' },
        ].map((item) => {
          const completion = new vscode.CompletionItem(
            item.name,
            vscode.CompletionItemKind.Function
          );
          completion.detail = `Dotprompt ${item.name} helper`;
          completion.documentation = item.doc;
          return completion;
        });

        return [...handlebarsHelpers, ...dotpromptHelpers];
      },
    },
    '{' // Trigger on '{'
  );
}

/**
 * Starts the LSP client to connect to the promptly LSP server.
 */
async function startLspClient(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel
): Promise<void> {
  outputChannel.appendLine('Dotprompt: Starting Promptly LSP client...');

  // Try to find the promptly binary
  const promptlyPath = await findPromptlyBinary(context, outputChannel);

  if (!promptlyPath) {
    // No promptly found - log a message but don't fail
    outputChannel.appendLine(
      'promptly binary not found. LSP features disabled. Install promptly for enhanced features.'
    );
    vscode.window.showWarningMessage(
      "Promptly LSP: Binary not found. Set 'dotprompt.promptlyPath' in settings."
    );
    return;
  }

  outputChannel.appendLine(`Found promptly at: ${promptlyPath}`);

  const serverOptions: ServerOptions = {
    command: promptlyPath,
    args: ['lsp'],
    transport: TransportKind.stdio,
  };

  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: 'file', language: 'dotprompt' }],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher('**/*.prompt'),
    },
    outputChannel: outputChannel,
  };

  client = new LanguageClient(
    'promptly',
    'Promptly Language Server',
    serverOptions,
    clientOptions
  );

  // Start the client
  try {
    await client.start();
    outputChannel.appendLine(
      'Dotprompt: Promptly LSP client started successfully'
    );
    vscode.window.showInformationMessage('Promptly LSP connected!');
  } catch (error) {
    outputChannel.appendLine(`Failed to start Promptly LSP client: ${error}`);
    vscode.window.showErrorMessage(`Promptly LSP failed to start: ${error}`);
    client = undefined;
  }
}

/**
 * Finds the promptly binary in common locations.
 */
async function findPromptlyBinary(
  context: vscode.ExtensionContext,
  outputChannel: vscode.OutputChannel
): Promise<string | undefined> {
  outputChannel.appendLine('Dotprompt: Searching for promptly binary...');

  // Check configuration first
  const config = vscode.workspace.getConfiguration('dotprompt');
  const configuredPath = config.get<string>('promptlyPath');
  outputChannel.appendLine(`  Config path: "${configuredPath || '(not set)'}"`);
  if (configuredPath && (await fileExists(configuredPath))) {
    outputChannel.appendLine(`  ✓ Found at configured path: ${configuredPath}`);
    return configuredPath;
  }

  // Check if promptly is in PATH
  outputChannel.appendLine('Dotprompt:   Checking PATH...');
  const promptlyInPath = await findInPath('promptly');
  if (promptlyInPath) {
    outputChannel.appendLine(`  ✓ Found in PATH: ${promptlyInPath}`);
    return promptlyInPath;
  }
  outputChannel.appendLine('Dotprompt:   ✗ Not found in PATH');

  // Check common cargo install location
  const homeDir = process.env.HOME || process.env.USERPROFILE;
  if (homeDir) {
    const cargoPath = path.join(homeDir, '.cargo', 'bin', 'promptly');
    outputChannel.appendLine(`  Checking cargo path: ${cargoPath}`);
    if (await fileExists(cargoPath)) {
      outputChannel.appendLine(`  ✓ Found at cargo path: ${cargoPath}`);
      return cargoPath;
    }
    outputChannel.appendLine('Dotprompt:   ✗ Not found at cargo path');
  }

  // Check relative to workspace for development
  const workspaceFolders = vscode.workspace.workspaceFolders;
  outputChannel.appendLine(
    `  Workspace folders: ${workspaceFolders?.length ?? 0}`
  );
  if (workspaceFolders) {
    for (const folder of workspaceFolders) {
      outputChannel.appendLine(`    Checking workspace: ${folder.uri.fsPath}`);
      const devPath = path.join(
        folder.uri.fsPath,
        'target',
        'debug',
        'promptly'
      );
      outputChannel.appendLine(`      Debug path: ${devPath}`);
      if (await fileExists(devPath)) {
        outputChannel.appendLine(`  ✓ Found at debug path: ${devPath}`);
        return devPath;
      }
      const releasePath = path.join(
        folder.uri.fsPath,
        'target',
        'release',
        'promptly'
      );
      outputChannel.appendLine(`      Release path: ${releasePath}`);
      if (await fileExists(releasePath)) {
        outputChannel.appendLine(`  ✓ Found at release path: ${releasePath}`);
        return releasePath;
      }
    }
  }

  outputChannel.appendLine(
    'Dotprompt:   ✗ promptly binary not found in any location'
  );
  return undefined;
}

/**
 * Checks if a file exists at the given path.
 */
async function fileExists(filePath: string): Promise<boolean> {
  try {
    await vscode.workspace.fs.stat(vscode.Uri.file(filePath));
    return true;
  } catch {
    return false;
  }
}

/**
 * Finds an executable in the system PATH.
 */
async function findInPath(executable: string): Promise<string | undefined> {
  const pathEnv = process.env.PATH || '';
  const pathSeparator = process.platform === 'win32' ? ';' : ':';
  const extensions = process.platform === 'win32' ? ['.exe', '.cmd', ''] : [''];

  for (const dir of pathEnv.split(pathSeparator)) {
    for (const ext of extensions) {
      const fullPath = path.join(dir, executable + ext);
      if (await fileExists(fullPath)) {
        return fullPath;
      }
    }
  }

  return undefined;
}

export async function deactivate(): Promise<void> {
  if (client) {
    await client.stop();
  }
}
