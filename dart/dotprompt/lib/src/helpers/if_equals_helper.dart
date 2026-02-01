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

/// ifEquals helper for conditional rendering based on equality.
///
/// The {{#ifEquals}} helper renders content if two values are equal.
///
/// ## Usage
///
/// ```handlebars
/// {{#ifEquals status "active"}}
/// User is active!
/// {{else}}
/// User is inactive.
/// {{/ifEquals}}
/// ```
library;

/// Marker class for the ifEquals helper.
///
/// This helper provides conditional rendering based on value equality.
class IfEqualsHelper {
  /// Private constructor to prevent instantiation.
  IfEqualsHelper._();

  /// The name of this helper in templates.
  static const String name = "ifEquals";

  /// Checks if two values are equal.
  ///
  /// Values are considered equal if:
  /// - They are identical (===)
  /// - Their string representations are equal
  /// - Both are null
  static bool areEqual(dynamic a, dynamic b) {
    if (identical(a, b)) return true;
    if (a == null && b == null) return true;
    if (a == null || b == null) return false;

    // Compare as strings for flexible matching
    return a.toString() == b.toString();
  }
}
