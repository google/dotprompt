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

/// Bazel Persistent Worker Protocol implementation for Dart/Flutter.
///
/// This library implements the Bazel persistent worker protocol, allowing
/// Dart compilation processes to stay alive between builds for faster
/// incremental compilation.
///
/// ## Protocol Overview
///
/// ```
/// ┌─────────────────────────────────────────────────────────────────┐
/// │                 Bazel Persistent Worker Protocol                │
/// ├─────────────────────────────────────────────────────────────────┤
/// │                                                                 │
/// │  Bazel ─────(WorkRequest)─────▶ Worker                         │
/// │                                   │                             │
/// │                                   ▼                             │
/// │                              Process Request                    │
/// │                                   │                             │
/// │                                   ▼                             │
/// │  Bazel ◀────(WorkResponse)───── Worker                         │
/// │                                                                 │
/// └─────────────────────────────────────────────────────────────────┘
/// ```
///
/// ## Message Format
///
/// Workers communicate using length-prefixed protocol buffers:
/// - WorkRequest: Contains arguments and input files
/// - WorkResponse: Contains exit code and output
///
/// ## References
///
/// - [Bazel Persistent Workers](https://bazel.build/remote/persistent)
/// - [Worker Protocol](https://github.com/bazelbuild/bazel/blob/master/src/main/protobuf/worker_protocol.proto)
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Input file for a work request.
class WorkerInput {
  /// Path to the input file.
  final String path;

  /// Digest of the file contents (SHA-256).
  final String digest;

  WorkerInput({required this.path, required this.digest});

  factory WorkerInput.fromJson(Map<String, dynamic> json) {
    return WorkerInput(
      path: json['path'] as String,
      digest: json['digest'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'path': path,
        'digest': digest,
      };
}

/// Request from Bazel to the worker.
class WorkRequest {
  /// Command-line arguments.
  final List<String> arguments;

  /// Input files for this request.
  final List<WorkerInput> inputs;

  /// Unique identifier for this request (for multiplexed workers).
  final int requestId;

  /// If true, this is a cancel request.
  final bool cancel;

  /// Verbosity level for logging.
  final int verbosity;

  /// Sandbox directory (if sandboxed execution).
  final String? sandboxDir;

  WorkRequest({
    required this.arguments,
    this.inputs = const [],
    this.requestId = 0,
    this.cancel = false,
    this.verbosity = 0,
    this.sandboxDir,
  });

  factory WorkRequest.fromJson(Map<String, dynamic> json) {
    return WorkRequest(
      arguments: (json['arguments'] as List<dynamic>?)?.cast<String>() ?? [],
      inputs: (json['inputs'] as List<dynamic>?)
              ?.map((e) => WorkerInput.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      requestId: json['requestId'] as int? ?? 0,
      cancel: json['cancel'] as bool? ?? false,
      verbosity: json['verbosity'] as int? ?? 0,
      sandboxDir: json['sandboxDir'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'arguments': arguments,
        'inputs': inputs.map((e) => e.toJson()).toList(),
        'requestId': requestId,
        'cancel': cancel,
        'verbosity': verbosity,
        if (sandboxDir != null) 'sandboxDir': sandboxDir,
      };
}

/// Response from the worker to Bazel.
class WorkResponse {
  /// Exit code (0 = success).
  final int exitCode;

  /// Output message (stdout + stderr combined).
  final String output;

  /// Request ID this response is for (for multiplexed workers).
  final int requestId;

  /// True if this response indicates the request was cancelled.
  final bool wasCancelled;

  WorkResponse({
    required this.exitCode,
    this.output = '',
    this.requestId = 0,
    this.wasCancelled = false,
  });

  factory WorkResponse.success({String output = '', int requestId = 0}) {
    return WorkResponse(exitCode: 0, output: output, requestId: requestId);
  }

  factory WorkResponse.failure(String error, {int requestId = 0}) {
    return WorkResponse(exitCode: 1, output: error, requestId: requestId);
  }

  factory WorkResponse.cancelled({int requestId = 0}) {
    return WorkResponse(exitCode: 0, requestId: requestId, wasCancelled: true);
  }

  Map<String, dynamic> toJson() => {
        'exitCode': exitCode,
        'output': output,
        'requestId': requestId,
        'wasCancelled': wasCancelled,
      };
}

/// Abstract base class for persistent workers.
///
/// Implement [processRequest] to handle work requests.
abstract class PersistentWorker {
  /// Name of this worker (for logging).
  String get name;

  /// Process a work request and return a response.
  Future<WorkResponse> processRequest(WorkRequest request);

  /// Called when the worker is shutting down.
  Future<void> shutdown() async {}

  /// Run the worker loop, reading requests from stdin and writing responses to stdout.
  Future<void> run() async {
    stderr.writeln('[$name] Worker started');

    final inputLines = stdin.transform(utf8.decoder).transform(const LineSplitter());

    await for (final line in inputLines) {
      if (line.isEmpty) continue;

      try {
        final json = jsonDecode(line) as Map<String, dynamic>;
        final request = WorkRequest.fromJson(json);

        if (request.cancel) {
          // Handle cancellation
          final response = WorkResponse.cancelled(requestId: request.requestId);
          _writeResponse(response);
          continue;
        }

        stderr.writeln('[$name] Processing request ${request.requestId}');
        final stopwatch = Stopwatch()..start();

        final response = await processRequest(request);

        stopwatch.stop();
        stderr.writeln('[$name] Completed in ${stopwatch.elapsedMilliseconds}ms');

        _writeResponse(response);
      } catch (e, st) {
        stderr.writeln('[$name] Error: $e\n$st');
        _writeResponse(WorkResponse.failure('Worker error: $e'));
      }
    }

    await shutdown();
    stderr.writeln('[$name] Worker shutdown');
  }

  void _writeResponse(WorkResponse response) {
    final json = jsonEncode(response.toJson());
    stdout.writeln(json);
  }
}

/// A simple echo worker for testing the protocol.
class EchoWorker extends PersistentWorker {
  @override
  String get name => 'EchoWorker';

  @override
  Future<WorkResponse> processRequest(WorkRequest request) async {
    final message = 'Echo: ${request.arguments.join(' ')}';
    return WorkResponse.success(output: message, requestId: request.requestId);
  }
}

/// Entry point for testing the echo worker.
void main(List<String> args) async {
  if (args.contains('--persistent_worker')) {
    await EchoWorker().run();
  } else {
    // Non-worker mode: just echo arguments
    print('Echo: ${args.join(' ')}');
  }
}
