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

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.jknack.handlebars.Context;
import com.github.jknack.handlebars.EscapingStrategy;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Helper;
import com.github.jknack.handlebars.Template;
import com.github.jknack.handlebars.io.StringTemplateSource;
import com.github.jknack.handlebars.io.TemplateLoader;
import com.github.jknack.handlebars.io.TemplateSource;
import com.google.dotprompt.helpers.Helpers;
import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.ParsedPrompt;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.Prompt;
import com.google.dotprompt.models.PromptFunction;
import com.google.dotprompt.models.PromptMetadata;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.Role;
import com.google.dotprompt.models.TextPart;
import com.google.dotprompt.models.ToolDefinition;
import com.google.dotprompt.parser.Parser;
import com.google.dotprompt.parser.Picoschema;
import com.google.dotprompt.resolvers.PartialResolver;
import com.google.dotprompt.resolvers.SchemaResolver;
import com.google.dotprompt.resolvers.ToolResolver;
import com.google.dotprompt.store.PromptStore;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Main entry point for the Dotprompt library.
 *
 * <p>This class provides the core functionality for parsing, rendering, and managing Dotprompt
 * templates. It integrates Handlebars for template processing and supports Picoschema for schema
 * definition.
 *
 * <p>Key features:
 *
 * <ul>
 *   <li>Template rendering with data and options merging.
 *   <li>Management of partials and helpers.
 *   <li>Configuration of default models and model-specific settings.
 *   <li>Tool definition and schema resolution.
 * </ul>
 */
public class Dotprompt {
  /** The Handlebars engine instance used for rendering templates. */
  private final Handlebars handlebars;

  /** A custom template loader that allows dynamic registration of partials. */
  private final DynamicLoader templateLoader;

  // Configuration maps
  private final Map<String, Object> modelConfigs;
  private final Map<String, ToolDefinition> toolDefinitions;
  private final String defaultModel;

  /** Optional partial resolver for dynamic partial loading. */
  private PartialResolver partialResolver;

  /** Optional tool resolver for dynamic tool resolution. */
  private ToolResolver toolResolver;

  /** Optional schema resolver for dynamic schema resolution. */
  private SchemaResolver schemaResolver;

  /** Optional prompt store for loading prompts and partials. */
  private PromptStore store;

  /** Constructs a new Dotprompt instance with default configuration. */
  public Dotprompt() {
    this(DotpromptOptions.builder().build());
  }

  /**
   * Constructs a new Dotprompt instance with the provided options.
   *
   * <p>This constructor matches the JavaScript API where all configuration is provided via
   * DotpromptOptions.
   *
   * @param options The configuration options for this Dotprompt instance.
   */
  public Dotprompt(DotpromptOptions options) {
    // Initialize handlebars and register built-in helpers.
    this.templateLoader = new DynamicLoader();
    this.handlebars = new Handlebars(templateLoader).with(EscapingStrategy.NOOP);

    // Initialize configuration from options.
    this.defaultModel = options.getDefaultModel();
    this.modelConfigs =
        options.getModelConfigs() != null
            ? new ConcurrentHashMap<>(options.getModelConfigs())
            : new ConcurrentHashMap<>();
    this.toolDefinitions =
        options.getTools() != null
            ? new ConcurrentHashMap<>(options.getTools())
            : new ConcurrentHashMap<>();
    this.toolResolver = options.getToolResolver();
    this.schemaResolver = options.getSchemaResolver();
    this.partialResolver = options.getPartialResolver();
    this.store = options.getStore();

    // Register initial helpers and partials.
    registerInitialHelpers(options.getHelpers());
    registerInitialPartials(options.getPartials());

    // Register initial schemas from options.
    if (options.getSchemas() != null) {
      schemas.putAll(options.getSchemas());
    }
  }

  /**
   * Defines a custom Handlebars helper.
   *
   * @param name The name of the helper.
   * @param helper The helper implementation.
   * @return This instance for method chaining.
   */
  public Dotprompt defineHelper(String name, Helper<?> helper) {
    handlebars.registerHelper(name, helper);
    return this;
  }

  /**
   * Defines a partial template for use in other templates.
   *
   * @param name The name of the partial.
   * @param template The template string.
   * @return This instance for method chaining.
   */
  public Dotprompt definePartial(String name, String template) {
    templateLoader.put(name, template);
    return this;
  }

