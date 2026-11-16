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

/// Section helper for organizing content into named sections.
///
/// The {{section}} helper creates metadata markers that organize content
/// into logical sections with associated purpose metadata.
///
/// ## Usage
///
/// ```handlebars
/// {{section "intro"}}
/// Introduction content here
/// {{section "main"}}
/// Main content here
/// ```
///
/// ## Markers
///
/// The helper emits `<<<dotprompt:{nonce}:section {name}>>>`, where `nonce`
/// is the per-render nonce that the part splitter also uses. Markers without
/// the right nonce (e.g. typed by an end user) stay plain text.
library;

import "package:meta/meta.dart";

import "../markers.dart";

/// Marker class for the section helper.
///
/// This helper creates section markers that are converted to MetadataPart
/// objects during message processing.
class SectionHelper {
  /// Private constructor to prevent instantiation.
  SectionHelper._();

  /// The name of this helper in templates.
  static const String name = "section";

  /// Creates a section marker for [sectionName] carrying the per-render
  /// [nonce].
  ///
  /// Throws [ArgumentError] if [nonce] is not 32 lowercase hex chars.
  ///
  /// Internal: only the renderer holds the per-render nonce, so this is not
  /// usable from outside `package:dotprompt`.
  @internal
  static String createMarker(String nonce, String sectionName) =>
      formatMarker(nonce, "$sectionMarkerBodyPrefix$sectionName");

  /// Extracts the section name from a marker body (`section {name}`), as
  /// produced by splitting with [mediaAndSectionMarkerRegex].
  ///
  /// Returns null if [body] is not a section marker body.
  ///
  /// Internal: marker bodies only come from splitting with the per-render
  /// nonce, so this is not meaningful outside `package:dotprompt`.
  @internal
  static String? sectionNameFromBody(String body) {
    if (!body.startsWith(sectionMarkerBodyPrefix)) return null;
    return body.substring(sectionMarkerBodyPrefix.length);
  }
}
