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

//! DirStore implementation.

#![allow(
    clippy::option_if_let_else,
    clippy::or_fun_call,
    clippy::collapsible_if,
    clippy::manual_let_else,
    clippy::redundant_pattern_matching,
    clippy::redundant_closure_for_method_calls,
    clippy::collapsible_else_if,
    clippy::doc_markdown,
    clippy::must_use_candidate
)]

use crate::error::{DotpromptError, Result};
use crate::store::{DeletePromptOrPartialOptions, PromptStore, PromptStoreWritable};
use crate::types::{
    ListPartialsOptions, ListPromptsOptions, LoadPartialOptions, LoadPromptOptions,
    PaginatedPartials, PaginatedPrompts, PartialData, PartialRef, PromptData, PromptRef,
};
use crate::util::validate_prompt_name;
use sha1::{Digest, Sha1};
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Configuration options for DirStore.
#[derive(Debug, Clone)]
pub struct DirStoreOptions {
    /// Base directory for prompts.
    pub directory: PathBuf,
}

/// A directory-based prompt store.
///
/// `DirStore` manages prompts stored as files in a directory structure.
/// It supports:
/// - Standard prompts (`name.prompt`)
/// - Partial prompts (`_name.prompt`)
/// - Variants (`name.variant.prompt`)
/// - Nested directories (`folder/name.prompt`)
///
/// It includes robust security checks to prevent path traversal attacks.
#[derive(Debug)]
pub struct DirStore {
    directory: PathBuf,
}

impl DirStore {
    /// Creates a new DirStore.
    pub fn new(options: DirStoreOptions) -> Self {
        Self {
            directory: options.directory,
        }
    }

    fn calculate_version(content: &str) -> String {
        let mut hasher = Sha1::new();
        hasher.update(content.as_bytes());
        let result = hasher.finalize();
        hex::encode(result)[..8].to_string()
    }

    /// Verifies that a given file path is contained within the store's base directory.
    fn verify_path_containment(&self, file_path: &Path, name: &str) -> Result<()> {
        let abs_base = if self.directory.is_absolute() {
            self.directory.clone()
        } else {
            std::env::current_dir()?.join(&self.directory)
        };
        let canonical_base = match fs::canonicalize(&abs_base) {
            Ok(p) => p,
            Err(e) => {
                return Err(DotpromptError::StoreError(format!(
                    "Failed to resolve store base directory: {e}"
                )));
            }
        };

        if file_path.exists() {
            let canonical_path = fs::canonicalize(file_path).map_err(|e| {
                DotpromptError::StoreError(format!(
                    "Failed to resolve path '{}': {e}",
                    file_path.display()
                ))
            })?;
            if !canonical_path.starts_with(&canonical_base) {
                return Err(DotpromptError::StoreError(format!(
                    "Path traversal attempt detected: '{name}'"
                )));
            }
        } else {
            if let Some(parent) = file_path.parent() {
                if parent.exists() {
                    let canonical_parent = fs::canonicalize(parent).map_err(|e| {
                        DotpromptError::StoreError(format!(
                            "Failed to resolve parent path '{}': {e}",
                            parent.display()
                        ))
                    })?;
                    if !canonical_parent.starts_with(&canonical_base) {
                        return Err(DotpromptError::StoreError(format!(
                            "Path traversal attempt detected: '{name}'"
                        )));
                    }
                }
            }
        }
        Ok(())
    }

    fn parse_filename(filename: &str) -> Option<(String, Option<String>)> {
        if !filename.ends_with(".prompt") {
            return None;
        }
        let stem = &filename[..filename.len() - 7];
        let parts: Vec<&str> = stem.split('.').collect();
        if parts.len() == 1 {
            Some((parts[0].to_string(), None))
        } else if let Some(variant) = parts.last() {
            let variant_string = variant.to_string();
            let name = parts[..parts.len() - 1].join(".");
            Some((name, Some(variant_string)))
        } else {
            None
        }
    }

    fn is_partial(filename: &str) -> bool {
        filename.starts_with('_')
    }
}

