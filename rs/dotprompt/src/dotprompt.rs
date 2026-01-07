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

//! Main Dotprompt class for template management and rendering.
//!
//! This module provides the core `Dotprompt` struct which manages template
//! compilation, rendering, and metadata resolution.

use crate::error::{DotpromptError, Result};
use crate::helpers::register_builtin_helpers;
use crate::parse::{parse_document, to_messages};
use crate::types::{
    DataArgument, JsonSchema, ParsedPrompt, PartialResolver, PromptFunction, PromptMetadata,
    RenderedPrompt, SchemaResolver, ToolDefinition, ToolResolver,
};
use handlebars::{Handlebars, HelperDef};
use std::collections::HashMap;

/// Options for configuring a Dotprompt instance.
#[derive(Default)]
pub struct DotpromptOptions {
    /// Default model to use if none specified.
    pub default_model: Option<String>,

    /// Model-specific configurations.
    pub model_configs: Option<HashMap<String, serde_json::Value>>,

    /// Pre-registered helpers.
    pub helpers: Option<HashMap<String, Box<dyn HelperDef + Send + Sync>>>,

    /// Pre-registered partials.
    pub partials: Option<HashMap<String, String>>,

    /// Pre-registered tools.
    pub tools: Option<HashMap<String, ToolDefinition>>,

    /// Pre-registered schemas.
    pub schemas: Option<HashMap<String, JsonSchema>>,

    /// Tool resolver for dynamic tool lookup.
    pub tool_resolver: Option<Box<dyn ToolResolver>>,

    /// Schema resolver for dynamic schema lookup.
    pub schema_resolver: Option<Box<dyn SchemaResolver>>,

    /// Partial resolver for dynamic partial lookup.
    pub partial_resolver: Option<Box<dyn PartialResolver>>,
}

/// The main Dotprompt class for template management.
///
/// This struct provides methods for parsing, compiling, and rendering
/// prompt templates with Handlebars and YAML frontmatter.
///
/// # Example
///
/// ```no_run
/// use dotprompt::{Dotprompt, DataArgument};
///
/// # fn example() -> Result<(), Box<dyn std::error::Error>> {
/// let dotprompt = Dotprompt::new(None);
/// let template = r#"---
/// model: gemini-pro
/// ---
/// Hello {{name}}!"#;
///
/// let mut data = DataArgument::default();
/// data.input = Some(serde_json::json!({"name": "World"}));
///
/// # Ok(())
/// # }
/// ```
impl std::fmt::Debug for DotpromptOptions {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("DotpromptOptions")
            .field("default_model", &self.default_model)
            .field("model_configs", &self.model_configs)
            .field("helpers", &"<helpers>")
            .field("partials", &self.partials)
            .field("tools", &self.tools)
            .field("schemas", &self.schemas)
            .field(
                "tool_resolver",
                &self.tool_resolver.as_ref().map(|_| "<resolver>"),
            )
            .field(
                "schema_resolver",
                &self.schema_resolver.as_ref().map(|_| "<resolver>"),
            )
            .field(
                "partial_resolver",
                &self.partial_resolver.as_ref().map(|_| "<resolver>"),
            )
            .finish()
    }
}

/// The main Dotprompt class for template management.
///
/// This struct provides methods for parsing, compiling, and rendering
/// prompt templates with Handlebars and YAML frontmatter.
#[allow(dead_code)] // Fields will be used in future functionality
pub struct Dotprompt {
    handlebars: Handlebars<'static>,
    default_model: Option<String>,
    model_configs: HashMap<String, serde_json::Value>,
    tools: HashMap<String, ToolDefinition>,
    schemas: HashMap<String, JsonSchema>,
    tool_resolver: Option<Box<dyn ToolResolver>>,
    schema_resolver: Option<Box<dyn SchemaResolver>>,
    partial_resolver: Option<Box<dyn PartialResolver>>,
}

