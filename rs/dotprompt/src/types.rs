// Copyright 2026 Google LLC
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

//! Core type definitions for the dotprompt library.
//!
//! This module contains all the data structures used to represent prompts,
//! messages, metadata, and related concepts. These types closely mirror the
//! canonical JavaScript implementation for cross-language compatibility.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Type alias for generic schemas.
pub type Schema = HashMap<String, serde_json::Value>;

/// Type alias for JSON Schema definitions.
pub type JsonSchema = serde_json::Value;

/// Trait for types that contain arbitrary metadata.
///
/// This matches the JS `HasMetadata` interface pattern.
pub trait HasMetadata {
    /// Returns the arbitrary metadata, if any.
    fn metadata(&self) -> Option<&HashMap<String, serde_json::Value>>;
}

/// Role of a message in a conversation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    /// User message.
    User,
    /// Model/assistant message.
    Model,
    /// Tool call message.
    Tool,
    /// System message.
    System,
}

/// Tool definition specifying inputs and outputs.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToolDefinition {
    /// Name of the tool.
    pub name: String,

    /// Optional description of what the tool does.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,

    /// JSON Schema for the tool's input parameters.
    pub input_schema: Schema,

    /// Optional JSON Schema for the tool's output.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_schema: Option<Schema>,
}

/// A tool argument can be either a tool name string or a full definition.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ToolArgument {
    /// Tool referenced by name (to be resolved via `ToolResolver`).
    Name(String),
    /// Full tool definition.
    Definition(ToolDefinition),
}

/// Reference to a prompt by name, variant, and version.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptRef {
    /// Name of the prompt.
    pub name: String,

    /// Optional variant identifier.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,

    /// Optional version identifier.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Prompt data including source template.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptData {
    /// Prompt reference fields.
    #[serde(flatten)]
    pub prompt_ref: PromptRef,

    /// Template source code.
    pub source: String,
}

/// Configuration for prompt input variables.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PromptInputConfig {
    /// Default values for input variables.
    #[serde(skip_serializing_if = "Option::is_none", rename = "default")]
    pub default: Option<HashMap<String, serde_json::Value>>,

    /// JSON Schema for input variables (can be picoschema string or JSON Schema object).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<serde_json::Value>,
}

/// Configuration for prompt output format.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PromptOutputConfig {
    /// Desired output format (e.g., "json", "text").
    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<String>,

    /// JSON Schema for output structure (can be picoschema string or JSON Schema object).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<serde_json::Value>,
}

/// Metadata associated with a prompt template.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PromptMetadata<M = serde_json::Value> {
    /// Name of the prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,

    /// Variant identifier.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,

    /// Version identifier.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,

    /// Human-readable description.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,

    /// Model identifier (e.g., "vertexai/gemini-1.0-pro").
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model: Option<String>,

    /// Names of tools available to this prompt.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<Vec<String>>,

    /// Inline tool definitions.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_defs: Option<Vec<ToolDefinition>>,

    /// Model-specific configuration.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub config: Option<M>,

    /// Input variable configuration.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<PromptInputConfig>,

    /// Output format configuration.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output: Option<PromptOutputConfig>,

    /// Raw frontmatter as parsed.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub raw: Option<HashMap<String, serde_json::Value>>,

    /// Extension fields organized by namespace.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ext: Option<HashMap<String, HashMap<String, serde_json::Value>>>,

    /// Arbitrary metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Parsed prompt with extracted metadata and template.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedPrompt<M = serde_json::Value> {
    /// Prompt metadata from frontmatter.
    #[serde(flatten)]
    pub metadata: PromptMetadata<M>,

    /// Template source with frontmatter removed.
    pub template: String,
}

/// Media content reference.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MediaContent {
    /// URL of the media.
    pub url: String,

    /// Optional content type (MIME type).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content_type: Option<String>,
}

/// Tool request content.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolRequestContent {
    /// Name of the tool being requested.
    pub name: String,

    /// Optional input parameters for the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<serde_json::Value>,

    /// Optional reference identifier.
    #[serde(skip_serializing_if = "Option::is_none", rename = "ref")]
    pub ref_: Option<String>,
}

/// Tool response content.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResponseContent {
    /// Name of the tool that was called.
    pub name: String,

    /// Optional output from the tool.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output: Option<serde_json::Value>,

    /// Optional reference identifier.
    #[serde(skip_serializing_if = "Option::is_none", rename = "ref")]
    pub ref_: Option<String>,
}

/// Content part within a message.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Part {
    /// Text content.
    Text(TextPart),
    /// Structured data content.
    Data(DataPart),
    /// Media reference (image, video, etc.).
    Media(MediaPart),
    /// Tool call request.
    ToolRequest(ToolRequestPart),
    /// Tool call response.
    ToolResponse(ToolResponsePart),
    /// Pending/placeholder content.
    Pending(PendingPart),
}

