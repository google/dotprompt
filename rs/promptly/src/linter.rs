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

//! Linter for `.prompt` files.
//!
//! This module provides static analysis for Dotprompt files, detecting errors
//! and warnings with Rust-style diagnostic messages.
//!
//! # Lint Rules
//!
//! ## Errors
//!
//! | Code | Description |
//! |------|-------------|
//! | invalid-yaml | Invalid YAML frontmatter |
//! | unclosed-block | Handlebars block not closed |
//! | unmatched-closing-block | Closing block without matching open |
//! | missing-partial | Referenced partial not found |
//! | circular-partial | Circular partial dependency |
//!
//! ## Hints
//!
//! | Code | Description |
//! |------|-------------|
//! | unverified-partial | Partial template used (verify it exists) |
//!
//! ## Warnings
//!
//! | Code | Description |
//! |------|-------------|
//! | unused-variable | Variable in schema but not used |
//! | undefined-variable | Variable used but not in schema |

use std::collections::HashSet;
use std::fs;
use std::path::Path;

use clap::ValueEnum;
use regex::Regex;
use serde::{Deserialize, Serialize};

use crate::span::{Span, position_at_offset};

/// Diagnostic severity levels.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) enum DiagnosticSeverity {
    /// An error that must be fixed.
    Error,
    /// A warning that should be addressed.
    Warning,
    /// Informational hint.
    Info,
}

/// Output format for diagnostics.
#[derive(Debug, Clone, Copy, Default, ValueEnum)]
pub(crate) enum OutputFormat {
    /// Human-readable text format.
    #[default]
    Text,
    /// Machine-readable JSON format.
    Json,
}

/// A diagnostic message from the linter.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub(crate) struct Diagnostic {
    /// The error/warning code (e.g., "invalid-yaml", "unclosed-block").
    pub code: String,
    /// The severity of the diagnostic.
    pub severity: DiagnosticSeverity,
    /// The diagnostic message.
    pub message: String,
    /// Optional help text with suggestions.
    pub help: Option<String>,
    /// Optional source span where the issue occurred.
    pub span: Option<Span>,
}

impl Diagnostic {
    /// Creates a new error diagnostic.
    #[must_use]
    pub(crate) fn error(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.to_string(),
            severity: DiagnosticSeverity::Error,
            message: message.into(),
            help: None,
            span: None,
        }
    }

    /// Creates a new info diagnostic.
    #[must_use]
    pub(crate) fn info(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.to_string(),
            severity: DiagnosticSeverity::Info,
            message: message.into(),
            help: None,
            span: None,
        }
    }

    /// Creates a new warning diagnostic.
    #[must_use]
    pub(crate) fn warning(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.to_string(),
            severity: DiagnosticSeverity::Warning,
            message: message.into(),
            help: None,
            span: None,
        }
    }

    /// Adds help text to the diagnostic.
    #[must_use]
    pub(crate) fn with_help(mut self, help: impl Into<String>) -> Self {
        self.help = Some(help.into());
        self
    }

    /// Adds a source span to the diagnostic.
    #[must_use]
    pub(crate) const fn with_span(mut self, span: Span) -> Self {
        self.span = Some(span);
        self
    }
}

/// The linter for `.prompt` files.
#[derive(Debug, Default)]
pub(crate) struct Linter {
    /// Regex for detecting partial references.
    partial_regex: Option<Regex>,
}

impl Linter {
    /// Creates a new linter instance.
    #[must_use]
    pub(crate) fn new() -> Self {
        Self {
            partial_regex: Regex::new(r"\{\{>\s*([\w-]+)\s*\}\}").ok(),
        }
    }

    /// Lints a `.prompt` file source and returns diagnostics.
    ///
    /// # Arguments
    ///
    /// * `source` - The source content of the `.prompt` file
    /// * `path` - Optional file path for error messages
    ///
    /// # Returns
    ///
    /// A vector of diagnostics found in the source.
    #[must_use]
    pub(crate) fn lint(&self, source: &str, path: Option<&Path>) -> Vec<Diagnostic> {
        let mut diagnostics = Vec::new();

        // Check YAML frontmatter syntax
        self.check_yaml_frontmatter(source, &mut diagnostics);

        // Check Handlebars syntax (blocks, braces)
        self.check_handlebars_syntax(source, &mut diagnostics);

        // Check partial references and resolution
        self.check_partial_references(source, path, &mut diagnostics);

        // Check for circular partial dependencies
        self.check_circular_partials(source, path, &mut diagnostics);

        // Check for unused/undefined variables
        Self::check_variables(source, &mut diagnostics);

        diagnostics
    }

