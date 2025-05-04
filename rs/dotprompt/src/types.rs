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

//! Rust equivalents of the core TypeScript/Python types used in Dotprompt.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

/// Use serde_json::Value to represent flexible Schemas, similar to `any` or `Record<string, any>`.
pub type Schema = Value;

/// Base trait/struct concept for types that can include arbitrary metadata.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct HasMetadata {
    /// Arbitrary metadata dictionary.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, Value>>,
}

/// Defines the structure and schemas for a tool callable by a model.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ToolDefinition {
    /// Name of the tool.
    pub name: String,
    /// Description of the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    /// Input schema for the tool.
    pub input_schema: Schema,
    /// Output schema for the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_schema: Option<Schema>,
}

/// Represents either a tool name (string) or a full ToolDefinition.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(untagged)]
pub enum ToolArgument {
    /// Name of the tool.
    Name(String),
    /// Full tool definition.
    Definition(ToolDefinition),
}

/// A reference to identify a specific prompt.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub struct PromptRef {
    /// Name of the prompt.
    pub name: String,
    /// Variant of the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    /// Version of the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Represents the complete data of a prompt, including its reference info and source.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PromptData {
    /// Reference to the prompt.
    #[serde(flatten)]
    pub reference: PromptRef,
    /// Source of the prompt.
    pub source: String,
}

/// Configuration settings related to the input variables of a prompt.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct PromptInputConfig {
    /// Default values for the input variables.
    #[serde(rename = "default", skip_serializing_if = "Option::is_none")]
    pub default_values: Option<HashMap<String, Value>>,
    /// Schema for the input variables.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<Schema>,
}

/// Configuration settings related to the expected output of a prompt.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct PromptOutputConfig {
    /// Format of the output.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<String>, // Could be an enum later: Json, Text
    /// Schema for the output.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<Schema>,
}

/// Metadata extracted from prompt frontmatter.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct PromptMetadata {
    /// Name of the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    /// Variant of the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    /// Version of the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,

    /// Description of the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    /// Model to use for the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>, // Consider making this a structured type later

    /// Names of tools.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<Vec<String>>,
    /// Full tool definitions.
    #[serde(rename = "toolDefs", skip_serializing_if = "Option::is_none")]
    pub tool_definitions: Option<Vec<ToolDefinition>>,

    /// Configuration for the model.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub config: Option<Value>, // Represents ModelConfig, using Value for flexibility

    /// Configuration for the input variables.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<PromptInputConfig>,
    /// Configuration for the expected output.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output: Option<PromptOutputConfig>,

    /// Raw frontmatter values before processing.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub raw: Option<HashMap<String, Value>>,

    /// Extension fields namespaced in the frontmatter.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ext: Option<HashMap<String, HashMap<String, Value>>>,

    /// Metadata for the prompt.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Prompt after parsing metadata and template body.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ParsedPrompt {
    /// Metadata for the prompt.
    #[serde(flatten)]
    pub metadata: PromptMetadata,
    /// Template body of the prompt.
    pub template: String,
}

// --- Message/Content Types ---

/// Represents a part containing plain text.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct TextPart {
    /// Text content of the part.
    pub text: String,
    /// Metadata for the part.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Represents a part containing structured data.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct DataPart {
    /// Structured data content of the part.
    pub data: Value,
    /// Metadata for the part.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Content details within a [MediaPart](cci:2://file:///Users/yesudeep/code/github.com/google/dotprompt/js/src/types.ts:110:0-112:2).
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MediaContent {
    /// URL of the media.
    pub url: String,
    /// Content type of the media.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content_type: Option<String>,
}

/// Represents a part containing media (image, audio, video).
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct MediaPart {
    /// Media content of the part.
    pub media: MediaContent,
    /// Metadata for the part.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Details of a tool request within a [ToolRequestPart](cci:2://file:///Users/yesudeep/code/github.com/google/dotprompt/js/src/types.ts:113:0-115:2).
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ToolRequestContent {
    /// Name of the tool.
    pub name: String,
    /// Input to the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<Value>,
    /// Reference to the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub r#ref: Option<String>, // Using r# for reserved keyword 'ref'
}

/// Represents a part containing a request to invoke a tool.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ToolRequestPart {
    /// Tool request content.
    pub tool_request: ToolRequestContent,
    /// Metadata for the part.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Details of a tool response within a [ToolResponsePart](cci:2://file:///Users/yesudeep/code/github.com/google/dotprompt/js/src/types.ts:116:0-118:2).
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ToolResponseContent {
    /// Name of the tool.
    pub name: String,
    /// Output from the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output: Option<Value>,
    /// Reference to the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub r#ref: Option<String>, // Using r# for reserved keyword 'ref'
}

/// Represents a part containing the result from a tool execution.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ToolResponsePart {
    /// Tool response content.
    pub tool_response: ToolResponseContent,
    /// Metadata for the part.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Metadata specific to a [PendingPart](cci:2://file:///Users/yesudeep/code/github.com/google/dotprompt/js/src/types.ts:119:0-121:2).
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PendingMetadata {
    /// Whether the part is pending.
    pub pending: bool, // Must be true
    /// Additional metadata.
    #[serde(flatten)]
    pub additional: HashMap<String, Value>, // Catch-all for other metadata
}

/// Represents a part indicating pending or awaited content.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PendingPart {

    /// Metadata for the part.
    #[serde(flatten)]
    pub has_metadata: HasMetadata, // Ensure metadata includes PendingMetadata structure
}


