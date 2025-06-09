// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

//! Type definitions for the dotprompt library.

use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;
use std::collections::HashMap;

/// A schema.
pub type Schema = HashMap<String, JsonValue>;

/// A JSON schema.
pub type JsonSchema = JsonValue;

/// A tool definition.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToolDefinition {
    /// The name of the tool.
    pub name: String,

    /// A description of the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,

    /// The schema of the tool's input.
    pub input_schema: Schema,

    /// The schema of the tool's output.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_schema: Option<Schema>,
}

/// A tool argument.
/// Corresponds to `export type ToolArgument = string | ToolDefinition;`
/// Uses `#[serde(untagged)]` to allow deserialization based on the content's structure.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ToolArgument {
    /// A tool name.
    Name(String),

    /// A tool definition.
    Definition(ToolDefinition),
}

/// Corresponds to `export type Role = 'user' | 'model' | 'tool' | 'system';`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    /// A user message.
    User,

    /// A model message.
    Model,

    /// A tool message.
    Tool,

    /// A system message.
    System,
}
