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

/**
 * Represents a prompt's data including its source code.
 *
 * @param name The name of the prompt.
 * @param variant The variant name for the prompt.
 * @param version The version of the prompt.
 * @param source The source code of the prompt.
 */
public record PromptData(String name, String variant, String version, String source) {
  public PromptData(String name, String source) {
    this(name, null, null, source);
  }
}
