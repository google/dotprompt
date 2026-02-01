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

/// User model using freezed for immutable data classes.
///
/// This demonstrates how to use dart_build_runner with Bazel
/// for code generation with freezed and json_serializable.
library;

import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:json_annotation/json_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

/// An immutable user model.
///
/// The @freezed annotation generates:
/// - Immutable copyWith methods
/// - == and hashCode
/// - toString
/// - Pattern matching via map/maybeMap
@freezed
class User with _$User {
  const factory User({
    required int id,
    required String name,
    required String email,
    Profile? profile,
  }) = _User;

  /// Create a User from JSON.
  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}

/// User profile information.
@freezed
class Profile with _$Profile {
  const factory Profile({
    required String bio,
    String? avatarUrl,
    DateTime? createdAt,
  }) = _Profile;

  /// Create a Profile from JSON.
  factory Profile.fromJson(Map<String, dynamic> json) => _$ProfileFromJson(json);
}
