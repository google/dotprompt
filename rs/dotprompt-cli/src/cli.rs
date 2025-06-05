// Copyright 2025 Google LLC
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

//! CLI parsing for Dotprompt.

use std::path::PathBuf;

use clap::builder::styling::{AnsiColor, Styles};
use clap::{Arg, Command, Parser, crate_authors, crate_description, crate_name, crate_version};

/// Configuration for the CLI.
#[derive(Debug, Parser)]
pub struct Config {
    /// The path to the template file.
    template: PathBuf,
    /// The JSON data object to render the template with.
    data: String,
    /// The path to the partials directory.
    partials_dir: Option<PathBuf>,
    /// The path to the helpers directory.
    helpers: String,
}

/// Styles for the CLI.
const CLI_STYLES: Styles = Styles::styled()
    .header(AnsiColor::Yellow.on_default().bold())
    .usage(AnsiColor::Yellow.on_default().bold())
    .literal(AnsiColor::Cyan.on_default().bold())
    .error(AnsiColor::Red.on_default().bold())
    .placeholder(AnsiColor::Magenta.on_default());

/// Parse the CLI arguments.
#[must_use]
fn cli() -> Command {
    let version = crate_version!();
    let authors = crate_authors!("\n");
    let description = crate_description!();
    let name = crate_name!();
    let repo = option_env!("CARGO_PKG_REPOSITORY");
    let license = option_env!("CARGO_PKG_LICENSE");
    let mut command = Command::new(name)
        .version(version)
        .author(authors)
        .styles(CLI_STYLES)
        .next_line_help(true)
        .arg_required_else_help(true);

    if !description.is_empty() {
        command = command.about(description);
    }

    if let Some(license) = license {
        command = command.before_help(format!("{name} v{version} ({license} license)"));
    } else {
        command = command.before_help(format!("{name} v{version}"));
    }

    if let Some(repo_url) = repo {
        command = command.after_help(format!("Please report bugs at <{repo_url}/issues>"));
    }

    command = command.subcommand(
        Command::new("render")
            .about("Render a template")
            .arg(
                Arg::new("template")
                    .short('t')
                    .long("template")
                    .required(true),
            )
            .arg(Arg::new("data").short('d').long("data").required(false))
            .arg(
                Arg::new("partials")
                    .short('p')
                    .long("partials")
                    .required(false),
            )
            .arg(
                Arg::new("helpers")
                    .short('h')
                    .long("helpers")
                    .required(false),
            ),
    );

    command
}

/// Parse the CLI arguments into a Config struct.
///
/// Panics:
/// - If the template path is not provided.
/// - If the data path is not provided.
/// - If the partials path is not provided.
/// - If the helpers path is not provided.
#[must_use]
pub fn parse_config() -> Config {
    let command = cli();
    let matches = command.get_matches();

    Config {
        template: matches
            .get_one::<String>("template")
            .unwrap()
            .to_string()
            .into(),
        data: matches.get_one::<String>("data").unwrap().to_string(),
        partials_dir: matches
            .get_one::<String>("partials")
            .map(|s| s.to_string().into()),
        helpers: matches.get_one::<String>("helpers").unwrap().to_string(),
    }
}
