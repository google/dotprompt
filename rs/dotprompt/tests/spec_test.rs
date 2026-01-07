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

//! Spec-based tests for dotprompt.
//!
//! This test runner reads YAML spec files and executes test cases defined
//! within them, comparing rendered output against expected results.
//!
//! # Spec File Discovery
//!
//! The test runner discovers spec files in the following order:
//! 1. **Environment variable**: `SPEC_FILE` (used by Bazel)
//! 2. **Command line argument**: `--spec-file <path>` (for manual runs)
//! 3. **Directory scan**: Scans `../spec/` for all YAML files (fallback)
//!
//! # Examples
//!
//! ```bash
//! # Run all specs (directory scan)
//! cargo test -p dotprompt --test spec_test
//!
//! # Run specific spec via CLI
//! cargo test -p dotprompt --test spec_test -- --spec-file spec/helpers.yaml
//!
//! # Run via Bazel (sets SPEC_FILE env var)
//! bazel test //rs/dotprompt:SpecTest_helpers
//! ```

#![allow(clippy::expect_used)]
#![allow(clippy::unwrap_used)]
#![allow(clippy::uninlined_format_args)]
#![allow(clippy::items_after_test_module)]
#![allow(clippy::collapsible_if)]
#![allow(clippy::too_many_lines)]
#![allow(clippy::assigning_clones)]
#![allow(clippy::panic)]
#![allow(clippy::expect_fun_call)]

use dotprompt::{DataArgument, Dotprompt, DotpromptOptions, Message, RenderedPrompt};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

/// A group of related tests.
#[derive(Debug, Deserialize)]
struct TestGroup {
    /// Name of the test group.
    name: String,

    /// Optional description.
    #[serde(skip_serializing_if = "Option::is_none")]
    description: Option<String>,

    /// Template source for this group.
    #[serde(skip_serializing_if = "Option::is_none")]
    template: Option<String>,

    /// Static partials for this group.
    #[serde(default)]
    partials: HashMap<String, String>,

    /// Resolver-provided partials for this group.
    #[serde(default, rename = "resolverPartials")]
    resolver_partials: HashMap<String, String>,

    /// Group-level data (e.g., shared messages for history tests).
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<serde_json::Value>,

    /// Test cases in this group.
    #[serde(default, alias = "tests")]
    cases: Vec<TestCase>,
}

/// Individual test case.
#[derive(Debug, Deserialize, Serialize)]
struct TestCase {
    /// Name of the test case.
    #[serde(skip_serializing_if = "Option::is_none")]
    name: Option<String>,

    /// Optional description.
    #[serde(alias = "desc", skip_serializing_if = "Option::is_none")]
    description: Option<String>,

    /// Template source (overrides group template if present).
    #[serde(skip_serializing_if = "Option::is_none")]
    template: Option<String>,

    /// Input data for template rendering.
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<serde_json::Value>,

    /// Options for rendering (includes input defaults).
    #[serde(skip_serializing_if = "Option::is_none")]
    options: Option<serde_json::Value>,

    /// Expected output.
    expect: ExpectedOutput,
}

/// Expected test output.
#[derive(Debug, Deserialize, Serialize)]
struct ExpectedOutput {
    /// Expected messages.
    #[serde(skip_serializing_if = "Option::is_none")]
    messages: Option<Vec<serde_json::Value>>,

    /// Expected metadata fields.
    #[serde(skip_serializing_if = "Option::is_none")]
    metadata: Option<HashMap<String, serde_json::Value>>,

    /// Expected error (if test should fail).
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

/// Default spec directory relative to the test binary location.
const DEFAULT_SPEC_DIR: &str = "spec";

/// Discovers spec files using three-tier approach:
/// 1. Environment variable `SPEC_FILE` (for Bazel)
/// 2. Command line argument `--spec-file <path>` (for manual runs)
/// 3. Directory scan of `spec/` directory (fallback)
fn get_spec_files() -> Vec<PathBuf> {
    // Tier 1: Check SPEC_FILE environment variable (Bazel)
    if let Ok(spec_file) = env::var("SPEC_FILE") {
        println!("Using SPEC_FILE from environment: {}", spec_file);
        return vec![PathBuf::from(spec_file)];
    }

    // Tier 2: Scan spec directory for all YAML files
    // Try multiple possible locations relative to where the test is run
    let possible_spec_dirs = [
        PathBuf::from(DEFAULT_SPEC_DIR),               // From repo root
        PathBuf::from("..").join(DEFAULT_SPEC_DIR),    // From rs/dotprompt
        PathBuf::from("../..").join(DEFAULT_SPEC_DIR), // From rs/dotprompt/tests
    ];

    for spec_dir in &possible_spec_dirs {
        if spec_dir.exists() && spec_dir.is_dir() {
            println!("Scanning spec directory: {}", spec_dir.display());
            let files = scan_spec_directory(spec_dir);
            if !files.is_empty() {
                return files;
            }
        }
    }

    println!("No spec files found. Set SPEC_FILE env var or run from repo root.");
    vec![]
}

/// Recursively scans a directory for YAML spec files.
fn scan_spec_directory(dir: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                files.extend(scan_spec_directory(&path));
            } else if path
                .extension()
                .is_some_and(|ext| ext == "yaml" || ext == "yml")
            {
                files.push(path);
            }
        }
    }
    files.sort();
    files
}

