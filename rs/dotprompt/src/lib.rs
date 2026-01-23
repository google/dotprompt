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

//! Dotprompt: Executable `GenAI` Prompt Templates for Rust
//!
//! This library provides a Rust implementation of the dotprompt format, which is
//! a language-neutral executable prompt template format for Generative AI.
//!
//! # Features
//!
//! - YAML frontmatter for prompt metadata
//! - Handlebars templating engine
//! - Picoschema to JSON Schema conversion
//! - Built-in helpers for common prompt patterns
//! - Type-safe prompt rendering
//!
//! # Example
//!
//! ```no_run
//! use dotprompt::{Dotprompt, DataArgument, RenderedPrompt};
//!
//! # fn example() -> Result<(), Box<dyn std::error::Error>> {
//! let dotprompt = Dotprompt::new(None);
//! let template = r#"---
//! model: gemini-pro
//! ---
//! Hello {{name}}!"#;
//!
//! let mut data = DataArgument::default();
//! data.input = Some(serde_json::json!({"name": "World"}));
//!
//! let rendered: RenderedPrompt = dotprompt.render(template, &data, None)?;
//! # Ok(())
//! # }
//! ```

#![forbid(unsafe_code)]
#![deny(missing_docs)]
#![deny(missing_debug_implementations)]

pub mod dotprompt;
pub mod error;
pub mod helpers;
pub mod parse;
pub mod picoschema;
pub mod store;
pub mod stores;
pub mod types;
pub mod util;

// Re-export main types for convenience
pub use dotprompt::{Dotprompt, DotpromptOptions};
pub use error::{DotpromptError, Result};
pub use store::{PromptStore, PromptStoreWritable};
pub use types::*;