  /**
   * Registers a tool definition for use in prompts.
   *
   * @param definition The tool definition to register.
   * @return This instance for method chaining.
   */
  public Dotprompt defineTool(ToolDefinition definition) {
    toolDefinitions.put(definition.name(), definition);
    return this;
  }

  /**
   * Parses a prompt template string into a structured ParsedPrompt object.
   *
   * <p>This method matches the JavaScript API and delegates to {@link
   * Parser#parseDocument(String)}.
   *
   * @param source The template source string to parse.
   * @return A parsed ParsedPrompt object with extracted metadata and template.
   * @throws IOException If parsing the YAML frontmatter fails.
   */
  public ParsedPrompt parse(String source) throws IOException {
    return Parser.parseDocument(source);
  }

  /**
   * Compiles a template into a reusable PromptFunction for rendering.
   *
   * <p>This method pre-parses the template and resolves partials, returning a function that can be
   * used to render the template multiple times with different data.
   *
   * @param source The template source string to compile.
   * @return A future resolving to a reusable PromptFunction.
   */
  public CompletableFuture<PromptFunction> compile(String source) {
    return compileInternal(source, null);
  }

  /**
   * Compiles a template with additional metadata.
   *
   * @param source The template source string to compile.
   * @param additionalMetadata Additional metadata to merge into the template.
   * @return A future resolving to a reusable PromptFunction.
   */
  public CompletableFuture<PromptFunction> compile(
      String source, Map<String, Object> additionalMetadata) {
    return compileInternal(source, additionalMetadata);
  }

  private CompletableFuture<PromptFunction> compileInternal(
      String source, Map<String, Object> additionalMetadata) {
    try {
      // Parse the source - get both the raw Prompt and typed ParsedPrompt
      Prompt rawPrompt = Parser.parse(source);
      PromptMetadata metadata = PromptMetadata.fromConfig(rawPrompt.config());
      final ParsedPrompt parsedPrompt = ParsedPrompt.fromMetadata(rawPrompt.template(), metadata);

      // Merge additional metadata into config
      Map<String, Object> mergedConfig = new HashMap<>(rawPrompt.config());
      if (additionalMetadata != null) {
        mergedConfig.putAll(additionalMetadata);
      }
      // Keep raw Prompt with merged config for rendering
      final Prompt promptForRendering = new Prompt(rawPrompt.template(), mergedConfig);

      // Resolve partials before compiling
      return resolvePartialsAsync(parsedPrompt.template())
          .thenApply(
              v -> {
                try {
                  Template template = handlebars.compileInline(parsedPrompt.template());

                  return new PromptFunction() {
                    @Override
                    public CompletableFuture<RenderedPrompt> render(Map<String, Object> data) {
                      return render(data, null);
                    }

                    @Override
                    public CompletableFuture<RenderedPrompt> render(
                        Map<String, Object> data, Map<String, Object> options) {
                      return CompletableFuture.supplyAsync(
                          () -> {
                            try {
                              return renderWithTemplate(
                                  template, promptForRendering, data, options);
                            } catch (IOException e) {
                              throw new RuntimeException("Failed to render template", e);
                            }
                          });
                    }

                    @Override
                    public ParsedPrompt getPrompt() {
                      return parsedPrompt;
                    }
                  };
                } catch (IOException e) {
                  throw new RuntimeException("Failed to compile template", e);
                }
              });
    } catch (IOException e) {
      return CompletableFuture.failedFuture(e);
    }
  }

  /**
   * Renders the metadata for a template without rendering the full template.
   *
   * <p>This is useful when you need the resolved metadata (tools, schemas, etc.) without actually
   * rendering the message content.
   *
   * @param source The template source string.
   * @return A future containing the resolved metadata.
   */
  public CompletableFuture<PromptMetadata> renderMetadata(String source) {
    return renderMetadata(source, (Map<String, Object>) null);
  }

  /**
   * Renders the metadata for a template with additional overrides.
   *
   * @param source The template source string.
   * @param additionalMetadata Additional metadata to merge.
   * @return A future containing the resolved metadata.
   */
  public CompletableFuture<PromptMetadata> renderMetadata(
      String source, Map<String, Object> additionalMetadata) {
    try {
      ParsedPrompt parsedPrompt = parse(source);
      return renderMetadata(parsedPrompt, additionalMetadata);
    } catch (IOException e) {
      return CompletableFuture.failedFuture(e);
    }
  }

