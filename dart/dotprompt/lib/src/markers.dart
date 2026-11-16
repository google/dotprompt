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

/// In-band markers used to turn a rendered template string into messages.
///
/// The `role`, `history`, `section` and `media` helpers emit markers into the
/// rendered string, which is then split back apart into messages and parts.
/// Because the rendered string also contains user-supplied variable values
/// verbatim, every marker carries a random per-render nonce and the splitter
/// only honors markers with that nonce. Anything else that merely looks like
/// a marker (e.g. typed by an end user) stays plain text.
///
/// ## Marker format
///
/// ```text
/// <<<dotprompt:{nonce}:{body}>>>
///
/// nonce: 32 lowercase hex chars (128 bits), fresh per render
/// body:  role:{name} | history | section {name} | media:url {url} {contentType}
/// ```
///
/// ## Flow
///
/// ```text
/// render() --nonce--> helpers --markers--> rendered string
///    |                                          |
///    +--nonce--> splitByMarkers(regex(nonce)) <-+
///                       |
///          [TextPiece | MarkerBodyPiece, ...]
/// ```
///
/// ## Visibility
///
/// This library is internal: it is deliberately not exported from
/// `package:dotprompt` (keep it that way). The nonce-taking members of the
/// exported `RoleHelper`, `HistoryHelper`, `SectionHelper` and `MediaHelper`
/// are annotated `@internal` for the same reason.
library;

import "dart:math";

import "package:meta/meta.dart";

/// Marker body prefix for role markers (`role:{name}`).
const String roleMarkerBodyPrefix = "role:";

/// Marker body for history markers.
const String historyMarkerBody = "history";

/// Marker body prefix for section markers (`section {name}`).
const String sectionMarkerBodyPrefix = "section ";

/// Marker body prefix for media markers (`media:url {url} {contentType}`).
const String mediaMarkerBodyPrefix = "media:url ";

final RegExp _noncePattern = RegExp(r"^[0-9a-f]{32}$");

/// Generates a fresh 128-bit nonce as 32 lowercase hex chars using a CSPRNG.
///
/// Call once per render; never reuse a nonce across renders.
String generateMarkerNonce() {
  final random = Random.secure();
  final buffer = StringBuffer();
  for (var i = 0; i < 16; i++) {
    buffer.write(random.nextInt(256).toRadixString(16).padLeft(2, "0"));
  }
  return buffer.toString();
}

/// Throws [ArgumentError] unless [nonce] is 32 lowercase hex chars.
///
/// The nonce is interpolated into a [RegExp], so it must stay strictly hex.
void _checkNonce(String nonce) {
  if (!_noncePattern.hasMatch(nonce)) {
    throw ArgumentError.value(nonce, "nonce", "Invalid dotprompt marker nonce");
  }
}

/// Formats a marker carrying [nonce] and [body].
///
/// Throws [ArgumentError] if [nonce] is not 32 lowercase hex chars.
///
/// ```dart
/// formatMarker(nonce, "role:user"); // <<<dotprompt:{nonce}:role:user>>>
/// ```
String formatMarker(String nonce, String body) {
  _checkNonce(nonce);
  return "<<<dotprompt:$nonce:$body>>>";
}

/// Matches role and history markers carrying [nonce].
///
/// The single capture group is the marker body (`role:user`, `history`).
/// Role names may be any run of characters other than `>`; they are resolved
/// case-insensitively by `Role.fromString` when converting to messages.
///
/// Throws [ArgumentError] if [nonce] is not 32 lowercase hex chars.
RegExp roleAndHistoryMarkerRegex(String nonce) {
  _checkNonce(nonce);
  return RegExp("<<<dotprompt:$nonce:($roleMarkerBodyPrefix[^>]+|$historyMarkerBody)>>>");
}

/// Matches media and section markers carrying [nonce].
///
/// The single capture group is the marker body
/// (`media:url https://... image/png`, `section code`).
///
/// The body is matched lazily up to the first `>>>`, across newlines
/// (`dotAll`): media URLs and section names come from template data, and a
/// newline in one must not make the trusted marker fall through as text
/// (which would drop the part and leak the nonce into the output).
///
/// Throws [ArgumentError] if [nonce] is not 32 lowercase hex chars.
RegExp mediaAndSectionMarkerRegex(String nonce) {
  _checkNonce(nonce);
  return RegExp("<<<dotprompt:$nonce:((?:media:url|section) .*?)>>>", dotAll: true);
}

/// A piece of a rendered string: either literal text or a trusted marker.
@immutable
sealed class MarkerPiece {
  const MarkerPiece();
}

/// Literal text between markers.
final class TextPiece extends MarkerPiece {
  /// Creates a [TextPiece].
  const TextPiece(this.text);

  /// The literal text.
  final String text;

  @override
  bool operator ==(Object other) => other is TextPiece && text == other.text;

  @override
  int get hashCode => text.hashCode;

  @override
  String toString() => "TextPiece($text)";
}

/// A marker that carried the expected nonce.
final class MarkerBodyPiece extends MarkerPiece {
  /// Creates a [MarkerBodyPiece].
  const MarkerBodyPiece(this.body);

  /// The marker body, e.g. `role:user` or `section code`.
  final String body;

  @override
  bool operator ==(Object other) => other is MarkerBodyPiece && body == other.body;

  @override
  int get hashCode => body.hashCode;

  @override
  String toString() => "MarkerBodyPiece($body)";
}

/// Splits [source] on markers matched by [regex], which must have exactly
/// one capture group (the marker body).
///
/// Pieces are classified by match position rather than content: whatever a
/// match covers is a marker, everything between matches is text. Text that
/// merely looks like a marker (or a marker body) stays text.
///
/// Empty text pieces are dropped. Unlike the JS implementation,
/// whitespace-only text is kept, because the Dart runtime has always
/// preserved it in message parts.
///
/// Throws [ArgumentError] if [regex] does not have exactly one group.
List<MarkerPiece> splitByMarkers(String source, RegExp regex) {
  final pieces = <MarkerPiece>[];
  var lastEnd = 0;
  for (final match in regex.allMatches(source)) {
    if (match.groupCount != 1) {
      throw ArgumentError.value(regex.pattern, "regex", "Must have exactly one capture group");
    }
    if (match.start > lastEnd) {
      pieces.add(TextPiece(source.substring(lastEnd, match.start)));
    }
    pieces.add(MarkerBodyPiece(match.group(1)!));
    lastEnd = match.end;
  }
  if (lastEnd < source.length) {
    pieces.add(TextPiece(source.substring(lastEnd)));
  }
  return pieces;
}