    /// Extracts partial names from a template source.
    fn extract_partial_names(&self, source: &str) -> Vec<String> {
        let template = match Self::extract_frontmatter_and_body(source) {
            Ok((_, body)) => body,
            Err(_) => source.to_string(),
        };

        let mut partials = Vec::new();
        if let Some(re) = &self.partial_regex {
            for cap in re.captures_iter(&template) {
                if let Some(name) = cap.get(1) {
                    partials.push(name.as_str().to_string());
                }
            }
        }
        partials
    }

    /// Extracts variable names used in the template with their positions.
    /// Returns a `HashMap` mapping variable name to (line, column) position.
    fn extract_template_variables_with_positions(
        source: &str,
    ) -> std::collections::HashMap<String, (u32, u32)> {
        let body_start_line = Self::calculate_body_start_line(source);
        let template = match Self::extract_frontmatter_and_body(source) {
            Ok((_, body)) => body,
            Err(_) => source.to_string(),
        };

        let mut variables = std::collections::HashMap::new();
        // Match {{ variable }} but not {{#block}}, {{/block}}, {{>partial}}, {{!comment}}
        let var_regex = Regex::new(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}").ok();
        if let Some(re) = var_regex {
            for cap in re.captures_iter(&template) {
                if let Some(name) = cap.get(1) {
                    let var_name = name.as_str();
                    // Skip built-in helpers and keywords
                    if !["this", "else", "true", "false", "null"].contains(&var_name) {
                        let offset = cap.get(0).map_or(0, |m| m.start());
                        let pos = position_at_offset(&template, offset);
                        let abs_line = pos.line + body_start_line - 1;
                        variables
                            .entry(var_name.to_string())
                            .or_insert((abs_line, pos.column));
                    }
                }
            }
        }
        variables
    }

    /// Parses schema variable names from YAML frontmatter.
    #[allow(clippy::collapsible_if)] // Using nested ifs for stable Rust compatibility (no let-chains)
    fn parse_schema_variables(source: &str) -> HashSet<String> {
        let mut variables = HashSet::new();

        if let Ok((yaml, _)) = Self::extract_frontmatter_and_body(source) {
            if let Ok(value) = serde_yaml::from_str::<serde_yaml::Value>(&yaml) {
                // Look for input.schema.properties or input.schema directly
                if let Some(input) = value.get("input") {
                    if let Some(schema) = input.get("schema") {
                        Self::extract_schema_keys(schema, &mut variables);
                    }
                }
            }
        }
        variables
    }

    /// Recursively extracts keys from a schema object.
    fn extract_schema_keys(schema: &serde_yaml::Value, variables: &mut HashSet<String>) {
        // Handle shorthand: { name: string, age: number }
        if let Some(obj) = schema.as_mapping() {
            for (key, _value) in obj {
                if let Some(key_str) = key.as_str() {
                    // Skip JSON Schema keywords
                    if ![
                        "type",
                        "properties",
                        "required",
                        "items",
                        "description",
                        "default",
                        "enum",
                    ]
                    .contains(&key_str)
                    {
                        variables.insert(key_str.to_string());
                    }
                }
            }
            // Also check properties if it exists
            if let Some(props) = schema.get("properties") {
                Self::extract_schema_keys(props, variables);
            }
        }
    }

    /// Extracts frontmatter and body from a prompt source.
    fn extract_frontmatter_and_body(source: &str) -> Result<(String, String), String> {
        // Find the first --- (start of frontmatter)
        let Some(first_delimiter) = source.find("---") else {
            return Ok((String::new(), source.to_string()));
        };

        // Find the closing ---
        let after_first = &source[first_delimiter + 3..];
        after_first.find("\n---").map_or_else(
            || Err("Frontmatter not properly closed with ---".to_string()),
            |end_pos| {
                let frontmatter = after_first[..end_pos].trim().to_string();
                let body = after_first[end_pos + 4..].to_string();
                Ok((frontmatter, body))
            },
        )
    }

