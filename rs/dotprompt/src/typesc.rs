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

//! Types for the Dotprompt library.

use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;
use std::collections::HashMap;
use std::future::Future;
use std::pin::Pin;

/// Type alias for JSON schema
pub type Schema = HashMap<String, JsonValue>;

/// Type alias for JSON Schema
pub type JsonSchema = JsonValue;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolDefinition {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub input_schema: Schema,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_schema: Option<Schema>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ToolArgument {
    Name(String),
    Definition(ToolDefinition),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptRef {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptData {
    #[serde(flatten)]
    pub prompt_ref: PromptRef,
    pub source: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptMetadata<ModelConfig = HashMap<String, JsonValue>> {
    /// Arbitrary metadata to be used by tooling or for informational purposes
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
    /// The name of the prompt
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    /// The variant name for the prompt
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    /// The version of the prompt
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
    /// A description of the prompt
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    /// The name of the model to use for this prompt, e.g. `vertexai/gemini-1.0-pro`
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,
    /// Names of tools (registered separately) to allow use of in this prompt
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<Vec<String>>,
    /// Definitions of tools to allow use of in this prompt
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_defs: Option<Vec<ToolDefinition>>,
    /// Model configuration. Not all models support all options
    #[serde(skip_serializing_if = "Option::is_none")]
    pub config: Option<ModelConfig>,
    /// Configuration for input variables
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<InputConfig>,
    /// Defines the expected model output format
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output: Option<OutputConfig>,
    /// This field will contain the raw frontmatter as parsed with no additional
    /// processing or substitutions
    #[serde(skip_serializing_if = "Option::is_none")]
    pub raw: Option<HashMap<String, JsonValue>>,
    /// Fields that contain a period will be considered "extension fields"
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ext: Option<HashMap<String, HashMap<String, JsonValue>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InputConfig {
    /// Defines the default input variable values to use if none are provided
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default: Option<HashMap<String, JsonValue>>,
    /// Schema definition for input variables
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<Schema>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputConfig {
    /// Desired output format for this prompt
    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<OutputFormat>,
    /// Schema defining the output structure
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<Schema>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum OutputFormat {
    Predefined(PredefinedFormat),
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PredefinedFormat {
    Json,
    Text,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedPrompt<ModelConfig = HashMap<String, JsonValue>> {
    #[serde(flatten)]
    pub metadata: PromptMetadata<ModelConfig>,
    /// The source of the template with metadata / frontmatter already removed
    pub template: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextPart {
    pub text: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataPart {
    pub data: HashMap<String, JsonValue>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaPart {
    pub media: MediaContent,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaContent {
    pub url: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content_type: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolRequestPart<Input = JsonValue> {
    pub tool_request: ToolRequest<Input>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolRequest<Input = JsonValue> {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<Input>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reference: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResponsePart<Output = JsonValue> {
    pub tool_response: ToolResponse<Output>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResponse<Output = JsonValue> {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output: Option<Output>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reference: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingPart {
    pub metadata: PendingMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingMetadata {
    pub pending: bool,
    #[serde(flatten)]
    pub extra: HashMap<String, JsonValue>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Part {
    Text(TextPart),
    Data(DataPart),
    Media(MediaPart),
    ToolRequest(ToolRequestPart),
    ToolResponse(ToolResponsePart),
    Pending(PendingPart),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    User,
    Model,
    Tool,
    System,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: Role,
    pub content: Vec<Part>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub content: Vec<Part>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, JsonValue>>,
}

/// DataArgument provides all of the information necessary to render a
/// template at runtime.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataArgument<Variables = HashMap<String, JsonValue>, State = JsonValue> {
    /// Input variables for the prompt template
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<Variables>,
    /// Relevant documents
    #[serde(skip_serializing_if = "Option::is_none")]
    pub docs: Option<Vec<Document>>,
    /// Previous messages in the history of a multi-turn conversation
    #[serde(skip_serializing_if = "Option::is_none")]
    pub messages: Option<Vec<Message>>,
    /// Items in the context argument are exposed as `@` variables
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context: Option<HashMap<String, JsonValue>>,
}

/// SchemaResolver is a function that can resolve a provided schema name to
/// an underlying JSON schema, utilized for shorthand to a schema library
/// provided by an external tool.
pub type SchemaResolver =
    Box<dyn Fn(&str) -> Pin<Box<dyn Future<Output = Option<JsonSchema>> + Send>> + Send + Sync>;

/// ToolResolver is a function that can resolve a provided tool name to
/// an underlying ToolDefinition, utilized for shorthand to a tool registry
/// provided by an external library.
pub type ToolResolver =
    Box<dyn Fn(&str) -> Pin<Box<dyn Future<Output = Option<ToolDefinition>> + Send>> + Send + Sync>;

/// RenderedPrompt is the final result of rendering a Dotprompt template.
/// It includes all of the prompt metadata as well as a set of `messages` to
/// be sent to the model.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RenderedPrompt<ModelConfig = HashMap<String, JsonValue>> {
    #[serde(flatten)]
    pub metadata: PromptMetadata<ModelConfig>,
    /// The rendered messages of the prompt
    pub messages: Vec<Message>,
}

/// PromptFunction is a function that takes runtime data / context and returns
/// a rendered prompt result.
pub trait PromptFunction<ModelConfig = HashMap<String, JsonValue>> {
    fn call(
        &self,
        data: DataArgument,
        options: Option<PromptMetadata<ModelConfig>>,
    ) -> Pin<
        Box<
            dyn Future<
                    Output = Result<
                        RenderedPrompt<ModelConfig>,
                        Box<dyn std::error::Error + Send + Sync>,
                    >,
                > + Send,
        >,
    >;

    fn prompt(&self) -> &ParsedPrompt<ModelConfig>;
}

/// PromptRefFunction is a function that takes runtime data / context and returns
/// a rendered prompt result after loading a prompt via reference.
pub trait PromptRefFunction<ModelConfig = HashMap<String, JsonValue>> {
    fn call(
        &self,
        data: DataArgument,
        options: Option<PromptMetadata<ModelConfig>>,
    ) -> Pin<
        Box<
            dyn Future<
                    Output = Result<
                        RenderedPrompt<ModelConfig>,
                        Box<dyn std::error::Error + Send + Sync>,
                    >,
                > + Send,
        >,
    >;

    fn prompt_ref(&self) -> &PromptRef;
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaginatedResponse {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartialRef {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartialData {
    #[serde(flatten)]
    pub partial_ref: PartialRef,
    pub source: String,
}

/// Options for listing prompts with pagination.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ListPromptsOptions {
    /// The cursor to start listing from.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
    /// The maximum number of items to return.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<usize>,
}

/// Options for listing partials with pagination.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ListPartialsOptions {
    /// The cursor to start listing from.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
    /// The maximum number of items to return.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<usize>,
}

/// Options for loading a prompt.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LoadPromptOptions {
    /// The specific variant identifier of the prompt to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    /// A specific version hash to load. If provided, an error is thrown if the
    /// calculated version of the file content does not match this value.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Options for loading a partial.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LoadPartialOptions {
    /// The specific variant identifier of the partial to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
    /// A specific version hash to load. If provided, an error is thrown if the
    /// calculated version of the file content does not match this value.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Options for deleting a prompt or partial.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DeletePromptOrPartialOptions {
    /// The specific variant identifier to delete. If omitted, targets the
    /// default (no variant) file.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
}

/// A paginated list of prompts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaginatedPrompts {
    /// The list of prompts.
    pub prompts: Vec<PromptRef>,
    /// The cursor to start the next page of results.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// A paginated list of partials.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PaginatedPartials {
    /// The list of partials.
    pub partials: Vec<PartialRef>,
    /// The cursor to start the next page of results.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// Error type for prompt store operations
#[derive(Debug, thiserror::Error)]
pub enum PromptStoreError {
    #[error("Prompt not found: {name}")]
    PromptNotFound { name: String },
    #[error("Partial not found: {name}")]
    PartialNotFound { name: String },
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("Custom error: {0}")]
    Custom(String),
}

/// PromptStore is a common interface that provides for reading and writing
/// prompts and partials (async version - default).
#[async_trait::async_trait]
pub trait PromptStore: Send + Sync {
    /// Return a list of all prompts in the store (optionally paginated).
    /// Some store providers may return limited metadata.
    async fn list(
        &self,
        options: Option<ListPromptsOptions>,
    ) -> Result<PaginatedPrompts, PromptStoreError>;

    /// Return a list of partial names available in this store.
    async fn list_partials(
        &self,
        options: Option<ListPartialsOptions>,
    ) -> Result<PaginatedPartials, PromptStoreError>;

    /// Retrieve a prompt from the store.
    async fn load(
        &self,
        name: &str,
        options: Option<LoadPromptOptions>,
    ) -> Result<PromptData, PromptStoreError>;

    /// Retrieve a partial from the store.
    async fn load_partial(
        &self,
        name: &str,
        options: Option<LoadPartialOptions>,
    ) -> Result<PartialData, PromptStoreError>;
}

/// PromptStoreWritable is a PromptStore that also has built-in methods for
/// writing prompts in addition to reading them (async version).
#[async_trait::async_trait]
pub trait PromptStoreWritable: PromptStore {
    /// Save a prompt in the store. May be destructive for prompt stores without versioning.
    async fn save(&self, prompt: PromptData) -> Result<(), PromptStoreError>;

    /// Delete a prompt from the store.
    async fn delete(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<(), PromptStoreError>;

    /// Save a partial in the store.
    async fn save_partial(&self, partial: PartialData) -> Result<(), PromptStoreError>;

    /// Delete a partial from the store.
    async fn delete_partial(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<(), PromptStoreError>;
}

/// Synchronous version of PromptStore for non-async environments.
pub trait PromptStoreSync: Send + Sync {
    /// Return a list of all prompts in the store (optionally paginated).
    /// Some store providers may return limited metadata.
    fn list(
        &self,
        options: Option<ListPromptsOptions>,
    ) -> Result<PaginatedPrompts, PromptStoreError>;

    /// Return a list of partial names available in this store.
    fn list_partials(
        &self,
        options: Option<ListPartialsOptions>,
    ) -> Result<PaginatedPartials, PromptStoreError>;

    /// Retrieve a prompt from the store.
    fn load(
        &self,
        name: &str,
        options: Option<LoadPromptOptions>,
    ) -> Result<PromptData, PromptStoreError>;

    /// Retrieve a partial from the store.
    fn load_partial(
        &self,
        name: &str,
        options: Option<LoadPartialOptions>,
    ) -> Result<PartialData, PromptStoreError>;
}

/// Synchronous writable version of PromptStore for non-async environments.
pub trait PromptStoreWritableSync: PromptStoreSync {
    /// Save a prompt in the store. May be destructive for prompt stores without versioning.
    fn save(&self, prompt: PromptData) -> Result<(), PromptStoreError>;

    /// Delete a prompt from the store.
    fn delete(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<(), PromptStoreError>;

    /// Save a partial in the store.
    fn save_partial(&self, partial: PartialData) -> Result<(), PromptStoreError>;

    /// Delete a partial from the store.
    fn delete_partial(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<(), PromptStoreError>;
}

/// A bundle of prompts and partials.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptBundle {
    pub partials: Vec<PartialData>,
    pub prompts: Vec<PromptData>,
}

impl Default for PromptBundle {
    fn default() -> Self {
        Self {
            partials: Vec::new(),
            prompts: Vec::new(),
        }
    }
}

// Helper implementations and utility functions

impl PromptRef {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            variant: None,
            version: None,
        }
    }

    pub fn with_variant(mut self, variant: impl Into<String>) -> Self {
        self.variant = Some(variant.into());
        self
    }

    pub fn with_version(mut self, version: impl Into<String>) -> Self {
        self.version = Some(version.into());
        self
    }
}

impl PartialRef {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            variant: None,
            version: None,
        }
    }

    pub fn with_variant(mut self, variant: impl Into<String>) -> Self {
        self.variant = Some(variant.into());
        self
    }

    pub fn with_version(mut self, version: impl Into<String>) -> Self {
        self.version = Some(version.into());
        self
    }
}

impl Part {
    pub fn text(content: impl Into<String>) -> Self {
        Part::Text(TextPart {
            text: content.into(),
            metadata: None,
        })
    }

    pub fn data(data: HashMap<String, JsonValue>) -> Self {
        Part::Data(DataPart {
            data,
            metadata: None,
        })
    }

    pub fn media(url: impl Into<String>, content_type: Option<String>) -> Self {
        Part::Media(MediaPart {
            media: MediaContent {
                url: url.into(),
                content_type,
            },
            metadata: None,
        })
    }
}
