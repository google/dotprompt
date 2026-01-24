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

//! Integration tests for the promptly CLI.

use std::fs;
use std::process::Command;

use tempfile::TempDir;

/// Gets the path to the promptly binary.
fn promptly_bin() -> String {
    // When running via cargo test, the binary is in target/debug
    env!("CARGO_BIN_EXE_promptly").to_string()
}

/// Creates a temporary directory with test prompt files.
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn setup_test_dir() -> TempDir {
    let dir = TempDir::new().expect("Failed to create temp dir");

    // Valid prompt
    fs::write(
        dir.path().join("valid.prompt"),
        r"---
model: gemini-2.0-flash
config:
  temperature: 0.7
---
Hello {{name}}!
",
    )
    .expect("Failed to write valid.prompt");

    // Invalid YAML
    fs::write(
        dir.path().join("invalid_yaml.prompt"),
        r#"---
model: gemini-2.0-flash
config:
  temperature: "unclosed string
---
Hello world!
"#,
    )
    .expect("Failed to write invalid_yaml.prompt");

    // Unclosed block
    fs::write(
        dir.path().join("unclosed_block.prompt"),
        r#"---
model: gemini-2.0-flash
---
{{#role "user"}}
Hello world!
"#,
    )
    .expect("Failed to write unclosed_block.prompt");

    dir
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_help_output() {
    let output = Command::new(promptly_bin())
        .arg("--help")
        .output()
        .expect("Failed to run promptly");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Promptly"));
    assert!(stdout.contains("check"));
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_help() {
    let output = Command::new(promptly_bin())
        .args(["check", "--help"])
        .output()
        .expect("Failed to run promptly check --help");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Check .prompt files"));
    assert!(stdout.contains("--format"));
    assert!(stdout.contains("--strict"));
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_valid_prompt() {
    let dir = setup_test_dir();
    let valid_path = dir.path().join("valid.prompt");

    let output = Command::new(promptly_bin())
        .args(["check", valid_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly check");

    // Valid prompt should pass (exit 0)
    assert!(
        output.status.success(),
        "Expected success for valid prompt, stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_invalid_yaml() {
    let dir = setup_test_dir();
    let invalid_path = dir.path().join("invalid_yaml.prompt");

    let output = Command::new(promptly_bin())
        .args(["check", invalid_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly check");

    // Invalid YAML should fail (exit non-zero)
    assert!(
        !output.status.success(),
        "Expected failure for invalid YAML"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("invalid-yaml"),
        "Expected invalid-yaml error code"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_unclosed_block() {
    let dir = setup_test_dir();
    let unclosed_path = dir.path().join("unclosed_block.prompt");

    let output = Command::new(promptly_bin())
        .args(["check", unclosed_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly check");

    // Unclosed block should fail
    assert!(
        !output.status.success(),
        "Expected failure for unclosed block"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("unclosed-block"),
        "Expected unclosed-block error code"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_json_output() {
    let dir = setup_test_dir();
    let invalid_path = dir.path().join("invalid_yaml.prompt");

    let output = Command::new(promptly_bin())
        .args(["check", "--format=json", invalid_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly check --format=json");

    let stdout = String::from_utf8_lossy(&output.stdout);

    // Should be valid JSON
    let parsed: Result<serde_json::Value, _> = serde_json::from_str(&stdout);
    assert!(parsed.is_ok(), "Expected valid JSON output: {stdout}");

    let json = parsed.expect("Already checked is_ok");
    assert!(json.is_array(), "Expected JSON array");
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_directory() {
    let dir = setup_test_dir();

    let output = Command::new(promptly_bin())
        .args(["check", dir.path().to_str().unwrap()])
        .output()
        .expect("Failed to run promptly check on directory");

    // Directory with invalid files should fail
    assert!(
        !output.status.success(),
        "Expected failure when checking directory with invalid files"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_nonexistent_path() {
    let output = Command::new(promptly_bin())
        .args(["check", "/nonexistent/path/to/prompts"])
        .output()
        .expect("Failed to run promptly check");

    assert!(
        !output.status.success(),
        "Expected failure for nonexistent path"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("does not exist") || stderr.contains("error"),
        "Expected error message about nonexistent path"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_version() {
    let output = Command::new(promptly_bin())
        .arg("--version")
        .output()
        .expect("Failed to run promptly --version");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("0.1.0"), "Expected version 0.1.0");
}

// ============================================================================
// fmt command tests
// ============================================================================

/// Creates a temporary directory with unformatted prompt files.
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn setup_unformatted_dir() -> TempDir {
    let dir = TempDir::new().expect("Failed to create temp dir");

    // Unformatted prompt (no spacing in handlebars, trailing whitespace)
    fs::write(
        dir.path().join("unformatted.prompt"),
        r"---
model: gemini-2.0-flash
---
Hello {{name}}!   
Goodbye {{friend}}",
    )
    .expect("Failed to write unformatted.prompt");

    // Already formatted prompt
    fs::write(
        dir.path().join("formatted.prompt"),
        r"---
model: gemini-2.0-flash
---

Hello {{ name }}!
",
    )
    .expect("Failed to write formatted.prompt");

    dir
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_fmt_help() {
    let output = Command::new(promptly_bin())
        .args(["fmt", "--help"])
        .output()
        .expect("Failed to run promptly fmt --help");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Format .prompt files"));
    assert!(stdout.contains("--check"));
    assert!(stdout.contains("--diff"));
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_fmt_check_unformatted() {
    let dir = setup_unformatted_dir();
    let unformatted_path = dir.path().join("unformatted.prompt");

    let output = Command::new(promptly_bin())
        .args(["fmt", "--check", unformatted_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly fmt --check");

    // Should fail because file needs formatting
    assert!(
        !output.status.success(),
        "Expected failure for unformatted file"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("would be reformatted") || stderr.contains("reformat"),
        "Expected message about reformatting: {stderr}"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_fmt_check_formatted() {
    let dir = setup_unformatted_dir();
    let formatted_path = dir.path().join("formatted.prompt");

    let output = Command::new(promptly_bin())
        .args(["fmt", "--check", formatted_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly fmt --check");

    // Should pass because file is already formatted
    assert!(
        output.status.success(),
        "Expected success for already formatted file, stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_fmt_formats_file() {
    let dir = setup_unformatted_dir();
    let unformatted_path = dir.path().join("unformatted.prompt");

    // Read original content
    let original = fs::read_to_string(&unformatted_path).expect("Failed to read file");
    assert!(
        original.contains("{{name}}"),
        "Original should have unspaced handlebars"
    );

    // Run fmt
    let output = Command::new(promptly_bin())
        .args(["fmt", unformatted_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly fmt");

    assert!(
        output.status.success(),
        "Expected success, stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    // Read formatted content
    let formatted = fs::read_to_string(&unformatted_path).expect("Failed to read formatted file");
    assert!(
        formatted.contains("{{ name }}"),
        "Formatted should have spaced handlebars: {formatted}"
    );
    assert!(
        formatted.ends_with('\n'),
        "Formatted should have final newline"
    );
    assert!(
        !formatted.contains("!   \n"),
        "Formatted should have no trailing whitespace"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_fmt_diff_shows_changes() {
    let dir = setup_unformatted_dir();
    let unformatted_path = dir.path().join("unformatted.prompt");

    let output = Command::new(promptly_bin())
        .args(["fmt", "--diff", unformatted_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly fmt --diff");

    // Should show diff output
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("---") || stderr.contains("+++"),
        "Expected diff output: {stderr}"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_fmt_directory() {
    let dir = setup_unformatted_dir();

    let output = Command::new(promptly_bin())
        .args(["fmt", "--check", dir.path().to_str().unwrap()])
        .output()
        .expect("Failed to run promptly fmt --check on directory");

    // Should fail because there are unformatted files
    assert!(
        !output.status.success(),
        "Expected failure for directory with unformatted files"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("file(s)"),
        "Expected summary message: {stderr}"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_fmt_nonexistent_path() {
    let output = Command::new(promptly_bin())
        .args(["fmt", "/nonexistent/path/to/prompts"])
        .output()
        .expect("Failed to run promptly fmt");

    assert!(
        !output.status.success(),
        "Expected failure for nonexistent path"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("does not exist") || stderr.contains("error"),
        "Expected error message: {stderr}"
    );
}

// ============================================================================
// check --fix tests
// ============================================================================

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_fix_formats_file() {
    let dir = setup_unformatted_dir();
    let unformatted_path = dir.path().join("unformatted.prompt");

    // Read original content
    let original = fs::read_to_string(&unformatted_path).expect("Failed to read file");
    assert!(
        original.contains("{{name}}"),
        "Original should have unspaced handlebars"
    );

    // Run check --fix
    let output = Command::new(promptly_bin())
        .args(["check", "--fix", unformatted_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly check --fix");

    // Should succeed (no lint errors in this file)
    assert!(
        output.status.success(),
        "Expected success, stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    // Read fixed content
    let fixed = fs::read_to_string(&unformatted_path).expect("Failed to read fixed file");
    assert!(
        fixed.contains("{{ name }}"),
        "Fixed should have spaced handlebars: {fixed}"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("Fixed"),
        "Expected 'Fixed' message: {stderr}"
    );
}

#[test]
#[allow(clippy::unwrap_used, clippy::expect_used)]
fn test_check_fix_with_strict() {
    let dir = setup_test_dir();
    let valid_path = dir.path().join("valid.prompt");

    let output = Command::new(promptly_bin())
        .args(["check", "--fix", "--strict", valid_path.to_str().unwrap()])
        .output()
        .expect("Failed to run promptly check --fix --strict");

    // Should succeed for valid prompt
    assert!(
        output.status.success(),
        "Expected success for valid prompt with --strict, stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}