  /**
   * Renders the metadata for a parsed prompt with additional overrides.
   *
   * @param parsedPrompt The parsed prompt object.
   * @return A future containing the resolved metadata.
   */
  public CompletableFuture<PromptMetadata> renderMetadata(ParsedPrompt parsedPrompt) {
    return renderMetadata(parsedPrompt, (Map<String, Object>) null);
  }

  /**
   * Renders the metadata for a parsed prompt with additional overrides (typed).
   *
   * @param parsedPrompt The parsed prompt object.
   * @param additionalMetadata Additional metadata to merge.
   * @return A future containing the resolved metadata.
   */
  public CompletableFuture<PromptMetadata> renderMetadata(
      ParsedPrompt parsedPrompt, PromptMetadata additionalMetadata) {
    Map<String, Object> map = additionalMetadata != null ? additionalMetadata.toConfig() : null;
    return renderMetadata(parsedPrompt, map);
  }

  /**
   * Renders the metadata for a parsed prompt with additional overrides.
   *
   * @param parsedPrompt The parsed prompt object.
   * @param additionalMetadata Additional metadata to merge.
   * @return A future containing the resolved metadata.
   */
  public CompletableFuture<PromptMetadata> renderMetadata(
      ParsedPrompt parsedPrompt, Map<String, Object> additionalMetadata) {

    Map<String, Object> result = new HashMap<>();

    // Determine model - use ParsedPrompt's typed accessor
    String model = parsedPrompt.model();
    if (model == null && additionalMetadata != null && additionalMetadata.containsKey("model")) {
      model = (String) additionalMetadata.get("model");
    }
    if (model == null) {
      model = this.defaultModel;
    }

    Map<String, Object> configMap = new HashMap<>();

    // Apply model config
    if (model != null && this.modelConfigs.containsKey(model)) {
      Object mc = this.modelConfigs.get(model);
      if (mc instanceof Map) {
        configMap.putAll((Map<String, Object>) mc);
      }
    }

    // Put resolved model
    if (model != null) {
      result.put("model", model);
    }

    // Merge prompt config
    if (parsedPrompt.config() != null) {
      configMap.putAll(parsedPrompt.config());
    }
    result.put("config", configMap);

    // Re-populate component fields from ParsedPrompt
    if (parsedPrompt.tools() != null) {
      result.put("tools", parsedPrompt.tools());
    }
    if (parsedPrompt.input() != null) {
      Map<String, Object> inputMap = new HashMap<>();
      if (parsedPrompt.input().defaultValues() != null)
        inputMap.put("default", parsedPrompt.input().defaultValues());
      if (parsedPrompt.input().schema() != null)
        inputMap.put("schema", parsedPrompt.input().schema());
      result.put("input", inputMap);
    }
    if (parsedPrompt.output() != null) {
      Map<String, Object> outputMap = new HashMap<>();
      if (parsedPrompt.output().format() != null)
        outputMap.put("format", parsedPrompt.output().format());
      if (parsedPrompt.output().schema() != null)
        outputMap.put("schema", parsedPrompt.output().schema());
      result.put("output", outputMap);
    }

    // Merge additional metadata
    if (additionalMetadata != null) {
      if (additionalMetadata.containsKey("config")
          && additionalMetadata.get("config") instanceof Map
          && result.containsKey("config")
          && result.get("config") instanceof Map) {

        @SuppressWarnings("unchecked")
        Map<String, Object> mergedConfig =
            new HashMap<>((Map<String, Object>) result.get("config"));
        @SuppressWarnings("unchecked")
        Map<String, Object> newConfig = (Map<String, Object>) additionalMetadata.get("config");
        mergedConfig.putAll(newConfig);

        // Merge all other top-level keys from additionalMetadata, then explicitly set the merged
        // config
        Map<String, Object> tempAdditional = new HashMap<>(additionalMetadata);
        tempAdditional.remove("config"); // Remove config to avoid overwriting with unmerged version
        result.putAll(tempAdditional);
        result.put("config", mergedConfig);
      } else {
        result.putAll(additionalMetadata);
      }
    }

    // Remove template if present
    result.remove("template");

    // Process schemas
    processConfigSchemas(result);

    // Resolve tools (async) and return final metadata
    return resolveTools(result).thenApply(PromptMetadata::fromConfig);
  }