impl std::fmt::Debug for Dotprompt {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Dotprompt")
            .field("handlebars", &"<handlebars>")
            .field("default_model", &self.default_model)
            .field("model_configs", &self.model_configs)
            .field("tools", &self.tools)
            .field("schemas", &self.schemas)
            .field(
                "tool_resolver",
                &self.tool_resolver.as_ref().map(|_| "<resolver>"),
            )
            .field(
                "schema_resolver",
                &self.schema_resolver.as_ref().map(|_| "<resolver>"),
            )
            .field(
                "partial_resolver",
                &self.partial_resolver.as_ref().map(|_| "<resolver>"),
            )
            .finish()
    }
}

impl Dotprompt {
    /// Creates a new Dotprompt instance.
    ///
    /// # Arguments
    ///
    /// * `options` - Optional configuration options
    ///
    /// # Returns
    ///
    /// Returns a new `Dotprompt` instance.
    pub fn new(options: Option<DotpromptOptions>) -> Self {
        let mut handlebars = Handlebars::new();
        handlebars.set_strict_mode(false);
        // Disable HTML escaping to match JS behavior
        handlebars.register_escape_fn(handlebars::no_escape);

        // Register built-in helpers
        register_builtin_helpers(&mut handlebars);

        let opts = options.unwrap_or_default();

        // Register custom helpers
        if let Some(helpers) = opts.helpers {
            for (name, helper) in helpers {
                handlebars.register_helper(&name, helper);
            }
        }

        // Register partials
        if let Some(partials) = opts.partials {
            for (name, source) in partials {
                let _ = handlebars.register_template_string(&name, source);
            }
        }

        Self {
            handlebars,
            default_model: opts.default_model,
            model_configs: opts.model_configs.unwrap_or_default(),
            tools: opts.tools.unwrap_or_default(),
            schemas: opts.schemas.unwrap_or_default(),
            tool_resolver: opts.tool_resolver,
            schema_resolver: opts.schema_resolver,
            partial_resolver: opts.partial_resolver,
        }
    }

    /// Registers a helper function.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the helper
    /// * `helper` - The helper implementation
    ///
    /// # Returns
    ///
    /// Returns a mutable reference to self for chaining.
    pub fn define_helper(
        &mut self,
        name: impl Into<String>,
        helper: Box<dyn HelperDef + Send + Sync>,
    ) -> &mut Self {
        self.handlebars.register_helper(&name.into(), helper);
        self
    }

    /// Registers a partial template.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the partial
    /// * `source` - Template source for the partial
    ///
    /// # Returns
    ///
    /// Returns a mutable reference to self for chaining.
    ///
    /// # Errors
    ///
    /// Returns error if template compilation fails.
    pub fn define_partial(
        &mut self,
        name: impl Into<String>,
        source: impl Into<String>,
    ) -> Result<&mut Self> {
        self.handlebars
            .register_template_string(&name.into(), source.into())
            .map_err(|e| DotpromptError::CompilationError(e.to_string()))?;
        Ok(self)
    }

    /// Registers a tool definition.
    ///
    /// # Arguments
    ///
    /// * `def` - The tool definition
    ///
    /// # Returns
    ///
    /// Returns a mutable reference to self for chaining.
    pub fn define_tool(&mut self, def: ToolDefinition) -> &mut Self {
        self.tools.insert(def.name.clone(), def);
        self
    }

    /// Parses a prompt template.
    ///
    /// # Arguments
    ///
    /// * `source` - The template source with frontmatter
    ///
    /// # Returns
    ///
    /// Returns a `ParsedPrompt` with metadata and template.
    ///
    /// # Errors
    ///
    /// Returns error if parsing fails.
    pub fn parse<M>(&self, source: impl AsRef<str>) -> Result<ParsedPrompt<M>>
    where
        M: serde::de::DeserializeOwned + Default,
    {
        parse_document(source.as_ref())
    }

