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

//! Prompt store trait and related types.
//!
//! This module defines the `PromptStore` trait for reading and writing
//! prompts and partials, matching the canonical JavaScript implementation.

use crate::error::Result;
use crate::types::{
    ListPartialsOptions, ListPromptsOptions, LoadPartialOptions, LoadPromptOptions,
    PaginatedPartials, PaginatedPrompts, PartialData, PromptData,
};

/// A store for reading prompts and partials.
///
/// This trait provides the common interface for prompt storage backends,
/// such as file systems, databases, or remote services.
pub trait PromptStore: Send + Sync {
    /// Returns a paginated list of all prompts in the store.
    ///
    /// # Arguments
    ///
    /// * `options` - Optional pagination options
    ///
    /// # Returns
    ///
    /// A paginated list of prompt references.
    ///
    /// # Errors
    ///
    /// Returns an error if the store cannot be accessed.
    fn list(&self, options: Option<ListPromptsOptions>) -> Result<PaginatedPrompts>;

    /// Returns a paginated list of all partials in the store.
    ///
    /// # Arguments
    ///
    /// * `options` - Optional pagination options
    ///
    /// # Returns
    ///
    /// A paginated list of partial references.
    ///
    /// # Errors
    ///
    /// Returns an error if the store cannot be accessed.
    fn list_partials(&self, options: Option<ListPartialsOptions>) -> Result<PaginatedPartials>;

    /// Loads a prompt by name.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the prompt to load
    /// * `options` - Optional loading options (variant, version)
    ///
    /// # Returns
    ///
    /// The prompt data including source.
    ///
    /// # Errors
    ///
    /// Returns an error if the prompt is not found or cannot be loaded.
    fn load(&self, name: &str, options: Option<LoadPromptOptions>) -> Result<PromptData>;

    /// Loads a partial by name.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the partial to load
    /// * `options` - Optional loading options (variant, version)
    ///
    /// # Returns
    ///
    /// The partial data including source.
    ///
    /// # Errors
    ///
    /// Returns an error if the partial is not found or cannot be loaded.
    fn load_partial(&self, name: &str, options: Option<LoadPartialOptions>) -> Result<PartialData>;
}

/// Options for deleting a prompt or partial.
#[derive(Debug, Clone, Default)]
pub struct DeletePromptOrPartialOptions {
    /// Specific variant to delete.
    pub variant: Option<String>,
}

/// A writable prompt store that supports saving and deleting.
pub trait PromptStoreWritable: PromptStore {
    /// Saves a prompt to the store.
    ///
    /// # Arguments
    ///
    /// * `prompt` - The prompt data to save
    ///
    /// # Errors
    ///
    /// Returns an error if the prompt cannot be saved.
    fn save(&self, prompt: PromptData) -> Result<()>;

    /// Deletes a prompt from the store.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the prompt to delete
    /// * `options` - Optional deletion options
    ///
    /// # Errors
    ///
    /// Returns an error if the prompt cannot be deleted.
    fn delete(&self, name: &str, options: Option<DeletePromptOrPartialOptions>) -> Result<()>;

    /// Saves a partial to the store.
    ///
    /// # Arguments
    ///
    /// * `partial` - The partial data to save
    ///
    /// # Errors
    ///
    /// Returns an error if the partial cannot be saved.
    fn save_partial(&self, partial: PartialData) -> Result<()>;

    /// Deletes a partial from the store.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the partial to delete
    /// * `options` - Optional deletion options
    ///
    /// # Errors
    ///
    /// Returns an error if the partial cannot be deleted.
    fn delete_partial(
        &self,
        name: &str,
        options: Option<DeletePromptOrPartialOptions>,
    ) -> Result<()>;
}
