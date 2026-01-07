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

//! Error types for the dotprompt library.

use thiserror::Error;

/// Result type alias for dotprompt operations.
pub type Result<T> = std::result::Result<T, DotpromptError>;

/// Errors that can occur when working with dotprompt templates.
#[derive(Debug, Error)]
pub enum DotpromptError {
    /// Failed to parse YAML frontmatter.
    #[error("failed to parse frontmatter: {0}")]
    FrontmatterParseError(#[from] serde_yaml::Error),

    /// Failed to parse JSON data.
    #[error("failed to parse JSON: {0}")]
    JsonParseError(#[from] serde_json::Error),

    /// Template compilation failed.
    #[error("template compilation failed: {0}")]
    CompilationError(String),

    /// Template rendering failed.
    #[error("template rendering failed: {0}")]
    RenderError(String),

    /// Required field is missing.
    #[error("required field '{0}' is missing")]
    MissingField(String),

    /// Invalid template format.
    #[error("invalid template format: {0}")]
    InvalidFormat(String),

    /// Picoschema conversion failed.
    #[error("picoschema conversion failed: {0}")]
    PicoschemaError(String),

    /// Tool resolution failed.
    #[error("tool resolution failed: {0}")]
    ToolResolutionError(String),

    /// Schema resolution failed.
    #[error("schema resolution failed: {0}")]
    SchemaResolutionError(String),

    /// Regex pattern error.
    #[error("regex pattern error: {0}")]
    RegexError(#[from] regex::Error),

    /// Handlebars error.
    #[error("handlebars error: {0}")]
    HandlebarsError(#[from] handlebars::RenderError),
}