impl PromptStore for DirStore {
    /// Lists all prompts in the store that match the given options.
    ///
    /// This method recursively walks the directory structure to find `.prompt` files.
    /// It filters out matching files based on the requested variant (if any).
    /// Files starting with `_` are treated as partials and excluded from this list.
    ///
    /// # Arguments
    ///
    /// * `options` - Optional filter criteria (limit, cursor, variant).
    fn list(&self, options: Option<ListPromptsOptions>) -> Result<PaginatedPrompts> {
        if let Some(opts) = &options {
            if let Some(v) = &opts.variant {
                validate_prompt_name(v)?;
            }
        }

        let mut prompts = Vec::new();
        for entry in WalkDir::new(&self.directory)
            .follow_links(false)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() {
                let file_name = entry.file_name().to_string_lossy();
                if file_name.ends_with(".prompt") && !Self::is_partial(&file_name) {
                    let path = entry.path();
                    if let Err(_) = self.verify_path_containment(path, &file_name) {
                        continue;
                    }

                    let content = match fs::read_to_string(path) {
                        Ok(c) => c,
                        Err(_) => continue,
                    };
                    let version = Self::calculate_version(&content);

                    let rel_path = match path.strip_prefix(&self.directory) {
                        Ok(p) => p,
                        Err(_) => continue,
                    };

                    let file_name_str = if let Some(n) = rel_path.file_name() {
                        n.to_string_lossy()
                    } else {
                        continue;
                    };

                    if let Some((parsed_name, variant)) = Self::parse_filename(&file_name_str) {
                        let parent = rel_path.parent();
                        let full_name = if let Some(p) = parent {
                            if p == Path::new("") {
                                parsed_name
                            } else {
                                let dir = p.to_string_lossy().replace('\\', "/");
                                format!("{dir}/{parsed_name}")
                            }
                        } else {
                            parsed_name
                        };

                        prompts.push(PromptRef {
                            name: full_name,
                            variant,
                            version: Some(version),
                        });
                    }
                }
            }
        }
        Ok(PaginatedPrompts {
            prompts,
            cursor: None,
        })
    }

    /// Lists all partials in the store.
    ///
    /// Similar to `list`, but only includes files starting with `_` (partials).
    fn list_partials(&self, options: Option<ListPartialsOptions>) -> Result<PaginatedPartials> {
        if let Some(opts) = &options {
            if let Some(v) = &opts.variant {
                validate_prompt_name(v)?;
            }
        }

        let mut partials = Vec::new();
        for entry in WalkDir::new(&self.directory)
            .follow_links(false)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() {
                let file_name = entry.file_name().to_string_lossy();
                if file_name.ends_with(".prompt") && Self::is_partial(&file_name) {
                    let path = entry.path();
                    if let Err(_) = self.verify_path_containment(path, &file_name) {
                        continue;
                    }

                    let content = match fs::read_to_string(path) {
                        Ok(c) => c,
                        Err(_) => continue,
                    };
                    let version = Self::calculate_version(&content);

                    let rel_path = match path.strip_prefix(&self.directory) {
                        Ok(p) => p,
                        Err(_) => continue,
                    };

                    let file_name_str = if let Some(n) = rel_path.file_name() {
                        n.to_string_lossy()
                    } else {
                        continue;
                    };

                    let actual_filename = &file_name_str[1..];
                    if let Some((parsed_name, variant)) = Self::parse_filename(actual_filename) {
                        let parent = rel_path.parent();
                        let full_name = if let Some(p) = parent {
                            if p == Path::new("") {
                                parsed_name
                            } else {
                                let dir = p.to_string_lossy().replace('\\', "/");
                                format!("{dir}/{parsed_name}")
                            }
                        } else {
                            parsed_name
                        };

                        partials.push(PartialRef {
                            name: full_name,
                            variant,
                            version: Some(version),
                        });
                    }
                }
            }
        }
        Ok(PaginatedPartials {
            partials,
            cursor: None,
        })
    }

    /// Loads a prompt by name.
    ///
    /// This method resolves the prompt name to a file path, checking for
    /// variant-specific files first if a variant is requested (or even if it isn't, based on usage patterns).
    /// It ensures the file exists and is within the store key.
    fn load(&self, name: &str, options: Option<LoadPromptOptions>) -> Result<PromptData> {
        validate_prompt_name(name)?;
        let variant = options.as_ref().and_then(|o| o.variant.clone());
        if let Some(ref v) = variant {
            validate_prompt_name(v)?;
        }
        let version_req = options.as_ref().and_then(|o| o.version.clone());

        let name_path = Path::new(name);
        let base_name = name_path
            .file_name()
            .ok_or_else(|| DotpromptError::InvalidPromptName(name.to_string()))?
            .to_string_lossy();
        let dir_name = name_path.parent().unwrap_or(Path::new(""));

        let file_name = if let Some(ref v) = variant {
            format!("{base_name}.{v}.prompt")
        } else {
            format!("{base_name}.prompt")
        };

        let file_path = self.directory.join(dir_name).join(file_name);

        self.verify_path_containment(&file_path, name)?;

        let source = fs::read_to_string(&file_path).map_err(|e| {
            if e.kind() == std::io::ErrorKind::NotFound {
                DotpromptError::StoreError(format!("Prompt not found: {name}"))
            } else {
                DotpromptError::StoreError(e.to_string())
            }
        })?;

        let version = Self::calculate_version(&source);

        if let Some(req) = version_req {
            if req != version {
                return Err(DotpromptError::StoreError(format!(
                    "Version mismatch for prompt '{name}': requested {req} but found {version}"
                )));
            }
        }

        Ok(PromptData {
            prompt_ref: PromptRef {
                name: name.to_string(),
                variant,
                version: Some(version),
            },
            source,
        })
    }

    /// Loads a partial prompt by name.
    ///
    /// Handles the `_` prefix convention for partials.
    fn load_partial(&self, name: &str, options: Option<LoadPartialOptions>) -> Result<PartialData> {
        validate_prompt_name(name)?;
        let variant = options.as_ref().and_then(|o| o.variant.clone());
        if let Some(ref v) = variant {
            validate_prompt_name(v)?;
        }
        let version_req = options.as_ref().and_then(|o| o.version.clone());

        let name_path = Path::new(name);
        let base_name = name_path
            .file_name()
            .ok_or_else(|| DotpromptError::InvalidPromptName(name.to_string()))?
            .to_string_lossy();
        let dir_name = name_path.parent().unwrap_or(Path::new(""));

        let file_name = if let Some(ref v) = variant {
            format!("_{base_name}.{v}.prompt")
        } else {
            format!("_{base_name}.prompt")
        };

        let file_path = self.directory.join(dir_name).join(file_name);

        self.verify_path_containment(&file_path, name)?;

        let source = fs::read_to_string(&file_path).map_err(|e| {
            if e.kind() == std::io::ErrorKind::NotFound {
                DotpromptError::StoreError(format!("Partial not found: {name}"))
            } else {
                DotpromptError::StoreError(e.to_string())
            }
        })?;

        let version = Self::calculate_version(&source);

        if let Some(req) = version_req {
            if req != version {
                return Err(DotpromptError::StoreError(format!(
                    "Version mismatch for partial '{name}': requested {req} but found {version}"
                )));
            }
        }

        Ok(PartialData {
            partial_ref: PartialRef {
                name: name.to_string(),
                variant,
                version: Some(version),
            },
            source,
        })
    }
}

