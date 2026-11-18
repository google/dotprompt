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
/// The {{role}} helper switches the role for the content that follows it.
///
/// ## Usage
///
/// ```handlebars
/// {{role "system"}}
/// You are a helpful assistant.
/// {{role "user"}}
/// Hello!
/// ```
///
/// ## Markers
///
/// The helper emits `<<<dotprompt:{nonce}:role:{name}>>>`, where `nonce` is
/// the per-render nonce that the message splitter also uses. Markers without
/// the right nonce (e.g. typed by an end user) stay plain text.
library;

import "package:meta/meta.dart";

import "../markers.dart";
import "../types.dart";

/// Marker class for the role helper.
///
/// This helper emits a marker indicating which role the following content
/// belongs to.
class RoleHelper {
  /// Private constructor to prevent instantiation.
  RoleHelper._();

  /// The name of this helper in templates.
  static const String name = "role";

  /// Creates a role marker for [role] carrying the per-render [nonce].
  ///
  /// Throws [ArgumentError] if [nonce] is not 32 lowercase hex chars.
  ///
  /// Internal: only the renderer holds the per-render nonce, so this is not
  /// usable from outside `package:dotprompt`.
  @internal
  static String createMarker(String nonce, Role role) => createMarkerFromString(nonce, role.value);

  /// Creates a role marker from a role string carrying the per-render [nonce].
  ///
  /// Throws [ArgumentError] if [nonce] is not 32 lowercase hex chars.
  ///
  /// Internal: only the renderer holds the per-render nonce, so this is not
  /// usable from outside `package:dotprompt`.
  @internal
  static String createMarkerFromString(String nonce, String role) => formatMarker(nonce, "$roleMarkerBodyPrefix$role");
}
