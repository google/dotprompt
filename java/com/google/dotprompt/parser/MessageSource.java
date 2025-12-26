/*
 * Copyright 2025 Google LLC
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

import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.Role;
import java.util.List;
import java.util.Map;

/**
 * A message with a source string and optional content and metadata.
 *
 * <p>This is an intermediate representation used during template parsing before converting to final
 * Message objects. It matches the structure of the {@code MessageSource} type in the JavaScript and
 * Python implementations.
 *
 * <p>This class is mutable to allow building up the source string during parsing. The role can also
 * be updated after construction as the parser discovers role markers.
 *
 * @see Parser#toMessages(String)
 */
public final class MessageSource {
  /** The role of the message (user, model, system, tool). */
  Role role;

  /** The source text of the message. */
  String source;

  /** The parsed content parts. */
  List<Part> content;

  /** Additional metadata for the message. */
  Map<String, Object> metadata;

  /**
   * Creates a new message source with the given role and source text.
   *
   * @param role The role of the message.
   * @param source The source text.
   */
  public MessageSource(Role role, String source) {
    this.role = role;
    this.source = source;
    this.content = null;
    this.metadata = null;
  }

  /**
   * Creates a new message source with the given role, content, and metadata.
   *
   * <p>This constructor is used when creating message sources from existing Message objects (e.g.,
   * for history messages).
   *
   * @param role The role of the message.
   * @param content The parsed content parts.
   * @param metadata Additional metadata.
   */
  public MessageSource(Role role, List<Part> content, Map<String, Object> metadata) {
    this.role = role;
    this.source = null;
    this.content = content;
    this.metadata = metadata;
  }

  /**
   * Returns the role of the message.
   *
   * @return The role.
   */
  public Role role() {
    return role;
  }

  /**
   * Returns the source text of the message.
   *
   * @return The source text, may be null.
   */
  public String source() {
    return source;
  }

  /**
   * Returns the parsed content parts.
   *
   * @return The content parts, may be null.
   */
  public List<Part> content() {
    return content;
  }

  /**
   * Returns the metadata.
   *
   * @return The metadata, may be null.
   */
  public Map<String, Object> metadata() {
    return metadata;
  }
}
