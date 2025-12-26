/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

package com.google.dotprompt;

import com.github.jknack.handlebars.Helper;
import com.google.dotprompt.models.ToolDefinition;
import com.google.dotprompt.resolvers.PartialResolver;
import com.google.dotprompt.resolvers.SchemaResolver;
import com.google.dotprompt.resolvers.ToolResolver;
import com.google.dotprompt.store.PromptStore;
import java.util.HashMap;
import java.util.Map;

/**
 * Configuration options for the {@link Dotprompt} class.
 *
 * <p>This class provides a builder pattern for configuring Dotprompt instances, matching the
 * TypeScript {@code DotpromptOptions} interface.
 *
 * <p>Example usage:
 *
 * <pre>{@code
 * DotpromptOptions options = DotpromptOptions.builder()
 *     .setDefaultModel("gemini-1.5-pro")
 *     .setToolResolver(name -> toolMap.get(name))
 *     .setSchemaResolver(name -> schemaMap.get(name))
 *     .addTool(myToolDefinition)
 *     .build();
 *
 * Dotprompt dotprompt = new Dotprompt(options);
 * }</pre>
 */
public final class DotpromptOptions {

  private final String defaultModel;
  private final Map<String, Object> modelConfigs;
  private final Map<String, Helper<?>> helpers;
  private final Map<String, String> partials;
  private final Map<String, ToolDefinition> tools;
  private final ToolResolver toolResolver;
  private final Map<String, Map<String, Object>> schemas;
  private final SchemaResolver schemaResolver;
  private final PartialResolver partialResolver;
  private final PromptStore store;

  private DotpromptOptions(Builder builder) {
    this.defaultModel = builder.defaultModel;
    this.modelConfigs = builder.modelConfigs;
    this.helpers = builder.helpers;
    this.partials = builder.partials;
    this.tools = builder.tools;
    this.toolResolver = builder.toolResolver;
    this.schemas = builder.schemas;
    this.schemaResolver = builder.schemaResolver;
    this.partialResolver = builder.partialResolver;
    this.store = builder.store;
  }

  /** Returns a new builder for DotpromptOptions. */
  public static Builder builder() {
    return new Builder();
  }

  /** Returns the default model to use if none is specified. */
  public String getDefaultModel() {
    return defaultModel;
  }

  /** Returns the model-specific configuration overrides. */
  public Map<String, Object> getModelConfigs() {
    return modelConfigs;
  }

  /** Returns the pre-registered helpers. */
  public Map<String, Helper<?>> getHelpers() {
    return helpers;
  }

  /** Returns the pre-registered partials. */
  public Map<String, String> getPartials() {
    return partials;
  }

  /** Returns the static tool definitions. */
  public Map<String, ToolDefinition> getTools() {
    return tools;
  }

  /** Returns the tool resolver for dynamic tool lookup. */
  public ToolResolver getToolResolver() {
    return toolResolver;
  }

  /** Returns the static schema definitions. */
  public Map<String, Map<String, Object>> getSchemas() {
    return schemas;
  }

  /** Returns the schema resolver for dynamic schema lookup. */
  public SchemaResolver getSchemaResolver() {
    return schemaResolver;
  }

  /** Returns the partial resolver for dynamic partial lookup. */
  public PartialResolver getPartialResolver() {
    return partialResolver;
  }

  /** Returns the prompt store for loading prompts and partials. */
  public PromptStore getStore() {
    return store;
  }

  /** Builder for {@link DotpromptOptions}. */
  public static final class Builder {
    private String defaultModel;
    private Map<String, Object> modelConfigs = new HashMap<>();
    private Map<String, Helper<?>> helpers = new HashMap<>();
    private Map<String, String> partials = new HashMap<>();
    private Map<String, ToolDefinition> tools = new HashMap<>();
    private ToolResolver toolResolver;
    private Map<String, Map<String, Object>> schemas = new HashMap<>();
    private SchemaResolver schemaResolver;
    private PartialResolver partialResolver;
    private PromptStore store;

    private Builder() {}

    /**
     * Sets the default model to use if none is specified.
     *
     * @param defaultModel The default model identifier.
     * @return This builder for chaining.
     */
    public Builder setDefaultModel(String defaultModel) {
      this.defaultModel = defaultModel;
      return this;
    }

