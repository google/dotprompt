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

/// Flutter gRPC client application.
///
/// This is a cross-platform Flutter app that connects to the Dart gRPC server.
/// Supports: iOS, Android, Web, macOS, Linux, Windows
library;

import 'package:flutter/material.dart';
import 'package:grpc/grpc.dart';
import 'package:grpc/grpc_web.dart';

import 'generated/helloworld.pbgrpc.dart';

void main() {
  runApp(const GreeterApp());
}

/// Main application widget.
class GreeterApp extends StatelessWidget {
  const GreeterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'gRPC Flutter Client',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const GreeterPage(),
    );
  }
}

/// Main page with gRPC client functionality.
class GreeterPage extends StatefulWidget {
  const GreeterPage({super.key});

  @override
  State<GreeterPage> createState() => _GreeterPageState();
}

class _GreeterPageState extends State<GreeterPage> {
  final TextEditingController _nameController = TextEditingController(text: 'Flutter');
  final TextEditingController _hostController = TextEditingController(text: 'localhost');
  late final TextEditingController _portController;
  final List<String> _messages = [];
  bool _isLoading = false;
  late bool _useGrpcWeb;
  bool _demoMode = false; // Demo mode when server unavailable
  String? _error;
  late bool _isWeb;

  // Port constants
  static const int grpcServerPort = 50051;
  static const int grpcWebProxyPort = 8080;