    /// Calculates the line number where the body starts (1-indexed).
    /// This counts all lines in the source up to and including the closing --- delimiter.
    /// Returns 0 if no frontmatter is found.
    /// Body positions should use: `pos.line + body_start_line - 1` for absolute line numbers.
    fn calculate_body_start_line(source: &str) -> u32 {
        // Find the first --- (start of frontmatter)
        let Some(first_delimiter) = source.find("---") else {
            return 0;
        };

        // Count lines before the first ---
        #[allow(clippy::cast_possible_truncation)]
        let lines_before_start = source[..first_delimiter].matches('\n').count() as u32;

        // Find the closing --- after the first one
        let after_first = &source[first_delimiter + 3..];
        let Some(closing_pos) = after_first.find("\n---") else {
            return 0;
        };

        // Count lines within the frontmatter content
        let frontmatter_content = &after_first[..closing_pos];
        #[allow(clippy::cast_possible_truncation)]
        let frontmatter_lines = frontmatter_content.matches('\n').count() as u32;

        // Total: lines_before + 1 (opening ---) + frontmatter_lines + 1 (closing --- line)
        // The body starts on the line AFTER the closing ---
        lines_before_start + 1 + frontmatter_lines + 1
    }

    /// Checks YAML frontmatter for syntax errors (E001).
    #[allow(clippy::unused_self)] // May use config in future
    fn check_yaml_frontmatter(&self, source: &str, diagnostics: &mut Vec<Diagnostic>) {
        match Self::extract_frontmatter_and_body(source) {
            Ok((yaml, _)) => {
                if !yaml.is_empty() {
                    // Try to parse the YAML to check for errors
                    if let Err(e) = serde_yaml::from_str::<serde_yaml::Value>(&yaml) {
                        let msg = format!(
                            "The YAML configuration at the top of this file has a syntax error: {e}"
                        );
                        let mut diag = Diagnostic::error("invalid-yaml", msg).with_help(
                            "Check for proper indentation, colons after keys, and matching quotes",
                        );

                        // Try to extract line number from YAML error
                        if let Some(location) = e.location() {
                            #[allow(clippy::cast_possible_truncation)]
                            let line = location.line() as u32;
                            #[allow(clippy::cast_possible_truncation)]
                            let column = location.column() as u32;
                            diag = diag.with_span(Span::from_line_col(line, column, line, column));
                        }

                        diagnostics.push(diag);
                    }
                }
            }
            Err(e) => {
                diagnostics.push(
                    Diagnostic::error(
                        "invalid-yaml",
                        format!("Could not find the end of the YAML configuration: {e}"),
                    )
                    .with_help(
                        "Make sure the configuration starts and ends with --- on its own line",
                    ),
                );
            }
        }
    }

