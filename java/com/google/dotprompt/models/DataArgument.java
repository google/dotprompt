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
 * Data provided to render a prompt, matching the JS {@code DataArgument}.
 *
 * <p>Each kind of runtime data has its own field, so values in {@code input} (which often come from
 * end users) can never be mistaken for conversation history or {@code @} data:
 *
 * <pre>
 *  ┌──────────┬───────────────────────────────────────────────────────────┐
 *  │ Field    │ Exposed to the template as                                │
 *  ├──────────┼───────────────────────────────────────────────────────────┤
 *  │ input    │ template variables, e.g. {{name}}                         │
 *  │ context  │ @ data, e.g. context {state: ...} is @state               │
 *  │ messages │ conversation history, placed by {{history}} or inserted   │
 *  │ docs     │ relevant documents (not used by the renderer itself)      │
 *  └──────────┴───────────────────────────────────────────────────────────┘
 * </pre>
 *
 * <p>All fields are optional; {@code null} is treated as empty.
 *
 * <h2>Usage Example</h2>
 *
 * <pre>{@code
 * DataArgument data =
 *     DataArgument.builder()
 *         .input(Map.of("question", userQuestion))
 *         .messages(history)
 *         .context(Map.of("state", sessionState))
 *         .build();
 * RenderedPrompt rendered = dotprompt.render(source, data).get();
 * }</pre>
 *
 * @param input Input variables for the prompt template.
 * @param docs Relevant documents.
 * @param messages Previous messages in the history of a multi-turn conversation.
 * @param context Items exposed as {@code @} variables, e.g. {@code {state: {...}}} is exposed as
 *     {@code @state}.
 */
public record DataArgument(
    Map<String, Object> input,
    List<Document> docs,
    List<Message> messages,
    Map<String, Object> context) {

  /**
   * Creates a DataArgument that only carries template input variables.
   *
   * @param input Input variables for the prompt template.
   */
  public DataArgument(Map<String, Object> input) {
    this(input, null, null, null);
  }

  /**
   * Returns a new builder for a DataArgument.
   *
   * @return An empty builder.
   */
  public static Builder builder() {
    return new Builder();
  }

  /** Builder for {@link DataArgument}. Unset fields are {@code null}. */
  public static final class Builder {
    private Map<String, Object> input;
    private List<Document> docs;
    private List<Message> messages;
    private Map<String, Object> context;

    private Builder() {}

    /**
     * Sets the template input variables.
     *
     * @param input Input variables for the prompt template.
     * @return This builder.
     */
    public Builder input(Map<String, Object> input) {
      this.input = input;
      return this;
    }

    /**
     * Sets the relevant documents.
     *
     * @param docs Relevant documents.
     * @return This builder.
     */
    public Builder docs(List<Document> docs) {
      this.docs = docs;
      return this;
    }

    /**
     * Sets the conversation history.
     *
     * @param messages Previous messages in the conversation.
     * @return This builder.
     */
    public Builder messages(List<Message> messages) {
      this.messages = messages;
      return this;
    }

    /**
     * Sets the items exposed as {@code @} variables.
     *
     * @param context Context items, e.g. {@code Map.of("state", state)} for {@code @state}.
     * @return This builder.
     */
    public Builder context(Map<String, Object> context) {
      this.context = context;
      return this;
    }

    /**
     * Builds the DataArgument.
     *
     * @return A new DataArgument with the values set on this builder.
     */
    public DataArgument build() {
      return new DataArgument(input, docs, messages, context);
    }
  }
}
