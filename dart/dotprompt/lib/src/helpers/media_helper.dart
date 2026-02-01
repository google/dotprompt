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

/// Media helper for including media content in prompts.
///
/// The {{media}} helper embeds images, audio, or video in prompts.
///
/// ## Usage
///
/// ```handlebars
/// {{media url=imageUrl}}
/// {{media url="https://example.com/image.png" contentType="image/png"}}
/// ```
library;

import "../types.dart";

/// Marker class for the media helper.
///
/// This helper creates media markers that are converted to MediaPart
/// objects during message processing.
class MediaHelper {
  /// Private constructor to prevent instantiation.
  MediaHelper._();

  /// The name of this helper in templates.
  static const String name = "media";

  /// The special marker prefix used in rendered output.
  static const String markerPrefix = "<<<dotprompt:media:";

  /// The special marker suffix used in rendered output.
  static const String markerSuffix = ">>>";

  /// Creates a media marker for the given URL and content type.
  static String createMarker({required String url, String? contentType}) {
    final ct = contentType ?? _inferContentType(url);
    return "$markerPrefix$url|$ct$markerSuffix";
  }

  /// Checks if a string contains a media marker.
  static bool containsMarker(String text) => text.contains(markerPrefix);

  /// Extracts media content from a marker string.
  static MediaContent? extractMedia(String marker) {
    if (!marker.startsWith(markerPrefix) || !marker.endsWith(markerSuffix)) {
      return null;
    }
    final content = marker.substring(
      markerPrefix.length,
      marker.length - markerSuffix.length,
    );
    final parts = content.split("|");
    if (parts.isEmpty) return null;

    return MediaContent(
      url: parts[0],
      contentType: parts.length > 1 ? parts[1] : "application/octet-stream",
    );
  }

  /// Infers content type from URL extension.
  static String _inferContentType(String url) {
    final lower = url.toLowerCase();
    if (lower.endsWith(".png")) return "image/png";
    if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
    if (lower.endsWith(".gif")) return "image/gif";
    if (lower.endsWith(".webp")) return "image/webp";
    if (lower.endsWith(".svg")) return "image/svg+xml";
    if (lower.endsWith(".mp3")) return "audio/mpeg";
    if (lower.endsWith(".wav")) return "audio/wav";
    if (lower.endsWith(".mp4")) return "video/mp4";
    if (lower.endsWith(".webm")) return "video/webm";
    return "application/octet-stream";
  }
}
