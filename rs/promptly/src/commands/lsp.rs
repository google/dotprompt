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

//! The `lsp` command for starting the Language Server.

use clap::Args;

/// Arguments for the lsp command.
#[derive(Args, Debug)]
pub(crate) struct LspArgs {
    /// Use stdio for communication (default)
    #[arg(long, default_value = "true")]
    pub stdio: bool,
}

/// Runs the LSP server.
///
/// # Errors
///
/// Returns an error if the server fails to start.
pub(crate) fn run(_args: &LspArgs) -> Result<(), String> {
    // Create a tokio runtime and run the LSP server
    let rt = tokio::runtime::Runtime::new()
        .map_err(|e| format!("Failed to create tokio runtime: {e}"))?;

    rt.block_on(async {
        crate::lsp::run_server()
            .await
            .map_err(|e| format!("LSP server error: {e}"))
    })
}