impl PromptStoreWritable for DirStore {
    /// Saves a prompt to the store.
    ///
    /// Writes the prompt source to a file, creating any necessary parent directories.
    /// The filename is constructed from the prompt name and variant.
    fn save(&self, prompt: PromptData) -> Result<()> {
        let name = &prompt.prompt_ref.name;
        if name.is_empty() {
            return Err(DotpromptError::StoreError(
                "Prompt name is required for saving".to_string(),
            ));
        }
        validate_prompt_name(name)?;
        let variant = prompt.prompt_ref.variant.as_ref();
        if let Some(v) = variant {
            validate_prompt_name(v)?;
        }
        let source = &prompt.source;

        let name_path = Path::new(name);
        let base_name = name_path
            .file_name()
            .ok_or_else(|| DotpromptError::InvalidPromptName(name.clone()))?
            .to_string_lossy();
        let dir_name = name_path.parent().unwrap_or(Path::new(""));

        let file_name = if let Some(v) = variant {
            format!("{base_name}.{v}.prompt")
        } else {
            format!("{base_name}.prompt")
        };

        let file_path = self.directory.join(dir_name).join(file_name);
        let file_dir = file_path
            .parent()
            .ok_or_else(|| DotpromptError::StoreError("Invalid file path".to_string()))?;

        self.verify_path_containment(&file_path, name)?;

        fs::create_dir_all(file_dir).map_err(|e| {
            DotpromptError::StoreError(format!("Failed to create directories: {e}"))
        })?;
        fs::write(&file_path, source)
            .map_err(|e| DotpromptError::StoreError(format!("Failed to write prompt file: {e}")))?;

        Ok(())
    }

