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

/// Role helper for specifying message roles in prompts.
///
/// The {{#role}} helper sets the role for a message section.
///
/// ## Usage
///
/// ```handlebars
/// {{#role "system"}}
/// You are a helpful assistant.
/// {{/role}}
///
/// {{#role "user"}}
/// Hello!
/// {{/role}}
/// ```
library;

import "../types.dart";

/// Marker class for the role helper.
///
/// This helper wraps content to indicate which role it belongs to.
class RoleHelper {
  /// Private constructor to prevent instantiation.
  RoleHelper._();

  /// The name of this helper in templates.
  static const String name = "role";

  /// The special marker prefix used in rendered output.
  static const String markerPrefix = "<<<dotprompt:role:";

  /// The special marker suffix used in rendered output.
  static const String markerSuffix = ">>>";

  /// Creates a role marker for the given role.
  static String createMarker(Role role) => "$markerPrefix${role.value}$markerSuffix";

  /// Creates a role marker from a role string.
  static String createMarkerFromString(String role) => "$markerPrefix$role$markerSuffix";

  /// Checks if a string contains a role marker.
  static bool containsMarker(String text) => text.contains(markerPrefix);

  /// Extracts the role from a marker string.
  static Role? extractRole(String marker) {
    if (!marker.startsWith(markerPrefix) || !marker.endsWith(markerSuffix)) {
      return null;
    }
    final roleStr = marker.substring(
      markerPrefix.length,
      marker.length - markerSuffix.length,
    );
    return Role.tryParse(roleStr);
  }
}