    /// Checks Handlebars syntax for errors (E002).
    #[allow(clippy::unused_self)] // May use config in future
    fn check_handlebars_syntax(&self, source: &str, diagnostics: &mut Vec<Diagnostic>) {
        // Calculate the line offset where body starts
        let body_start_line = Self::calculate_body_start_line(source);

        // Extract the template body
        let template = match Self::extract_frontmatter_and_body(source) {
            Ok((_, body)) => body,
            Err(_) => source.to_string(),
        };

        // Check for unbalanced Handlebars blocks
        let mut block_stack: Vec<(String, usize)> = Vec::new();

        // Find all block starts and ends
        let block_start_re = Regex::new(r"\{\{#(\w+)").ok();
        let block_end_re = Regex::new(r"\{\{/(\w+)").ok();

        if let Some(re) = &block_start_re {
            for cap in re.captures_iter(&template) {
                if let Some(name) = cap.get(1) {
                    let offset = cap.get(0).map_or(0, |m| m.start());
                    block_stack.push((name.as_str().to_string(), offset));
                }
            }
        }

        if let Some(re) = &block_end_re {
            for cap in re.captures_iter(&template) {
                if let Some(name) = cap.get(1) {
                    let block_name = name.as_str();
                    let offset = cap.get(0).map_or(0, |m| m.start());

                    // Look for matching opening block
                    if let Some(pos) = block_stack.iter().rposition(|(n, _)| n == block_name) {
                        block_stack.remove(pos);
                    } else {
                        let pos = position_at_offset(&template, offset);
                        diagnostics.push(
                            Diagnostic::error(
                                "unmatched-closing-block",
                                format!("Found '{{{{/{block_name}}}}}' but no matching '{{{{#{block_name}}}}}' was opened"),
                            )
                            .with_span(Span::from_line_col(
                                pos.line + body_start_line - 1,
                                pos.column,
                                pos.line + body_start_line - 1,
                                pos.column,
                            ))
                            .with_help(format!("Either add '{{{{#{block_name}}}}}' before this, or remove this closing tag")),
                        );
                    }
                }
            }
        }

        // Report unclosed blocks
        for (name, offset) in block_stack {
            let pos = position_at_offset(&template, offset);
            diagnostics.push(
                Diagnostic::error(
                    "unclosed-block",
                    format!("Block '{{{{#{name}}}}}' was never closed"),
                )
                .with_span(Span::from_line_col(
                    pos.line + body_start_line - 1,
                    pos.column,
                    pos.line + body_start_line - 1,
                    pos.column,
                ))
                .with_help(format!(
                    "Add '{{{{/{name}}}}}' somewhere after this to close the block"
                )),
            );
        }

        // Check for unbalanced braces
        let mut brace_count = 0i32;
        let mut in_handlebars = false;

        for (i, ch) in template.chars().enumerate() {
            if ch == '{' {
                brace_count += 1;
                if brace_count >= 2 {
                    in_handlebars = true;
                }
            } else if ch == '}' {
                brace_count -= 1;
                if brace_count < 0 {
                    let pos = position_at_offset(&template, i);
                    diagnostics.push(
                        Diagnostic::error(
                            "unbalanced-brace",
                            "Found a closing '}}' without a matching opening '{{'",
                        )
                        .with_span(Span::from_line_col(
                            pos.line + body_start_line - 1,
                            pos.column,
                            pos.line + body_start_line - 1,
                            pos.column,
                        ))
                        .with_help(
                            "Add the missing opening braces or remove the extra closing braces",
                        ),
                    );
                    brace_count = 0;
                }
                if brace_count == 0 {
                    in_handlebars = false;
                }
            } else if !in_handlebars {
                brace_count = 0;
            }
        }
    }

    /// Checks for partial references (E003).
    fn check_partial_references(
        &self,
        source: &str,
        _path: Option<&Path>,
        diagnostics: &mut Vec<Diagnostic>,
    ) {
        // Calculate the line offset where body starts
        let body_start_line = Self::calculate_body_start_line(source);

        // Extract the template body
        let template = match Self::extract_frontmatter_and_body(source) {
            Ok((_, body)) => body,
            Err(_) => source.to_string(),
        };

        // Find all partial references
        if let Some(re) = &self.partial_regex {
            for cap in re.captures_iter(&template) {
                if let Some(name) = cap.get(1) {
                    let partial_name = name.as_str();
                    let offset = cap.get(0).map_or(0, |m| m.start());

                    // For now, just emit an info diagnostic about partials found
                    // Full resolution requires access to the file system
                    let pos = position_at_offset(&template, offset);
                    diagnostics.push(
                        Diagnostic::info(
                            "unverified-partial",
                            format!("Uses partial template '{partial_name}' — ensure this partial exists"),
                        )
                            .with_span(Span::from_line_col(
                                pos.line + body_start_line - 1,
                                pos.column,
                                pos.line + body_start_line - 1,
                                pos.column,
                            )),
                    );
                }
            }
        }
    }

