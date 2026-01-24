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

//! The `check` command for linting `.prompt` files.

use std::fs;
use std::path::{Path, PathBuf};

use ariadne::{Color, Label, Report, ReportKind, Source};
use clap::Args;
use owo_colors::OwoColorize;
use walkdir::WalkDir;

use crate::config::Config;
use crate::formatter::{Formatter, FormatterConfig};
use crate::linter::{Diagnostic, DiagnosticSeverity, Linter, OutputFormat};

/// Arguments for the check command.
#[derive(Args, Debug)]
pub(crate) struct CheckArgs {
    /// Paths to check (files or directories)
    #[arg(default_value = ".")]
    pub paths: Vec<PathBuf>,

    /// Output format (text or json)
    #[arg(long, short, default_value = "text")]
    pub format: OutputFormat,

    /// Treat warnings as errors
    #[arg(long)]
    pub strict: bool,

    /// Automatically fix problems where possible
    #[arg(long)]
    pub fix: bool,

    /// Allow (disable) specific rules (can be repeated)
    #[arg(long, short = 'A', value_name = "RULE")]
    pub allow: Vec<String>,

    /// Deny (enable as error) specific rules (can be repeated)
    #[arg(long, short = 'D', value_name = "RULE")]
    pub deny: Vec<String>,
}

/// Result from processing a single file.
struct FileResult {
    path: PathBuf,
    source: String,
    diagnostics: Vec<Diagnostic>,
}

/// Runs the check command.
///
/// # Errors
///
/// Returns an error if file reading fails or if there are lint errors.
pub(crate) fn run(args: &CheckArgs) -> Result<(), String> {
    // Load configuration from promptly.toml
    let start_dir = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let mut config = Config::load(&start_dir);

    // Merge CLI flags into config (CLI takes precedence)
    config.merge_cli(&args.allow, &args.deny, args.strict);

    let linter = Linter::new();
    let results = collect_results(&linter, args, &config)?;

    let has_errors = output_results(&results, args, &config);
    let (error_count, warning_count) = count_diagnostics(&results);

    print_summary(error_count, warning_count);

    if has_errors || (config.warnings_as_errors && warning_count > 0) {
        Err("Check failed".to_string())
    } else {
        Ok(())
    }
}

/// Collects results from all paths.
fn collect_results(
    linter: &Linter,
    args: &CheckArgs,
    config: &Config,
) -> Result<Vec<FileResult>, String> {
    let mut results = Vec::new();

    for path in &args.paths {
        if path.is_file() {
            if is_prompt_file(path) {
                results.push(process_file(linter, path, args.fix, config)?);
            }
        } else if path.is_dir() {
            for entry in WalkDir::new(path)
                .follow_links(true)
                .into_iter()
                .filter_map(Result::ok)
            {
                let entry_path = entry.path();
                if entry_path.is_file() && is_prompt_file(entry_path) {
                    results.push(process_file(linter, entry_path, args.fix, config)?);
                }
            }
        } else {
            return Err(format!("Path does not exist: {}", path.display()));
        }
    }

    Ok(results)
}

/// Checks if a path is a .prompt file.
fn is_prompt_file(path: &Path) -> bool {
    path.extension().is_some_and(|ext| ext == "prompt")
}

/// Processes a single file and returns the result.
fn process_file(
    linter: &Linter,
    path: &Path,
    fix: bool,
    config: &Config,
) -> Result<FileResult, String> {
    let source = fs::read_to_string(path)
        .map_err(|e| format!("Failed to read {}: {}", path.display(), e))?;

    let all_diagnostics = linter.lint(&source, Some(path));

    // Filter diagnostics based on config (skip allowed rules)
    let diagnostics: Vec<Diagnostic> = all_diagnostics
        .into_iter()
        .filter(|d| !config.is_allowed(&d.code))
        .collect();

    // If --fix is enabled and there are formatting issues, apply formatting
    if fix {
        let fmt = Formatter::new(FormatterConfig::default());
        if fmt.needs_formatting(&source) {
            let result = fmt.format(&source);
            fs::write(path, &result)
                .map_err(|e| format!("Failed to write {}: {}", path.display(), e))?;
            eprintln!("{}: {}", "Fixed".green().bold(), path.display());
        }
    }

    Ok(FileResult {
        path: path.to_path_buf(),
        source,
        diagnostics,
    })
}

