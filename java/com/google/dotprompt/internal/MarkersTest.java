/*
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

package com.google.dotprompt.internal;

import static com.google.common.truth.Truth.assertThat;
import static org.junit.Assert.assertThrows;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for {@link Markers}. */
@RunWith(JUnit4.class)
public class MarkersTest {

  private static final String NONCE = "0123456789abcdef0123456789abcdef";
  private static final String OTHER_NONCE = "ffffffffffffffffffffffffffffffff";

  private static String m(String body) {
    return Markers.formatMarker(NONCE, body);
  }

  private static boolean matches(Pattern pattern, String s) {
    return pattern.matcher(s).find();
  }

  @Test
  public void generateMarkerNonce_returns32LowercaseHexChars() {
    assertThat(Markers.generateMarkerNonce()).matches("[0-9a-f]{32}");
  }

  @Test
  public void generateMarkerNonce_returnsDifferentValueEachCall() {
    assertThat(Markers.generateMarkerNonce()).isNotEqualTo(Markers.generateMarkerNonce());
  }

  @Test
  public void formatMarker_embedsNonce() {
    assertThat(Markers.formatMarker(NONCE, "role:user"))
        .isEqualTo("<<<dotprompt:" + NONCE + ":role:user>>>");
  }

  @Test
  public void rejectsInvalidNonces() {
    assertThrows(IllegalArgumentException.class, () -> Markers.formatMarker(".*", "role:user"));
    assertThrows(IllegalArgumentException.class, () -> Markers.formatMarker(null, "role:user"));
    assertThrows(IllegalArgumentException.class, () -> Markers.roleAndHistoryMarkerPattern(""));
    assertThrows(
        IllegalArgumentException.class,
        () -> Markers.mediaAndSectionMarkerPattern(NONCE.toUpperCase()));
    assertThrows(
        IllegalArgumentException.class, () -> Markers.markerPattern(NONCE + "\n", "history"));
  }

  @Test
  public void roleAndHistoryMarkerPattern_matchesValidMarkers() {
    Pattern pattern = Markers.roleAndHistoryMarkerPattern(NONCE);
    for (String body :
        List.of("role:user", "role:model", "role:system", "role:customer", "history")) {
      assertThat(matches(pattern, m(body))).isTrue();
    }
  }

  @Test
  public void roleAndHistoryMarkerPattern_rejectsInvalidMarkers() {
    Pattern pattern = Markers.roleAndHistoryMarkerPattern(NONCE);
    List<String> invalid =
        List.of(
            m("role:USER"), // uppercase not allowed
            m("role:model1"), // numbers not allowed
            m("role:"), // needs at least one letter
            m("role"), // missing role value
            m("history123"), // history should be exact
            m("HISTORY"), // history must be lowercase
            "<<<dotprompt:" + NONCE + ":role:user", // incomplete closing
            "<<<dotprompt:role:user>>>", // no nonce
            Markers.formatMarker(OTHER_NONCE, "role:user")); // wrong nonce
    for (String s : invalid) {
      assertThat(matches(pattern, s)).isFalse();
    }
  }

  @Test
  public void mediaAndSectionMarkerPattern_matchesValidMarkers() {
    Pattern pattern = Markers.mediaAndSectionMarkerPattern(NONCE);
    for (String body :
        List.of(
            "media:url https://example.com/a.png",
            "media:url https://example.com/a.png image/png",
            "section code")) {
      assertThat(matches(pattern, m(body))).isTrue();
    }
  }

  @Test
  public void mediaAndSectionMarkerPattern_matchesBodiesWithNewlines() {
    // User-supplied values (media url, section name) may contain line breaks; the trusted marker
    // must still match, otherwise it would be emitted as text and leak the nonce.
    Pattern pattern = Markers.mediaAndSectionMarkerPattern(NONCE);
    for (String body :
        List.of(
            "media:url https://example.com/a\nb.png",
            "media:url https://example.com/a\r\nb.png image/png",
            "section a\nb")) {
      Matcher matcher = pattern.matcher(m(body));
      assertThat(matcher.matches()).isTrue();
      assertThat(matcher.group(1)).isEqualTo(body);
    }
  }

