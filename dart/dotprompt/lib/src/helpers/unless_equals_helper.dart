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

/// unlessEquals helper for conditional rendering based on inequality.
///
/// The {{#unlessEquals}} helper renders content if two values are NOT equal.
///
/// ## Usage
///
/// ```handlebars
/// {{#unlessEquals status "active"}}
/// User is NOT active!
/// {{else}}
/// User is active.
/// {{/unlessEquals}}
/// ```
library;

import "if_equals_helper.dart";

/// Marker class for the unlessEquals helper.
///
/// This helper provides conditional rendering based on value inequality.
/// It's the inverse of [IfEqualsHelper].
class UnlessEqualsHelper {
  /// Private constructor to prevent instantiation.
  UnlessEqualsHelper._();

  /// The name of this helper in templates.
  static const String name = "unlessEquals";

  /// Checks if two values are NOT equal.
  static bool areNotEqual(dynamic a, dynamic b) => !IfEqualsHelper.areEqual(a, b);
}
