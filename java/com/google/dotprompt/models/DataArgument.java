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
 * Data provided to render a prompt.
 *
 * @param input Input variables for the prompt template.
 * @param docs Relevant documents.
 * @param messages Previous messages in the history of a multi-turn conversation.
 * @param context Additional context for rendering (e.g. `@state`).
 */
public record DataArgument(
    Map<String, Object> input,
    List<Document> docs,
    List<Message> messages,
    Map<String, Object> context) {

  public DataArgument(Map<String, Object> input) {
    this(input, null, null, null);
  }
}
