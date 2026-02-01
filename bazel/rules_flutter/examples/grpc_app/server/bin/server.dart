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

/// Dart gRPC server implementation following official gRPC quickstart.
///
/// This server implements the Greeter service defined in helloworld.proto.
/// Based on: https://grpc.io/docs/languages/dart/quickstart/
library;

import 'dart:async';

import 'package:fixnum/fixnum.dart';
import 'package:grpc/grpc.dart';

import 'package:grpc_server/generated/helloworld.pbgrpc.dart';

/// Port the server listens on.
const int serverPort = 50051;

/// Greeter service implementation with request/response logging.
class GreeterService extends GreeterServiceBase {
  void _logRequest(String method, String clientInfo, HelloRequest request) {
    final timestamp = DateTime.now().toIso8601String();
    print('');
    print('[$timestamp] 📥 $method');
    print('  Client: $clientInfo');
    print('  Request: name="${request.name}"');
  }

  void _logResponse(String method, HelloReply reply) {
    print('  Response: message="${reply.message}"');
    print('  ✅ $method completed');
  }

  String _getClientInfo(ServiceCall call) {
    final peer = call.clientMetadata?[':authority'] ?? 'unknown';
    return peer;
  }

  @override
  Future<HelloReply> sayHello(ServiceCall call, HelloRequest request) async {
    _logRequest('SayHello', _getClientInfo(call), request);
    
    final reply = HelloReply()
      ..message = 'Hello, ${request.name}!'
      ..timestamp = Int64(DateTime.now().millisecondsSinceEpoch);
    
    _logResponse('SayHello', reply);
    return reply;
  }

  @override
  Future<HelloReply> sayHelloAgain(ServiceCall call, HelloRequest request) async {
    _logRequest('SayHelloAgain', _getClientInfo(call), request);
    
    final reply = HelloReply()
      ..message = 'Hello again, ${request.name}!'
      ..timestamp = Int64(DateTime.now().millisecondsSinceEpoch);
    
    _logResponse('SayHelloAgain', reply);
    return reply;
  }

  @override
  Stream<HelloReply> sayHelloStream(ServiceCall call, HelloRequest request) async* {
    _logRequest('SayHelloStream', _getClientInfo(call), request);
    
    for (var i = 1; i <= 5; i++) {
      final reply = HelloReply()
        ..message = 'Hello ${request.name}! (message $i of 5)'
        ..timestamp = Int64(DateTime.now().millisecondsSinceEpoch);
      
      print('  Stream [$i/5]: "${reply.message}"');
      yield reply;
      await Future.delayed(Duration(milliseconds: 500));
    }
    print('  ✅ SayHelloStream completed (5 messages)');
  }
}

/// Main entry point for the gRPC server.
Future<void> main(List<String> args) async {
  final server = Server.create(
    services: [GreeterService()],
    codecRegistry: CodecRegistry(codecs: const [GzipCodec(), IdentityCodec()]),
  );

  await server.serve(port: serverPort);
  
  print('gRPC Server Example');
  print('===================');
  print('');
  print('Server listening on port ${server.port}...');
  print('');
  print('Endpoints:');
  print('  - SayHello: grpc://localhost:$serverPort/greeter.Greeter/SayHello');
  print('  - SayHelloAgain: grpc://localhost:$serverPort/greeter.Greeter/SayHelloAgain');
  print('  - SayHelloStream: grpc://localhost:$serverPort/greeter.Greeter/SayHelloStream');
  print('');
  print('Run the Flutter client:');
  print('  flutter run -d chrome');
  print('  flutter run -d macos');
}
