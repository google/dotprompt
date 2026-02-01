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

/// Hot Reload Worker for Flutter applications.
///
/// This worker enables hot reload functionality for Flutter apps built with
/// Bazel. It connects to the running Flutter app's VM Service and triggers
/// hot reload when source files change.
///
/// ## Architecture
///
/// ```
/// ┌─────────────────────────────────────────────────────────────────────────┐
/// │                        Hot Reload Architecture                          │
/// ├─────────────────────────────────────────────────────────────────────────┤
/// │                                                                         │
/// │  ┌──────────┐    ┌──────────────┐    ┌──────────────┐                  │
/// │  │  ibazel  │───▶│  Hot Reload  │───▶│   Flutter    │                  │
/// │  │ (watcher)│    │    Worker    │    │  VM Service  │                  │
/// │  └──────────┘    └──────────────┘    └──────────────┘                  │
/// │       │                │                    │                          │
/// │       ▼                ▼                    ▼                          │
/// │  File change      Recompile            Update app                      │
/// │  detected         changed files        (state preserved)               │
/// │                                                                         │
/// └─────────────────────────────────────────────────────────────────────────┘
/// ```
///
/// ## Usage
///
/// 1. Start the Flutter app with VM Service enabled
/// 2. Run the hot reload worker with the VM Service URI
/// 3. Make changes to source files
/// 4. Worker detects changes and triggers hot reload
///
/// ## References
///
/// - [Flutter Hot Reload](https://docs.flutter.dev/tools/hot-reload)
/// - [Dart VM Service Protocol](https://github.com/dart-lang/sdk/blob/main/runtime/vm/service/service.md)
library;

import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'protocol.dart';

/// Client for the Dart VM Service protocol.
///
/// Connects to a running Dart/Flutter application and enables hot reload.
class VmServiceClient {
  final String host;
  final int port;
  final String? authToken;

  WebSocket? _socket;
  int _requestId = 0;
  final Map<int, Completer<Map<String, dynamic>>> _pendingRequests = {};

  VmServiceClient({
    required this.host,
    required this.port,
    this.authToken,
  });

  /// Connect to the VM Service.
  Future<void> connect() async {
    final uri = authToken != null
        ? 'ws://$host:$port/$authToken/ws'
        : 'ws://$host:$port/ws';

    stderr.writeln('[VmService] Connecting to $uri');
    _socket = await WebSocket.connect(uri);

    _socket!.listen(
      _handleMessage,
      onError: (error) => stderr.writeln('[VmService] Error: $error'),
      onDone: () => stderr.writeln('[VmService] Connection closed'),
    );

    stderr.writeln('[VmService] Connected');
  }

  void _handleMessage(dynamic data) {
    final json = jsonDecode(data as String) as Map<String, dynamic>;

    if (json.containsKey('id')) {
      final id = json['id'] as int;
      final completer = _pendingRequests.remove(id);
      if (completer != null) {
        if (json.containsKey('error')) {
          completer.completeError(json['error']);
        } else {
          completer.complete(json['result'] as Map<String, dynamic>?);
        }
      }
    } else if (json.containsKey('method')) {
      // Handle events
      final method = json['method'] as String;
      stderr.writeln('[VmService] Event: $method');
    }
  }

  /// Send a JSON-RPC request and wait for response.
  Future<Map<String, dynamic>?> _request(
    String method, [
    Map<String, dynamic>? params,
  ]) async {
    if (_socket == null) throw StateError('Not connected');

    final id = _requestId++;
    final request = {
      'jsonrpc': '2.0',
      'id': id,
      'method': method,
      if (params != null) 'params': params,
    };

    final completer = Completer<Map<String, dynamic>>();
    _pendingRequests[id] = completer;

    _socket!.add(jsonEncode(request));

    return completer.future.timeout(
      const Duration(seconds: 30),
      onTimeout: () {
        _pendingRequests.remove(id);
        throw TimeoutException('Request $method timed out');
      },
    );
  }

  /// Get the version of the VM Service protocol.
  Future<String> getVersion() async {
    final result = await _request('getVersion');
    final major = result?['major'] ?? 0;
    final minor = result?['minor'] ?? 0;
    return '$major.$minor';
  }

  /// Get list of all isolates.
  Future<List<String>> getIsolates() async {
    final result = await _request('getVM');
    final isolates = result?['isolates'] as List<dynamic>? ?? [];
    return isolates.map((e) => (e as Map)['id'] as String).toList();
  }