  @override
  void initState() {
    super.initState();
    // Detect platform
    _isWeb = identical(0, 0.0); // Web has identical int/double
    
    // Set defaults based on platform
    _useGrpcWeb = _isWeb; // Web requires gRPC-Web
    _portController = TextEditingController(
      text: _useGrpcWeb ? '$grpcWebProxyPort' : '$grpcServerPort',
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _hostController.dispose();
    _portController.dispose();
    super.dispose();
  }

  void _updatePortForMode() {
    // Update port when gRPC-Web mode changes
    if (_useGrpcWeb) {
      _portController.text = '$grpcWebProxyPort';
    } else {
      _portController.text = '$grpcServerPort';
    }
  }

  GreeterClient _createClient() {
    final host = _hostController.text;
    final port = int.tryParse(_portController.text) ?? grpcServerPort;

    if (_useGrpcWeb) {
      // For web browser, use gRPC-Web (requires proxy on port 8080)
      final channel = GrpcWebClientChannel.xhr(Uri.parse('http://$host:$port'));
      return GreeterClient(channel);
    } else {
      // For native platforms, use standard gRPC (direct to server on port 50051)
      final channel = ClientChannel(
        host,
        port: port,
        options: const ChannelOptions(credentials: ChannelCredentials.insecure()),
      );
      return GreeterClient(channel);
    }
  }

  Future<void> _sayHello() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      if (_demoMode) {
        // Simulate gRPC response
        await Future.delayed(const Duration(milliseconds: 300));
        final name = _nameController.text;
        final timestamp = DateTime.now().millisecondsSinceEpoch;
        setState(() {
          _messages.add('Hello, $name! (demo mode, timestamp: $timestamp)');
        });
      } else {
        final client = _createClient();
        final request = HelloRequest()..name = _nameController.text;
        final response = await client.sayHello(request);
        
        setState(() {
          _messages.add('${response.message} (timestamp: ${response.timestamp})');
        });
      }
    } catch (e) {
      setState(() {
        _error = 'gRPC Error: $e\n\nTip: Enable "Demo Mode" to test the UI without a server,\nor start the server with: ./run.sh server';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _sayHelloAgain() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      if (_demoMode) {
        await Future.delayed(const Duration(milliseconds: 300));
        final name = _nameController.text;
        final timestamp = DateTime.now().millisecondsSinceEpoch;
        setState(() {
          _messages.add('Hello again, $name! (demo mode, timestamp: $timestamp)');
        });
      } else {
        final client = _createClient();
        final request = HelloRequest()..name = _nameController.text;
        final response = await client.sayHelloAgain(request);
        
        setState(() {
          _messages.add('${response.message} (timestamp: ${response.timestamp})');
        });
      }
    } catch (e) {
      setState(() {
        _error = 'gRPC Error: $e\n\nTip: Enable "Demo Mode" to test without a server.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _sayHelloStream() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      if (_demoMode) {
        final name = _nameController.text;
        for (var i = 1; i <= 5; i++) {
          await Future.delayed(const Duration(milliseconds: 300));
          final timestamp = DateTime.now().millisecondsSinceEpoch;
          setState(() {
            _messages.add('Hello $name! Stream $i/5 (demo mode, timestamp: $timestamp)');
          });
        }
      } else {
        final client = _createClient();
        final request = HelloRequest()..name = _nameController.text;
        
        await for (final response in client.sayHelloStream(request)) {
          setState(() {
            _messages.add('${response.message} (timestamp: ${response.timestamp})');
          });
        }
      }
    } catch (e) {
      setState(() {
        _error = 'gRPC Error: $e\n\nTip: Enable "Demo Mode" to test without a server.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _clearMessages() {
    setState(() {
      _messages.clear();
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('gRPC Flutter Client'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            onPressed: _clearMessages,
            tooltip: 'Clear messages',
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Server config row
            Row(
              children: [
                Expanded(
                  flex: 3,
                  child: TextField(
                    controller: _hostController,
                    decoration: const InputDecoration(
                      labelText: 'Host',
                      hintText: 'localhost',
                      prefixIcon: Icon(Icons.computer),
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  flex: 1,
                  child: TextField(
                    controller: _portController,
                    decoration: const InputDecoration(
                      labelText: 'Port',
                      hintText: '50051',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // gRPC-Web toggle
            SwitchListTile(
              title: const Text('Use gRPC-Web'),
              subtitle: Text(_isWeb 
                ? 'Required for web browser (port 8080 → proxy → 50051)'
                : 'Native gRPC (direct to port 50051)'),
              value: _useGrpcWeb,
              onChanged: _demoMode ? null : (value) {
                setState(() {
                  _useGrpcWeb = value;
                  _updatePortForMode();
                });
              },
            ),
            
            // Demo mode toggle
            SwitchListTile(
              title: const Text('Demo Mode'),
              subtitle: const Text('Simulate responses without a real server'),
              value: _demoMode,
              onChanged: (value) => setState(() => _demoMode = value),
              secondary: Icon(
                Icons.science,
                color: _demoMode ? Theme.of(context).colorScheme.primary : null,
              ),
            ),
            const SizedBox(height: 8),
            
            // Name input
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Your Name',
                hintText: 'Enter your name',
                prefixIcon: Icon(Icons.person),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),

            // Action buttons
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: _isLoading ? null : _sayHello,
                  icon: const Icon(Icons.waving_hand),
                  label: const Text('Say Hello'),
                ),
                FilledButton.tonal(
                  onPressed: _isLoading ? null : _sayHelloAgain,
                  child: const Text('Say Hello Again'),
                ),
                OutlinedButton.icon(
                  onPressed: _isLoading ? null : _sayHelloStream,
                  icon: const Icon(Icons.stream),
                  label: const Text('Stream (5 messages)'),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Error display
            if (_error != null)
              Card(
                color: Theme.of(context).colorScheme.errorContainer,
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.error, color: Theme.of(context).colorScheme.error),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _error!,
                          style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

            // Loading indicator
            if (_isLoading)
              const Padding(
                padding: EdgeInsets.all(8.0),
                child: LinearProgressIndicator(),
              ),

            const SizedBox(height: 16),
            
            // Messages list
            Expanded(
              child: Card(
                child: _messages.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.message_outlined,
                              size: 48,
                              color: Theme.of(context).colorScheme.outline,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'No messages yet',
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.outline,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Start the server and click "Say Hello"',
                              style: TextStyle(
                                fontSize: 12,
                                color: Theme.of(context).colorScheme.outline,
                              ),
                            ),
                          ],
                        ),
                      )
                    : ListView.builder(
                        reverse: true,
                        padding: const EdgeInsets.all(8),
                        itemCount: _messages.length,
                        itemBuilder: (context, index) {
                          // Reverse index for display numbering
                          final reversedIndex = _messages.length - 1 - index;
                          return ListTile(
                            leading: CircleAvatar(
                              child: Text('${reversedIndex + 1}'),
                            ),
                            title: Text(_messages[reversedIndex]),
                          );
                        },
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