    /// Deletes a prompt or partial from the store.
    fn delete(&self, name: &str, options: Option<DeletePromptOrPartialOptions>) -> Result<()> {
        validate_prompt_name(name)?;
        let variant = options.as_ref().and_then(|o| o.variant.clone());
        if let Some(ref v) = variant {
            validate_prompt_name(v)?;
        }

        let name_path = Path::new(name);
        let base_name = name_path
            .file_name()
            .ok_or_else(|| DotpromptError::InvalidPromptName(name.to_string()))?
            .to_string_lossy();
        let dir_name = name_path.parent().unwrap_or(Path::new(""));

        let prompt_file_name = if let Some(ref v) = variant {
            format!("{base_name}.{v}.prompt")
        } else {
            format!("{base_name}.prompt")
        };
        let prompt_file_path = self.directory.join(dir_name).join(prompt_file_name);

        let partial_file_name = if let Some(ref v) = variant {
            format!("_{base_name}.{v}.prompt")
        } else {
            format!("_{base_name}.prompt")
        };
        let partial_file_path = self.directory.join(dir_name).join(partial_file_name);

        self.verify_path_containment(&prompt_file_path, name)?;
        self.verify_path_containment(&partial_file_path, name)?;

        // Try deleting prompt first
        if prompt_file_path.exists() {
            fs::remove_file(&prompt_file_path)
                .map_err(|e| DotpromptError::StoreError(format!("Failed to delete prompt: {e}")))?;
            Ok(())
        } else if partial_file_path.exists() {
            fs::remove_file(&partial_file_path).map_err(|e| {
                DotpromptError::StoreError(format!("Failed to delete partial: {e}"))
            })?;
            Ok(())
        } else {
            Err(DotpromptError::StoreError(format!(
                "Failed to delete '{name}': File not found"
            )))
        }
    }

    /// Saves a partial to the store.
    fn save_partial(&self, partial: PartialData) -> Result<()> {
        let name = &partial.partial_ref.name;
        if name.is_empty() {
            return Err(DotpromptError::StoreError(
                "Partial name is required for saving".to_string(),
            ));
        }
        validate_prompt_name(name)?;
        let variant = partial.partial_ref.variant.as_ref();
        if let Some(v) = variant {
            validate_prompt_name(v)?;
        }
        let source = &partial.source;

        let name_path = Path::new(name);
        let base_name = name_path
            .file_name()
            .ok_or_else(|| DotpromptError::InvalidPromptName(name.clone()))?
            .to_string_lossy();
        let dir_name = name_path.parent().unwrap_or(Path::new(""));

        let file_name = if let Some(v) = variant {
            format!("_{base_name}.{v}.prompt")
        } else {
            format!("_{base_name}.prompt")
        };

        let file_path = self.directory.join(dir_name).join(file_name);
        let file_dir = file_path
            .parent()
            .ok_or_else(|| DotpromptError::StoreError("Invalid file path".to_string()))?;

        self.verify_path_containment(&file_path, name)?;

        fs::create_dir_all(file_dir).map_err(|e| {
            DotpromptError::StoreError(format!("Failed to create directories: {e}"))
        })?;
        fs::write(&file_path, source).map_err(|e| {
            DotpromptError::StoreError(format!("Failed to write partial file: {e}"))
        })?;
        Ok(())
    }

    /// Deletes a partial from the store.
    fn delete_partial(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<()> {
        validate_prompt_name(name)?;
        let variant = options.as_ref().and_then(|o| o.variant.clone());
        if let Some(ref v) = variant {
            validate_prompt_name(v)?;
        }

        let name_path = Path::new(name);
        let base_name = name_path
            .file_name()
            .ok_or_else(|| DotpromptError::InvalidPromptName(name.to_string()))?
            .to_string_lossy();
        let dir_name = name_path.parent().unwrap_or(Path::new(""));

        let file_name = if let Some(ref v) = variant {
            format!("_{base_name}.{v}.prompt")
        } else {
            format!("_{base_name}.prompt")
        };
        let file_path = self.directory.join(dir_name).join(file_name);

        self.verify_path_containment(&file_path, name)?;

        if file_path.exists() {
            fs::remove_file(&file_path).map_err(|e| {
                DotpromptError::StoreError(format!("Failed to delete partial: {e}"))
            })?;
            Ok(())
        } else {
            Err(DotpromptError::StoreError(format!(
                "Failed to delete partial '{name}': File not found"
            )))
        }
    }
}
