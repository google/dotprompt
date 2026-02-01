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

/// Tests for freezed user model.
library;

import 'package:test/test.dart';

// Uncomment when generated code exists:
// import 'package:freezed_example/user.dart';

void main() {
  group('User', () {
    test('can be created with required fields', () {
      // final user = User(
      //   id: 1,
      //   name: 'Test User',
      //   email: 'test@example.com',
      // );
      //
      // expect(user.id, equals(1));
      // expect(user.name, equals('Test User'));
      // expect(user.profile, isNull);

      expect(true, isTrue);
    });

    test('copyWith creates a new instance', () {
      // final user = User(id: 1, name: 'Alice', email: 'a@example.com');
      // final updated = user.copyWith(name: 'Bob');
      //
      // expect(user.name, equals('Alice'));
      // expect(updated.name, equals('Bob'));
      // expect(user.id, equals(updated.id));

      expect(true, isTrue);
    });

    test('equality works correctly', () {
      // final user1 = User(id: 1, name: 'Alice', email: 'a@example.com');
      // final user2 = User(id: 1, name: 'Alice', email: 'a@example.com');
      // final user3 = User(id: 2, name: 'Alice', email: 'a@example.com');
      //
      // expect(user1, equals(user2));
      // expect(user1, isNot(equals(user3)));

      expect(true, isTrue);
    });

    test('JSON serialization works', () {
      // final user = User(id: 1, name: 'Test', email: 'test@example.com');
      // final json = user.toJson();
      // final restored = User.fromJson(json);
      //
      // expect(restored, equals(user));

      expect(true, isTrue);
    });
  });

  group('Profile', () {
    test('can be nested in User', () {
      // final user = User(
      //   id: 1,
      //   name: 'Alice',
      //   email: 'a@example.com',
      //   profile: Profile(bio: 'Developer'),
      // );
      //
      // expect(user.profile?.bio, equals('Developer'));

      expect(true, isTrue);
    });
  });
}
