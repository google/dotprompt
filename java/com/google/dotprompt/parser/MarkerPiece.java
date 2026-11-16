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

package com.google.dotprompt.parser;

/**
 * A piece of a rendered template string: either literal text or a trusted marker.
 *
 * <p>Produced by {@link Markers#splitByMarkers}. A {@link Marker} is only ever produced for a
 * marker carrying the per-render nonce, so its body can be trusted; everything else is {@link
 * Text}.
 */
public sealed interface MarkerPiece permits MarkerPiece.Text, MarkerPiece.Marker {

  /**
   * Literal text between markers.
   *
   * @param text The text, never whitespace-only.
   */
  record Text(String text) implements MarkerPiece {}

  /**
   * A trusted marker.
   *
   * @param body The marker body, e.g. {@code role:user}, {@code history}, {@code section code} or
   *     {@code media:url https://example.com/a.png image/png}.
   */
  record Marker(String body) implements MarkerPiece {}
}
