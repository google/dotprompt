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

/// Example application using freezed models.
library;

import 'dart:convert';
import 'dart:io';

// Uncomment when generated code exists:
// import 'user.dart';

void main() {
  print('Freezed Example');
  print('===============');
  print('');
  print('This example demonstrates dart_build_runner for code generation.');
  print('');
  print('Generated files:');
  print('  - user.freezed.dart (immutable classes, copyWith, ==, hashCode)');
  print('  - user.g.dart (JSON serialization)');
  print('');
  print('Build commands:');
  print('  bazel build //:generated     # Run build_runner');
  print('  bazel build //:models        # Build library with generated code');
  print('  bazel run //:example         # Run this example');
  print('');

  // Example usage (uncomment when generated code exists):
  // final user = User(
  //   id: 1,
  //   name: 'Alice',
  //   email: 'alice@example.com',
  //   profile: Profile(bio: 'Dart developer'),
  // );
  //
  // // Immutable copyWith
  // final updated = user.copyWith(name: 'Alice Smith');
  // print('Original: ${user.name}');
  // print('Updated: ${updated.name}');
  //
  // // JSON serialization
  // final json = jsonEncode(user.toJson());
  // print('JSON: $json');

  exit(0);
}