  private CompletableFuture<Map<String, Object>> resolveTools(Map<String, Object> config) {
    Object toolsObj = config.get("tools");
    if (toolsObj == null) {
      return CompletableFuture.completedFuture(config);
    }

    List<String> tools = new ArrayList<>();
    if (toolsObj instanceof List) {
      for (Object t : (List<?>) toolsObj) {
        if (t instanceof String) tools.add((String) t);
      }
    }

    if (tools.isEmpty()) {
      return CompletableFuture.completedFuture(config);
    }

    List<ToolDefinition> toolDefs = new ArrayList<>();
    List<String> unresolvedTools = new ArrayList<>();
    List<CompletableFuture<Void>> futures = new ArrayList<>();

    for (String toolName : tools) {
      // 1. Check registered definitions
      if (toolDefinitions.containsKey(toolName)) {
        toolDefs.add(toolDefinitions.get(toolName));
        continue;
      }

      // 2. Check resolver
      if (toolResolver != null) {
        // We need proper chaining for store fallback
        CompletableFuture<Void> chain =
            toolResolver
                .resolve(toolName)
                .thenCompose(
                    toolDef -> {
                      if (toolDef != null) {
                        synchronized (toolDefs) {
                          toolDefs.add(toolDef);
                        }
                        return CompletableFuture.completedFuture(null);
                      } else if (store != null) {
                        return store
                            .load(toolName, null)
                            .thenAccept(
                                promptData -> {
                                  if (promptData != null && promptData.source() != null) {
                                    try {
                                      ParsedPrompt parsedPrompt = parse(promptData.source());
                                      if (parsedPrompt.toolDefs() != null
                                          && !parsedPrompt.toolDefs().isEmpty()) {
                                        synchronized (toolDefs) {
                                          toolDefs.addAll(parsedPrompt.toolDefs());
                                        }
                                      } else {
                                        synchronized (unresolvedTools) {
                                          unresolvedTools.add(toolName);
                                        }
                                      }
                                    } catch (IOException e) {
                                      synchronized (unresolvedTools) {
                                        unresolvedTools.add(toolName);
                                      }
                                    }
                                  } else {
                                    synchronized (unresolvedTools) {
                                      unresolvedTools.add(toolName);
                                    }
                                  }
                                })
                            .exceptionally(
                                e -> {
                                  synchronized (unresolvedTools) {
                                    unresolvedTools.add(toolName);
                                  }
                                  return null;
                                });
                      } else {
                        synchronized (unresolvedTools) {
                          unresolvedTools.add(toolName);
                        }
                        return CompletableFuture.completedFuture(null);
                      }
                    });
        futures.add(chain);
      } else if (store != null) {

        // 3. Check store directly
        CompletableFuture<Void> chain =
            store
                .load(toolName, null)
                .thenAccept(
                    promptData -> {
                      if (promptData != null && promptData.source() != null) {
                        try {
                          ParsedPrompt parsedPrompt = parse(promptData.source());
                          if (parsedPrompt.toolDefs() != null
                              && !parsedPrompt.toolDefs().isEmpty()) {
                            synchronized (toolDefs) {
                              toolDefs.addAll(parsedPrompt.toolDefs());
                            }
                          } else {
                            synchronized (unresolvedTools) {
                              unresolvedTools.add(toolName);
                            }
                          }
                        } catch (IOException e) {
                          synchronized (unresolvedTools) {
                            unresolvedTools.add(toolName);
                          }
                        }
                      } else {
                        synchronized (unresolvedTools) {
                          unresolvedTools.add(toolName);
                        }
                      }
                    })
                .exceptionally(
                    e -> {
                      synchronized (unresolvedTools) {
                        unresolvedTools.add(toolName);
                      }
                      return null;
                    });
        futures.add(chain);
      } else {
        unresolvedTools.add(toolName);
      }
    }

    if (futures.isEmpty()) {
      config.put("tools", unresolvedTools);
      config.put("toolDefs", toolDefs);
      return CompletableFuture.completedFuture(config);
    }

    return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
        .thenApply(
            v -> {
              config.put("tools", unresolvedTools);
              config.put("toolDefs", toolDefs);
              return config;
            });
  }