/// Outputs results and returns whether there are errors.
fn output_results(results: &[FileResult], args: &CheckArgs, config: &Config) -> bool {
    match args.format {
        OutputFormat::Text => {
            for result in results {
                for diag in &result.diagnostics {
                    // Check if denied rule should be promoted to error
                    let effective_diag = if config.is_denied(&diag.code) {
                        Diagnostic {
                            severity: DiagnosticSeverity::Error,
                            ..diag.clone()
                        }
                    } else {
                        diag.clone()
                    };
                    print_diagnostic_rich(&result.path, &result.source, &effective_diag);
                }
            }
        }
        OutputFormat::Json => {
            let output: Vec<_> = results
                .iter()
                .flat_map(|r| {
                    r.diagnostics.iter().map(move |d| {
                        let severity = if config.is_denied(&d.code) {
                            "error"
                        } else {
                            &format!("{:?}", d.severity).to_lowercase()
                        };
                        serde_json::json!({
                            "file": r.path.display().to_string(),
                            "code": d.code,
                            "severity": severity,
                            "message": d.message,
                            "line": d.span.as_ref().map(|s| s.start.line),
                            "column": d.span.as_ref().map(|s| s.start.column),
                        })
                    })
                })
                .collect();
            println!(
                "{}",
                serde_json::to_string_pretty(&output).unwrap_or_default()
            );
        }
    }

    // Calculate has_errors - include denied rules as errors
    results
        .iter()
        .flat_map(|r| &r.diagnostics)
        .any(|d| d.severity == DiagnosticSeverity::Error || config.is_denied(&d.code))
}

/// Counts errors and warnings in results.
fn count_diagnostics(results: &[FileResult]) -> (usize, usize) {
    let error_count = results
        .iter()
        .flat_map(|r| &r.diagnostics)
        .filter(|d| d.severity == DiagnosticSeverity::Error)
        .count();
    let warning_count = results
        .iter()
        .flat_map(|r| &r.diagnostics)
        .filter(|d| d.severity == DiagnosticSeverity::Warning)
        .count();
    (error_count, warning_count)
}

/// Prints the summary of errors and warnings.
fn print_summary(error_count: usize, warning_count: usize) {
    if error_count > 0 || warning_count > 0 {
        eprintln!();
        if error_count > 0 {
            eprint!("{}: {error_count} error(s)", "error".red().bold());
        }
        if warning_count > 0 {
            if error_count > 0 {
                eprint!(", ");
            }
            eprint!("{}: {warning_count} warning(s)", "warning".yellow().bold());
        }
        eprintln!(" generated");
    }
}

/// Prints a diagnostic with rich formatting using ariadne.
fn print_diagnostic_rich(path: &Path, source: &str, diag: &Diagnostic) {
    let filename = path.display().to_string();

    // Determine report kind and color based on severity
    let (kind, color) = match diag.severity {
        DiagnosticSeverity::Error => (ReportKind::Error, Color::Red),
        DiagnosticSeverity::Warning => (ReportKind::Warning, Color::Yellow),
        DiagnosticSeverity::Info => (ReportKind::Advice, Color::Cyan),
    };

    // For diagnostics with a span, show line context
    // For file-level diagnostics (no span), just show the message
    if let Some(span) = &diag.span {
        let start =
            line_col_to_offset(source, span.start.line as usize, span.start.column as usize);
        let end = line_col_to_offset(source, span.end.line as usize, span.end.column as usize);
        // Ensure we have at least 1 character span
        let end = if end <= start { start + 1 } else { end };
        // Clamp to source length
        let (start_offset, end_offset) = (start, end.min(source.len()));

        // Build the report with label
        let mut builder = Report::<(String, std::ops::Range<usize>)>::build(
            kind,
            (filename.clone(), start_offset..end_offset),
        )
        .with_code(&diag.code)
        .with_message(&diag.message);

        let label = Label::new((filename.clone(), start_offset..end_offset)).with_color(color);

        let label = if let Some(help) = &diag.help {
            label.with_message(help)
        } else {
            label
        };

        builder = builder.with_label(label);
        let report = builder.finish();
        report.eprint((filename, Source::from(source))).ok();
    } else {
        // File-level diagnostic: no line context, just message and help
        let prefix = match diag.severity {
            DiagnosticSeverity::Error => format!("\x1b[1;31m[{}] Error:\x1b[0m", diag.code),
            DiagnosticSeverity::Warning => format!("\x1b[1;33m[{}] Warning:\x1b[0m", diag.code),
            DiagnosticSeverity::Info => format!("\x1b[1;36m[{}] Advice:\x1b[0m", diag.code),
        };
        eprintln!("{} {} ({})", prefix, diag.message, filename);
        if let Some(help) = &diag.help {
            eprintln!("  \x1b[1;36mhelp:\x1b[0m {help}");
        }
    }
}

/// Converts 1-indexed line and column to byte offset.
fn line_col_to_offset(source: &str, line: usize, col: usize) -> usize {
    let mut offset = 0;
    for (i, l) in source.lines().enumerate() {
        if i + 1 == line {
            return offset + col.saturating_sub(1).min(l.len());
        }
        offset += l.len() + 1; // +1 for newline
    }
    offset.min(source.len())
}
