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

//! Formatter for `.prompt` files.
//!
//! This module provides consistent formatting for Dotprompt files,
//! including YAML frontmatter and Handlebars templates.
//!
//! # Formatting Rules
//!
//! - Consistent 2-space indentation
//! - Normalized Handlebars spacing: `{{ variable }}` not `{{variable}}`
//! - Trimmed trailing whitespace
//! - Ensured final newline
//! - Blank line between frontmatter and template

use regex::Regex;

/// Formatter configuration options.
#[derive(Debug, Clone)]
pub(crate) struct FormatterConfig {
    /// Number of spaces for indentation (reserved for future use).
    #[allow(dead_code)]
    pub indent_size: usize,
    /// Whether to add spaces inside Handlebars expressions.
    pub handlebars_spacing: bool,
    /// Whether to trim trailing whitespace.
    pub trim_trailing_whitespace: bool,
    /// Whether to ensure a final newline.
    pub ensure_final_newline: bool,
}

impl Default for FormatterConfig {
    fn default() -> Self {
        Self {
            indent_size: 2,
            handlebars_spacing: true,
            trim_trailing_whitespace: true,
            ensure_final_newline: true,
        }
    }
}

/// The formatter for `.prompt` files.
#[derive(Debug)]
pub(crate) struct Formatter {
    config: FormatterConfig,
    /// Regex for matching Handlebars expressions without spacing.
    expr_regex: Option<Regex>,
}

impl Default for Formatter {
    fn default() -> Self {
        Self::new(FormatterConfig::default())
    }
}

impl Formatter {
    /// Creates a new formatter with the given configuration.
    #[must_use]
    pub(crate) fn new(config: FormatterConfig) -> Self {
        // Match {{ or {{# or {{/ or {{> followed by non-space content
        let expr_regex = Regex::new(r"\{\{([#/>!]?)(\S)").ok();

        Self { config, expr_regex }
    }

    /// Formats a `.prompt` file source.
    ///
    /// # Arguments
    ///
    /// * `source` - The source content of the `.prompt` file
    ///
    /// # Returns
    ///
    /// The formatted source.
    #[must_use]
    pub(crate) fn format(&self, source: &str) -> String {
        let mut result = source.to_string();

        // Apply formatting rules
        result = self.format_handlebars_spacing(&result);
        result = self.trim_trailing_whitespace(&result);
        result = self.normalize_frontmatter_spacing(&result);
        result = self.ensure_final_newline(&result);

        result
    }

    /// Adds spacing inside Handlebars expressions.
    ///
    /// This adds consistent spacing: `{{ variable }}` not `{{variable}}`.
    /// Block helpers preserve their prefix: `{{#if}}` stays as `{{#if }}`, not `{{# if }}`.
    fn format_handlebars_spacing(&self, source: &str) -> String {
        if !self.config.handlebars_spacing {
            return source.to_string();
        }

        let mut result = source.to_string();

        // Add space after opening braces for simple expressions: {{x -> {{ x
        // For block/partial/comment prefixes (#, /, >, !), keep them attached: {{#if -> {{#if
        if let Some(re) = &self.expr_regex {
            result = re
                .replace_all(&result, |caps: &regex::Captures| {
                    let prefix = caps.get(1).map_or("", |m| m.as_str());
                    let first_char = caps.get(2).map_or("", |m| m.as_str());
                    if prefix.is_empty() {
                        // Simple expression like {{variable}} -> {{ variable
                        format!("{{{{ {first_char}")
                    } else {
                        // Block/partial/comment like {{#if or {{/if -> no extra space after prefix
                        format!("{{{{{prefix}{first_char}")
                    }
                })
                .to_string();
        }

        // Add space before closing braces: x}} -> x }}
        // But be careful not to add space after space
        let closing_re = Regex::new(r"(\S)\}\}").ok();
        if let Some(re) = closing_re {
            result = re
                .replace_all(&result, |caps: &regex::Captures| {
                    let last_char = caps.get(1).map_or("", |m| m.as_str());
                    format!("{last_char} }}}}")
                })
                .to_string();
        }

        result
    }

    /// Trims trailing whitespace from each line.
    fn trim_trailing_whitespace(&self, source: &str) -> String {
        if !self.config.trim_trailing_whitespace {
            return source.to_string();
        }

        source
            .lines()
            .map(str::trim_end)
            .collect::<Vec<_>>()
            .join("\n")
    }

    /// Ensures there's a blank line after the frontmatter closing ---.
    #[allow(clippy::unused_self)] // May use config in future
    fn normalize_frontmatter_spacing(&self, source: &str) -> String {
        // Simple approach: find second --- and ensure blank line after
        let lines: Vec<&str> = source.lines().collect();
        let mut in_frontmatter = false;
        let mut output_lines: Vec<String> = Vec::new();

        for (i, line) in lines.iter().enumerate() {
            output_lines.push((*line).to_string());

            if *line == "---" {
                if in_frontmatter {
                    // This is the closing ---
                    // Check if next line exists and is not blank
                    if i + 1 < lines.len() && !lines[i + 1].is_empty() {
                        output_lines.push(String::new());
                    }
                    in_frontmatter = false;
                } else {
                    in_frontmatter = true;
                }
            }
        }

        output_lines.join("\n")
    }