/// Text content part.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextPart {
    /// The text content.
    pub text: String,

    /// Optional metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Structured data part.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataPart {
    /// The data content as a JSON object.
    pub data: HashMap<String, serde_json::Value>,

    /// Optional metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Media reference part.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaPart {
    /// The media content reference.
    pub media: MediaContent,

    /// Optional metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Tool request part.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToolRequestPart {
    /// The tool request details.
    pub tool_request: ToolRequestContent,

    /// Optional metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Tool response part.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ToolResponsePart {
    /// The tool response details.
    pub tool_response: ToolResponseContent,

    /// Optional metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Pending/placeholder part.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingPart {
    /// Metadata must contain `pending: true`.
    pub metadata: HashMap<String, serde_json::Value>,
}

/// A message in a conversation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    /// Role of the message sender.
    pub role: Role,

    /// Content parts of the message.
    pub content: Vec<Part>,

    /// Optional metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// A document with structured content.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    /// Content parts of the document.
    pub content: Vec<Part>,

    /// Optional metadata.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, serde_json::Value>>,
}

/// Data provided to render a prompt template.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DataArgument<V = serde_json::Value> {
    /// Input variables for template rendering.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub input: Option<V>,

    /// Relevant documents for context.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub docs: Option<Vec<Document>>,

    /// Previous messages in multi-turn conversation.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub messages: Option<Vec<Message>>,

    /// Context variables (exposed as `@` variables in templates).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context: Option<HashMap<String, serde_json::Value>>,
}

/// Rendered prompt output with messages.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RenderedPrompt<M = serde_json::Value> {
    /// Prompt metadata.
    #[serde(flatten)]
    pub metadata: PromptMetadata<M>,

    /// Rendered messages to send to the model.
    pub messages: Vec<Message>,
}

/// Reference to a partial template.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartialRef {
    /// Name of the partial.
    pub name: String,

    /// Optional variant identifier.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,

    /// Optional version identifier.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Partial template data with source.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PartialData {
    /// Partial reference fields.
    #[serde(flatten)]
    pub partial_ref: PartialRef,

    /// Template source for the partial.
    pub source: String,
}

/// Resolves schema names to JSON Schema definitions.
///
/// Used by the picoschema system to look up named schemas from a registry.
pub trait SchemaResolver: Send + Sync {
    /// Resolves a schema name to its JSON Schema definition.
    fn resolve(&self, name: &str) -> Option<JsonSchema>;
}

/// Resolves tool names to tool definitions.
///
/// Used to look up tool definitions by name from a registry.
pub trait ToolResolver: Send + Sync {
    /// Resolves a tool name to its definition.
    fn resolve(&self, name: &str) -> Option<ToolDefinition>;
}

/// Resolves partial names to their template source.
///
/// Used to dynamically load partial templates.
pub trait PartialResolver: Send + Sync {
    /// Resolves a partial name to its template source.
    fn resolve(&self, name: &str) -> Option<String>;
}

/// Options for listing prompts with pagination.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ListPromptsOptions {
    /// Cursor to start listing from.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,

    /// Maximum number of items to return.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<usize>,

    /// Specific variant to filter.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
}

/// Options for listing partials with pagination.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ListPartialsOptions {
    /// Cursor to start listing from.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,

    /// Maximum number of items to return.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<usize>,

    /// Specific variant to filter.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,
}

/// Options for loading a prompt.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LoadPromptOptions {
    /// Specific variant to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,

    /// Specific version hash to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// Options for loading a partial.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct LoadPartialOptions {
    /// Specific variant to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub variant: Option<String>,

    /// Specific version hash to load.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

/// A paginated list of prompts.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PaginatedPrompts {
    /// The list of prompts.
    pub prompts: Vec<PromptRef>,

    /// Cursor for the next page.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// A paginated list of partials.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PaginatedPartials {
    /// The list of partials.
    pub partials: Vec<PartialRef>,

    /// Cursor for the next page.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<String>,
}

/// Base trait for paginated responses.
pub trait PaginatedResponse {
    /// Returns the cursor for the next page, if any.
    fn cursor(&self) -> Option<&str>;
}

impl PaginatedResponse for PaginatedPrompts {
    fn cursor(&self) -> Option<&str> {
        self.cursor.as_deref()
    }
}

impl PaginatedResponse for PaginatedPartials {
    fn cursor(&self) -> Option<&str> {
        self.cursor.as_deref()
    }
}

/// A compiled prompt function that can be rendered with data.
///
/// This wraps a parsed prompt and provides a callable interface for rendering.
#[derive(Debug, Clone)]
pub struct PromptFunction<M = serde_json::Value> {
    /// The parsed prompt with metadata.
    pub prompt: ParsedPrompt<M>,
}

/// A prompt function that loads from a reference.
///
/// This allows deferred loading of prompts via a store.
#[derive(Debug, Clone)]
pub struct PromptRefFunction {
    /// The prompt reference.
    pub prompt_ref: PromptRef,
}

/// A bundle of prompts and partials.
///
/// Used for bulk operations and serialization.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct PromptBundle {
    /// Partial templates.
    pub partials: Vec<PartialData>,
    /// Prompt templates.
    pub prompts: Vec<PromptData>,
}
