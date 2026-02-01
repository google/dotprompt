// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

/// Bazel Persistent Worker for rules_dart.
///
/// This worker implements the JSON worker protocol, allowing Bazel to
/// keep a Dart VM instance running across multiple build actions.
///
/// Protocol:
/// - Request: {"arguments": ["dart", "compile", ...], "inputs": [...]}
/// - Response: {"exitCode": 0, "output": "..."}
/// - Requests/responses are newline-delimited JSON
///
/// Usage:
///   dart run worker.dart --persistent_worker  # Start in worker mode
///   dart run worker.dart <cmd> [args...]      # One-shot mode
library;

import 'dart:convert';
import 'dart:io';

/// Entry point for the worker.
void main(List<String> args) async {
  if (args.contains('--persistent_worker')) {
    await _runWorkerLoop();
  } else if (args.contains('--help') || args.contains('-h')) {
    _printHelp();
  } else if (args.isEmpty) {
    _printHelp();
    exit(1);
  } else {
    // One-shot execution mode
    exit(await _runOneShot(args));
  }
}

/// Print help information.
void _printHelp() {
  print('''
rules_dart Persistent Worker

Usage:
  worker --persistent_worker    Start in persistent worker mode (JSON protocol)
  worker <executable> [args...] Run a command in one-shot mode
  worker --help                 Show this help message

Worker Protocol (JSON):
  Request:  {"arguments": ["dart", "compile", "exe", "main.dart"]}
  Response: {"exitCode": 0, "output": "Compilation successful"}
''');
}

/// Run in one-shot mode - execute a single command and exit.
Future<int> _runOneShot(List<String> args) async {
  if (args.isEmpty) {
    stderr.writeln('Error: No command provided');
    return 1;
  }

  final executable = args.first;
  final arguments = args.skip(1).toList();

  try {
    final process = await Process.start(
      executable,
      arguments,
      mode: ProcessStartMode.inheritStdio,
    );
    return await process.exitCode;
  } catch (e) {
    stderr.writeln('Error executing command: $e');
    return 1;
  }
}

/// Run the persistent worker loop.
///
/// Reads JSON requests from stdin, executes them, and writes JSON responses
/// to stdout. The worker continues until stdin is closed.
Future<void> _runWorkerLoop() async {
  // Use line-based input for JSON protocol
  final inputStream = stdin.transform(utf8.decoder).transform(const LineSplitter());

  await for (final line in inputStream) {
    if (line.trim().isEmpty) continue;

    final response = await _processRequest(line);
    print(jsonEncode(response));
  }
}

/// Process a single worker request.
Future<Map<String, dynamic>> _processRequest(String requestJson) async {
  try {
    final request = jsonDecode(requestJson) as Map<String, dynamic>;
    final args = (request['arguments'] as List?)?.cast<String>() ?? [];

    if (args.isEmpty) {
      return {
        'exitCode': 1,
        'output': 'Error: No arguments provided in request',
      };
    }

    final executable = args.first;
    final arguments = args.skip(1).toList();

    // Execute the command
    final result = await Process.run(
      executable,
      arguments,
      runInShell: Platform.isWindows, // Use shell on Windows for better compatibility
    );

    final output = StringBuffer();
    if (result.stdout.toString().isNotEmpty) {
      output.write(result.stdout);
    }
    if (result.stderr.toString().isNotEmpty) {
      if (output.isNotEmpty) output.write('\n');
      output.write(result.stderr);
    }

    return {
      'exitCode': result.exitCode,
      'output': output.toString(),
    };
  } on FormatException catch (e) {
    return {
      'exitCode': 1,
      'output': 'Error: Invalid JSON request: $e',
    };
  } catch (e, stackTrace) {
    return {
      'exitCode': 1,
      'output': 'Error: $e\n$stackTrace',
    };
  }
}
