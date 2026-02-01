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
library;

/// Marker class for the section helper.
///
/// This helper creates section markers that are converted to MetadataPart
/// objects during message processing.
class SectionHelper {
  /// Private constructor to prevent instantiation.
  SectionHelper._();

  /// The name of this helper in templates.
  static const String name = "section";

  /// The special marker prefix used in rendered output.
  static const String markerPrefix = "<<<dotprompt:section ";

  /// The special marker suffix used in rendered output.
  static const String markerSuffix = ">>>";

  /// Creates a section marker for the given section name.
  static String createMarker(String sectionName) => "$markerPrefix$sectionName$markerSuffix";

  /// Checks if a string contains a section marker.
  static bool containsMarker(String text) => text.contains(markerPrefix);

  /// Extracts the section name from a marker string.
  ///
  /// Returns null if the marker is invalid.
  static String? extractSectionName(String marker) {
    if (!marker.startsWith(markerPrefix) || !marker.endsWith(markerSuffix)) {
      return null;
    }
    return marker.substring(
      markerPrefix.length,
      marker.length - markerSuffix.length,
    );
  }
}