    /// Renders a prompt template.
    ///
    /// # Arguments
    ///
    /// * `source` - The template source
    /// * `data` - Data for rendering
    /// * `options` - Additional metadata options
    ///
    /// # Returns
    ///
    /// Returns a `RenderedPrompt` with messages.
    ///
    /// # Errors
    ///
    /// Returns error if rendering fails.
    pub fn render<V, M>(
        &self,
        source: impl AsRef<str>,
        data: &DataArgument<V>,
        options: Option<PromptMetadata<M>>,
    ) -> Result<RenderedPrompt<M>>
    where
        V: serde::Serialize + Default + Clone,
        M: serde::de::DeserializeOwned + Default + Clone,
    {
        // Delegate to sync implementation
        self.render_sync(source, data, options)
    }

    /// Renders a prompt template synchronously.
    ///
    /// This is the synchronous version of `render`. Use this when you don't need
    /// async resolution of tools, schemas, or partials.
    ///
    /// # Arguments
    ///
    /// * `source` - The template source
    /// * `data` - Data for rendering
    /// * `options` - Additional metadata options
    ///
    /// # Returns
    ///
    /// Returns a `RenderedPrompt` with messages.
    ///
    /// # Errors
    ///
    /// Returns error if rendering fails.
    pub fn render_sync<V, M>(
        &self,
        source: impl AsRef<str>,
        data: &DataArgument<V>,
        _options: Option<PromptMetadata<M>>,
    ) -> Result<RenderedPrompt<M>>
    where
        V: serde::Serialize + Default + Clone,
        M: serde::de::DeserializeOwned + Default + Clone,
    {
        let parsed: ParsedPrompt<M> = self.parse(source.as_ref())?;

        // Build render context from input
        let mut render_context = data.input.as_ref().map_or_else(
            || serde_json::Value::Object(serde_json::Map::new()),
            |input| {
                serde_json::to_value(input)
                    .unwrap_or_else(|_| serde_json::Value::Object(serde_json::Map::new()))
            },
        );

        // Add @state from context.state if available
        if let (serde_json::Value::Object(map), Some(context)) =
            (&mut render_context, &data.context)
        {
            // context is HashMap<String, Value>, get "state" key
            // Add state as __state (workaround for Handlebars @ prefix)
            if let Some(state) = context.get("state") {
                if let Some(state_obj) = state.as_object() {
                    for (k, v) in state_obj {
                        // Add each state field as __state.field
                        let at_state = map
                            .entry("__state".to_string())
                            .or_insert(serde_json::Value::Object(serde_json::Map::new()));
                        if let serde_json::Value::Object(at_state_map) = at_state {
                            at_state_map.insert(k.clone(), v.clone());
                        }
                    }
                } else {
                    // If state is not an object, just insert it directly
                    map.insert("__state".to_string(), state.clone());
                }
            }
        }

        // Preprocess template to replace @state with __state for Handlebars compatibility
        // Handlebars treats @ as special prefix for private data, so we use __state as workaround
        let preprocessed_template = parsed
            .template
            .replace("{{@state.", "{{__state.")
            .replace("{{ @state.", "{{ __state.");

        // Render template
        let rendered_string = self
            .handlebars
            .render_template(&preprocessed_template, &render_context)
            .map_err(|e| DotpromptError::RenderError(e.to_string()))?;

        // Convert to messages (passing data for history)
        let messages = to_messages(&rendered_string, Some(data));

        Ok(RenderedPrompt {
            metadata: parsed.metadata,
            messages,
        })
    }

    /// Registers a schema definition.
    ///
    /// # Arguments
    ///
    /// * `name` - Name of the schema
    /// * `schema` - The JSON Schema definition
    ///
    /// # Returns
    ///
    /// Returns a mutable reference to self for chaining.
    pub fn define_schema(&mut self, name: impl Into<String>, schema: JsonSchema) -> &mut Self {
        self.schemas.insert(name.into(), schema);
        self
    }

