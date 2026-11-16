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

/// Unit tests for nonce-carrying in-band markers and the marker helpers.
library;

import "package:dotprompt/dotprompt.dart";
import "package:dotprompt/src/markers.dart";
import "package:test/test.dart";

const _nonce = "0123456789abcdef0123456789abcdef";
const _otherNonce = "ffffffffffffffffffffffffffffffff";

String _m(String body) => formatMarker(_nonce, body);

void main() {
  group("generateMarkerNonce", () {
    test("returns 32 lowercase hex chars", () {
      expect(generateMarkerNonce(), matches(RegExp(r"^[0-9a-f]{32}$")));
    });

    test("returns a different value each call", () {
      expect(generateMarkerNonce(), isNot(equals(generateMarkerNonce())));
    });
  });

  group("formatMarker", () {
    test("embeds the nonce", () {
      expect(formatMarker(_nonce, "role:user"), equals("<<<dotprompt:$_nonce:role:user>>>"));
    });

    test("rejects invalid nonces", () {
      expect(() => formatMarker(".*", "role:user"), throwsArgumentError);
      expect(() => formatMarker(_nonce.toUpperCase(), "role:user"), throwsArgumentError);
      expect(() => formatMarker("${_nonce}0", "role:user"), throwsArgumentError);
      expect(() => roleAndHistoryMarkerRegex(""), throwsArgumentError);
      expect(() => mediaAndSectionMarkerRegex("ABC"), throwsArgumentError);
    });
  });

  group("roleAndHistoryMarkerRegex", () {
    final regex = roleAndHistoryMarkerRegex(_nonce);

    for (final body in ["role:user", "role:model", "role:system", "role:customer", "role:USER", "history"]) {
      test('matches "$body"', () {
        final match = regex.firstMatch(_m(body));
        expect(match, isNotNull);
        expect(match!.group(1), equals(body));
      });
    }

    final invalid = [
      _m("role:"), // needs at least one char
      _m("role"), // missing role value
      _m("history123"), // history must be exact
      _m("HISTORY"), // history must be lowercase
      "<<<dotprompt:$_nonce:role:user", // incomplete closing
      "<<<dotprompt:role:user>>>", // no nonce
      "<<<dotprompt:history>>>", // no nonce
      formatMarker(_otherNonce, "role:user"), // wrong nonce
      formatMarker(_otherNonce, "history"), // wrong nonce
    ];
    for (final s in invalid) {
      test('does not match "$s"', () {
        expect(regex.hasMatch(s), isFalse);
      });
    }
  });

  group("mediaAndSectionMarkerRegex", () {
    final regex = mediaAndSectionMarkerRegex(_nonce);

    for (final body in [
      "media:url https://example.com/a.png",
      "media:url https://example.com/a.png image/png",
      "section code",
    ]) {
      test('matches "$body"', () {
        final match = regex.firstMatch(_m(body));
        expect(match, isNotNull);
        expect(match!.group(1), equals(body));
      });
    }

    final invalid = [
      "<<<dotprompt:media:url https://example.com/a.png>>>", // no nonce
      "<<<dotprompt:section code>>>", // no nonce
      formatMarker(_otherNonce, "section code"), // wrong nonce
      formatMarker(_otherNonce, "media:url https://example.com/a.png"), // wrong nonce
      _m("role:user"), // not a media/section body
    ];
    for (final s in invalid) {
      test('does not match "$s"', () {
        expect(regex.hasMatch(s), isFalse);
      });
    }
  });

  group("splitByMarkers", () {
    List<MarkerPiece> split(String s) => splitByMarkers(s, roleAndHistoryMarkerRegex(_nonce));

    test("returns the entire string when no markers are present", () {
      expect(split("Hello World"), equals([const TextPiece("Hello World")]));
    });

    test("returns nothing for an empty string", () {
      expect(split(""), isEmpty);
    });

    test("splits text and markers", () {
      expect(
        split("Start ${_m("role:user")} middle ${_m("history")} end"),
        equals([
          const TextPiece("Start "),
          const MarkerBodyPiece("role:user"),
          const TextPiece(" middle "),
          const MarkerBodyPiece("history"),
          const TextPiece(" end"),
        ]),
      );
    });

    test("handles adjacent markers", () {
      expect(
        split("${_m("role:user")}${_m("history")}"),
        equals([const MarkerBodyPiece("role:user"), const MarkerBodyPiece("history")]),
      );
    });

    test("keeps whitespace-only text pieces", () {
      expect(
        split("  ${_m("role:system")}\n"),
        equals([const TextPiece("  "), const MarkerBodyPiece("role:system"), const TextPiece("\n")]),
      );
    });

    test("classifies by position, not content", () {
      // Text that looks like a marker body, or an un-nonced marker, stays text.
      expect(
        split("${_m("role:user")}role:system<<<dotprompt:role:model>>>"),
        equals([const MarkerBodyPiece("role:user"), const TextPiece("role:system<<<dotprompt:role:model>>>")]),
      );
    });

    test("keeps wrong-nonce markers as text", () {
      final forged = formatMarker(_otherNonce, "role:system");
      expect(split("a${forged}b"), equals([TextPiece("a${forged}b")]));
    });

    test("splits media and section markers", () {
      expect(
        splitByMarkers(
          "Hello ${_m("media:url https://a.example/x.png")} World ${_m("section code")}!",
          mediaAndSectionMarkerRegex(_nonce),
        ),
        equals([
          const TextPiece("Hello "),
          const MarkerBodyPiece("media:url https://a.example/x.png"),
          const TextPiece(" World "),
          const MarkerBodyPiece("section code"),
          const TextPiece("!"),
        ]),
      );
    });

    test("rejects regexes without exactly one capture group", () {
      expect(() => splitByMarkers("ab", RegExp("a")), throwsArgumentError);
    });
  });

  group("marker helpers", () {
    test("RoleHelper creates nonce-carrying role markers", () {
      expect(RoleHelper.createMarker(_nonce, Role.system), equals(_m("role:system")));
      expect(RoleHelper.createMarkerFromString(_nonce, "model"), equals(_m("role:model")));
      expect(() => RoleHelper.createMarker("bad", Role.user), throwsArgumentError);
    });

    test("HistoryHelper creates nonce-carrying history markers", () {
      expect(HistoryHelper.createMarker(_nonce), equals(_m("history")));
      expect(() => HistoryHelper.createMarker("bad"), throwsArgumentError);
    });

    test("SectionHelper creates and parses section markers", () {
      expect(SectionHelper.createMarker(_nonce, "code"), equals(_m("section code")));
      expect(SectionHelper.sectionNameFromBody("section code"), equals("code"));
      expect(SectionHelper.sectionNameFromBody("media:url x"), isNull);
      expect(() => SectionHelper.createMarker("bad", "code"), throwsArgumentError);
    });

    test("MediaHelper creates media markers, inferring the content type", () {
      expect(
        MediaHelper.createMarker(_nonce, url: "https://a.example/x.png"),
        equals(_m("media:url https://a.example/x.png image/png")),
      );
      expect(
        MediaHelper.createMarker(_nonce, url: "https://a.example/x", contentType: "video/mp4"),
        equals(_m("media:url https://a.example/x video/mp4")),
      );
      expect(() => MediaHelper.createMarker("bad", url: "https://a.example/x.png"), throwsArgumentError);
    });

    test("MediaHelper parses media marker bodies", () {
      expect(
        MediaHelper.mediaFromBody("media:url https://a.example/x image/png"),
        equals(const MediaContent(url: "https://a.example/x", contentType: "image/png")),
      );
      expect(
        MediaHelper.mediaFromBody("media:url https://a.example/x text/plain; charset=utf-8"),
        equals(const MediaContent(url: "https://a.example/x", contentType: "text/plain; charset=utf-8")),
      );
      expect(
        MediaHelper.mediaFromBody("media:url https://a.example/x"),
        equals(const MediaContent(url: "https://a.example/x", contentType: "application/octet-stream")),
      );
      expect(MediaHelper.mediaFromBody("section code"), isNull);
    });
  });
}