/// Union of different content part types.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase", untagged)] // Use untagged for enum representation based on fields
pub enum Part {
    /// Text content of the part.
    Text(TextPart),
    /// Structured data content of the part.
    Data(DataPart),
    /// Media content of the part.
    Media(MediaPart),
    /// Tool request content of the part.
    ToolRequest(ToolRequestPart),
    /// Tool response content of the part.
    ToolResponse(ToolResponsePart),
    /// Pending content of the part.
    Pending(PendingPart),
}

/// Defines roles in a conversation.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "lowercase")] // Matches 'user', 'model', 'tool', 'system'
pub enum Role {
    /// User role.
    User,
    /// Model role.
    Model,
    /// Tool role.
    Tool,
    /// System role.
    System,
}

/// Represents a single message in a conversation history.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Message {
    /// Role of the message.
    pub role: Role,
    /// Content of the message.
    pub content: Vec<Part>,
    /// Metadata for the message.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Represents an external document used for context.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct Document {
    /// Content of the document.
    pub content: Vec<Part>,
    /// Metadata for the document.
    #[serde(flatten, skip_serializing_if = "Option::is_none")]
    pub has_metadata: Option<HasMetadata>,
}

/// Data provided at runtime to render a template.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct DataArgument {
    /// Template variables.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<HashMap<String, Value>>,
    /// External documents.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub docs: Option<Vec<Document>>,
    /// Conversation history.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub messages: Option<Vec<Message>>,
    /// Additional context.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context: Option<HashMap<String, Value>>,
}

/// Final output after rendering a prompt template.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct RenderedPrompt {
    /// Metadata for the prompt.
    #[serde(flatten)]
    pub metadata: PromptMetadata, // Includes merged/final metadata
    /// Messages to be sent to the model.
    pub messages: Vec<Message>, // Messages to be sent to the model
                                // Could also include raw rendered string if needed:
                                // pub rendered_template: Option<String>,
}

// --- Prompt Store Related Types ---

/// A reference to identify a specific partial template.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Eq, Hash)]
#[serde(rename_all = "camelCase")]
pub struct PartialRef {
    /// Name of the partial template.
    pub name: String,
    /// Variant of the partial template.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    /// Version of the partial template.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Represents the complete data of a partial template.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct PartialData {
    /// Reference to the partial template.
    #[serde(flatten)]
    pub reference: PartialRef,
    /// Source of the partial template.
    pub source: String,
}

/// Options for listing prompts or partials with pagination.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct ListOptions {
    /// Cursor for pagination.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
    /// Number of results to return.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<u32>,
}

/// Options for listing prompts.
pub type ListPromptsOptions = ListOptions;
/// Options for listing partials.
pub type ListPartialsOptions = ListOptions;

/// Options for loading a specific prompt version/variant.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct LoadOptions {
    /// Variant of the prompt to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    /// Version of the prompt to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>, // Version hash for verification
}

/// Options for loading a specific prompt.
pub type LoadPromptOptions = LoadOptions;

/// Options for loading a specific partial.
pub type LoadPartialOptions = LoadOptions;

/// Options for deleting a prompt or partial.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct DeletePromptOrPartialOptions {
    /// Variant of the prompt to delete.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>, // If omitted, targets default
}

/// Represents a single page of results when listing prompts.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct PaginatedPrompts {
    /// List of prompts.
    pub prompts: Vec<PromptRef>,
    /// Cursor for pagination.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// Represents a single page of results when listing partials.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct PaginatedPartials {
    /// List of partials.
    pub partials: Vec<PartialRef>,
    /// Cursor for pagination.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// A container for packaging multiple prompts and partials.
#[derive(Serialize, Deserialize, Debug, Clone, PartialEq, Default)]
#[serde(rename_all = "camelCase")]
pub struct PromptBundle {
    /// List of partials.
    #[serde(default)]
    pub partials: Vec<PartialData>,
    /// List of prompts.
    #[serde(default)]
    pub prompts: Vec<PromptData>,
}