    /// Compiles a template into a reusable prompt function.
    ///
    /// # Arguments
    ///
    /// * `source` - The template source or parsed prompt
    /// * `additional_metadata` - Optional additional metadata
    ///
    /// # Returns
    ///
    /// Returns a `PromptFunction` that can be used to render the template.
    ///
    /// # Errors
    ///
    /// Returns error if compilation fails.
    pub fn compile<M>(
        &self,
        source: impl AsRef<str>,
        _additional_metadata: Option<PromptMetadata<M>>,
    ) -> Result<PromptFunction<M>>
    where
        M: serde::de::DeserializeOwned + Default + Clone,
    {
        let prompt: ParsedPrompt<M> = self.parse(source.as_ref())?;
        Ok(PromptFunction { prompt })
    }

    /// Processes and resolves all metadata for a prompt template.
    ///
    /// # Arguments
    ///
    /// * `source` - The template source
    /// * `additional_metadata` - Additional metadata to include
    ///
    /// # Returns
    ///
    /// Returns the fully processed metadata.
    ///
    /// # Errors
    ///
    /// Returns error if parsing fails.
    pub fn render_metadata<M>(
        &self,
        source: impl AsRef<str>,
        additional_metadata: Option<PromptMetadata<M>>,
    ) -> Result<PromptMetadata<M>>
    where
        M: serde::de::DeserializeOwned + Default + Clone,
    {
        let parsed: ParsedPrompt<M> = self.parse(source.as_ref())?;
        self.resolve_metadata(parsed.metadata, additional_metadata)
    }

    /// Merges multiple metadata objects together, resolving tools and schemas.
    ///
    /// # Arguments
    ///
    /// * `base` - The base metadata object
    /// * `additional` - Additional metadata to merge
    ///
    /// # Returns
    ///
    /// Returns the merged and processed metadata.
    ///
    /// # Errors
    ///
    /// Returns error if resolution fails.
    pub fn resolve_metadata<M>(
        &self,
        mut base: PromptMetadata<M>,
        additional: Option<PromptMetadata<M>>,
    ) -> Result<PromptMetadata<M>>
    where
        M: Default + Clone,
    {
        // Merge additional metadata if provided
        if let Some(extra) = additional {
            if extra.model.is_some() {
                base.model = extra.model;
            }
            if extra.config.is_some() {
                base.config = extra.config;
            }
            if extra.tools.is_some() {
                base.tools = extra.tools;
            }
            if extra.input.is_some() {
                base.input = extra.input;
            }
            if extra.output.is_some() {
                base.output = extra.output;
            }
        }

        // Apply default model if none specified
        if base.model.is_none() {
            base.model.clone_from(&self.default_model);
        }

        // Resolve tool references
        base = self.resolve_tools(base);

        Ok(base)
    }

    /// Resolves tool names to their definitions.
    ///
    /// # Arguments
    ///
    /// * `meta` - The metadata containing tool references
    ///
    /// # Returns
    ///
    /// Returns metadata with resolved tool definitions.
    pub fn resolve_tools<M>(&self, mut meta: PromptMetadata<M>) -> PromptMetadata<M> {
        if let Some(tool_names) = &meta.tools {
            let mut resolved_defs = meta.tool_defs.take().unwrap_or_default();

            for name in tool_names {
                // Check registered tools first
                if let Some(def) = self.tools.get(name) {
                    resolved_defs.push(def.clone());
                } else if let Some(resolver) = &self.tool_resolver {
                    // Try resolver
                    if let Some(def) = resolver.resolve(name) {
                        resolved_defs.push(def);
                    }
                }
            }

            if !resolved_defs.is_empty() {
                meta.tool_defs = Some(resolved_defs);
            }
        }
        meta
    }