/// Runs tests for a single spec file.
fn run_spec_file(spec_file_path: &Path) -> (usize, usize, Vec<(String, String)>) {
    let spec_content = fs::read_to_string(spec_file_path).unwrap_or_else(|e| {
        panic!(
            "Failed to read spec file {}: {}",
            spec_file_path.display(),
            e
        )
    });

    let groups: Vec<TestGroup> = serde_yaml::from_str(&spec_content).unwrap_or_else(|e| {
        panic!(
            "Failed to parse spec file {}: {}",
            spec_file_path.display(),
            e
        )
    });

    println!("\nRunning spec: {}", spec_file_path.display());

    let mut total_tests = 0;
    let mut passed_tests = 0;
    let mut failed_tests = Vec::new();

    // Run each test group
    for group in &groups {
        println!("\n=== Test Group: {} ===", group.name);
        if let Some(desc) = &group.description {
            println!("Description: {}", desc);
        }

        for case in &group.cases {
            total_tests += 1;
            let case_name = case
                .name
                .as_deref()
                .or(case.description.as_deref())
                .unwrap_or("unnamed");
            let test_name = format!("{} > {}", group.name, case_name);

            // Get template source (case-specific or group default)
            let template = case
                .template
                .as_ref()
                .or(group.template.as_ref())
                .expect(&format!("No template found for test: {}", test_name));

            // Run test with group for partials
            match run_single_test(&test_name, template, case, group) {
                Ok(()) => {
                    println!("  ✓ {}", case_name);
                    passed_tests += 1;
                }
                Err(e) => {
                    println!("  ✗ {}: {}", case_name, e);
                    failed_tests.push((test_name.clone(), e));
                }
            }
        }
    }

    // Summary
    println!("\n=== Test Summary ===");
    println!(
        "Total: {}, Passed: {}, Failed: {}",
        total_tests,
        passed_tests,
        failed_tests.len()
    );

    if !failed_tests.is_empty() {
        println!("\nFailed tests:");
        for (name, error) in &failed_tests {
            println!("  - {}: {}", name, error);
        }
    }

    (total_tests, passed_tests, failed_tests)
}

#[test]
fn run_spec_tests() {
    let spec_files = get_spec_files();

    if spec_files.is_empty() {
        println!("No spec files found. Skipping tests.");
        println!("To run specs, either:");
        println!("  - Set SPEC_FILE environment variable");
        println!("  - Pass --spec-file <path> argument");
        println!("  - Run from a directory containing the 'spec/' folder");
        return;
    }

    println!("Found {} spec file(s)", spec_files.len());

    let mut grand_total = 0;
    let mut grand_passed = 0;
    let mut all_failed: Vec<(String, String)> = Vec::new();

    for spec_file in &spec_files {
        let (total, passed, failed) = run_spec_file(spec_file);
        grand_total += total;
        grand_passed += passed;
        all_failed.extend(failed);
    }

    // Grand summary
    println!("\n========================================");
    println!(
        "GRAND TOTAL: {} tests, {} passed, {} failed",
        grand_total,
        grand_passed,
        all_failed.len()
    );
    println!("========================================");

    if !all_failed.is_empty() {
        println!("\nAll failed tests:");
        for (name, error) in &all_failed {
            println!("  - {}: {}", name, error);
        }
        panic!(
            "{} test(s) failed across {} spec file(s)",
            all_failed.len(),
            spec_files.len()
        );
    }
}

