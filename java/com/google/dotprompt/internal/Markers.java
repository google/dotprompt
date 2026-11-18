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

import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * In-band markers used to turn a rendered template string into messages.
 *
 * <p><b>Internal implementation detail, not a public API.</b> This class may change or be removed
 * in any release with no compatibility guarantees. It is {@code public} only so the {@code
 * helpers}, {@code parser} and root dotprompt packages can share it; emitting markers from custom
 * helpers is not supported.
 *
 * <p>The {@code role}, {@code history}, {@code section} and {@code media} helpers emit markers into
 * the rendered string, which is then split back apart into messages and parts. Because the rendered
 * string also contains user-supplied variable values verbatim, every marker carries a random
 * per-render nonce and the splitter only honors markers with that nonce. Anything else that merely
 * looks like a marker (e.g. typed by an end user) stays plain text.
 *
 * <pre>
 *  Marker format: &lt;&lt;&lt;dotprompt:{nonce}:{body}&gt;&gt;&gt;
 *
 *  ┌─────────────────────────────────┬───────────────────────────────────┐
 *  │ Body                            │ Emitted by                        │
 *  ├─────────────────────────────────┼───────────────────────────────────┤
 *  │ role:{name}                     │ {{role "name"}}                   │
 *  │ history                         │ {{history}}                       │
 *  │ section {name}                  │ {{section "name"}}                │
 *  │ media:url {url} [{contentType}] │ {{media url=... contentType=...}} │
 *  └─────────────────────────────────┴───────────────────────────────────┘
 *
 *  nonce: 32 lowercase hex chars (128 bits from SecureRandom), fresh per render.
 *  body:  may contain any character, including newlines (from user-supplied values),
 *         and ends at the first &gt;&gt;&gt;.
 * </pre>
 *
 * <p>Example:
 *
 * <pre>{@code
 * String nonce = Markers.generateMarkerNonce();
 * String rendered = "Hi" + Markers.formatMarker(nonce, "role:model") + "Hello";
 * List<MarkerPiece> pieces =
 *     Markers.splitByMarkers(rendered, Markers.roleAndHistoryMarkerPattern(nonce));
 * // [Text("Hi"), Marker("role:model"), Text("Hello")]
 * }</pre>
 */
public final class Markers {

  /**
   * Key under which the per-render nonce is stored in the Handlebars data frame (readable by
   * helpers via {@code options.data(MARKER_NONCE_DATA_KEY)}). Written after the user-supplied
   * {@code context} entries so they can't override it.
   */
  public static final String MARKER_NONCE_DATA_KEY = "__dotpromptMarkerNonce";

  private static final Pattern NONCE_PATTERN = Pattern.compile("[0-9a-f]{32}");

  private static final int NONCE_BYTES = 16;

  // SecureRandom is thread-safe; one shared instance avoids reseeding per render.
  private static final SecureRandom RANDOM = new SecureRandom();

  private static final HexFormat HEX = HexFormat.of();

  private Markers() {}

  /**
   * Generates a fresh 128-bit nonce as 32 lowercase hex chars. Call once per render.
   *
   * @return The nonce.
   */
  public static String generateMarkerNonce() {
    byte[] bytes = new byte[NONCE_BYTES];
    RANDOM.nextBytes(bytes);
    return HEX.formatHex(bytes);
  }

  /**
   * Formats a marker with the given nonce and body.
   *
   * @param nonce The per-render nonce.
   * @param body The marker body, e.g. {@code role:user}.
   * @return The marker string.
   * @throws IllegalArgumentException If the nonce is not 32 lowercase hex chars.
   */
  public static String formatMarker(String nonce, String body) {
    checkNonce(nonce);
    return "<<<dotprompt:" + nonce + ":" + body + ">>>";
  }

  /**
   * Builds a pattern matching markers with the given nonce whose body matches {@code bodyRegex}.
   * The pattern has exactly one capture group: the marker body.
   *
   * <p>The pattern is compiled with {@link Pattern#DOTALL}, so {@code .} in {@code bodyRegex} also
   * matches line breaks. Bodies embed user-supplied values (media URLs, section names) that may
   * contain newlines; without DOTALL such a trusted marker would not match and would be emitted as
   * text, leaking the nonce. Use a lazy quantifier ({@code .*?}) so the body ends at the first
   * {@code >>>}.
   *
   * @param nonce The per-render nonce.
   * @param bodyRegex Regex for the marker body. Must not contain capture groups (use {@code (?:
   *     ...)}), otherwise {@link #splitByMarkers} would read the wrong group.
   * @return The compiled pattern.
   * @throws IllegalArgumentException If the nonce is not 32 lowercase hex chars.
   */
  public static Pattern markerPattern(String nonce, String bodyRegex) {
    checkNonce(nonce);
    return Pattern.compile("<<<dotprompt:" + nonce + ":(" + bodyRegex + ")>>>", Pattern.DOTALL);
  }

  /**
   * Matches role and history markers for the given nonce. The capture group is the marker body
   * ({@code role:user}, {@code history}). Only lowercase letters are allowed in role names.
   *
   * @param nonce The per-render nonce.
   * @return The compiled pattern.
   * @throws IllegalArgumentException If the nonce is not 32 lowercase hex chars.
   */
  public static Pattern roleAndHistoryMarkerPattern(String nonce) {
    return markerPattern(nonce, "role:[a-z]+|history");
  }

  /**
   * Matches media and section markers for the given nonce. The capture group is the marker body
   * ({@code media:url https://... image/png}, {@code section code}), which may span lines and ends
   * at the first {@code >>>}.
   *
   * @param nonce The per-render nonce.
   * @return The compiled pattern.
   * @throws IllegalArgumentException If the nonce is not 32 lowercase hex chars.
   */
  public static Pattern mediaAndSectionMarkerPattern(String nonce) {
    return markerPattern(nonce, "(?:media:url|section) .*?");
  }

  /**
   * Splits {@code source} on markers matched by {@code pattern}, which must have exactly one
   * capture group (the marker body), as built by {@link #markerPattern}.
   *
   * <p>Pieces are classified by position (inside vs. between matches), never by content, so text
   * that happens to look like a marker or marker body stays text. Whitespace-only text pieces are
   * dropped.
   *
   * @param source The rendered string; null or empty yields an empty list.
   * @param pattern The marker pattern.
   * @return The pieces in order.
   */
  public static List<MarkerPiece> splitByMarkers(String source, Pattern pattern) {
    List<MarkerPiece> pieces = new ArrayList<>();
    if (source == null || source.isEmpty()) {
      return pieces;
    }
    Matcher matcher = pattern.matcher(source);
    int lastEnd = 0;
    while (matcher.find()) {
      addText(pieces, source.substring(lastEnd, matcher.start()));
      pieces.add(new MarkerPiece.Marker(matcher.group(1)));
      lastEnd = matcher.end();
    }
    addText(pieces, source.substring(lastEnd));
    return pieces;
  }

  private static void addText(List<MarkerPiece> pieces, String text) {
    if (!text.trim().isEmpty()) {
      pieces.add(new MarkerPiece.Text(text));
    }
  }

  private static void checkNonce(String nonce) {
    // The nonce is interpolated into a regex, so keep it strictly hex.
    if (nonce == null || !NONCE_PATTERN.matcher(nonce).matches()) {
      throw new IllegalArgumentException("dotprompt: invalid marker nonce");
    }
  }
}
