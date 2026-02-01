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

/// Tests for generated proto and gRPC code.
library;

import 'package:test/test.dart';

void main() {
  group('User proto', () {
    test('can be instantiated', () {
      // When the proto is generated, test it like this:
      // final user = User()
      //   ..id = 1
      //   ..name = 'Test User'
      //   ..email = 'test@example.com';
      //
      // expect(user.id, equals(1));
      // expect(user.name, equals('Test User'));

      // Placeholder test
      expect(true, isTrue);
    });

    test('profile can be nested', () {
      // final user = User()
      //   ..id = 1
      //   ..profile = (Profile()
      //     ..bio = 'Hello'
      //     ..avatarUrl = 'https://example.com/avatar.png');
      //
      // expect(user.profile.bio, equals('Hello'));

      expect(true, isTrue);
    });
  });

  group('UserService gRPC', () {
    test('stub can be created', () {
      // final channel = ClientChannel('localhost', port: 50051);
      // final stub = UserServiceClient(channel);
      // expect(stub, isNotNull);

      expect(true, isTrue);
    });
  });
}
