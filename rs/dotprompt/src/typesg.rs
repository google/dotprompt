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

// You would need to add these to your Cargo.toml:
// [dependencies]
// serde = { version = "1.0", features = ["derive"] }
// serde_json = "1.0"
// async-trait = "0.1"
// url = { version = "2.0", features = ["serde"] }
// thiserror = "1.0" // Add thiserror for custom error handling

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use thiserror::Error;
use url::Url; // Import the Error macro from thiserror

// --- Custom Error Type ---

/// Custom error type for prompt store operations using `thiserror`.
#[derive(Debug, Error)]
pub enum PromptStoreError {
    /// Error indicating a prompt or partial was not found.
    #[error("Prompt or partial '{0}' not found")]
    NotFound(String),
    /// Error indicating an I/O problem during store operations.
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    /// Error during JSON serialization or deserialization.
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    /// Error for invalid URL format.
    #[error("Invalid URL: {0}")]
    InvalidUrl(#[from] url::ParseError),
    /// Generic error for other issues.
    #[error("An unexpected error occurred: {0}")]
    Other(String),
}

// --- Core Data Structures ---

/// Corresponds to `type Schema = Record<string, any>;`
pub type Schema = serde_json::Value;

/// Corresponds to `export interface ToolDefinition`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToolDefinition {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub input_schema: Schema,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_schema: Option<Schema>,
}

/// Corresponds to `export type ToolArgument = string | ToolDefinition;`
/// Uses `#[serde(untagged)]` to allow deserialization based on the content's structure.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ToolArgument {
    String(String),
    Definition(ToolDefinition),
}

/// Helper struct for fields that correspond to `HasMetadata` in TypeScript.
/// Used with `#[serde(flatten)]` to integrate its fields directly into the parent struct.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct HasMetadataFields {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Corresponds to `export interface PromptRef`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PromptRef {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Corresponds to `export interface PromptData extends PromptRef`
/// Combines fields from `PromptRef` and adds `source`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PromptData {
    #[serde(flatten)] // Flattens fields from PromptRef
    pub prompt_ref: PromptRef,
    pub source: String,
}

/// Helper struct for `PromptMetadata`'s `input` field.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PromptInputConfig {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default: Option<HashMap<String, serde_json::Value>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<Schema>,
}

/// Helper enum for `PromptMetadata`'s `output.format` field.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum OutputFormat {
    Json,
    Text,
    #[serde(other)] // Catch-all for any other string values
    Custom(String),
}

/// Helper struct for `PromptMetadata`'s `output` field.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PromptOutputConfig {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<OutputFormat>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<Schema>,
}

/// Corresponds to `export interface PromptMetadata<ModelConfig = Record<string, any>>`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PromptMetadata<ModelConfig = serde_json::Value>
where
    ModelConfig: Serialize + for<'de> Deserialize<'de> + Clone, // Add bounds for ModelConfig
{
    #[serde(flatten)] // Flattens fields from HasMetadataFields
    pub has_metadata: HasMetadataFields,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_defs: Option<Vec<ToolDefinition>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    #[serde(bound(
        serialize = "ModelConfig: Serialize",
        deserialize = "ModelConfig: for<'de> Deserialize<'de>"
    ))]
    pub config: Option<ModelConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<PromptInputConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output: Option<PromptOutputConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub raw: Option<HashMap<String, serde_json::Value>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ext: Option<HashMap<String, HashMap<String, serde_json::Value>>>,
}

/// Corresponds to `export interface ParsedPrompt<ModelConfig = Record<string, any>> extends PromptMetadata<ModelConfig>`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ParsedPrompt<ModelConfig = serde_json::Value>
where
    ModelConfig: Serialize + for<'de> Deserialize<'de> + Clone,
{
    #[serde(flatten)] // Flattens fields from PromptMetadata
    pub metadata: PromptMetadata<ModelConfig>,
    pub template: String,
}

// --- Part Types (for Message and Document content) ---

/// Helper struct for `MediaPart`'s `media` field.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MediaData {
    pub url: Url, // Using the `url` crate's Url type for robustness
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content_type: Option<String>,
}

/// Helper struct for `ToolRequestPart`'s `toolRequest` field.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToolRequestData<Input = serde_json::Value>
where
    Input: Serialize + for<'de> Deserialize<'de>,
{
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    #[serde(bound(
        serialize = "Input: Serialize",
        deserialize = "Input: for<'de> Deserialize<'de>"
    ))]
    pub input: Option<Input>,
    #[serde(rename = "ref", skip_serializing_if = "Option::is_none")] // `ref` is a Rust keyword
    pub r#ref: Option<String>,
}