fn run_single_test(
    _test_name: &str,
    template: &str,
    case: &TestCase,
    group: &TestGroup,
) -> Result<(), String> {
    // Create Dotprompt instance with partials from group
    let mut all_partials = HashMap::new();
    all_partials.extend(group.partials.clone());
    all_partials.extend(group.resolver_partials.clone());

    let options = DotpromptOptions {
        partials: Some(all_partials),
        ..Default::default()
    };
    let dotprompt = Dotprompt::new(Some(options));

    // Prepare data - extract from nested structure
    let mut data = DataArgument::default();

    // First, extract default values from options if present
    let mut input_defaults: serde_json::Map<String, serde_json::Value> = serde_json::Map::new();
    if let Some(opts) = &case.options {
        if let Some(input_opts) = opts.get("input") {
            if let Some(defaults) = input_opts.get("default") {
                if let Some(defaults_obj) = defaults.as_object() {
                    input_defaults = defaults_obj.clone();
                }
            }
        }
    }

    // Merge group data with case data (case data takes precedence)
    let merged_data: Option<serde_json::Value> = match (&group.data, &case.data) {
        (Some(group_data), Some(case_data)) => {
            // Merge group data with case data
            let mut merged = group_data.clone();
            if let (Some(merged_obj), Some(case_obj)) =
                (merged.as_object_mut(), case_data.as_object())
            {
                for (k, v) in case_obj {
                    merged_obj.insert(k.clone(), v.clone());
                }
            }
            Some(merged)
        }
        (Some(group_data), None) => Some(group_data.clone()),
        (None, Some(case_data)) => Some(case_data.clone()),
        (None, None) => None,
    };

    if let Some(test_data) = &merged_data {
        // Test data can be structured as { input: {...}, messages: [...] }
        // or directly as input values
        if let Some(input) = test_data.get("input") {
            // Merge defaults with input (input overrides defaults)
            if let Some(input_obj) = input.as_object() {
                for (k, v) in input_obj {
                    input_defaults.insert(k.clone(), v.clone());
                }
            }
            data.input = Some(serde_json::Value::Object(input_defaults));
        } else {
            // If no "input" key, treat entire data as input
            data.input = Some(test_data.clone());
        }

        // Extract messages for history
        if let Some(messages) = test_data.get("messages") {
            if let Ok(msgs) = serde_json::from_value::<Vec<Message>>(messages.clone()) {
                data.messages = Some(msgs);
            }
        }

        // Extract context if present
        if let Some(context) = test_data.get("context") {
            if let Some(ctx_obj) = context.as_object() {
                let ctx: HashMap<String, serde_json::Value> = ctx_obj
                    .iter()
                    .map(|(k, v)| (k.clone(), v.clone()))
                    .collect();
                data.context = Some(ctx);
            }
        }
    }

    // Render template
    let result: Result<RenderedPrompt, _> = dotprompt.render(template, &data, None);

    // Check if error was expected
    if let Some(expected_error) = &case.expect.error {
        return match result {
            Err(e) => {
                let error_msg = e.to_string();
                if error_msg.contains(expected_error) {
                    Ok(())
                } else {
                    Err(format!(
                        "Expected error containing '{}', got: {}",
                        expected_error, error_msg
                    ))
                }
            }
            Ok(_) => Err(format!(
                "Expected error '{}', but rendering succeeded",
                expected_error
            )),
        };
    }

    // Otherwise, rendering should succeed
    let rendered = result.map_err(|e| format!("Rendering failed: {}", e))?;

    // Verify messages if specified
    if let Some(expected_messages) = &case.expect.messages {
        let actual_messages = serde_json::to_value(&rendered.messages)
            .map_err(|e| format!("Failed to serialize messages: {}", e))?;

        let expected = serde_json::to_value(expected_messages)
            .map_err(|e| format!("Failed to serialize expected messages: {}", e))?;

        if actual_messages != expected {
            return Err(format!(
                "Message mismatch:\nExpected: {}\nActual: {}",
                serde_json::to_string_pretty(&expected).unwrap(),
                serde_json::to_string_pretty(&actual_messages).unwrap()
            ));
        }
    }

    // Verify metadata if specified
    if let Some(expected_metadata) = &case.expect.metadata {
        // Check RenderedPrompt metadata (from render())
        let actual_metadata = serde_json::to_value(&rendered.metadata)
            .map_err(|e| format!("Failed to serialize metadata: {}", e))?;

        for (key, expected_value) in expected_metadata {
            let actual_value = actual_metadata
                .get(key)
                .ok_or_else(|| format!("Missing metadata field in render result: {}", key))?;

            if actual_value != expected_value {
                return Err(format!(
                    "Metadata mismatch in render result for field '{}':\nExpected: {}\nActual: {}",
                    key,
                    serde_json::to_string_pretty(expected_value).unwrap(),
                    serde_json::to_string_pretty(actual_value).unwrap()
                ));
            }
        }

        // Check explicit render_metadata() call (parity with JS runner)
        let metadata_only: dotprompt::PromptMetadata<serde_json::Value> = dotprompt
            .render_metadata(template, None)
            .map_err(|e| format!("render_metadata failed: {}", e))?;

        let actual_metadata_only = serde_json::to_value(&metadata_only)
            .map_err(|e| format!("Failed to serialize metadata_only: {}", e))?;

        for (key, expected_value) in expected_metadata {
            let actual_value = actual_metadata_only.get(key).ok_or_else(|| {
                format!("Missing metadata field in render_metadata result: {}", key)
            })?;

            if actual_value != expected_value {
                return Err(format!(
                    "Metadata mismatch in render_metadata result for field '{}':\nExpected: {}\nActual: {}",
                    key,
                    serde_json::to_string_pretty(expected_value).unwrap(),
                    serde_json::to_string_pretty(actual_value).unwrap()
                ));
            }
        }
    }

    Ok(())
}