  /**
   * Resolves all partials referenced in a template asynchronously.
   *
   * <p>This method identifies all partial references ({{> partialName}}) in the template and
   * resolves them using the configured partialResolver or store.
   *
   * @param template The template string to scan for partial references.
   * @return A future that completes when all partials are resolved.
   */
  private CompletableFuture<Void> resolvePartialsAsync(String template) {
    if (partialResolver == null && store == null) {
      return CompletableFuture.completedFuture(null);
    }

    Set<String> partialNames = identifyPartials(template);
    if (partialNames.isEmpty()) {
      return CompletableFuture.completedFuture(null);
    }

    List<CompletableFuture<Void>> futures = new ArrayList<>();

    for (String name : partialNames) {
      // Check if already registered
      if (templateLoader.templates.containsKey(name)) {
        continue;
      }

      CompletableFuture<Void> resolution = CompletableFuture.completedFuture(null);

      if (partialResolver != null) {
        resolution =
            partialResolver
                .resolve(name)
                .thenCompose(
                    content -> {
                      if (content != null) {
                        definePartial(name, content);
                        // Recursively resolve partials in the content
                        return resolvePartialsAsync(content);
                      } else if (store != null) {
                        // Try store as fallback
                        return store
                            .loadPartial(name, null)
                            .thenCompose(
                                data -> {
                                  if (data != null && data.source() != null) {
                                    definePartial(name, data.source());
                                    return resolvePartialsAsync(data.source());
                                  }
                                  return CompletableFuture.completedFuture(null);
                                });
                      }
                      return CompletableFuture.completedFuture(null);
                    });
      } else if (store != null) {
        resolution =
            store
                .loadPartial(name, null)
                .thenCompose(
                    data -> {
                      if (data != null && data.source() != null) {
                        definePartial(name, data.source());
                        return resolvePartialsAsync(data.source());
                      }
                      return CompletableFuture.completedFuture(null);
                    });
      }

      futures.add(resolution);
    }

    return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
  }

  /**
   * Identifies all partial references in a template.
   *
   * @param template The template to scan.
   * @return A set of partial names referenced in the template.
   */
  private Set<String> identifyPartials(String template) {
    Set<String> partials = new HashSet<>();
    // Match {{> partialName}} or {{> partialName context}}
    Pattern pattern = Pattern.compile("\\{\\{>\\s*([a-zA-Z0-9_-]+)");
    Matcher matcher = pattern.matcher(template);
    while (matcher.find()) {
      partials.add(matcher.group(1));
    }
    return partials;
  }

  /** Internal render method used by compiled PromptFunction. */
  private RenderedPrompt renderWithTemplate(
      Template template, Prompt prompt, Map<String, Object> data, Map<String, Object> options)
      throws IOException {

    Map<String, Object> mergedData = new HashMap<>();

    // Model config
    String model = null;
    if (prompt.config() != null && prompt.config().containsKey("model")) {
      model = (String) prompt.config().get("model");
    } else if (options != null && options.containsKey("model")) {
      model = (String) options.get("model");
    } else {
      model = this.defaultModel;
    }

    if (model != null && this.modelConfigs.containsKey(model)) {
      Object mc = this.modelConfigs.get(model);
      if (mc instanceof Map) {
        mergedData.putAll((Map<String, Object>) mc);
      }
    }

    // File defaults and config
    mergeDefaults(mergedData, prompt.config());
    if (prompt.config() != null) {
      mergedData.putAll(prompt.config());
    }

    // Options
    mergeDefaults(mergedData, options);
    if (options != null) {
      mergedData.putAll(options);
    }

    // Data
    if (data != null) {
      mergedData.putAll(data);
    }

    // Context handling
    Map<String, Object> contextData = new HashMap<>();
    if (data != null && data.containsKey("context")) {
      Map<String, Object> ctx = (Map<String, Object>) data.get("context");
      if (ctx.containsKey("state")) {
        contextData.put("state", ctx.get("state"));
      }
    }

    Context context = Context.newBuilder(mergedData).build();
    for (Map.Entry<String, Object> entry : contextData.entrySet()) {
      context.data(entry.getKey(), entry.getValue());
    }

    String renderedString = template.apply(context);

    List<Message> messages = toMessages(renderedString, mergedData);

    // Construct result config
    Map<String, Object> resultConfig = new HashMap<>();
    if (model != null && this.modelConfigs.containsKey(model)) {
      Object mc = this.modelConfigs.get(model);
      if (mc instanceof Map) {
        resultConfig.putAll((Map<String, Object>) mc);
      }
    }
    if (prompt.config() != null) {
      resultConfig.putAll(prompt.config());
    }
    if (options != null) {
      resultConfig.putAll(options);
    }

    processConfigSchemas(resultConfig);

    return new RenderedPrompt(resultConfig, messages);
  }

