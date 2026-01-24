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

//! Shell completion generation and installation command.

use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::Command;

use clap::{Args, CommandFactory, Subcommand};
use clap_complete::{Generator, Shell};
use owo_colors::OwoColorize;

/// Arguments for the completions command.
#[derive(Args, Debug)]
pub(crate) struct CompletionsArgs {
    /// Completions subcommand
    #[command(subcommand)]
    pub command: CompletionsCommand,
}

/// Completions subcommands.
#[derive(Subcommand, Debug)]
pub(crate) enum CompletionsCommand {
    /// Generate completions for a specific shell (prints to stdout)
    Generate {
        /// Shell to generate completions for
        #[arg(value_enum)]
        shell: Shell,
    },
    /// Install completions for all detected shells
    Install {
        /// Force overwrite existing completion files
        #[arg(long)]
        force: bool,
    },
}

/// Information about a shell and its completion directory.
struct ShellInfo {
    shell: Shell,
    name: &'static str,
    filename: &'static str,
    dirs: &'static [&'static str],
}

/// Shell configurations with their completion directories.
const SHELLS: &[ShellInfo] = &[
    ShellInfo {
        shell: Shell::Bash,
        name: "bash",
        filename: "promptly",
        dirs: &[
            "~/.local/share/bash-completion/completions",
            "~/.bash_completion.d",
            "/usr/local/share/bash-completion/completions",
            "/etc/bash_completion.d",
        ],
    },
    ShellInfo {
        shell: Shell::Zsh,
        name: "zsh",
        filename: "_promptly",
        dirs: &[
            "~/.zsh/completions",
            "~/.local/share/zsh/site-functions",
            "/usr/local/share/zsh/site-functions",
        ],
    },
    ShellInfo {
        shell: Shell::Fish,
        name: "fish",
        filename: "promptly.fish",
        dirs: &[
            "~/.config/fish/completions",
            "/usr/local/share/fish/vendor_completions.d",
        ],
    },
];

/// Generates shell completions to stdout.
fn print_completions<G: Generator>(generator: G, cmd: &mut clap::Command) {
    clap_complete::generate(
        generator,
        cmd,
        cmd.get_name().to_string(),
        &mut std::io::stdout(),
    );
}

/// Generates shell completions to a buffer.
fn generate_completions<G: Generator>(generator: G, cmd: &mut clap::Command) -> Vec<u8> {
    let mut buf = Vec::new();
    clap_complete::generate(generator, cmd, cmd.get_name().to_string(), &mut buf);
    buf
}

/// Expand tilde in path.
#[allow(clippy::collapsible_if)]
fn expand_tilde(path: &str) -> PathBuf {
    if let Some(stripped) = path.strip_prefix("~/") {
        if let Some(home) = dirs::home_dir() {
            return home.join(stripped);
        }
    }
    PathBuf::from(path)
}

/// Check if a shell binary is available.
fn is_shell_installed(name: &str) -> bool {
    Command::new("which")
        .arg(name)
        .output()
        .is_ok_and(|output| output.status.success())
}

/// Check if a path is writable.
fn is_writable(path: &std::path::Path) -> bool {
    path.metadata()
        .map(|m| !m.permissions().readonly())
        .unwrap_or(false)
}

/// Find the first writable completion directory.
#[allow(clippy::collapsible_if)]
fn find_completion_dir(dirs: &[&str]) -> Option<PathBuf> {
    for dir in dirs {
        let path = expand_tilde(dir);
        // If directory exists and is writable, use it
        if path.exists() && is_writable(&path) {
            return Some(path);
        }
        // If parent exists and is writable, we can create the directory
        if let Some(parent) = path.parent() {
            if parent.exists() && is_writable(parent) {
                return Some(path);
            }
        }
    }
    None
}

/// Install completions for all detected shells.
#[allow(clippy::unnecessary_wraps)]
fn install_completions(force: bool) -> Result<(), String> {
    let mut installed = 0;
    let mut skipped = 0;

    println!("{} shell completions...\n", "Installing".green().bold());

    for info in SHELLS {
        // Check if shell is installed
        if !is_shell_installed(info.name) {
            println!("  {} {} (not installed)", "⊘".dimmed(), info.name.dimmed());
            continue;
        }

        // Find completion directory
        let Some(dir) = find_completion_dir(info.dirs) else {
            println!(
                "  {} {} (no writable completion directory found)",
                "⊘".yellow(),
                info.name
            );
            skipped += 1;
            continue;
        };

        let file_path = dir.join(info.filename);

        // Check if file exists
        if file_path.exists() && !force {
            println!(
                "  {} {} (already exists at {})",
                "⊘".yellow(),
                info.name,
                file_path.display()
            );
            skipped += 1;
            continue;
        }

        // Create directory if needed
        if !dir.exists() {
            match fs::create_dir_all(&dir) {
                Ok(()) => {}
                Err(e) => {
                    println!(
                        "  {} {} (failed to create directory: {e})",
                        "✗".red().bold(),
                        info.name
                    );
                    continue;
                }
            }
        }

        // Generate and write completions
        let mut cmd = crate::Cli::command();
        let completions = generate_completions(info.shell, &mut cmd);

        match fs::File::create(&file_path) {
            Ok(mut file) => {
                if let Err(e) = file.write_all(&completions) {
                    println!(
                        "  {} {} (failed to write: {e})",
                        "✗".red().bold(),
                        info.name
                    );
                    continue;
                }
                println!(
                    "  {} {} → {}",
                    "✓".green().bold(),
                    info.name.bold(),
                    file_path.display()
                );
                installed += 1;
            }
            Err(e) => {
                println!(
                    "  {} {} (failed to create file: {e})",
                    "✗".red().bold(),
                    info.name
                );
            }
        }
    }

    println!();
    if installed > 0 {
        println!(
            "{} Installed completions for {} shell(s)",
            "✓".green().bold(),
            installed
        );
        println!(
            "\n{} Restart your shell or source the completion file to enable completions.",
            "Note:".cyan().bold()
        );
    }

    if skipped > 0 && !force {
        println!(
            "\n{} Use {} to overwrite existing files.",
            "Tip:".blue().bold(),
            "--force".bold()
        );
    }

    Ok(())
}

/// Runs the completions command.
///
/// # Errors
///
/// Returns an error if completion installation fails.
#[allow(clippy::unnecessary_wraps)]
pub(crate) fn run(args: &CompletionsArgs) -> Result<(), String> {
    match &args.command {
        CompletionsCommand::Generate { shell } => {
            let mut cmd = crate::Cli::command();
            print_completions(*shell, &mut cmd);
            Ok(())
        }
        CompletionsCommand::Install { force } => install_completions(*force),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_expand_tilde() {
        let path = expand_tilde("~/test");
        assert!(path.to_string_lossy().contains("test"));
        assert!(!path.to_string_lossy().starts_with('~'));
    }

    #[test]
    fn test_generate_completions_produces_output() {
        let mut cmd = clap::Command::new("test");
        let output = generate_completions(Shell::Bash, &mut cmd);
        assert!(!output.is_empty());
    }
}
