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

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

/**
 * Defines a tool that can be called by a model.
 *
 * @param name The unique identifier for the tool.
 * @param description A human-readable explanation of the tool's purpose.
 * @param inputSchema A schema definition for the expected input parameters.
 * @param outputSchema An optional schema definition for the output.
 */
public record ToolDefinition(
    String name,
    String description,
    @JsonProperty("inputSchema") Map<String, Object> inputSchema,
    @JsonProperty("outputSchema") Map<String, Object> outputSchema) {}
