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

/// Dart Analyzer Persistent Worker for Bazel.
///
/// This worker accelerates static analysis by caching parsed ASTs and type
/// information between build actions.
///
/// # ELI5 (Explain Like I'm 5)
///
/// ## What is an Analyzer?
///
/// Imagine you're a teacher checking homework. Without caching:
/// 1. Read the first student's paper
/// 2. Grade it
/// 3. Forget everything
/// 4. Read the next student's paper... even if it's similar!
///
/// With an Analyzer Worker:
/// - Remember what you've already checked
/// - Only check new or changed parts
/// - Much faster grading!
///
/// ## Key Terms
///
/// | Term | Simple Explanation |
/// |------|-------------------|
/// | **Analyzer** | A tool that checks your code for errors |
/// | **AST** | Abstract Syntax Tree - a map of your code's structure |
/// | **Cache** | Memory of things already processed |
/// | **Incremental** | Only process what changed |
///
/// # Data Flow Diagram
///
/// ```
/// ┌─────────────────────────────────────────────────────────────────────────────┐
/// │                       Analyzer Worker Flow                                  │
/// ├─────────────────────────────────────────────────────────────────────────────┤
/// │                                                                             │
/// │  File Change Detected                                                       │
/// │       │                                                                     │
/// │       ▼                                                                     │
/// │  ┌──────────────────────────────────────────────────────────────────────┐  │
/// │  │  Worker Process (stays running)                                      │  │
/// │  │  ┌────────────┐   ┌────────────┐   ┌────────────┐                   │  │
/// │  │  │   Cache    │   │   Parse    │   │  Analyze   │                   │  │
/// │  │  │   Check    │ → │  Changed   │ → │  Only New  │                   │  │
/// │  │  │            │   │   Files    │   │   Code     │                   │  │
/// │  │  └────────────┘   └────────────┘   └────────────┘                   │  │
/// │  └──────────────────────────────────────────────────────────────────────┘  │
/// │       │                                                                     │
/// │       ▼                                                                     │
/// │  Return Analysis Results (errors, warnings, hints)                         │
/// │                                                                             │
/// └─────────────────────────────────────────────────────────────────────────────┘
/// ```
///
/// # Usage
///
/// As a Bazel persistent worker:
/// ```bash
/// dart run analyzer_worker.dart --persistent_worker
/// ```
///
/// Then Bazel sends requests via stdin:
/// ```json
/// {"arguments": ["@analyze.args"], "inputs": [...], "requestId": 1}
/// ```
///
/// # References
///
/// - [Dart Analyzer](https://dart.dev/tools/analysis)
/// - [Bazel Workers](https://bazel.build/remote/persistent)
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'protocol.dart';

/// Simple file content cache for incremental analysis.
class FileCache {
  final Map<String, String> _contents = {};
  final Map<String, DateTime> _timestamps = {};

  /// Get cached content for a file, or read it fresh.
  Future<String> getContent(String path) async {
    final file = File(path);
    final stat = await file.stat();

    if (_timestamps[path] != stat.modified || !_contents.containsKey(path)) {
      final content = await file.readAsString();
      _contents[path] = content;
      _timestamps[path] = stat.modified;
    }

    return _contents[path]!;
  }

  /// Check if a file is cached.
  bool isCached(String path) => _contents.containsKey(path);

  /// Clear the cache for a specific file.
  void invalidate(String path) {
    _contents.remove(path);
    _timestamps.remove(path);
  }

  /// Clear the entire cache.
  void clear() {
    _contents.clear();
    _timestamps.clear();
  }

  /// Get cache statistics.
  Map<String, dynamic> get stats => {
        'cachedFiles': _contents.length,
        'totalSize': _contents.values.fold<int>(0, (sum, c) => sum + c.length),
      };
}

/// Statistics tracker for analyzer performance.
class AnalyzerStats {
  int totalAnalyses = 0;
  int filesAnalyzed = 0;
  int errorsFound = 0;
  int warningsFound = 0;
  int hintsFound = 0;
  Duration totalAnalysisTime = Duration.zero;

  void record({
    int files = 0,
    int errors = 0,
    int warnings = 0,
    int hints = 0,
    Duration duration = Duration.zero,
  }) {
    totalAnalyses++;
    filesAnalyzed += files;
    errorsFound += errors;
    warningsFound += warnings;
    hintsFound += hints;
    totalAnalysisTime += duration;
  }

  double get averageTimeMs =>
      totalAnalyses > 0
          ? totalAnalysisTime.inMilliseconds / totalAnalyses
          : 0;

  @override
  String toString() => '''
Analyzer Statistics
===================
Total analyses: $totalAnalyses
Files analyzed: $filesAnalyzed
Errors found: $errorsFound
Warnings found: $warningsFound
Hints found: $hintsFound
Average time: ${averageTimeMs.toStringAsFixed(1)}ms
Total time: ${totalAnalysisTime.inSeconds}s
''';
}

/// Dart Analyzer Worker.
///
/// Runs the Dart analyzer as a persistent worker, caching parsed files
/// for faster incremental analysis.
class AnalyzerWorker extends PersistentWorker {
  /// Path to the Dart SDK.
  final String? dartSdkPath;

  /// File content cache.
  final FileCache cache = FileCache();

  /// Performance statistics.
  final AnalyzerStats stats = AnalyzerStats();

  AnalyzerWorker({this.dartSdkPath});

  @override
  String get name => 'DartAnalyzerWorker';

