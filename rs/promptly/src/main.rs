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

//! Promptly: Cargo for prompts
//!
//! A comprehensive CLI toolchain for `.prompt` files.

#![forbid(unsafe_code)]
#![deny(missing_docs)]
#![deny(missing_debug_implementations)]
// Allow pub(crate) in private modules - we use this pattern intentionally
// for when we later expose modules publicly
#![allow(clippy::redundant_pub_crate)]
// Multiple crate versions are expected with async/tower dependencies
#![allow(clippy::multiple_crate_versions)]

mod commands;
pub(crate) mod config;
mod formatter;
mod linter;
mod lsp;
mod span;

use clap::{Parser, Subcommand};
use commands::lsp as lsp_cmd;
use commands::{check, completions, fmt};
use owo_colors::OwoColorize;

/// Promptly: Cargo for prompts - lint, format, test, and publish .prompt files
#[derive(Parser, Debug)]
#[command(name = "promptly")]
#[command(author, version, about, long_about = None)]
#[command(styles = get_styles())]
pub struct Cli {
    /// Subcommand to execute
    #[command(subcommand)]
    command: Commands,
}

/// Returns custom styles for clap.
const fn get_styles() -> clap::builder::Styles {
    clap::builder::Styles::styled()
        .usage(
            anstyle::Style::new()
                .bold()
                .fg_color(Some(anstyle::Color::Ansi(anstyle::AnsiColor::Yellow))),
        )
        .header(
            anstyle::Style::new()
                .bold()
                .fg_color(Some(anstyle::Color::Ansi(anstyle::AnsiColor::Yellow))),
        )
        .literal(
            anstyle::Style::new()
                .bold()
                .fg_color(Some(anstyle::Color::Ansi(anstyle::AnsiColor::Green))),
        )
        .placeholder(
            anstyle::Style::new().fg_color(Some(anstyle::Color::Ansi(anstyle::AnsiColor::Cyan))),
        )
}

/// Available commands
#[derive(Subcommand, Debug)]
enum Commands {
    /// Check .prompt files for errors and warnings
    Check(check::CheckArgs),
    /// Generate shell completions
    Completions(completions::CompletionsArgs),
    /// Format .prompt files
    Fmt(fmt::FmtArgs),
    /// Start the Language Server Protocol (LSP) server
    Lsp(lsp_cmd::LspArgs),
}

fn main() {
    let cli = Cli::parse();

    let result = match cli.command {
        Commands::Check(args) => check::run(&args),
        Commands::Completions(args) => completions::run(&args),
        Commands::Fmt(args) => fmt::run(&args),
        Commands::Lsp(args) => lsp_cmd::run(&args),
    };

    if let Err(e) = result {
        eprintln!("{}: {e}", "error".red().bold());
        std::process::exit(1);
    }
}