/// Helper struct for `ToolResponsePart`'s `toolResponse` field.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToolResponseData<Output = serde_json::Value>
where
    Output: Serialize + for<'de> Deserialize<'de>,
{
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    #[serde(bound(
        serialize = "Output: Serialize",
        deserialize = "Output: for<'de> Deserialize<'de>"
    ))]
    pub output: Option<Output>,
    #[serde(rename = "ref", skip_serializing_if = "Option::is_none")] // `ref` is a Rust keyword
    pub r#ref: Option<String>,
}

/// Corresponds to `export type Part = ...;` (a discriminated union in TypeScript)
/// Uses `#[serde(untagged)]` to try deserializing into each variant until one matches.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Part {
    #[serde(rename_all = "camelCase")]
    Text {
        #[serde(flatten)]
        has_metadata: HasMetadataFields,
        text: String,
    },
    #[serde(rename_all = "camelCase")]
    Data {
        #[serde(flatten)]
        has_metadata: HasMetadataFields,
        data: serde_json::Value,
    },
    #[serde(rename_all = "camelCase")]
    Media {
        #[serde(flatten)]
        has_metadata: HasMetadataFields,
        media: MediaData,
    },
    #[serde(rename_all = "camelCase")]
    ToolRequest {
        #[serde(flatten)]
        has_metadata: HasMetadataFields,
        tool_request: ToolRequestData,
    },
    #[serde(rename_all = "camelCase")]
    ToolResponse {
        #[serde(flatten)]
        has_metadata: HasMetadataFields,
        tool_response: ToolResponseData,
    },
    #[serde(rename_all = "camelCase")]
    // For PendingPart, metadata is required and contains 'pending: true'
    Pending {
        metadata: HashMap<String, serde_json::Value>,
    },
}

/// Corresponds to `export type Role = 'user' | 'model' | 'tool' | 'system';`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum Role {
    User,
    Model,
    Tool,
    System,
}

/// Corresponds to `export interface Message extends HasMetadata`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Message {
    #[serde(flatten)]
    pub has_metadata: HasMetadataFields,
    pub role: Role,
    pub content: Vec<Part>,
}

/// Corresponds to `export interface Document extends HasMetadata`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Document {
    #[serde(flatten)]
    pub has_metadata: HasMetadataFields,
    pub content: Vec<Part>,
}

/// Corresponds to `export interface DataArgument<Variables = any, State = any>`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct DataArgument<Variables = serde_json::Value, State = serde_json::Value>
where
    Variables: Serialize + for<'de> Deserialize<'de>,
    State: Serialize + for<'de> Deserialize<'de>,
{
    #[serde(skip_serializing_if = "Option::is_none")]
    #[serde(bound(
        serialize = "Variables: Serialize",
        deserialize = "Variables: for<'de> Deserialize<'de>"
    ))]
    pub input: Option<Variables>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub docs: Option<Vec<Document>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub messages: Option<Vec<Message>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    #[serde(bound(
        serialize = "State: Serialize",
        deserialize = "State: for<'de> Deserialize<'de>"
    ))]
    pub context: Option<HashMap<String, State>>,
}

/// Corresponds to `export type JSONSchema = any;`
pub type JsonSchema = Schema; // Re-use the Schema alias

// --- Resolver Traits ---

/// Corresponds to `export type SchemaResolver` for synchronous resolution.
pub trait SyncSchemaResolver {
    fn resolve(&self, schema_name: &str) -> Option<JsonSchema>;
}

/// Corresponds to `export type ToolResolver` for synchronous resolution.
pub trait SyncToolResolver {
    fn resolve(&self, tool_name: &str) -> Option<ToolDefinition>;
}

/// Corresponds to `export type SchemaResolver` for asynchronous resolution.
#[async_trait]
pub trait AsyncSchemaResolver {
    async fn resolve(&self, schema_name: &str) -> Option<JsonSchema>;
}

/// Corresponds to `export type ToolResolver` for asynchronous resolution.
#[async_trait]
pub trait AsyncToolResolver {
    async fn resolve(&self, tool_name: &str) -> Option<ToolDefinition>;
}

/// Corresponds to `export interface RenderedPrompt<ModelConfig = Record<string, any>>`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RenderedPrompt<ModelConfig = serde_json::Value>
where
    ModelConfig: Serialize + for<'de> Deserialize<'de> + Clone,
{
    #[serde(flatten)]
    pub metadata: PromptMetadata<ModelConfig>,
    pub messages: Vec<Message>,
}

// --- Prompt Function Representation ---
// In TypeScript, these are callable objects with properties.
// In Rust, this is typically represented by a struct that holds the data
// and has a method to perform the 'call' logic.