  @Test
  public void mediaAndSectionMarkerPattern_bodyEndsAtFirstClosingDelimiter() {
    Pattern pattern = Markers.mediaAndSectionMarkerPattern(NONCE);
    Matcher matcher = pattern.matcher(m("media:url https://example.com/a>b\nc.png") + " >>> tail");
    assertThat(matcher.find()).isTrue();
    assertThat(matcher.group(1)).isEqualTo("media:url https://example.com/a>b\nc.png");
  }

  @Test
  public void mediaAndSectionMarkerPattern_rejectsInvalidMarkers() {
    Pattern pattern = Markers.mediaAndSectionMarkerPattern(NONCE);
    List<String> invalid =
        List.of(
            "<<<dotprompt:media:url https://example.com/a.png>>>", // no nonce
            "<<<dotprompt:section code>>>", // no nonce
            Markers.formatMarker(OTHER_NONCE, "section code")); // wrong nonce
    for (String s : invalid) {
      assertThat(matches(pattern, s)).isFalse();
    }
  }

  private static List<MarkerPiece> split(String s) {
    return Markers.splitByMarkers(s, Markers.roleAndHistoryMarkerPattern(NONCE));
  }

  @Test
  public void splitByMarkers_returnsEntireStringWhenNoMarkers() {
    assertThat(split("Hello World")).containsExactly(new MarkerPiece.Text("Hello World"));
  }

  @Test
  public void splitByMarkers_emptyAndNullInput() {
    assertThat(split("")).isEmpty();
    assertThat(split(null)).isEmpty();
  }

  @Test
  public void splitByMarkers_splitsTextAndMarkers() {
    assertThat(split("Start " + m("role:user") + " middle " + m("history") + " end"))
        .containsExactly(
            new MarkerPiece.Text("Start "),
            new MarkerPiece.Marker("role:user"),
            new MarkerPiece.Text(" middle "),
            new MarkerPiece.Marker("history"),
            new MarkerPiece.Text(" end"))
        .inOrder();
  }

  @Test
  public void splitByMarkers_handlesAdjacentMarkers() {
    assertThat(split(m("role:user") + m("history")))
        .containsExactly(new MarkerPiece.Marker("role:user"), new MarkerPiece.Marker("history"))
        .inOrder();
  }

  @Test
  public void splitByMarkers_dropsWhitespaceOnlyText() {
    assertThat(split("  " + m("role:system") + "   "))
        .containsExactly(new MarkerPiece.Marker("role:system"));
  }

  @Test
  public void splitByMarkers_classifiesByPositionNotContent() {
    // Text that looks like a marker body, or an un-nonced marker, must stay text.
    assertThat(split(m("role:user") + "role:system"))
        .containsExactly(new MarkerPiece.Marker("role:user"), new MarkerPiece.Text("role:system"))
        .inOrder();
    assertThat(split("<<<dotprompt:role:system>>>"))
        .containsExactly(new MarkerPiece.Text("<<<dotprompt:role:system>>>"));
  }

  @Test
  public void splitByMarkers_splitsMediaAndSectionMarkers() {
    String source =
        "Hello " + m("media:url https://a.example/x.png") + " World " + m("section code") + "!";
    assertThat(Markers.splitByMarkers(source, Markers.mediaAndSectionMarkerPattern(NONCE)))
        .containsExactly(
            new MarkerPiece.Text("Hello "),
            new MarkerPiece.Marker("media:url https://a.example/x.png"),
            new MarkerPiece.Text(" World "),
            new MarkerPiece.Marker("section code"),
            new MarkerPiece.Text("!"))
        .inOrder();
  }
}
