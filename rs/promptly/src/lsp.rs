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

//! Language Server Protocol (LSP) backend for `.prompt` files.
//!
//! This module implements an LSP server that provides:
//! - Diagnostics (errors and warnings)
//! - Document formatting
//! - Hover documentation

use std::collections::HashMap;
use std::sync::{Arc, RwLock};

use tower_lsp::jsonrpc::Result;
use tower_lsp::lsp_types::Diagnostic as LspDiagnostic;
use tower_lsp::lsp_types::DiagnosticSeverity as LspDiagSeverity;
use tower_lsp::lsp_types::{
    DidChangeTextDocumentParams, DidCloseTextDocumentParams, DidOpenTextDocumentParams,
    DidSaveTextDocumentParams, DocumentFormattingParams, Hover, HoverContents, HoverParams,
    HoverProviderCapability, InitializeParams, InitializeResult, InitializedParams, MarkupContent,
    MarkupKind, MessageType, NumberOrString, OneOf, Position, Range, ServerCapabilities,
    ServerInfo, TextDocumentSyncCapability, TextDocumentSyncKind, TextEdit, Url,
};
use tower_lsp::{Client, LanguageServer, LspService, Server};

use crate::formatter::{Formatter, FormatterConfig};
use crate::linter::{DiagnosticSeverity as LintSeverity, Linter};

/// Documentation for built-in Handlebars helpers.
fn get_helper_docs(name: &str) -> Option<&'static str> {
    match name {
        "if" => Some(
            "## `{{#if condition}}`\n\n\
            Conditionally renders content based on a truthy value.\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{#if user}}\n  \
            Hello, {{user.name}}!\n\
            {{else}}\n  \
            Hello, guest!\n\
            {{/if}}\n\
            ```",
        ),
        "unless" => Some(
            "## `{{#unless condition}}`\n\n\
            Renders content only if the condition is falsy (inverse of `if`).\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{#unless loggedIn}}\n  \
            Please log in.\n\
            {{/unless}}\n\
            ```",
        ),
        "each" => Some(
            "## `{{#each array}}`\n\n\
            Iterates over an array or object.\n\n\
            **Variables:**\n\
            - `@index` - current index (arrays)\n\
            - `@key` - current key (objects)\n\
            - `@first` - true if first iteration\n\
            - `@last` - true if last iteration\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{#each items}}\n  \
            - {{this}}\n\
            {{/each}}\n\
            ```",
        ),
        "with" => Some(
            "## `{{#with context}}`\n\n\
            Changes the context for the enclosed block.\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{#with user}}\n  \
            Name: {{name}}\n  \
            Email: {{email}}\n\
            {{/with}}\n\
            ```",
        ),
        "json" => Some(
            "## `{{json value}}`\n\n\
            Serializes a value to JSON format.\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{json data}}\n\
            {{json data indent=2}}\n\
            ```",
        ),
        "role" => Some(
            "## `{{#role name}}`\n\n\
            Defines a message with a specific role (system, user, model).\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{#role \"system\"}}\n\
            You are a helpful assistant.\n\
            {{/role}}\n\n\
            {{#role \"user\"}}\n\
            {{query}}\n\
            {{/role}}\n\
            ```",
        ),
        "media" => Some(
            "## `{{media url}}`\n\n\
            Embeds media content (images, audio, video).\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{media imageUrl}}\n\
            {{media url=imageUrl contentType=\"image/png\"}}\n\
            ```",
        ),
        "section" => Some(
            "## `{{#section name}}`\n\n\
            Defines a named section for structured output.\n\n\
            **Example:**\n\
            ```handlebars\n\
            {{#section \"reasoning\"}}\n\
            Think step by step...\n\
            {{/section}}\n\
            ```",
        ),
        _ => None,
    }
}

/// Documentation for YAML frontmatter fields.
fn get_frontmatter_field_docs(field: &str) -> Option<&'static str> {
    match field {
        "model" => Some(
            "## `model`\n\n\
            Specifies the AI model to use.\n\n\
            **Example:**\n\
            ```yaml\n\
            model: googleai/gemini-2.5-flash\n\
            ```",
        ),
        "input" => Some(
            "## `input`\n\n\
            Defines the input schema for the prompt.\n\n\
            **Example:**\n\
            ```yaml\n\
            input:\n  \
              schema:\n    \
                type: object\n    \
                properties:\n      \
                  query: { type: string }\n\
            ```",
        ),
        "output" => Some(
            "## `output`\n\n\
            Defines the expected output format.\n\n\
            **Example:**\n\
            ```yaml\n\
            output:\n  \
              format: json\n  \
              schema:\n    \
                type: object\n\
            ```",
        ),
        "config" => Some(
            "## `config`\n\n\
            Model configuration options.\n\n\
            **Example:**\n\
            ```yaml\n\
            config:\n  \
              temperature: 0.7\n  \
              maxOutputTokens: 1024\n\
            ```",
        ),
        "tools" => Some(
            "## `tools`\n\n\
            List of tools available to the model.\n\n\
            **Example:**\n\
            ```yaml\n\
            tools:\n  \
              - search\n  \
              - calculator\n\
            ```",
        ),
        _ => None,
    }
}