/// Trait representing the core logic of a PromptFunction.
/// Corresponds to the callable part of `export interface PromptFunction`.
#[allow(unused_variables)]
pub trait PromptFunctionLogic<ModelConfig = serde_json::Value> {
    fn render(
        &self,
        data: DataArgument,
        options: Option<PromptMetadata<ModelConfig>>,
    ) -> Result<RenderedPrompt<ModelConfig>, PromptStoreError>
    // Changed error type
    where
        ModelConfig: Serialize + for<'de> Deserialize<'de> + Clone + 'static,
    {
        unimplemented!("PromptFunctionLogic::render not implemented for this type")
    }
}

/// A struct that encapsulates a `ParsedPrompt` and provides a rendering method.
/// Corresponds to `export interface PromptFunction<ModelConfig = Record<string, any>>`
/// where the `prompt` property is `self.parsed_prompt`.
#[derive(Debug, Clone)]
pub struct PromptFunction<ModelConfig = serde_json::Value>
where
    ModelConfig: Serialize + for<'de> Deserialize<'de> + Clone,
{
    pub parsed_prompt: ParsedPrompt<ModelConfig>,
    // You might add a Box<dyn PromptFunctionLogic> here or implement directly
    // depending on your design. For simplicity, we just keep the parsed prompt.
}

/// Trait representing the core logic of a PromptRefFunction.
/// Corresponds to the callable part of `export interface PromptRefFunction`.
#[allow(unused_variables)]
pub trait PromptRefFunctionLogic<ModelConfig = serde_json::Value> {
    fn render(
        &self,
        data: DataArgument,
        options: Option<PromptMetadata<ModelConfig>>,
    ) -> Result<RenderedPrompt<ModelConfig>, PromptStoreError>
    // Changed error type
    where
        ModelConfig: Serialize + for<'de> Deserialize<'de> + Clone + 'static,
    {
        unimplemented!("PromptRefFunctionLogic::render not implemented for this type")
    }
}

/// A struct that encapsulates a `PromptRef` and provides a rendering method
/// after loading a prompt via reference.
/// Corresponds to `export interface PromptRefFunction<ModelConfig = Record<string, any>>`
/// where the `promptRef` property is `self.prompt_ref`.
#[derive(Debug, Clone)]
pub struct PromptRefFunction<ModelConfig = serde_json::Value>
where
    ModelConfig: Serialize + for<'de> Deserialize<'de> + Clone,
{
    pub prompt_ref: PromptRef,
}

// --- Pagination and List Options ---

/// Corresponds to `export interface PaginatedResponse`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PaginatedResponse {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// Corresponds to `export interface PartialRef`
pub type PartialRef = PromptRef;

/// Corresponds to `export interface PartialData extends PartialRef`
pub type PartialData = PromptData;

/// Corresponds to `export interface ListPromptsOptions`
#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ListPromptsOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<u32>,
}

/// Corresponds to `export interface ListPartialsOptions`
pub type ListPartialsOptions = ListPromptsOptions;

/// Corresponds to `export interface LoadPromptOptions`
#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LoadPromptOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Corresponds to `export interface LoadPartialOptions`
pub type LoadPartialOptions = LoadPromptOptions;

/// Corresponds to `export interface DeletePromptOrPartialOptions`
#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DeletePromptOrPartialOptions {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
}

/// Corresponds to `export interface PaginatedPrompts`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PaginatedPrompts {
    pub prompts: Vec<PromptRef>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// Corresponds to `export interface PaginatedPartials`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PaginatedPartials {
    pub partials: Vec<PartialRef>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

// --- Prompt Store Traits (Sync and Async) ---

/// Corresponds to `export interface PromptStore` for synchronous implementations.
/// Methods return `Result<T, PromptStoreError>` for custom error handling.
pub trait PromptStore {
    fn list(
        &self,
        options: Option<ListPromptsOptions>,
    ) -> Result<PaginatedPrompts, PromptStoreError>;
    fn list_partials(
        &self,
        options: Option<ListPartialsOptions>,
    ) -> Result<PaginatedPartials, PromptStoreError>;
    fn load(
        &self,
        name: &str,
        options: Option<LoadPromptOptions>,
    ) -> Result<PromptData, PromptStoreError>;
    fn load_partial(
        &self,
        name: &str,
        options: Option<LoadPartialOptions>,
    ) -> Result<PromptData, PromptStoreError>;
}