  /**
   * Renders a prompt template with the provided data.
   *
   * <p>This method matches the JavaScript and Python API where {@code render()} takes a template
   * source string directly.
   *
   * @param source The template source string to render.
   * @param data The data to use for rendering.
   * @return A future containing the rendered prompt.
   */
  public CompletableFuture<RenderedPrompt> render(String source, Map<String, Object> data) {
    return render(source, data, null);
  }

  /**
   * Renders a prompt template with the provided data and options.
   *
   * <p>This method matches the JavaScript and Python API where {@code render()} takes a template
   * source string directly.
   *
   * @param source The template source string to render.
   * @param data The data to use for rendering.
   * @param options Additional options (overrides/defaults).
   * @return A future containing the rendered prompt.
   */
  public CompletableFuture<RenderedPrompt> render(
      String source, Map<String, Object> data, Map<String, Object> options) {
    return compile(source)
        .thenCompose(
            promptFn -> {
              try {
                return promptFn.render(data, options);
              } catch (Exception e) {
                CompletableFuture<RenderedPrompt> failed = new CompletableFuture<>();
                failed.completeExceptionally(e);
                return failed;
              }
            });
  }

  /** registry for named Picoschema definitions. */
  private final ConcurrentHashMap<String, Map<String, Object>> schemas = new ConcurrentHashMap<>();

  /** Registers a named schema for internal resolution (used by Picoschema). */
  private void registerSchema(String name, Map<String, Object> schema) {
    schemas.put(name, schema);
  }

  /**
   * Processes schema fields in the configuration, parsing them with Picoschema.
   *
   * @param config The configuration map to process (modified in place).
   */
  private void processConfigSchemas(Map<String, Object> config) {
    processSchemaField(config, "input");
    processSchemaField(config, "output");
  }

  /**
   * Processes a specific schema field (e.g., "input" or "output").
   *
   * @param config The configuration map.
   * @param key The key of the field to process.
   */
  private void processSchemaField(Map<String, Object> config, String key) {
    if (config.containsKey(key)) {
      Object val = config.get(key);
      if (val instanceof Map) {
        Map<String, Object> section = new HashMap<>((Map<String, Object>) val);
        if (section.containsKey("schema")) {
          Object schema = section.get("schema");
          // Use Picoschema to parse, using registered schemas as resolver
          try {
            SchemaResolver resolver =
                name -> {
                  if (this.schemas.containsKey(name)) {
                    return CompletableFuture.completedFuture(this.schemas.get(name));
                  }
                  if (this.schemaResolver != null) {
                    return this.schemaResolver.resolve(name);
                  }
                  return CompletableFuture.completedFuture(null);
                };

            section.put("schema", Picoschema.parse(schema, resolver).get());
          } catch (Exception e) {
            throw new RuntimeException("Failed to parse schema", e);
          }
        }
        config.put(key, section);
      }
    }
  }

  /**
   * Merges default configuration values from source to target.
   *
   * @param target The target map to merge into.
   * @param source The source map containing defaults.
   */
  @SuppressWarnings("unchecked")
  private void mergeDefaults(Map<String, Object> target, Map<String, Object> source) {
    if (source != null) {
      Map<String, Object> inputConfig = (Map<String, Object>) source.get("input");
      if (inputConfig != null) {
        Map<String, Object> defaults = (Map<String, Object>) inputConfig.get("default");
        if (defaults != null) {
          target.putAll(defaults);
        }
      }
    }
  }

  private static final String ROLE_MARKER_PREFIX = "<<<dotprompt:role:";
  private static final String HISTORY_MARKER_PREFIX = "<<<dotprompt:history";

  // Regex to match <<<dotprompt:(role:xxx|history|media:xxx|section:xxx)>>> markers.
  private static final Pattern MARKER_PATTERN =
      Pattern.compile(
          "(?s)<<<dotprompt:(?:role:[a-zA-Z0-9_]+|history|media:[^>]+|section\\s+[a-zA-Z0-9_]+)>>>");