/// Thread-safe document storage.
type DocumentStore = Arc<RwLock<HashMap<Url, String>>>;

/// The LSP backend for promptly.
#[derive(Debug)]
pub(crate) struct Backend {
    client: Client,
    linter: Arc<Linter>,
    formatter: Arc<Formatter>,
    /// Document content storage for formatting support.
    documents: DocumentStore,
}

impl Backend {
    /// Creates a new backend instance.
    pub(crate) fn new(client: Client) -> Self {
        Self {
            client,
            linter: Arc::new(Linter::new()),
            formatter: Arc::new(Formatter::new(FormatterConfig::default())),
            documents: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Publishes diagnostics for a document.
    async fn publish_diagnostics(&self, uri: Url, text: &str) {
        let diagnostics = self.linter.lint(text, None);

        let lsp_diagnostics: Vec<LspDiagnostic> = diagnostics
            .into_iter()
            .map(|d| {
                let severity = match d.severity {
                    LintSeverity::Error => Some(LspDiagSeverity::ERROR),
                    LintSeverity::Warning => Some(LspDiagSeverity::WARNING),
                    LintSeverity::Info => Some(LspDiagSeverity::INFORMATION),
                };

                let range = d.span.map_or_else(
                    || Range::new(Position::new(0, 0), Position::new(0, 0)),
                    |span| {
                        Range::new(
                            Position::new(
                                span.start.line.saturating_sub(1),
                                span.start.column.saturating_sub(1),
                            ),
                            Position::new(
                                span.end.line.saturating_sub(1),
                                span.end.column.saturating_sub(1),
                            ),
                        )
                    },
                );

                LspDiagnostic {
                    range,
                    severity,
                    code: Some(NumberOrString::String(d.code)),
                    code_description: None,
                    source: Some("promptly".to_string()),
                    message: d.message,
                    related_information: None,
                    tags: None,
                    data: None,
                }
            })
            .collect();

        self.client
            .publish_diagnostics(uri, lsp_diagnostics, None)
            .await;
    }

    /// Formats a document and returns text edits.
    fn format_document(&self, text: &str) -> Vec<TextEdit> {
        let formatted = self.formatter.format(text);

        if formatted == text {
            return Vec::new();
        }

        // Replace the entire document
        let lines: Vec<&str> = text.lines().collect();
        let last_line = lines.len().saturating_sub(1);
        #[allow(clippy::cast_possible_truncation)]
        let last_char = lines.last().map_or(0, |s| s.len()) as u32;

        vec![TextEdit {
            range: Range::new(
                Position::new(0, 0),
                #[allow(clippy::cast_possible_truncation)]
                Position::new(last_line as u32, last_char),
            ),
            new_text: formatted,
        }]
    }
}

#[tower_lsp::async_trait]
impl LanguageServer for Backend {
    async fn initialize(&self, _: InitializeParams) -> Result<InitializeResult> {
        Ok(InitializeResult {
            capabilities: ServerCapabilities {
                text_document_sync: Some(TextDocumentSyncCapability::Kind(
                    TextDocumentSyncKind::FULL,
                )),
                document_formatting_provider: Some(OneOf::Left(true)),
                hover_provider: Some(HoverProviderCapability::Simple(true)),
                ..Default::default()
            },
            server_info: Some(ServerInfo {
                name: "promptly".to_string(),
                version: Some(env!("CARGO_PKG_VERSION").to_string()),
            }),
        })
    }

    async fn initialized(&self, _: InitializedParams) {
        self.client
            .log_message(MessageType::INFO, "promptly LSP initialized")
            .await;
    }

    async fn shutdown(&self) -> Result<()> {
        Ok(())
    }

    async fn did_open(&self, params: DidOpenTextDocumentParams) {
        let uri = params.text_document.uri.clone();
        let text = params.text_document.text.clone();

        // Store the document content
        if let Ok(mut docs) = self.documents.write() {
            docs.insert(uri.clone(), text.clone());
        }

        self.publish_diagnostics(uri, &text).await;
    }

    async fn did_change(&self, params: DidChangeTextDocumentParams) {
        if let Some(change) = params.content_changes.into_iter().last() {
            let uri = params.text_document.uri.clone();
            let text = change.text.clone();

            // Update stored document content
            if let Ok(mut docs) = self.documents.write() {
                docs.insert(uri.clone(), text.clone());
            }

            self.publish_diagnostics(uri, &text).await;
        }
    }

    async fn did_save(&self, params: DidSaveTextDocumentParams) {
        if let Some(text) = params.text {
            self.publish_diagnostics(params.text_document.uri, &text)
                .await;
        }
    }

    async fn did_close(&self, params: DidCloseTextDocumentParams) {
        // Remove stored document content
        if let Ok(mut docs) = self.documents.write() {
            docs.remove(&params.text_document.uri);
        }

        // Clear diagnostics when document is closed
        self.client
            .publish_diagnostics(params.text_document.uri, Vec::new(), None)
            .await;
    }

    async fn formatting(&self, params: DocumentFormattingParams) -> Result<Option<Vec<TextEdit>>> {
        // Get the document content from our store
        let text = self
            .documents
            .read()
            .ok()
            .and_then(|docs| docs.get(&params.text_document.uri).cloned());

        Ok(text.map(|content| self.format_document(&content)))
    }

    async fn hover(&self, params: HoverParams) -> Result<Option<Hover>> {
        let uri = &params.text_document_position_params.text_document.uri;
        let position = params.text_document_position_params.position;

        // Get document content
        let text = self
            .documents
            .read()
            .ok()
            .and_then(|docs| docs.get(uri).cloned());

        let Some(content) = text else {
            return Ok(None);
        };

        // Get the line at the cursor position
        let lines: Vec<&str> = content.lines().collect();
        #[allow(clippy::cast_possible_truncation)]
        let line_idx = position.line as usize;

        if line_idx >= lines.len() {
            return Ok(None);
        }

        let line = lines[line_idx];
        #[allow(clippy::cast_possible_truncation)]
        let col = position.character as usize;

        // Check if we're in a Handlebars expression
        // Note: Using nested if-let instead of let-chains for Bazel compatibility
        // (rules_rust stable toolchain doesn't support let-chains yet)
        #[allow(clippy::collapsible_if)]
        if let Some(helper_name) = find_helper_at_position(line, col) {
            if let Some(docs) = get_helper_docs(&helper_name) {
                return Ok(Some(Hover {
                    contents: HoverContents::Markup(MarkupContent {
                        kind: MarkupKind::Markdown,
                        value: docs.to_string(),
                    }),
                    range: None,
                }));
            }
        }

        // Check if we're in YAML frontmatter
        #[allow(clippy::collapsible_if)]
        if is_in_frontmatter(&content, line_idx) {
            if let Some(field_name) = find_yaml_field_at_position(line, col) {
                if let Some(docs) = get_frontmatter_field_docs(&field_name) {
                    return Ok(Some(Hover {
                        contents: HoverContents::Markup(MarkupContent {
                            kind: MarkupKind::Markdown,
                            value: docs.to_string(),
                        }),
                        range: None,
                    }));
                }
            }
        }

        Ok(None)
    }
}

/// Finds a Handlebars helper name at the given column position.
fn find_helper_at_position(line: &str, col: usize) -> Option<String> {
    // Look for patterns like {{#helper, {{/helper, or {{helper
    let chars: Vec<char> = line.chars().collect();
    let line_len = chars.len();

    // Search backwards to find the start of a Handlebars expression
    let mut start = col.min(line_len);
    while start > 0 && chars[start - 1] != '{' {
        start -= 1;
    }

    // Check if we're in a {{ expression
    if start >= 2 && chars[start - 1] == '{' && chars[start - 2] == '{' {
        // Skip the opening braces and any # or /
        let mut name_start = start;
        while name_start < line_len && (chars[name_start] == '#' || chars[name_start] == '/') {
            name_start += 1;
        }

        // Extract the helper name
        let mut name_end = name_start;
        while name_end < line_len
            && (chars[name_end].is_alphanumeric()
                || chars[name_end] == '_'
                || chars[name_end] == '-')
        {
            name_end += 1;
        }

        if name_end > name_start {
            let name: String = chars[name_start..name_end].iter().collect();
            return Some(name);
        }
    }

    None
}

/// Checks if a line index is within the YAML frontmatter section.
fn is_in_frontmatter(content: &str, line_idx: usize) -> bool {
    let lines: Vec<&str> = content.lines().collect();

    // Frontmatter must start at line 0 with ---
    if lines.is_empty() || lines[0].trim() != "---" {
        return false;
    }

    // Find the closing ---
    for (i, line) in lines.iter().enumerate().skip(1) {
        if line.trim() == "---" {
            return line_idx > 0 && line_idx < i;
        }
    }

    false
}

/// Finds a YAML field name at the given column position.
fn find_yaml_field_at_position(line: &str, col: usize) -> Option<String> {
    // Look for pattern like "field:" at the start of the line
    let trimmed = line.trim_start();
    let indent = line.len() - trimmed.len();

    // Check if cursor is in the field name area
    if col < indent {
        return None;
    }

    // Find the field name (before the colon)
    if let Some(colon_idx) = trimmed.find(':') {
        let field_name = trimmed[..colon_idx].trim();
        if !field_name.is_empty() && !field_name.starts_with('-') {
            // Only return if cursor is on or near the field name
            let col_in_trimmed = col.saturating_sub(indent);
            if col_in_trimmed <= colon_idx + 1 {
                return Some(field_name.to_string());
            }
        }
    }

    None
}

/// Runs the LSP server.
///
/// # Errors
///
/// Returns an error if the server fails to start.
pub(crate) async fn run_server() -> std::result::Result<(), Box<dyn std::error::Error + Send + Sync>>
{
    let stdin = tokio::io::stdin();
    let stdout = tokio::io::stdout();

    let (service, socket) = LspService::new(Backend::new);
    Server::new(stdin, stdout, socket).serve(service).await;

    Ok(())
}
