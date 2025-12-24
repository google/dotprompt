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

import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;

/**
 * Marker interface for message parts (e.g. text, media).
 *
 * <p>Uses Jackson polymorphism to deserialize into specific sub-types.
 */
@JsonTypeInfo(use = JsonTypeInfo.Id.DEDUCTION)
@JsonSubTypes({
  @JsonSubTypes.Type(value = TextPart.class),
  @JsonSubTypes.Type(value = MediaPart.class),
  @JsonSubTypes.Type(value = ToolRequestPart.class),
  @JsonSubTypes.Type(value = ToolResponsePart.class),
  @JsonSubTypes.Type(value = DataPart.class),
  @JsonSubTypes.Type(value = PendingPart.class)
})
public interface Part {}
