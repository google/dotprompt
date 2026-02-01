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

/// Dart Compilation Persistent Worker for Bazel.
///
/// This worker accelerates Dart compilation by keeping the Dart VM warm
/// between build actions, avoiding the overhead of VM startup.
///
/// # ELI5 (Explain Like I'm 5)
///
/// ## What is a Worker?
///
/// Imagine you're building with LEGO. Without a worker, every time you want
/// to build something, you have to:
/// 1. Go to the closet
/// 2. Get out all your LEGO
/// 3. Build the thing
/// 4. Put all the LEGO back
/// 5. Close the closet
///
/// That's slow! A "worker" is like leaving the LEGO out on the table.
/// The next time you want to build, the LEGO is already there - you just
/// build! Much faster.
///
/// ## Key Terms
///
/// | Term | Simple Explanation |
/// |------|-------------------|
/// | **Worker** | A helper program that stays running between builds |
/// | **Persistent** | The helper doesn't quit - it stays ready for more work |
/// | **Flagfile** | A text file with instructions (like a to-do list) |
/// | **VM** | Virtual Machine - the engine that runs Dart code |
/// | **Cold Start** | Starting from scratch (slow) |
/// | **Warm Start** | Already running and ready (fast) |
///
/// # Data Flow Diagram
///
/// ## Without Workers (Cold Start Every Time)
///
/// ```
/// ┌─────────────────────────────────────────────────────────────────────────────┐
/// │                        Traditional Build (Cold)                             │
/// ├─────────────────────────────────────────────────────────────────────────────┤
/// │                                                                             │
/// │  Build 1:                                                                   │
/// │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
/// │  │ Start VM │ → │ Load SDK │ → │ Parse    │ → │ Compile  │ → │ Exit VM  │  │
/// │  │ (2 sec)  │   │ (2 sec)  │   │ (0.5 sec)│   │ (0.5 sec)│   │          │  │
/// │  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘  │
/// │  Total: ~5 seconds                                                         │
/// │                                                                             │
/// │  Build 2: (Same thing again!)                                               │
/// │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
/// │  │ Start VM │ → │ Load SDK │ → │ Parse    │ → │ Compile  │ → │ Exit VM  │  │
/// │  │ (2 sec)  │   │ (2 sec)  │   │ (0.5 sec)│   │ (0.5 sec)│   │          │  │
/// │  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘  │
/// │  Total: ~5 seconds (again!)                                                │
/// │                                                                             │
/// └─────────────────────────────────────────────────────────────────────────────┘
/// ```
///
/// ## With Workers (Stay Warm)
///
/// ```
/// ┌─────────────────────────────────────────────────────────────────────────────┐
/// │                        Persistent Worker Build                              │
/// ├─────────────────────────────────────────────────────────────────────────────┤
/// │                                                                             │
/// │  First Build (startup cost):                                                │
/// │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                 │
/// │  │ Start VM │ → │ Load SDK │ → │ Parse    │ → │ Compile  │  ← Worker stays │
/// │  │ (2 sec)  │   │ (2 sec)  │   │ (0.5 sec)│   │ (0.5 sec)│    running!     │
/// │  └──────────┘   └──────────┘   └──────────┘   └──────────┘                 │
/// │                                                                             │
/// │  Subsequent Builds (warm):                                                  │
/// │                                ┌──────────┐   ┌──────────┐                 │
/// │                                │ Parse    │ → │ Compile  │  VM already     │
/// │                                │ (0.1 sec)│   │ (0.3 sec)│  running!       │
/// │                                └──────────┘   └──────────┘                 │
/// │  Total: ~0.4 seconds (10x faster!)                                         │
/// │                                                                             │
/// └─────────────────────────────────────────────────────────────────────────────┘
/// ```
///
/// # Protocol Data Flow
///
/// ```
/// ┌─────────────────────────────────────────────────────────────────────────────┐
/// │                      Bazel ←→ Worker Communication                         │
/// ├─────────────────────────────────────────────────────────────────────────────┤
/// │                                                                             │
/// │  ┌─────────────┐                              ┌─────────────────────────┐  │
/// │  │   Bazel     │                              │   Worker Process        │  │
/// │  │             │                              │                         │  │
/// │  │  Action 1   │───── stdin (JSON) ─────────▶│  1. Parse JSON request  │  │
/// │  │             │                              │  2. Read @flagfile      │  │
/// │  │  ┌────────┐ │                              │  3. Execute dart compile│  │
/// │  │  │Request │ │                              │  4. Collect output      │  │
/// │  │  │@file.a │ │                              │                         │  │
/// │  │  │rgs     │ │◀──── stdout (JSON) ─────────│  5. Send JSON response  │  │
/// │  │  └────────┘ │                              │                         │  │
/// │  │             │                              │  [Worker stays alive]   │  │
/// │  │  Action 2   │───── stdin (JSON) ─────────▶│                         │  │
/// │  │  ...        │                              │  [Repeat steps 1-5]     │  │
/// │  └─────────────┘                              └─────────────────────────┘  │
/// │                                                                             │
/// └─────────────────────────────────────────────────────────────────────────────┘
/// ```
///
/// # Flagfile Format
///
/// The flagfile (@args.txt) contains one argument per line:
///
/// ```
/// --output=/path/to/output.exe
/// --main=/path/to/main.dart
/// --package-dir=/path/to/package
/// compile
/// exe
/// ```
///
/// This avoids command-line length limits and enables worker reuse.
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'protocol.dart';