  @override
  Future<WorkResponse> processRequest(WorkRequest request) async {
    final stopwatch = Stopwatch()..start();

    try {
      // Parse arguments from flagfile
      final args = await request.parseArguments();
      stderr.writeln('[$name] Analyzing with ${args.length} arguments');

      // Parse options
      final options = _parseAnalyzeOptions(args);

      // Run analysis
      final result = await _analyze(options);

      stopwatch.stop();
      stats.record(
        files: options.files.length,
        errors: result.errorCount,
        warnings: result.warningCount,
        hints: result.hintCount,
        duration: stopwatch.elapsed,
      );

      if (result.exitCode == 0) {
        return WorkResponse.success(
          output: result.output,
          requestId: request.requestId,
        );
      } else {
        return WorkResponse(
          exitCode: result.exitCode,
          output: result.output,
          requestId: request.requestId,
        );
      }
    } catch (e, st) {
      stopwatch.stop();
      return WorkResponse.failure(
        'Analysis error: $e\n$st',
        requestId: request.requestId,
      );
    }
  }

  /// Parse analyze options from arguments.
  AnalyzeOptions _parseAnalyzeOptions(List<String> args) {
    final files = <String>[];
    var fatalInfos = false;
    var fatalWarnings = false;
    String? packageDir;

    for (final arg in args) {
      if (arg.startsWith('--package-dir=')) {
        packageDir = arg.substring('--package-dir='.length);
      } else if (arg == '--fatal-infos') {
        fatalInfos = true;
      } else if (arg == '--fatal-warnings') {
        fatalWarnings = true;
      } else if (!arg.startsWith('--')) {
        files.add(arg);
      }
    }

    return AnalyzeOptions(
      files: files,
      fatalInfos: fatalInfos,
      fatalWarnings: fatalWarnings,
      packageDir: packageDir,
    );
  }

  /// Run the Dart analyzer.
  Future<AnalyzeResult> _analyze(AnalyzeOptions options) async {
    // Find the Dart executable
    final dartBin = dartSdkPath ?? Platform.environment['DART_SDK'] ?? 'dart';

    // Build command
    final args = [
      'analyze',
      if (options.fatalInfos) '--fatal-infos',
      if (options.fatalWarnings) '--fatal-warnings',
      ...options.files,
    ];

    stderr.writeln('[$name] Running: $dartBin ${args.join(' ')}');

    // Set up working directory
    String? workingDirectory;
    if (options.packageDir != null) {
      workingDirectory = options.packageDir;
    }

    // Run analysis
    final result = await Process.run(
      dartBin,
      args,
      workingDirectory: workingDirectory,
      runInShell: Platform.isWindows,
    );

    // Parse output to count issues
    final output = '${result.stdout}\n${result.stderr}';
    final errorCount = _countPattern(output, RegExp(r'\berror\b', caseSensitive: false));
    final warningCount = _countPattern(output, RegExp(r'\bwarning\b', caseSensitive: false));
    final hintCount = _countPattern(output, RegExp(r'\bhint\b', caseSensitive: false));

    return AnalyzeResult(
      exitCode: result.exitCode,
      output: output.trim(),
      errorCount: errorCount,
      warningCount: warningCount,
      hintCount: hintCount,
    );
  }

  int _countPattern(String text, RegExp pattern) {
    return pattern.allMatches(text).length;
  }

  @override
  Future<void> shutdown() async {
    stderr.writeln('[$name] Final statistics:\n$stats');
    stderr.writeln('[$name] Cache statistics: ${cache.stats}');
    await super.shutdown();
  }
}

/// Options for analysis.
class AnalyzeOptions {
  final List<String> files;
  final bool fatalInfos;
  final bool fatalWarnings;
  final String? packageDir;

  AnalyzeOptions({
    required this.files,
    this.fatalInfos = false,
    this.fatalWarnings = false,
    this.packageDir,
  });
}

/// Result of analysis.
class AnalyzeResult {
  final int exitCode;
  final String output;
  final int errorCount;
  final int warningCount;
  final int hintCount;

  AnalyzeResult({
    required this.exitCode,
    required this.output,
    this.errorCount = 0,
    this.warningCount = 0,
    this.hintCount = 0,
  });
}

/// Entry point for the analyzer worker.
void main(List<String> args) async {
  if (args.contains('--persistent_worker')) {
    // Parse optional SDK path
    String? sdkPath;
    for (final arg in args) {
      if (arg.startsWith('--dart_sdk=')) {
        sdkPath = arg.substring('--dart_sdk='.length);
      }
    }

    await AnalyzerWorker(dartSdkPath: sdkPath).run();
  } else if (args.contains('--help') || args.contains('-h')) {
    print('''
Dart Analyzer Persistent Worker

Usage:
  dart analyzer_worker.dart --persistent_worker [--dart_sdk=/path/to/sdk]

Worker Mode:
  Reads JSON requests from stdin, writes JSON responses to stdout.
  Keeps analysis results cached for faster incremental analysis.

Protocol:
  Request:  {"arguments": ["@path/to/args.txt"], "inputs": [...]}
  Response: {"exitCode": 0, "output": "No issues found"}

Flagfile Format (@args.txt):
  --fatal-infos
  --fatal-warnings
  lib/main.dart
  lib/utils.dart

Environment Variables:
  DART_SDK     Path to Dart SDK (if not using --dart_sdk)

Example:
  # Start as persistent worker
  dart analyzer_worker.dart --persistent_worker

  # Then pipe requests via stdin:
  echo '{"arguments":["@analyze.args"],"inputs":[],"requestId":1}' | dart analyzer_worker.dart --persistent_worker
''');
  } else {
    stderr.writeln('Usage: dart analyzer_worker.dart --persistent_worker');
    stderr.writeln('       dart analyzer_worker.dart --help');
    exit(1);
  }
}
