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

package com.google.dotprompt.models;

import java.util.List;
import java.util.Map;

/**
 * Represents a chat message in a prompt.
 *
 * @param role The role of the message sender (user, model, etc.).
 * @param content The list of parts forming the message content.
 * @param metadata Arbitrary metadata.
 */
public record Message(Role role, List<Part> content, Map<String, Object> metadata) {
  public Message(Role role, List<Part> content) {
    this(role, content, null);
  }
}