/// Statistics for monitoring worker performance.
class CompileStats {
  int totalCompilations = 0;
  int successfulCompilations = 0;
  int failedCompilations = 0;
  Duration totalCompileTime = Duration.zero;

  void recordSuccess(Duration duration) {
    totalCompilations++;
    successfulCompilations++;
    totalCompileTime += duration;
  }

  void recordFailure(Duration duration) {
    totalCompilations++;
    failedCompilations++;
    totalCompileTime += duration;
  }

  double get averageCompileTimeMs =>
      totalCompilations > 0
          ? totalCompileTime.inMilliseconds / totalCompilations
          : 0;

  double get successRate =>
      totalCompilations > 0 ? successfulCompilations / totalCompilations : 0;

  @override
  String toString() => '''
Compilation Statistics
======================
Total compilations: $totalCompilations
Successful: $successfulCompilations
Failed: $failedCompilations
Success rate: ${(successRate * 100).toStringAsFixed(1)}%
Average compile time: ${averageCompileTimeMs.toStringAsFixed(1)}ms
Total compile time: ${totalCompileTime.inSeconds}s
''';
}

/// Dart Compilation Worker.
///
/// Handles compile requests from Bazel, keeping the Dart VM warm between
/// compilations for faster incremental builds.
class CompileWorker extends PersistentWorker {
  /// Path to the Dart SDK.
  final String? dartSdkPath;

  /// Compilation statistics.
  final CompileStats stats = CompileStats();

  CompileWorker({this.dartSdkPath});

  @override
  String get name => 'DartCompileWorker';

  @override
  Future<WorkResponse> processRequest(WorkRequest request) async {
    final stopwatch = Stopwatch()..start();

    try {
      // Parse arguments from flagfile
      final args = await request.parseArguments();
      stderr.writeln('[$name] Received ${args.length} arguments');

      // Parse compilation options
      final options = _parseCompileOptions(args);

      // Run the compilation
      final result = await _compile(options);

      stopwatch.stop();

      if (result.exitCode == 0) {
        stats.recordSuccess(stopwatch.elapsed);
        return WorkResponse.success(
          output: result.output,
          requestId: request.requestId,
        );
      } else {
        stats.recordFailure(stopwatch.elapsed);
        return WorkResponse.failure(
          result.output,
          requestId: request.requestId,
        );
      }
    } catch (e, st) {
      stopwatch.stop();
      stats.recordFailure(stopwatch.elapsed);
      return WorkResponse.failure(
        'Compilation error: $e\n$st',
        requestId: request.requestId,
      );
    }
  }