    /// Checks for circular partial dependencies.
    fn check_circular_partials(
        &self,
        source: &str,
        path: Option<&Path>,
        diagnostics: &mut Vec<Diagnostic>,
    ) {
        let Some(file_path) = path else { return };
        let Some(parent_dir) = file_path.parent() else {
            return;
        };

        let partials = self.extract_partial_names(source);
        if partials.is_empty() {
            return;
        }

        // Get the current file's stem for cycle detection
        let current_name = file_path.file_stem().and_then(|s| s.to_str()).unwrap_or("");

        // DFS to detect cycles
        let mut visited = HashSet::new();
        let mut path_stack = vec![current_name.to_string()];

        for partial in &partials {
            if let Some(cycle) = self.find_cycle(parent_dir, partial, &mut visited, &mut path_stack)
            {
                diagnostics.push(
                    Diagnostic::error(
                        "circular-partial",
                        format!("Circular dependency detected: {}", cycle.join(" → ")),
                    )
                    .with_help("Break the cycle by removing one of the partial references"),
                );
            }
        }
    }

    /// DFS helper to find cycles in partial dependencies.
    fn find_cycle(
        &self,
        base_dir: &Path,
        partial_name: &str,
        visited: &mut HashSet<String>,
        path_stack: &mut Vec<String>,
    ) -> Option<Vec<String>> {
        // Check if this creates a cycle
        if path_stack.contains(&partial_name.to_string()) {
            let mut cycle = path_stack.clone();
            cycle.push(partial_name.to_string());
            return Some(cycle);
        }

        // Skip if already visited in another branch
        if visited.contains(partial_name) {
            return None;
        }

        // Try to read the partial file
        let partial_path = base_dir.join(format!("{partial_name}.prompt"));
        let Ok(partial_source) = fs::read_to_string(&partial_path) else {
            return None; // File doesn't exist, handled by missing-partial check
        };

        visited.insert(partial_name.to_string());
        path_stack.push(partial_name.to_string());

        // Check nested partials
        let nested_partials = self.extract_partial_names(&partial_source);
        for nested in &nested_partials {
            if let Some(cycle) = self.find_cycle(base_dir, nested, visited, path_stack) {
                return Some(cycle);
            }
        }

        path_stack.pop();
        None
    }

    /// Checks for unused and undefined variables.
    fn check_variables(source: &str, diagnostics: &mut Vec<Diagnostic>) {
        let schema_vars = Self::parse_schema_variables(source);
        let template_vars = Self::extract_template_variables_with_positions(source);
        let template_var_names: HashSet<_> = template_vars.keys().cloned().collect();

        // Skip if no schema defined
        if schema_vars.is_empty() {
            return;
        }

        // Check for unused variables (in schema but not template)
        // For unused vars, point to input.schema section (roughly line 5-6 in most files)
        for var in &schema_vars {
            if !template_var_names.contains(var) {
                diagnostics.push(
                    Diagnostic::warning(
                        "unused-variable",
                        format!("Variable '{var}' is defined in schema but never used in template"),
                    )
                    .with_help("Remove from schema if not needed, or use it in the template"),
                );
            }
        }

        // Check for undefined variables (in template but not schema)
        // For undefined vars, point to where the variable is used
        for (var, (line, col)) in &template_vars {
            if !schema_vars.contains(var) {
                diagnostics.push(
                    Diagnostic::warning(
                        "undefined-variable",
                        format!("Variable '{var}' is used in template but not defined in schema"),
                    )
                    .with_span(Span::from_line_col(*line, *col, *line, *col))
                    .with_help("Add to input.schema in frontmatter, or remove from template"),
                );
            }
        }
    }
}

#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::expect_used, clippy::needless_collect)]
mod tests {
    use super::*;

    #[test]
    fn test_lint_valid_prompt() {
        let source = r"---
model: gemini-2.0-flash
config:
  temperature: 0.7
---
Hello {{name}}!
";

        let linter = Linter::new();
        let diagnostics = linter.lint(source, None);

        // Should have no errors or warnings
        let errors: Vec<_> = diagnostics
            .iter()
            .filter(|d| d.severity == DiagnosticSeverity::Error)
            .collect();
        assert!(errors.is_empty(), "Expected no errors, got: {errors:?}");
    }

    #[test]
    fn test_lint_invalid_yaml() {
        let source = r#"---
model: gemini-2.0-flash
config:
  temperature: "not a number
---
Hello world!
"#;

        let linter = Linter::new();
        let diagnostics = linter.lint(source, None);

        let errors: Vec<_> = diagnostics
            .iter()
            .filter(|d| d.code == "invalid-yaml")
            .collect();
        assert!(
            !errors.is_empty(),
            "Expected invalid-yaml error for invalid YAML"
        );
    }

