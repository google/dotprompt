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
///
/// ## Markers
///
/// The helper emits `<<<dotprompt:{nonce}:media:url {url} {contentType}>>>`,
/// where `nonce` is the per-render nonce that the part splitter also uses.
/// Markers without the right nonce (e.g. typed by an end user) stay plain
/// text, so user input can't inject media parts with arbitrary URLs.
///
/// When `contentType` is omitted it is inferred from the URL extension
/// (falling back to `application/octet-stream`).
library;

import "package:meta/meta.dart";

import "../markers.dart";
import "../types.dart";

/// Content type used when none is given and none can be inferred.
const String _defaultContentType = "application/octet-stream";

/// Marker class for the media helper.
///
/// This helper creates media markers that are converted to MediaPart
/// objects during message processing.
class MediaHelper {
  /// Private constructor to prevent instantiation.
  MediaHelper._();

  /// The name of this helper in templates.
  static const String name = "media";

  /// Creates a media marker for [url] and [contentType] carrying the
  /// per-render [nonce].
  ///
  /// Throws [ArgumentError] if [nonce] is not 32 lowercase hex chars.
  ///
  /// Internal: only the renderer holds the per-render nonce, so this is not
  /// usable from outside `package:dotprompt`.
  @internal
  static String createMarker(String nonce, {required String url, String? contentType}) {
    final ct = contentType ?? _inferContentType(url);
    return formatMarker(nonce, "$mediaMarkerBodyPrefix$url $ct");
  }

  /// Extracts media content from a marker body
  /// (`media:url {url} [{contentType}]`), as produced by splitting with
  /// [mediaAndSectionMarkerRegex].
  ///
  /// The URL ends at the first space; everything after it is the content
  /// type, which may itself contain spaces (e.g. `text/plain; charset=utf-8`).
  ///
  /// Returns null if [body] is not a media marker body.
  ///
  /// Internal: marker bodies only come from splitting with the per-render
  /// nonce, so this is not meaningful outside `package:dotprompt`.
  @internal
  static MediaContent? mediaFromBody(String body) {
    if (!body.startsWith(mediaMarkerBodyPrefix)) return null;
    final rest = body.substring(mediaMarkerBodyPrefix.length);
    final space = rest.indexOf(" ");
    if (space < 0) {
      return MediaContent(url: rest, contentType: _defaultContentType);
    }
    return MediaContent(url: rest.substring(0, space), contentType: rest.substring(space + 1));
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
    return _defaultContentType;
  }
}
