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

//! Configuration management for promptly.
//!
//! This module handles loading and merging configuration from:
//! 1. `promptly.toml` files (searched in current and parent directories)
//! 2. CLI flags (which override config file settings)

use std::collections::HashSet;
use std::fs;
use std::path::Path;

use serde::Deserialize;

/// The name of the configuration file.
const CONFIG_FILE_NAME: &str = "promptly.toml";

/// Root configuration structure matching the TOML file format.
#[derive(Debug, Deserialize, Default)]
struct TomlConfig {
    /// Lint configuration section.
    #[serde(default)]
    lint: LintTomlConfig,
}

/// Lint section of the TOML configuration.
#[derive(Debug, Deserialize, Default)]
struct LintTomlConfig {
    /// Rules to allow (disable).
    #[serde(default)]
    allow: Vec<String>,

    /// Rules to deny (enable as errors).
    #[serde(default)]
    deny: Vec<String>,

    /// Treat warnings as errors.
    #[serde(default, rename = "warnings-as-errors")]
    warnings_as_errors: bool,

    /// File patterns to ignore.
    #[serde(default)]
    ignore: Vec<String>,
}

/// Runtime configuration for promptly.
#[derive(Debug, Default, Clone)]
pub(crate) struct Config {
    /// Rules to allow (disable).
    pub allow: HashSet<String>,

    /// Rules to deny (enable as errors).
    pub deny: HashSet<String>,

    /// Treat warnings as errors.
    pub warnings_as_errors: bool,

    /// File patterns to ignore (future use).
    #[allow(dead_code)]
    pub(crate) ignore: Vec<String>,
}

impl Config {
    /// Creates a new empty configuration.
    #[cfg(test)]
    pub(crate) fn new() -> Self {
        Self::default()
    }

    /// Loads configuration from `promptly.toml` by searching the current directory
    /// and all parent directories.
    ///
    /// # Arguments
    ///
    /// * `start_dir` - The directory to start searching from
    ///
    /// # Returns
    ///
    /// A `Config` loaded from the file, or default configuration if no file is found.
    #[must_use]
    #[allow(clippy::collapsible_if)] // Using nested ifs for stable Rust compatibility (no let-chains)
    pub(crate) fn load(start_dir: &Path) -> Self {
        let mut current = start_dir;

        loop {
            let config_path = current.join(CONFIG_FILE_NAME);
            if config_path.exists() {
                if let Ok(content) = fs::read_to_string(&config_path) {
                    if let Ok(toml_config) = toml::from_str::<TomlConfig>(&content) {
                        return Self::from_toml(toml_config);
                    }
                }
            }

            match current.parent() {
                Some(parent) => current = parent,
                None => break,
            }
        }

        Self::default()
    }

    /// Converts a parsed TOML config into runtime config.
    fn from_toml(toml: TomlConfig) -> Self {
        Self {
            allow: toml.lint.allow.into_iter().collect(),
            deny: toml.lint.deny.into_iter().collect(),
            warnings_as_errors: toml.lint.warnings_as_errors,
            ignore: toml.lint.ignore,
        }
    }

    /// Merges CLI flags into this configuration.
    ///
    /// CLI flags take precedence over config file settings.
    pub(crate) fn merge_cli(&mut self, allow: &[String], deny: &[String], strict: bool) {
        for rule in allow {
            self.allow.insert(rule.clone());
            // Remove from deny if present (CLI allow overrides)
            self.deny.remove(rule);
        }

        for rule in deny {
            self.deny.insert(rule.clone());
            // Remove from allow if present (CLI deny overrides)
            self.allow.remove(rule);
        }

        if strict {
            self.warnings_as_errors = true;
        }
    }

    /// Checks if a rule is allowed (disabled).
    #[must_use]
    pub(crate) fn is_allowed(&self, rule: &str) -> bool {
        self.allow.contains(rule)
    }

    /// Checks if a rule is explicitly denied.
    #[must_use]
    pub(crate) fn is_denied(&self, rule: &str) -> bool {
        self.deny.contains(rule)
    }
}

#[cfg(test)]
#[allow(clippy::unwrap_used, clippy::expect_used)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::TempDir;

    #[test]
    fn test_load_missing_file() {
        let temp_dir = TempDir::new().unwrap();
        let config = Config::load(temp_dir.path());

        assert!(config.allow.is_empty());
        assert!(config.deny.is_empty());
        assert!(!config.warnings_as_errors);
    }

    #[test]
    fn test_load_valid_config() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("promptly.toml");

        let mut file = fs::File::create(&config_path).unwrap();
        writeln!(
            file,
            r#"
[lint]
allow = ["unused-variable", "unverified-partial"]
deny = ["undefined-variable"]
warnings-as-errors = true
ignore = ["examples/*"]
"#
        )
        .unwrap();

        let config = Config::load(temp_dir.path());

        assert!(config.is_allowed("unused-variable"));
        assert!(config.is_allowed("unverified-partial"));
        assert!(config.is_denied("undefined-variable"));
        assert!(config.warnings_as_errors);
        assert_eq!(config.ignore, vec!["examples/*"]);
    }

    #[test]
    fn test_merge_cli_overrides() {
        let mut config = Config::new();
        config.allow.insert("rule-a".to_string());
        config.deny.insert("rule-b".to_string());

        // CLI deny overrides config allow
        config.merge_cli(&[], &["rule-a".to_string()], false);
        assert!(!config.is_allowed("rule-a"));
        assert!(config.is_denied("rule-a"));

        // CLI allow overrides config deny
        config.merge_cli(&["rule-b".to_string()], &[], false);
        assert!(config.is_allowed("rule-b"));
        assert!(!config.is_denied("rule-b"));
    }

    #[test]
    fn test_merge_cli_strict() {
        let mut config = Config::new();
        assert!(!config.warnings_as_errors);

        config.merge_cli(&[], &[], true);
        assert!(config.warnings_as_errors);
    }

    #[test]
    fn test_load_from_parent_directory() {
        let temp_dir = TempDir::new().unwrap();
        let sub_dir = temp_dir.path().join("subdir");
        fs::create_dir(&sub_dir).unwrap();

        let config_path = temp_dir.path().join("promptly.toml");
        let mut file = fs::File::create(&config_path).unwrap();
        writeln!(
            file,
            r#"
[lint]
allow = ["parent-rule"]
"#
        )
        .unwrap();

        // Load from subdirectory should find parent config
        let config = Config::load(&sub_dir);
        assert!(config.is_allowed("parent-rule"));
    }
}