  /// Parse compilation options from arguments.
  CompileOptions _parseCompileOptions(List<String> args) {
    String? output;
    String? main;
    String? packageDir;
    String command = 'exe';
    final extraArgs = <String>[];

    for (final arg in args) {
      if (arg.startsWith('--output=')) {
        output = arg.substring('--output='.length);
      } else if (arg.startsWith('--main=')) {
        main = arg.substring('--main='.length);
      } else if (arg.startsWith('--package-dir=')) {
        packageDir = arg.substring('--package-dir='.length);
      } else if (arg.startsWith('--command=')) {
        command = arg.substring('--command='.length);
      } else if (arg.startsWith('--')) {
        extraArgs.add(arg);
      } else if (['exe', 'js', 'wasm', 'aot-snapshot', 'kernel'].contains(arg)) {
        command = arg;
      } else if (main == null && arg.endsWith('.dart')) {
        main = arg;
      }
    }

    if (main == null) {
      throw ArgumentError('Missing main Dart file');
    }
    if (output == null) {
      throw ArgumentError('Missing --output argument');
    }

    return CompileOptions(
      main: main,
      output: output,
      command: command,
      packageDir: packageDir,
      extraArgs: extraArgs,
    );
  }

  /// Run the Dart compiler.
  Future<CompileResult> _compile(CompileOptions options) async {
    // Find the Dart executable
    final dartBin = dartSdkPath ?? Platform.environment['DART_SDK'] ?? 'dart';

    // Build command
    final args = [
      'compile',
      options.command,
      '-o', options.output,
      ...options.extraArgs,
      options.main,
    ];

    stderr.writeln('[$name] Running: $dartBin ${args.join(' ')}');

    // Set up working directory
    String? workingDirectory;
    if (options.packageDir != null) {
      workingDirectory = options.packageDir;
    }

    // Run compilation
    final result = await Process.run(
      dartBin,
      args,
      workingDirectory: workingDirectory,
      runInShell: Platform.isWindows,
    );

    final output = StringBuffer();
    if (result.stdout.toString().isNotEmpty) {
      output.write(result.stdout);
    }
    if (result.stderr.toString().isNotEmpty) {
      if (output.isNotEmpty) output.write('\n');
      output.write(result.stderr);
    }

    return CompileResult(
      exitCode: result.exitCode,
      output: output.toString(),
    );
  }

  @override
  Future<void> shutdown() async {
    stderr.writeln('[$name] Final statistics:\n$stats');
    await super.shutdown();
  }
}

/// Options for a compilation request.
class CompileOptions {
  final String main;
  final String output;
  final String command;
  final String? packageDir;
  final List<String> extraArgs;

  CompileOptions({
    required this.main,
    required this.output,
    required this.command,
    this.packageDir,
    this.extraArgs = const [],
  });
}

/// Result of a compilation.
class CompileResult {
  final int exitCode;
  final String output;

  CompileResult({required this.exitCode, required this.output});
}

/// Entry point for the compilation worker.
void main(List<String> args) async {
  if (args.contains('--persistent_worker')) {
    // Parse optional SDK path
    String? sdkPath;
    for (final arg in args) {
      if (arg.startsWith('--dart_sdk=')) {
        sdkPath = arg.substring('--dart_sdk='.length);
      }
    }

    await CompileWorker(dartSdkPath: sdkPath).run();
  } else if (args.contains('--help') || args.contains('-h')) {
    print('''
Dart Compilation Persistent Worker

Usage:
  dart compile_worker.dart --persistent_worker [--dart_sdk=/path/to/sdk]

Worker Mode:
  Reads JSON requests from stdin, writes JSON responses to stdout.
  Keeps the Dart VM warm between compilations for 10-50x speedup.

Protocol:
  Request:  {"arguments": ["@path/to/args.txt"], "inputs": [...]}
  Response: {"exitCode": 0, "output": "Compiled successfully"}

Flagfile Format (@args.txt):
  --output=/path/to/output
  --main=/path/to/main.dart
  --package-dir=/path/to/package
  exe

Supported Commands:
  exe          Native executable
  js           JavaScript
  wasm         WebAssembly
  aot-snapshot AOT snapshot
  kernel       Kernel file

Environment Variables:
  DART_SDK     Path to Dart SDK (if not using --dart_sdk)
''');
  } else {
    stderr.writeln('Usage: dart compile_worker.dart --persistent_worker');
    stderr.writeln('       dart compile_worker.dart --help');
    exit(1);
  }
}
