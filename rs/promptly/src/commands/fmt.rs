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

//! The `fmt` command for formatting `.prompt` files.

use std::fs;
use std::path::{Path, PathBuf};

use clap::Args;
use walkdir::WalkDir;

use crate::formatter::{Formatter, FormatterConfig};

/// Arguments for the fmt command.
#[derive(Args, Debug)]
pub(crate) struct FmtArgs {
    /// Paths to format (files or directories)
    #[arg(default_value = ".")]
    pub paths: Vec<PathBuf>,

    /// Check if files are formatted without modifying them
    #[arg(long)]
    pub check: bool,

    /// Show diff of changes
    #[arg(long)]
    pub diff: bool,
}

/// Result of formatting a file.
#[derive(Debug)]
struct FormatResult {
    /// Path to the file.
    path: PathBuf,
    /// Whether the file was changed.
    changed: bool,
    /// The original content.
    original: String,
    /// The formatted content.
    output: String,
}

/// Checks if a path is a .prompt file.
fn is_prompt_file(path: &Path) -> bool {
    path.extension().is_some_and(|ext| ext == "prompt")
}

/// Runs the fmt command.
///
/// # Errors
///
/// Returns an error if file reading/writing fails or if `--check` finds unformatted files.
pub(crate) fn run(args: &FmtArgs) -> Result<(), String> {
    let fmt = Formatter::new(FormatterConfig::default());
    let mut results: Vec<FormatResult> = Vec::new();
    let mut error_count = 0;

    for path in &args.paths {
        if path.is_file() {
            if is_prompt_file(path) {
                match format_file(&fmt, path, args.check) {
                    Ok(result) => results.push(result),
                    Err(e) => {
                        eprintln!("error: {e}");
                        error_count += 1;
                    }
                }
            }
        } else if path.is_dir() {
            for entry in WalkDir::new(path)
                .follow_links(true)
                .into_iter()
                .filter_map(Result::ok)
            {
                let entry_path = entry.path();
                if entry_path.is_file() && is_prompt_file(entry_path) {
                    match format_file(&fmt, entry_path, args.check) {
                        Ok(result) => results.push(result),
                        Err(e) => {
                            eprintln!("error: {e}");
                            error_count += 1;
                        }
                    }
                }
            }
        } else {
            return Err(format!("Path does not exist: {}", path.display()));
        }
    }

    // Count changed files
    let changed_count = results.iter().filter(|r| r.changed).count();
    let total_count = results.len();

    // Output results
    for result in &results {
        if result.changed {
            if args.check {
                eprintln!("Would reformat: {}", result.path.display());
            } else if args.diff {
                print_diff(&result.path, &result.original, &result.output);
            } else {
                eprintln!("Formatted: {}", result.path.display());
            }
        }
    }

    // Summary
    if args.check {
        if changed_count > 0 {
            eprintln!();
            eprintln!(
                "{changed_count} file(s) would be reformatted, {total_count} file(s) checked."
            );
            return Err("Check failed: some files need formatting".to_string());
        }
        eprintln!("{total_count} file(s) checked, all formatted correctly.");
    } else if changed_count > 0 {
        eprintln!();
        eprintln!("{changed_count} file(s) reformatted, {total_count} file(s) checked.");
    } else {
        eprintln!("{total_count} file(s) checked, nothing to format.");
    }

    if error_count > 0 {
        Err(format!("{error_count} error(s) occurred"))
    } else {
        Ok(())
    }
}

/// Formats a single file.
fn format_file(fmt: &Formatter, path: &Path, check_only: bool) -> Result<FormatResult, String> {
    let original = fs::read_to_string(path)
        .map_err(|e| format!("Failed to read {}: {}", path.display(), e))?;

    let output = fmt.format(&original);
    let changed = output != original;

    if changed && !check_only {
        fs::write(path, &output)
            .map_err(|e| format!("Failed to write {}: {}", path.display(), e))?;
    }

    Ok(FormatResult {
        path: path.to_path_buf(),
        changed,
        original,
        output,
    })
}

/// Prints a simple diff between original and formatted content.
fn print_diff(path: &Path, original: &str, output: &str) {
    eprintln!("--- {}", path.display());
    eprintln!("+++ {}", path.display());

    let original_lines: Vec<&str> = original.lines().collect();
    let output_lines: Vec<&str> = output.lines().collect();

    let max_lines = original_lines.len().max(output_lines.len());

    for i in 0..max_lines {
        let orig = original_lines.get(i).copied();
        let out = output_lines.get(i).copied();

        match (orig, out) {
            (Some(o), Some(f)) if o != f => {
                eprintln!("-{o}");
                eprintln!("+{f}");
            }
            (Some(o), None) => {
                eprintln!("-{o}");
            }
            (None, Some(f)) => {
                eprintln!("+{f}");
            }
            _ => {}
        }
    }
    eprintln!();
}