  /**
   * Converts a rendered string into a list of messages.
   *
   * @param renderedString The rendered template string.
   * @param data The data map (used to extract potential history).
   * @return A list of parsed Message objects.
   */
  @SuppressWarnings("unchecked")
  private List<Message> toMessages(String renderedString, Map<String, Object> data) {
    if (renderedString == null) {
      return List.of();
    }

    List<MessageBuilder> messageSources = new ArrayList<>();
    // Initial message source
    MessageBuilder currentMessage = new MessageBuilder(Role.USER);
    messageSources.add(currentMessage);

    // Extract history messages from data if available
    List<Message> historyMessages = new ArrayList<>();
    if (data != null && data.containsKey("messages")) {
      Object msgsObj = data.get("messages");
      if (msgsObj instanceof List) {
        List<?> rawList = (List<?>) msgsObj;
        for (Object item : rawList) {
          if (item instanceof Message) {
            historyMessages.add((Message) item);
          } else if (item instanceof Map) {
            try {
              Map<String, Object> map = (Map<String, Object>) item;
              String roleStr = (String) map.get("role");
              Role role = Role.fromString(roleStr != null ? roleStr : "user");

              Object contentObj = map.get("content");
              List<Part> parts = new ArrayList<>();

              if (contentObj instanceof String) {
                parts.add(new TextPart((String) contentObj));
              } else if (contentObj instanceof List) {
                List<?> contentList = (List<?>) contentObj;
                for (Object partObj : contentList) {
                  if (partObj instanceof Map) {
                    Map<String, Object> partMap = (Map<String, Object>) partObj;
                    if (partMap.containsKey("text")) {
                      parts.add(new TextPart((String) partMap.get("text")));
                    } else if (partMap.containsKey("media")) {
                      Map<String, String> mediaMap = (Map<String, String>) partMap.get("media");
                      parts.add(new MediaPart(mediaMap.get("contentType"), mediaMap.get("url")));
                    }
                  }
                }
              }
              Map<String, Object> metadata = null;
              if (map.containsKey("metadata")) {
                metadata = (Map<String, Object>) map.get("metadata");
              }
              historyMessages.add(new Message(role, parts, metadata));
            } catch (Exception e) {
              // ignore
            }
          }
        }
      }
    }
    List<Message> historySources = Parser.transformMessagesToHistory(historyMessages);

    boolean historyInjected = false;
    Matcher matcher = MARKER_PATTERN.matcher(renderedString);
    int lastEnd = 0;

    ObjectMapper mapper = new ObjectMapper();

    while (matcher.find()) {
      String text = renderedString.substring(lastEnd, matcher.start());
      if (!text.isEmpty()) {
        currentMessage.appendSource(text);
      }

      // Marker is inside <<<dotprompt: ... >>>
      String markerContent = renderedString.substring(matcher.start() + 13, matcher.end() - 3);

      try {
        if (markerContent.startsWith("role:")) {
          String roleName = markerContent.substring(5);
          Role role = Role.fromString(roleName);

          if (currentMessage.hasSource() || !currentMessage.content.isEmpty()) {
            currentMessage = new MessageBuilder(role);
            messageSources.add(currentMessage);
          } else {
            currentMessage.role = role;
          }
        } else if (markerContent.equals("history")) {
          historyInjected = true;
          if (!historySources.isEmpty()) {
            if (currentMessage.hasSource() || !currentMessage.content.isEmpty()) {
              // current message content finished
              // no need to add, already in list
            }

            for (Message hMsg : historySources) {
              MessageBuilder hSource = new MessageBuilder(hMsg.role());
              hSource.content.addAll(hMsg.content());
              messageSources.add(hSource);
            }

            currentMessage = new MessageBuilder(Role.MODEL);
            messageSources.add(currentMessage);
          } else {
            if (currentMessage.hasSource() || !currentMessage.content.isEmpty()) {
              currentMessage = new MessageBuilder(Role.MODEL);
              messageSources.add(currentMessage);
            }
          }
        } else if (markerContent.startsWith("media:")) {
          // Format: media:url URL [TYPE]
          String mediaPayload = markerContent.substring(6).trim();
          if (mediaPayload.startsWith("url ")) {
            String[] parts = mediaPayload.substring(4).split("\\s+");
            String url = parts[0];
            String contentType = parts.length > 1 ? parts[1] : "";
            currentMessage.addPart(new MediaPart(contentType, url));
          }
        } else if (markerContent.startsWith("section")) {
          // Format: section NAME
          currentMessage.addPart(new TextPart(matcher.group()));
        }
      } catch (Exception e) {
        // ignore parsing errors
      }

      lastEnd = matcher.end();
    }

    if (lastEnd < renderedString.length()) {
      currentMessage.appendSource(renderedString.substring(lastEnd));
    }

    List<Message> messages = new ArrayList<>();
    for (MessageBuilder source : messageSources) {
      List<Part> parts = source.toParts();
      if (!parts.isEmpty()) {
        messages.add(new Message(source.role, parts));
      }
    }

    boolean historyUsed = historyInjected;
    if (!historyUsed && !historyMessages.isEmpty() && !Parser.messagesHaveHistory(messages)) {
      return Parser.insertHistory(messages, historyMessages);
    }

    return messages;
  }

