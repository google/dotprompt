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

/// gRPC client example following the official Dart gRPC quickstart.
///
/// This demonstrates calling a gRPC service using generated stubs.
/// Based on: https://grpc.io/docs/languages/dart/quickstart/
library;

import 'dart:io';

// TODO(#issue): Uncomment when Bazel generates the proto code:
// import 'package:grpc/grpc.dart';
// import 'generated/helloworld.pbgrpc.dart';

/// Main entry point for the gRPC client.
///
/// Example usage (following official quickstart):
/// ```dart
/// Future<void> main(List<String> args) async {
///   final channel = ClientChannel(
///     'localhost',
///     port: 50051,
///     options: ChannelOptions(credentials: ChannelCredentials.insecure()),
///   );
///
///   final stub = GreeterClient(channel);
///   final name = args.isNotEmpty ? args[0] : 'world';
///
///   try {
///     var response = await stub.sayHello(HelloRequest()..name = name);
///     print('Greeter client received: ${response.message}');
///
///     response = await stub.sayHelloAgain(HelloRequest()..name = name);
///     print('Greeter client received: ${response.message}');
///   } catch (e) {
///     print('Caught error: $e');
///   }
///
///   await channel.shutdown();
/// }
/// ```
void main(List<String> args) async {
  print('gRPC Client Example');
  print('===================');
  print('');
  print('This example demonstrates calling a gRPC service with Bazel.');
  print('');
  print('Build and run:');
  print('  bazel build //:client');
  print('  bazel run //:client -- Alice');
  print('');
  print('Expected output:');
  print('  Greeter client received: Hello, Alice!');
  print('  Greeter client received: Hello again, Alice!');
  print('');

  final name = args.isNotEmpty ? args[0] : 'world';
  print('Would greet: $name');

  // Uncomment when proto generation is working:
  // final channel = ClientChannel(
  //   'localhost',
  //   port: 50051,
  //   options: ChannelOptions(credentials: ChannelCredentials.insecure()),
  // );
  // final stub = GreeterClient(channel);
  //
  // try {
  //   var response = await stub.sayHello(HelloRequest()..name = name);
  //   print('Greeter client received: ${response.message}');
  //
  //   response = await stub.sayHelloAgain(HelloRequest()..name = name);
  //   print('Greeter client received: ${response.message}');
  // } catch (e) {
  //   print('Caught error: $e');
  // }
  //
  // await channel.shutdown();

  exit(0);
}