/// Corresponds to `export interface PromptStoreWritable extends PromptStore`
/// for synchronous implementations.
pub trait PromptStoreWritable: PromptStore {
    fn save(&self, prompt: PromptData) -> Result<(), PromptStoreError>;
    fn delete(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<(), PromptStoreError>;
}

/// Corresponds to `export interface PromptStore` for asynchronous implementations.
/// Uses `#[async_trait]` macro for `async` methods in traits.
#[async_trait]
pub trait AsyncPromptStore {
    async fn list(
        &self,
        options: Option<ListPromptsOptions>,
    ) -> Result<PaginatedPrompts, PromptStoreError>;
    async fn list_partials(
        &self,
        options: Option<ListPartialsOptions>,
    ) -> Result<PaginatedPartials, PromptStoreError>;
    async fn load(
        &self,
        name: &str,
        options: Option<LoadPromptOptions>,
    ) -> Result<PromptData, PromptStoreError>;
    async fn load_partial(
        &self,
        name: &str,
        options: Option<LoadPartialOptions>,
    ) -> Result<PromptData, PromptStoreError>;
}

/// Corresponds to `export interface PromptStoreWritable extends PromptStore`
/// for asynchronous implementations.
#[async_trait]
pub trait AsyncPromptStoreWritable: AsyncPromptStore {
    async fn save(&self, prompt: PromptData) -> Result<(), PromptStoreError>;
    async fn delete(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<(), PromptStoreError>;
}

// --- Prompt Bundle ---

/// Corresponds to `export interface PromptBundle`
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PromptBundle {
    pub partials: Vec<PartialData>,
    pub prompts: Vec<PromptData>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_tool_definition_serialization() {
        let tool_def = ToolDefinition {
            name: "myTool".to_string(),
            description: Some("A test tool".to_string()),
            input_schema: json!({"type": "object", "properties": {"query": {"type": "string"}}}),
            output_schema: None,
        };
        let expected_json = r#"{"name":"myTool","description":"A test tool","inputSchema":{"type":"object","properties":{"query":{"type":"string"}}}}"#;
        assert_eq!(serde_json::to_string(&tool_def).unwrap(), expected_json);
    }

    #[test]
    fn test_part_enum_text() {
        let part = Part::Text {
            has_metadata: HasMetadataFields { metadata: None },
            text: "Hello, world!".to_string(),
        };
        let expected_json = r#"{"text":"Hello, world!"}"#;
        assert_eq!(serde_json::to_string(&part).unwrap(), expected_json);

        let deserialized: Part = serde_json::from_str(expected_json).unwrap();
        assert_eq!(deserialized, part);
    }

    #[test]
    fn test_part_enum_pending_with_metadata() {
        let part = Part::Pending {
            metadata: HashMap::from([
                ("pending".to_string(), json!(true)),
                ("requestId".to_string(), json!("abc-123")),
            ]),
        };
        let expected_json = r#"{"metadata":{"pending":true,"requestId":"abc-123"}}"#;
        let serialized = serde_json::to_string(&part).unwrap();
        // Use a contains check for metadata as HashMap order isn't guaranteed
        assert!(serialized.contains(r#""pending":true"#));
        assert!(serialized.contains(r#""requestId":"abc-123""#));

        let deserialized: Part = serde_json::from_str(expected_json).unwrap();
        assert_eq!(deserialized, part);
    }

    #[test]
    fn test_prompt_data_serialization() {
        let prompt_data = PromptData {
            prompt_ref: PromptRef {
                name: "testPrompt".to_string(),
                variant: Some("dev".to_string()),
                version: None,
            },
            source: "prompt source content".to_string(),
        };
        let expected_json =
            r#"{"name":"testPrompt","variant":"dev","source":"prompt source content"}"#;
        assert_eq!(serde_json::to_string(&prompt_data).unwrap(), expected_json);
    }

    #[test]
    fn test_data_argument_serialization() {
        let data_arg = DataArgument {
            input: Some(json!({"param1": "value1"})),
            docs: None,
            messages: None,
            context: Some(HashMap::from([(
                "state".to_string(),
                json!({"status": "active"}),
            )])),
        };
        let expected_json =
            r#"{"input":{"param1":"value1"},"context":{"state":{"status":"active"}}}"#;
        let serialized = serde_json::to_string(&data_arg).unwrap();
        assert!(serialized.contains(r#""input":{"param1":"value1"}"#));
        assert!(serialized.contains(r#""context":{"state":{"status":"active"}}"#));
    }

    // Example of how a custom error might be returned
    #[test]
    fn test_prompt_store_error() {
        let error = PromptStoreError::NotFound("my_prompt".to_string());
        assert_eq!(
            format!("{}", error),
            "Prompt or partial 'my_prompt' not found"
        );

        let io_error = std::io::Error::new(std::io::ErrorKind::Other, "disk full");
        let error_from_io = PromptStoreError::from(io_error);
        assert_eq!(format!("{}", error_from_io), "I/O error: disk full");
    }
}