    #[test]
    fn test_lint_unclosed_block() {
        let source = r#"---
model: gemini-2.0-flash
---
{{#role "user"}}
Hello world!
"#;

        let linter = Linter::new();
        let diagnostics = linter.lint(source, None);

        let errors: Vec<_> = diagnostics
            .iter()
            .filter(|d| d.code == "unclosed-block")
            .collect();
        assert!(
            !errors.is_empty(),
            "Expected unclosed-block error for unclosed block"
        );
    }

    #[test]
    fn test_calculate_body_start_line_no_frontmatter() {
        let source = "Hello world!";
        assert_eq!(Linter::calculate_body_start_line(source), 0);
    }

    #[test]
    fn test_calculate_body_start_line_simple_frontmatter() {
        // 3 lines: ---, model: ..., ---
        let source = "---\nmodel: gemini\n---\nHello";
        assert_eq!(Linter::calculate_body_start_line(source), 3);
    }

    #[test]
    fn test_calculate_body_start_line_multiline_frontmatter() {
        // 5 lines: ---, model, config, temp, ---
        let source = "---\nmodel: gemini\nconfig:\n  temp: 0.7\n---\nHello";
        assert_eq!(Linter::calculate_body_start_line(source), 5);
    }

    #[test]
    fn test_unclosed_block_reports_correct_line_number() {
        // Lines:
        // 1: ---
        // 2: model: gemini
        // 3: ---
        // 4: Hello
        // 5: {{#if test}}
        // 6: content
        let source = "---\nmodel: gemini\n---\nHello\n{{#if test}}\ncontent";

        let linter = Linter::new();
        let diagnostics = linter.lint(source, None);

        let unclosed: Vec<_> = diagnostics
            .iter()
            .filter(|d| d.code == "unclosed-block")
            .collect();

        assert_eq!(
            unclosed.len(),
            1,
            "Expected exactly one unclosed-block error"
        );

        let span = unclosed[0]
            .span
            .as_ref()
            .expect("Expected span on diagnostic");
        assert_eq!(
            span.start.line, 5,
            "Unclosed block should be on line 5, got line {}",
            span.start.line
        );
    }

    #[test]
    fn test_partial_reference_reports_correct_line_number() {
        // Lines:
        // 1: ---
        // 2: model: gemini
        // 3: ---
        // 4: Hello
        // 5:
        // 6: {{>myPartial}}
        let source = "---\nmodel: gemini\n---\nHello\n\n{{>myPartial}}";

        let linter = Linter::new();
        let diagnostics = linter.lint(source, None);

        let partials: Vec<_> = diagnostics
            .iter()
            .filter(|d| d.code == "unverified-partial")
            .collect();

        assert_eq!(partials.len(), 1, "Expected exactly one unverified-partial");

        let span = partials[0]
            .span
            .as_ref()
            .expect("Expected span on diagnostic");
        assert_eq!(
            span.start.line, 6,
            "Partial reference should be on line 6, got line {}",
            span.start.line
        );
    }

    #[test]
    fn test_yaml_error_reports_correct_line_number() {
        // Lines:
        // 1: ---
        // 2: model: gemini
        // 3: config:
        // 4:   temp: "unclosed string
        // 5: ---
        // 6: Hello
        let source = "---\nmodel: gemini\nconfig:\n  temp: \"unclosed\n---\nHello";

        let linter = Linter::new();
        let diagnostics = linter.lint(source, None);

        let yaml_errors: Vec<_> = diagnostics
            .iter()
            .filter(|d| d.code == "invalid-yaml")
            .collect();

        assert_eq!(
            yaml_errors.len(),
            1,
            "Expected exactly one invalid-yaml error"
        );

        // YAML errors should have a span (though exact line depends on parser)
        let span = yaml_errors[0]
            .span
            .as_ref()
            .expect("Expected span on YAML error");
        assert!(
            span.start.line >= 1 && span.start.line <= 5,
            "YAML error line should be within frontmatter (1-5), got {}",
            span.start.line
        );
    }
}
