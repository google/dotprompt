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

import com.fasterxml.jackson.annotation.JsonValue;

/** Represents the role of a message sender in a conversation. */
public enum Role {
  /** User role. */
  USER("user"),
  /** Model (AI) role. */
  MODEL("model"),
  /** Tool role. */
  TOOL("tool"),
  /** System role. */
  SYSTEM("system");

  private final String value;

  Role(String value) {
    this.value = value;
  }

  /**
   * Returns the string representation of the role.
   *
   * @return The role name.
   */
  @JsonValue
  public String getValue() {
    return value;
  }

  /**
   * Parses a string into a Role enum.
   *
   * @param value The string value (case-insensitive).
   * @return The corresponding Role, or USER if invalid/null.
   */
  public static Role fromString(String value) {
    if (value == null) {
      return Role.USER;
    }
    try {
      return Role.valueOf(value.toUpperCase());
    } catch (IllegalArgumentException e) {
      return Role.USER;
    }
  }
}