  /// Trigger hot reload for an isolate.
  ///
  /// Returns true if the reload was successful.
  Future<bool> hotReload(String isolateId) async {
    try {
      final result = await _request('reloadSources', {
        'isolateId': isolateId,
        'force': false,
        'pause': false,
      });

      final success = result?['success'] as bool? ?? false;
      if (success) {
        stderr.writeln('[VmService] Hot reload successful for $isolateId');
      } else {
        final message = result?['notices']?.toString() ?? 'Unknown error';
        stderr.writeln('[VmService] Hot reload failed: $message');
      }
      return success;
    } catch (e) {
      stderr.writeln('[VmService] Hot reload error: $e');
      return false;
    }
  }

  /// Trigger hot restart (full app restart with state loss).
  Future<bool> hotRestart(String isolateId) async {
    try {
      // Hot restart uses the Flutter extension
      await _request('ext.flutter.reassemble', {
        'isolateId': isolateId,
      });
      stderr.writeln('[VmService] Hot restart successful');
      return true;
    } catch (e) {
      stderr.writeln('[VmService] Hot restart error: $e');
      return false;
    }
  }

  /// Disconnect from the VM Service.
  Future<void> disconnect() async {
    await _socket?.close();
    _socket = null;
    stderr.writeln('[VmService] Disconnected');
  }
}

/// Hot Reload Worker implementation.
///
/// Handles hot reload requests from Bazel and communicates with the
/// running Flutter application via the VM Service.
class HotReloadWorker extends PersistentWorker {
  VmServiceClient? _client;
  String? _currentIsolateId;

  @override
  String get name => 'HotReloadWorker';

  @override
  Future<WorkResponse> processRequest(WorkRequest request) async {
    final args = _parseArgs(request.arguments);

    switch (args['command']) {
      case 'connect':
        return _handleConnect(args);
      case 'reload':
        return _handleReload(args);
      case 'restart':
        return _handleRestart(args);
      case 'disconnect':
        return _handleDisconnect(args);
      default:
        return WorkResponse.failure(
          'Unknown command: ${args['command']}',
          requestId: request.requestId,
        );
    }
  }

  Map<String, String> _parseArgs(List<String> arguments) {
    final result = <String, String>{};
    for (final arg in arguments) {
      if (arg.startsWith('--')) {
        final parts = arg.substring(2).split('=');
        if (parts.length == 2) {
          result[parts[0]] = parts[1];
        } else {
          result[parts[0]] = 'true';
        }
      }
    }
    return result;
  }

  Future<WorkResponse> _handleConnect(Map<String, String> args) async {
    final host = args['host'] ?? 'localhost';
    final port = int.tryParse(args['port'] ?? '8181') ?? 8181;
    final authToken = args['auth_token'];

    try {
      _client = VmServiceClient(host: host, port: port, authToken: authToken);
      await _client!.connect();

      final version = await _client!.getVersion();
      final isolates = await _client!.getIsolates();

      if (isolates.isNotEmpty) {
        _currentIsolateId = isolates.first;
      }

      return WorkResponse.success(
        output: 'Connected to VM Service v$version\n'
            'Isolates: ${isolates.join(', ')}\n'
            'Current isolate: $_currentIsolateId',
      );
    } catch (e) {
      return WorkResponse.failure('Failed to connect: $e');
    }
  }

  Future<WorkResponse> _handleReload(Map<String, String> args) async {
    if (_client == null || _currentIsolateId == null) {
      return WorkResponse.failure('Not connected. Run connect first.');
    }

    final success = await _client!.hotReload(_currentIsolateId!);
    return success
        ? WorkResponse.success(output: 'Hot reload successful')
        : WorkResponse.failure('Hot reload failed');
  }

  Future<WorkResponse> _handleRestart(Map<String, String> args) async {
    if (_client == null || _currentIsolateId == null) {
      return WorkResponse.failure('Not connected. Run connect first.');
    }

    final success = await _client!.hotRestart(_currentIsolateId!);
    return success
        ? WorkResponse.success(output: 'Hot restart successful')
        : WorkResponse.failure('Hot restart failed');
  }

  Future<WorkResponse> _handleDisconnect(Map<String, String> args) async {
    await _client?.disconnect();
    _client = null;
    _currentIsolateId = null;
    return WorkResponse.success(output: 'Disconnected');
  }

  @override
  Future<void> shutdown() async {
    await _client?.disconnect();
    await super.shutdown();
  }
}

/// Entry point for the hot reload worker.
void main(List<String> args) async {
  if (args.contains('--persistent_worker')) {
    await HotReloadWorker().run();
  } else {
    // Non-worker mode: print usage
    print('''
Hot Reload Worker for Flutter/Bazel

Usage:
  dart hot_reload_worker.dart --persistent_worker

Commands (sent via worker protocol):
  --command=connect --host=localhost --port=8181 --auth_token=xxx
  --command=reload
  --command=restart
  --command=disconnect
''');
  }
}
