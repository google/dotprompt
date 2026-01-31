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

/// Section helper for organizing prompt sections.
///
/// The {{#section}} helper groups content into labeled sections.
///
/// ## Usage
///
/// ```handlebars
/// {{#section "instructions"}}
/// You are a helpful assistant.
/// {{/section}}
///
/// {{#section "context"}}
/// The user is working on a project.
/// {{/section}}
/// ```
library;

/// Marker class for the section helper.
///
/// This helper creates section markers that can be used to organize
/// and potentially filter/reorder prompt sections.
class SectionHelper {
  /// Private constructor to prevent instantiation.
  SectionHelper._();

  /// The name of this helper in templates.
  static const String name = "section";

  /// The special marker prefix for section start.
  static const String startMarkerPrefix = "<<<dotprompt:section:";

  /// The special marker for section end.
  static const String endMarker = "<<<dotprompt:section:end>>>";

  /// The special marker suffix used in rendered output.
  static const String markerSuffix = ">>>";

  /// Creates a section start marker.
  static String createStartMarker(String sectionName) =>
      "$startMarkerPrefix$sectionName$markerSuffix";

  /// Creates a section end marker.
  static String createEndMarker() => endMarker;

  /// Checks if a string contains section markers.
  static bool containsMarker(String text) =>
      text.contains(startMarkerPrefix) || text.contains(endMarker);

  /// Extracts the section name from a start marker.
  static String? extractSectionName(String marker) {
    if (!marker.startsWith(startMarkerPrefix) ||
        !marker.endsWith(markerSuffix)) {
      return null;
    }
    return marker.substring(
      startMarkerPrefix.length,
      marker.length - markerSuffix.length,
    );
  }
}