// Note: PromptStore, PromptFunction, Resolvers etc. are interfaces/protocols/functions.
// Their direct translation would involve Rust traits and function types,
// which might be defined elsewhere depending on the library's structure.
// This file focuses on the core data structures.

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json;

    #[test]
    fn test_serialize_deserialize_text_part() {
        let part = Part::Text(TextPart { text: "Hello".to_string(), has_metadata: None });
        let json = serde_json::to_string(&part).unwrap();
        // Expected: untagged enum means just the inner struct's fields
        assert!(json.contains(r#""text":"Hello""#));
        let deserialized: Part = serde_json::from_str(&json).unwrap();
        assert_eq!(part, deserialized);
    }

     #[test]
    fn test_serialize_deserialize_tool_request_part() {
        let content = ToolRequestContent {
            name: "calculator".to_string(),
            input: Some(serde_json::json!({"query": "2+2"})),
            r#ref: Some("req-123".to_string()),
        };
        let part = Part::ToolRequest(ToolRequestPart { tool_request: content, has_metadata: None });
        let json = serde_json::to_string(&part).unwrap();

        assert!(json.contains(r#""toolRequest""#));
        assert!(json.contains(r#""name":"calculator""#));
        assert!(json.contains(r#""input":{"query":"2+2"}"#));
        assert!(json.contains(r#""ref":"req-123""#));

        let deserialized: Part = serde_json::from_str(&json).unwrap();
         match deserialized {
            Part::ToolRequest(req) => {
                assert_eq!(req.tool_request.name, "calculator");
                assert_eq!(req.tool_request.input, Some(serde_json::json!({"query": "2+2"})));
                assert_eq!(req.tool_request.r#ref, Some("req-123".to_string()));
            }
            _ => panic!("Deserialized into wrong Part variant"),
        }
    }

    #[test]
    fn test_serialize_deserialize_message() {
        let msg = Message {
            role: Role::User,
            content: vec![
                Part::Text(TextPart { text: "Hello".to_string(), has_metadata: None }),
            ],
            has_metadata: None,
        };
        let json = serde_json::to_string(&msg).unwrap();
        assert!(json.contains(r#""role":"user""#)); // Check lowercase role
        assert!(json.contains(r#""content":[{"text":"Hello"}]"#));
        let deserialized: Message = serde_json::from_str(&json).unwrap();
        assert_eq!(msg, deserialized);
    }

     #[test]
    fn test_serialize_deserialize_prompt_metadata() {
        let meta = PromptMetadata {
            name: Some("my-prompt".to_string()),
            variant: Some("test-variant".to_string()),
            description: Some("A test prompt".to_string()),
            model: Some("gemini-pro".to_string()),
            tools: Some(vec!["search".to_string()]),
            input: Some(PromptInputConfig {
                schema: Some(serde_json::json!({"type": "object", "properties": {"query": {"type": "string"}}})),
                ..Default::default()
            }),
            ..Default::default()
        };
        let json = serde_json::to_string(&meta).unwrap();
        println!("{}", json); // For debugging
        assert!(json.contains(r#""name":"my-prompt""#));
        assert!(json.contains(r#""variant":"test-variant""#));
        assert!(json.contains(r#""model":"gemini-pro""#));
        assert!(json.contains(r#""tools":["search"]"#));
        assert!(json.contains(r#""input":{"schema":{"#));
        let deserialized: PromptMetadata = serde_json::from_str(&json).unwrap();
        assert_eq!(meta, deserialized);
    }

    #[test]
    fn test_tool_argument_name() {
        let arg = ToolArgument::Name("my_tool".to_string());
        let json = serde_json::to_string(&arg).unwrap();
        assert_eq!(json, r#""my_tool""#);
        let deserialized: ToolArgument = serde_json::from_str(&json).unwrap();
        assert_eq!(arg, deserialized);
    }

    #[test]
    fn test_tool_argument_definition() {
        let def = ToolDefinition {
            name: "my_tool_def".to_string(),
            description: None,
            input_schema: serde_json::json!({"type": "string"}),
            output_schema: None,
        };
        let arg = ToolArgument::Definition(def.clone());
        let json = serde_json::to_string(&arg).unwrap();
         // Matches the structure of ToolDefinition
        assert!(json.contains(r#""name":"my_tool_def""#));
        assert!(json.contains(r#""inputSchema":{"type":"string"}"#));

        let deserialized: ToolArgument = serde_json::from_str(&json).unwrap();
        assert_eq!(arg, deserialized);
    }
}