  /** Helper class to build messages from text fragments and parts. */
  private static class MessageBuilder {
    Role role;
    StringBuilder currentText = new StringBuilder();
    List<Part> content = new ArrayList<>();

    MessageBuilder(Role role) {
      this.role = role;
    }

    void appendSource(String text) {
      currentText.append(text);
    }

    void addPart(Part part) {
      flushText();
      content.add(part);
    }

    private void flushText() {
      if (currentText.length() > 0 && !currentText.toString().trim().isEmpty()) {
        content.add(new TextPart(currentText.toString()));
        currentText.setLength(0);
      } else if (currentText.length() > 0 && currentText.toString().trim().isEmpty()) {
        currentText.setLength(0);
      }
    }

    boolean hasSource() {
      return (currentText.length() > 0 && !currentText.toString().trim().isEmpty())
          || !content.isEmpty();
    }

    List<Part> toParts() {
      flushText();
      return new ArrayList<>(content);
    }
  }

  // Helper to merge config maps
  private Map<String, Object> mergeConfigs(
      Map<String, Object> promptConfig, Map<String, Object> options) {
    if (options == null || options.isEmpty()) {
      return promptConfig;
    }
    // Simple shallow merge for top-level keys, favoring options
    Map<String, Object> result = new HashMap<>(promptConfig);
    result.putAll(options);
    return result;
  }

  /**
   * A custom Handlebars template loader that supports dynamic registration of partials.
   *
   * <p>This loader stores template strings in an in-memory map, allowing templates to be registered
   * and retrieved by name at runtime.
   */
  private static class DynamicLoader implements TemplateLoader {
    /** In-memory storage for registered partials/templates, mapped by name. */
    private final Map<String, String> templates = new ConcurrentHashMap<>();

    /**
     * Registers a source string for a given template name.
     *
     * @param name The name of the template/partial.
     * @param source The equivalent template source string.
     */
    void put(String name, String source) {
      templates.put(name, source);
    }

    @Override
    public TemplateSource sourceAt(String location) throws IOException {
      String source = templates.get(location);
      if (source == null) {
        throw new IOException("Template not found: " + location);
      }
      return new StringTemplateSource(location, source);
    }

    @Override
    public String resolve(String location) {
      return location;
    }

    @Override
    public String getPrefix() {
      return "";
    }

    @Override
    public String getSuffix() {
      return "";
    }

    @Override
    public void setPrefix(String prefix) {}

    @Override
    public void setSuffix(String suffix) {}

    @Override
    public Charset getCharset() {
      return Charset.forName("UTF-8");
    }

    @Override
    public void setCharset(Charset charset) {}
  }

  /**
   * Registers initial helpers from built-in helpers and options.
   *
   * @param customHelpers Custom helpers from options to register.
   */
  private void registerInitialHelpers(Map<String, Helper<?>> customHelpers) {
    // Register built-in helpers.
    Helpers.register(handlebars);

    // Register custom helpers from options.
    if (customHelpers != null) {
      customHelpers.forEach(this::defineHelper);
    }
  }

  /**
   * Registers initial partials from the options.
   *
   * @param partials The partials to register.
   */
  private void registerInitialPartials(Map<String, String> partials) {
    if (partials != null) {
      partials.forEach(this::definePartial);
    }
  }
}