    /// Ensures the file ends with a newline.
    fn ensure_final_newline(&self, source: &str) -> String {
        if !self.config.ensure_final_newline {
            return source.to_string();
        }

        if source.ends_with('\n') {
            source.to_string()
        } else {
            format!("{source}\n")
        }
    }

    /// Checks if a file needs formatting.
    ///
    /// # Returns
    ///
    /// `true` if the formatted output differs from the input.
    #[must_use]
    pub(crate) fn needs_formatting(&self, source: &str) -> bool {
        self.format(source) != source
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_handlebars_spacing() {
        let formatter = Formatter::default();

        let input = "Hello {{name}}!";
        let output = formatter.format(input);
        assert!(
            output.contains("{{ name }}"),
            "Expected spaced handlebars: {output}"
        );
    }

    #[test]
    fn test_trim_trailing_whitespace() {
        let formatter = Formatter::default();

        let input = "Hello world   \nSecond line  \n";
        let output = formatter.format(input);
        assert!(!output.contains("   \n"), "Expected no trailing whitespace");
        assert!(output.contains("Hello world\n"), "Expected trimmed line");
    }

    #[test]
    fn test_ensure_final_newline() {
        let formatter = Formatter::default();

        let input = "Hello world";
        let output = formatter.format(input);
        assert!(output.ends_with('\n'), "Expected final newline");

        // Already has newline
        let input2 = "Hello world\n";
        let output2 = formatter.format(input2);
        assert_eq!(output2, "Hello world\n", "Should not double newline");
    }

    #[test]
    fn test_needs_formatting() {
        let formatter = Formatter::default();

        // Needs formatting
        assert!(formatter.needs_formatting("Hello {{name}}"));

        // Already formatted
        assert!(!formatter.needs_formatting("Hello {{ name }}\n"));
    }

    #[test]
    fn test_format_full_prompt() {
        let formatter = Formatter::default();

        let input = r"---
model: gemini-2.0-flash
config:
  temperature: 0.7
---
Hello {{name}}!   
{{#each items}}
  - {{this}}
{{/each}}";

        let output = formatter.format(input);

        // Should have spacing in handlebars
        assert!(output.contains("{{ name }}"), "Expected spaced name");
        // Should have final newline
        assert!(output.ends_with('\n'), "Expected final newline");
        // Should have trimmed trailing whitespace
        assert!(
            !output.contains("!   \n"),
            "Expected no trailing whitespace"
        );
    }

    #[test]
    fn test_format_block_helpers_preserve_prefix() {
        let formatter = Formatter::default();

        // Test {{#if}} - should preserve # attached to helper
        let input = "{{#if condition}}content{{/if}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{#if "),
            "Expected {{#if with space after helper, got: {output}"
        );
        assert!(
            !output.contains("{{# if"),
            "Should NOT have space between # and if, got: {output}"
        );
        assert!(
            output.contains("{{/if }"),
            "Expected {{/if with space before }}, got: {output}"
        );
        assert!(
            !output.contains("{{/ if"),
            "Should NOT have space between / and if, got: {output}"
        );
    }

    #[test]
    fn test_format_each_helper() {
        let formatter = Formatter::default();

        let input = "{{#each items}}{{this}}{{/each}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{#each "),
            "Expected {{#each, got: {output}"
        );
        assert!(
            !output.contains("{{# each"),
            "Should NOT have space after #, got: {output}"
        );
        assert!(
            output.contains("{{/each }"),
            "Expected {{/each }}, got: {output}"
        );
    }

    #[test]
    fn test_format_partial_helper() {
        let formatter = Formatter::default();

        let input = "{{>partialName}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{>partialName }"),
            "Expected {{>partialName }}, got: {output}"
        );
        assert!(
            !output.contains("{{> partialName"),
            "Should NOT have space after >, got: {output}"
        );
    }

    #[test]
    fn test_format_comment() {
        let formatter = Formatter::default();

        let input = "{{!comment}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{!comment }"),
            "Expected {{!comment }}, got: {output}"
        );
        assert!(
            !output.contains("{{! comment"),
            "Should NOT have space after !, got: {output}"
        );
    }

    #[test]
    fn test_format_role_helper() {
        let formatter = Formatter::default();

        let input = "{{#role \"system\"}}content{{/role}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{#role "),
            "Expected {{#role, got: {output}"
        );
        assert!(
            !output.contains("{{# role"),
            "Should NOT have space after #, got: {output}"
        );
    }

    #[test]
    fn test_format_unless_helper() {
        let formatter = Formatter::default();

        let input = "{{#unless disabled}}enabled{{/unless}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{#unless "),
            "Expected {{#unless, got: {output}"
        );
        assert!(
            !output.contains("{{# unless"),
            "Should NOT have space after #, got: {output}"
        );
    }

    #[test]
    fn test_format_with_helper() {
        let formatter = Formatter::default();

        let input = "{{#with user}}{{name}}{{/with}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{#with "),
            "Expected {{#with, got: {output}"
        );
        assert!(
            !output.contains("{{# with"),
            "Should NOT have space after #, got: {output}"
        );
    }

    #[test]
    fn test_format_simple_expression_gets_space() {
        let formatter = Formatter::default();

        // Simple expressions should get space after {{
        let input = "{{variable}}";
        let output = formatter.format(input);
        assert!(
            output.contains("{{ variable }}"),
            "Expected {{ variable }}, got: {output}"
        );
    }
}
