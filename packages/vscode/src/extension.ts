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
  State,
  TransportKind,
} from 'vscode-languageclient/node';

let client: LanguageClient | undefined;
let outputChannel: vscode.OutputChannel;
let statusBarItem: vscode.StatusBarItem;

export async function activate(context: vscode.ExtensionContext) {
  // Create output channel early for debugging
  outputChannel = vscode.window.createOutputChannel('Dotprompt LSP');
  context.subscriptions.push(outputChannel);

  outputChannel.appendLine('Dotprompt: Extension activated!');
  outputChannel.appendLine(
    `Dotprompt: Extension path: ${context.extensionPath}`
  );

  // Create status bar item
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  statusBarItem.command = 'dotprompt.showOutput';
  context.subscriptions.push(statusBarItem);
  updateStatusBar('$(loading~spin) Dotprompt', 'Initializing...');

  // Register completions (existing functionality)
  const completionProvider = registerCompletionProvider();
  context.subscriptions.push(completionProvider);

  // Register commands
  try {
    const formatCmd = vscode.commands.registerCommand(
      'dotprompt.formatDocument',
      formatDocument
    );
    context.subscriptions.push(formatCmd);
    outputChannel.appendLine(
      'Dotprompt: Registered command: dotprompt.formatDocument'
    );

    const restartCmd = vscode.commands.registerCommand(
      'dotprompt.restartLsp',
      () => restartLspClient(context)
    );
    context.subscriptions.push(restartCmd);
    outputChannel.appendLine(
      'Dotprompt: Registered command: dotprompt.restartLsp'
    );

    const showOutputCmd = vscode.commands.registerCommand(
      'dotprompt.showOutput',
      () => outputChannel.show()
    );
    context.subscriptions.push(showOutputCmd);
    outputChannel.appendLine(
      'Dotprompt: Registered command: dotprompt.showOutput'
    );
  } catch (error) {
    outputChannel.appendLine(`Dotprompt: ERROR registering commands: ${error}`);
    console.error('Dotprompt: ERROR registering commands:', error);
  }

  // Register format on save
  context.subscriptions.push(
    vscode.workspace.onWillSaveTextDocument(async (event) => {
      const config = vscode.workspace.getConfiguration('dotprompt');
      if (
        config.get<boolean>('formatOnSave') &&
        event.document.languageId === 'dotprompt' &&
        client?.state === State.Running
      ) {
        const edit = await formatDocumentEdit(event.document);
        if (edit) {
          event.waitUntil(Promise.resolve([edit]));
        }
      }
    })
  );

  // Start LSP client if promptly is available
  const config = vscode.workspace.getConfiguration('dotprompt');
  if (config.get<boolean>('enableLsp', true)) {
    await startLspClient(context, outputChannel);
  } else {
    updateStatusBar('$(circle-slash) Dotprompt', 'LSP disabled');
  }
}

/**
 * Updates the status bar with current LSP state.
 */
function updateStatusBar(text: string, tooltip: string) {
  statusBarItem.text = text;
  statusBarItem.tooltip = tooltip;
  statusBarItem.show();
}

/**
 * Formats the current document using the LSP.
 */
async function formatDocument() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== 'dotprompt') {
    vscode.window.showWarningMessage('No Dotprompt file is active.');
    return;
  }

  if (!client || client.state !== State.Running) {
    vscode.window.showWarningMessage(
      'Dotprompt LSP is not running. Install promptly for formatting.'
    );
    return;
  }

  await vscode.commands.executeCommand('editor.action.formatDocument');
}

/**
 * Gets a text edit for formatting a document.
 */
async function formatDocumentEdit(
  document: vscode.TextDocument
): Promise<vscode.TextEdit | undefined> {
  if (!client || client.state !== State.Running) {
    return undefined;
  }

  try {
    const edits = await client.sendRequest('textDocument/formatting', {
      textDocument: { uri: document.uri.toString() },
      options: {
        tabSize: 2,
        insertSpaces: true,
      },
    });

    if (Array.isArray(edits) && edits.length > 0) {
      // Convert LSP edits to VS Code edits
      const edit = edits[0] as {
        range: {
          start: { line: number; character: number };
          end: { line: number; character: number };
        };
        newText: string;
      };
      return new vscode.TextEdit(
        new vscode.Range(
          edit.range.start.line,
          edit.range.start.character,
          edit.range.end.line,
          edit.range.end.character
        ),
        edit.newText
      );
    }
  } catch (error) {
    outputChannel.appendLine(`Format error: ${error}`);
  }

  return undefined;
}

/**
 * Restarts the LSP client.
 */
async function restartLspClient(context: vscode.ExtensionContext) {
  outputChannel.appendLine('Dotprompt: Restarting LSP client...');
  updateStatusBar('$(loading~spin) Dotprompt', 'Restarting...');

  if (client) {
    await client.stop();
    client = undefined;
  }

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
    updateStatusBar(
      '$(warning) Dotprompt',
      'promptly not found. Click to see details.'
    );
    vscode.window
      .showWarningMessage(
        "Promptly LSP: Binary not found. Install with 'cargo install promptly' or set path in settings.",
        'Open Settings',
        'Show Output'
      )
      .then((selection) => {
        if (selection === 'Open Settings') {
          vscode.commands.executeCommand(
            'workbench.action.openSettings',
            'dotprompt.promptlyPath'
          );
        } else if (selection === 'Show Output') {
          outputChannel.show();
        }
      });
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

  // Listen for state changes
  client.onDidChangeState((event) => {
    switch (event.newState) {
      case State.Running:
        updateStatusBar('$(check) Dotprompt', 'LSP connected');
        break;
      case State.Starting:
        updateStatusBar('$(loading~spin) Dotprompt', 'LSP starting...');
        break;
      case State.Stopped:
        updateStatusBar('$(error) Dotprompt', 'LSP stopped');
        break;
    }
  });

  // Start the client
  try {
    await client.start();
    outputChannel.appendLine(
      'Dotprompt: Promptly LSP client started successfully'
    );
  } catch (error) {
    outputChannel.appendLine(`Failed to start Promptly LSP client: ${error}`);
    updateStatusBar(
      '$(error) Dotprompt',
      `LSP failed to start: ${error}. Click for details.`
    );
    vscode.window
      .showErrorMessage(
        `Promptly LSP failed to start: ${error}`,
        'Show Output',
        'Retry'
      )
      .then((selection) => {
        if (selection === 'Show Output') {
          outputChannel.show();
        } else if (selection === 'Retry') {
          restartLspClient(context);
        }
      });
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
    // Check ~/.local/bin first (where install_vscode_ext installs it)
    const localBinPath = path.join(homeDir, '.local', 'bin', 'promptly');
    outputChannel.appendLine(`  Checking local bin path: ${localBinPath}`);
    if (await fileExists(localBinPath)) {
      outputChannel.appendLine(`  ✓ Found at local bin path: ${localBinPath}`);
      return localBinPath;
    }
    outputChannel.appendLine('  ✗ Not found at local bin path');

    // Check cargo install location
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