    /// Identifies all partial references in a template.
    ///
    /// # Arguments
    ///
    /// * `template` - The template to scan
    ///
    /// # Returns
    ///
    /// Returns a set of partial names referenced in the template.
    ///
    /// # Panics
    ///
    /// Panics if the internal regex pattern fails to compile (should never happen).
    #[must_use]
    #[allow(clippy::expect_used)]
    pub fn identify_partials(&self, template: &str) -> std::collections::HashSet<String> {
        let mut partials = std::collections::HashSet::new();
        // Simple regex-based partial detection: {{> partialName}}
        let re = regex::Regex::new(r"\{\{>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
            .expect("internal regex pattern should compile");
        for cap in re.captures_iter(template) {
            if let Some(name) = cap.get(1) {
                partials.insert(name.as_str().to_string());
            }
        }
        partials
    }

    /// Resolves and registers all partials referenced in a template.
    ///
    /// # Arguments
    ///
    /// * `template` - The template containing partial references
    ///
    /// # Errors
    ///
    /// Returns error if a partial cannot be resolved.
    pub fn resolve_partials(&mut self, template: &str) -> Result<()> {
        let partial_names = self.identify_partials(template);

        for name in partial_names {
            // Skip if already registered
            if self.handlebars.get_template(&name).is_some() {
                continue;
            }

            // Try resolver
            #[allow(clippy::collapsible_if)]
            if let Some(resolver) = &self.partial_resolver {
                if let Some(source) = resolver.resolve(&name) {
                    self.handlebars
                        .register_template_string(&name, source)
                        .map_err(|e| DotpromptError::CompilationError(e.to_string()))?;
                }
            }
        }
        Ok(())
    }

    /// Processes schema definitions in picoschema format into standard JSON Schema.
    ///
    /// This resolves any compact picoschema syntax in the input/output schemas
    /// to their full JSON Schema equivalents.
    ///
    /// # Arguments
    ///
    /// * `meta` - The prompt metadata containing schema definitions
    ///
    /// # Returns
    ///
    /// Returns the processed metadata with expanded schemas.
    ///
    /// # Errors
    ///
    /// Returns error if picoschema conversion fails.
    pub fn render_picoschema<M>(&self, mut meta: PromptMetadata<M>) -> Result<PromptMetadata<M>>
    where
        M: Default + Clone,
    {
        use crate::picoschema::picoschema_to_json_schema;

        // Process input schema if present
        #[allow(clippy::collapsible_if)]
        if let Some(ref mut input) = meta.input {
            if let Some(ref schema) = input.schema {
                let converted = picoschema_to_json_schema(schema)?;
                input.schema = Some(converted);
            }
        }

        // Process output schema if present
        #[allow(clippy::collapsible_if)]
        if let Some(ref mut output) = meta.output {
            if let Some(ref schema) = output.schema {
                let converted = picoschema_to_json_schema(schema)?;
                output.schema = Some(converted);
            }
        }

        Ok(meta)
    }
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_new_dotprompt() {
        let dp = Dotprompt::new(None);
        assert!(dp.tools.is_empty());
    }

    #[test]
    fn test_parse() {
        let dp = Dotprompt::new(None);
        let source = "---\nmodel: gemini-pro\n---\nHello!";
        let parsed: ParsedPrompt = dp.parse(source).expect("parse should succeed");
        assert_eq!(parsed.metadata.model, Some("gemini-pro".to_string()));
    }

    #[test]
    fn test_render_simple() {
        let dp = Dotprompt::new(None);
        let source = "Hello {{name}}!";
        let data = DataArgument {
            input: Some(json!({"name": "World"})),
            ..Default::default()
        };

        let rendered = dp
            .render(source, &data, None::<PromptMetadata>)
            .expect("render should succeed");
        assert_eq!(rendered.messages.len(), 1);
    }

    #[test]
    fn test_define_tool() {
        let mut dp = Dotprompt::new(None);
        let tool = ToolDefinition {
            name: "test".to_string(),
            description: Some("Test tool".to_string()),
            input_schema: HashMap::new(),
            output_schema: None,
        };
        dp.define_tool(tool);
        assert!(dp.tools.contains_key("test"));
    }
}