    /**
     * Sets the model-specific configuration overrides.
     *
     * @param modelConfigs Map of model names to configuration objects.
     * @return This builder for chaining.
     */
    public Builder setModelConfigs(Map<String, Object> modelConfigs) {
      this.modelConfigs = modelConfigs != null ? new HashMap<>(modelConfigs) : new HashMap<>();
      return this;
    }

    /**
     * Adds a model-specific configuration.
     *
     * @param model The model identifier.
     * @param config The configuration for this model.
     * @return This builder for chaining.
     */
    public Builder addModelConfig(String model, Object config) {
      this.modelConfigs.put(model, config);
      return this;
    }

    /**
     * Sets the pre-registered helpers.
     *
     * @param helpers Map of helper names to implementations.
     * @return This builder for chaining.
     */
    public Builder setHelpers(Map<String, Helper<?>> helpers) {
      this.helpers = helpers != null ? new HashMap<>(helpers) : new HashMap<>();
      return this;
    }

    /**
     * Adds a helper.
     *
     * @param name The helper name.
     * @param helper The helper implementation.
     * @return This builder for chaining.
     */
    public Builder addHelper(String name, Helper<?> helper) {
      this.helpers.put(name, helper);
      return this;
    }

    /**
     * Sets the pre-registered partials.
     *
     * @param partials Map of partial names to template strings.
     * @return This builder for chaining.
     */
    public Builder setPartials(Map<String, String> partials) {
      this.partials = partials != null ? new HashMap<>(partials) : new HashMap<>();
      return this;
    }

    /**
     * Adds a partial.
     *
     * @param name The partial name.
     * @param template The template string.
     * @return This builder for chaining.
     */
    public Builder addPartial(String name, String template) {
      this.partials.put(name, template);
      return this;
    }

    /**
     * Sets the static tool definitions.
     *
     * @param tools Map of tool names to definitions.
     * @return This builder for chaining.
     */
    public Builder setTools(Map<String, ToolDefinition> tools) {
      this.tools = tools != null ? new HashMap<>(tools) : new HashMap<>();
      return this;
    }

    /**
     * Adds a tool definition.
     *
     * @param definition The tool definition.
     * @return This builder for chaining.
     */
    public Builder addTool(ToolDefinition definition) {
      this.tools.put(definition.name(), definition);
      return this;
    }

    /**
     * Sets the tool resolver for dynamic tool lookup.
     *
     * @param toolResolver The tool resolver.
     * @return This builder for chaining.
     */
    public Builder setToolResolver(ToolResolver toolResolver) {
      this.toolResolver = toolResolver;
      return this;
    }

    /**
     * Sets the static schema definitions.
     *
     * @param schemas Map of schema names to JSON Schema definitions.
     * @return This builder for chaining.
     */
    public Builder setSchemas(Map<String, Map<String, Object>> schemas) {
      this.schemas = schemas != null ? new HashMap<>(schemas) : new HashMap<>();
      return this;
    }

    /**
     * Adds a schema definition.
     *
     * @param name The schema name.
     * @param schema The JSON Schema definition.
     * @return This builder for chaining.
     */
    public Builder addSchema(String name, Map<String, Object> schema) {
      this.schemas.put(name, schema);
      return this;
    }

    /**
     * Sets the schema resolver for dynamic schema lookup.
     *
     * @param schemaResolver The schema resolver.
     * @return This builder for chaining.
     */
    public Builder setSchemaResolver(SchemaResolver schemaResolver) {
      this.schemaResolver = schemaResolver;
      return this;
    }

    /**
     * Sets the partial resolver for dynamic partial lookup.
     *
     * @param partialResolver The partial resolver.
     * @return This builder for chaining.
     */
    public Builder setPartialResolver(PartialResolver partialResolver) {
      this.partialResolver = partialResolver;
      return this;
    }

    /**
     * Sets the prompt store for loading prompts and partials.
     *
     * @param store The prompt store.
     * @return This builder for chaining.
     */
    public Builder setStore(PromptStore store) {
      this.store = store;
      return this;
    }

    /**
     * Builds the DotpromptOptions instance.
     *
     * @return A new DotpromptOptions configured with this builder's settings.
     */
    public DotpromptOptions build() {
      return new DotpromptOptions(this);
    }
  }
}
