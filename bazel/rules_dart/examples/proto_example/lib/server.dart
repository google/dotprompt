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

/// gRPC server example following the official Dart gRPC quickstart.
///
/// This demonstrates implementing a gRPC service using generated stubs.
/// Based on: https://grpc.io/docs/languages/dart/quickstart/
library;

import 'dart:io';

// TODO(#issue): Uncomment when Bazel generates the proto code:
// import 'package:grpc/grpc.dart';
// import 'generated/helloworld.pbgrpc.dart';

/// Implementation of the Greeter service.
///
/// This class extends the generated GreeterServiceBase and implements
/// the RPC methods defined in helloworld.proto.
///
/// Example usage:
/// ```dart
/// class GreeterService extends GreeterServiceBase {
///   @override
///   Future<HelloReply> sayHello(ServiceCall call, HelloRequest request) async {
///     return HelloReply()..message = 'Hello, ${request.name}!';
///   }
///
///   @override
///   Future<HelloReply> sayHelloAgain(ServiceCall call, HelloRequest request) async {
///     return HelloReply()..message = 'Hello again, ${request.name}!';
///   }
/// }
/// ```
void main(List<String> args) async {
  print('gRPC Server Example');
  print('===================');
  print('');
  print('This example demonstrates building a gRPC server with Bazel.');
  print('');
  print('Prerequisites (already handled by Bazel):');
  print('  1. protoc (Protocol Buffer compiler)');
  print('  2. protoc-gen-dart plugin');
  print('');
  print('Build targets:');
  print('  bazel build //:helloworld_dart_proto  # Proto messages');
  print('  bazel build //:helloworld_dart_grpc   # gRPC stubs');
  print('  bazel build //:server                  # This server');
  print('');
  print('The generated service base class provides:');
  print('  - sayHello(ServiceCall, HelloRequest) -> HelloReply');
  print('  - sayHelloAgain(ServiceCall, HelloRequest) -> HelloReply');
  print('');

  // Uncomment when proto generation is working:
  // final server = Server.create(services: [GreeterService()]);
  // await server.serve(port: 50051);
  // print('Server listening on port ${server.port}...');

  print('Server would listen on port 50051');
  exit(0);
}
