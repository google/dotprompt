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

import com.github.jknack.handlebars.EscapingStrategy;
import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;
import com.github.jknack.handlebars.io.StringTemplateSource;
import com.github.jknack.handlebars.io.TemplateLoader;
import com.github.jknack.handlebars.io.TemplateSource;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.util.concurrent.MoreExecutors;
import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.RenderedPrompt;
import com.google.dotprompt.models.Role;
import com.google.dotprompt.models.TextPart;
import com.google.dotprompt.parser.Picoschema;
import com.google.dotprompt.resolvers.SchemaResolver;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.List;
import java.util.Map;

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

  /** The loader responsible for retrieving prompt sources. */
  private final PromptLoader promptLoader;

  /** A custom template loader that allows dynamic registration of partials. */
  private final DynamicLoader templateLoader;

  // Configuration maps
  private final Map<String, Object> modelConfigs;
  private final Map<String, Object> toolDefinitions;
  private final String defaultModel;

  /** Optional partial resolver for dynamic partial loading. */
  private com.google.dotprompt.resolvers.PartialResolver partialResolver;

  /** Optional prompt store for loading prompts and partials. */
  private com.google.dotprompt.store.PromptStore store;

  /**
   * Constructs a new Dotprompt instance with the given loader.
   *
   * @param promptLoader The loader to use for retrieving prompt templates.
   */
  public Dotprompt(PromptLoader promptLoader) {
    this(promptLoader, null, null, null);
  }

  /**
   * Constructs a new Dotprompt instance with full configuration.
   *
   * @param promptLoader The loader to use for retrieving prompt templates.
   * @param defaultModel The default model to use if none is specified in the prompt or options.
   * @param modelConfigs Configuration maps for specific models.
   * @param toolDefinitions definitions for tools available to the prompts.
   */
  public Dotprompt(
      PromptLoader promptLoader,
      String defaultModel,
      Map<String, Object> modelConfigs,
      Map<String, Object> toolDefinitions) {
    this.templateLoader = new DynamicLoader();
    this.handlebars = new Handlebars(templateLoader).with(EscapingStrategy.NOOP);
    Helpers.register(this);
    this.promptLoader = promptLoader;
    this.defaultModel = defaultModel;
    this.modelConfigs =
        modelConfigs != null
            ? new java.util.concurrent.ConcurrentHashMap<>(modelConfigs)
            : new java.util.concurrent.ConcurrentHashMap<>();
    this.toolDefinitions =
        toolDefinitions != null
            ? new java.util.concurrent.ConcurrentHashMap<>(toolDefinitions)
            : new java.util.concurrent.ConcurrentHashMap<>();
  }

  /**
   * Sets the partial resolver for dynamic partial loading.
   *
   * @param resolver The partial resolver to use.
   * @return This instance for method chaining.
   */
  public Dotprompt setPartialResolver(com.google.dotprompt.resolvers.PartialResolver resolver) {
    this.partialResolver = resolver;
    return this;
  }

  /**
   * Sets the prompt store for loading prompts and partials.
   *
   * @param store The prompt store to use.
   * @return This instance for method chaining.
   */
  public Dotprompt setStore(com.google.dotprompt.store.PromptStore store) {
    this.store = store;
    return this;
  }

  /**
   * Defines a tool available for use in prompts.
   *
   * @param name The name of the tool.
   * @param definition The tool definition object.
   */
  public void defineTool(String name, Object definition) {
    toolDefinitions.put(name, definition);
  }

  /**
   * Defines configuration overrides for a specific model.
   *
   * @param model The model identifier (e.g., "gemini-1.5-pro").
   * @param config The configuration map to apply when this model is selected.
   */
  public void defineModelConfig(String model, Object config) {
    modelConfigs.put(model, config);
  }

  /**
   * Registers a partial template.
   *
   * @param name The name of the partial.
   * @param template The template string.
   */
  public void registerPartial(String name, String template) {
    templateLoader.put(name, template);
  }

  /**
   * Registers a custom Handlebars helper.
   *
   * @param name The name of the helper.
   * @param helper The helper implementation.
   */
  public void registerHelper(String name, com.github.jknack.handlebars.Helper<?> helper) {
    handlebars.registerHelper(name, helper);
  }

  /**
   * Parses a prompt template string into a structured Prompt object.
   *
   * @param source The template source string to parse.
   * @return A parsed Prompt object with extracted metadata and template.
   * @throws IOException If parsing the YAML frontmatter fails.
   */
  public com.google.dotprompt.models.Prompt parse(String source) throws IOException {
    return com.google.dotprompt.parser.Parser.parse(source);
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
  public java.util.concurrent.CompletableFuture<com.google.dotprompt.models.PromptFunction> compile(
      String source) {
    return compileInternal(source, null);
  }

  /**
   * Compiles a template with additional metadata.
   *
   * @param source The template source string to compile.
   * @param additionalMetadata Additional metadata to merge into the template.
   * @return A future resolving to a reusable PromptFunction.
   */
  public java.util.concurrent.CompletableFuture<com.google.dotprompt.models.PromptFunction> compile(
      String source, Map<String, Object> additionalMetadata) {
    return compileInternal(source, additionalMetadata);
  }

  private java.util.concurrent.CompletableFuture<com.google.dotprompt.models.PromptFunction>
      compileInternal(String source, Map<String, Object> additionalMetadata) {
    try {
      com.google.dotprompt.models.Prompt parsedPrompt = parse(source);

      // Merge additional metadata into config
      Map<String, Object> mergedConfig = new java.util.HashMap<>(parsedPrompt.config());
      if (additionalMetadata != null) {
        mergedConfig.putAll(additionalMetadata);
      }
      final com.google.dotprompt.models.Prompt finalPrompt =
          new com.google.dotprompt.models.Prompt(parsedPrompt.template(), mergedConfig);

      // Resolve partials before compiling
      return resolvePartialsAsync(parsedPrompt.template())
          .thenApply(
              v -> {
                try {
                  Template template = handlebars.compileInline(parsedPrompt.template());
                  final Dotprompt self = this;

                  return new com.google.dotprompt.models.PromptFunction() {
                    @Override
                    public java.util.concurrent.CompletableFuture<RenderedPrompt> render(
                        Map<String, Object> data) {
                      return render(data, null);
                    }

                    @Override
                    public java.util.concurrent.CompletableFuture<RenderedPrompt> render(
                        Map<String, Object> data, Map<String, Object> options) {
                      return java.util.concurrent.CompletableFuture.supplyAsync(
                          () -> {
                            try {
                              return renderWithTemplate(template, finalPrompt, data, options);
                            } catch (IOException e) {
                              throw new RuntimeException("Failed to render template", e);
                            }
                          });
                    }

                    @Override
                    public com.google.dotprompt.models.Prompt getPrompt() {
                      return finalPrompt;
                    }
                  };
                } catch (IOException e) {
                  throw new RuntimeException("Failed to compile template", e);
                }
              });
    } catch (IOException e) {
      return java.util.concurrent.CompletableFuture.failedFuture(e);
    }
  }

  /**
   * Renders the metadata for a template without rendering the full template.
   *
   * <p>This is useful when you need the resolved metadata (tools, schemas, etc.) without actually
   * rendering the message content.
   *
   * @param source The template source string.
   * @return A future containing the resolved metadata as a map.
   */
  public java.util.concurrent.CompletableFuture<Map<String, Object>> renderMetadata(String source) {
    return renderMetadata(source, null);
  }

  /**
   * Renders the metadata for a template with additional overrides.
   *
   * @param source The template source string.
   * @param additionalMetadata Additional metadata to merge.
   * @return A future containing the resolved metadata as a map.
   */
  public java.util.concurrent.CompletableFuture<Map<String, Object>> renderMetadata(
      String source, Map<String, Object> additionalMetadata) {
    try {
      com.google.dotprompt.models.Prompt parsedPrompt = parse(source);

      Map<String, Object> result = new java.util.HashMap<>();

      // Determine model
      String model = null;
      if (parsedPrompt.config() != null && parsedPrompt.config().containsKey("model")) {
        model = (String) parsedPrompt.config().get("model");
      } else if (additionalMetadata != null && additionalMetadata.containsKey("model")) {
        model = (String) additionalMetadata.get("model");
      } else {
        model = this.defaultModel;
      }

      // Apply model config
      if (model != null && this.modelConfigs.containsKey(model)) {
        Object mc = this.modelConfigs.get(model);
        if (mc instanceof Map) {
          result.putAll((Map<String, Object>) mc);
        }
      }

      // Merge prompt config
      if (parsedPrompt.config() != null) {
        result.putAll(parsedPrompt.config());
      }

      // Merge additional metadata
      if (additionalMetadata != null) {
        result.putAll(additionalMetadata);
      }

      // Remove template if present
      result.remove("template");

      // Process schemas
      processConfigSchemas(result);

      return java.util.concurrent.CompletableFuture.completedFuture(result);
    } catch (IOException e) {
      return java.util.concurrent.CompletableFuture.failedFuture(e);
    }
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
  private java.util.concurrent.CompletableFuture<Void> resolvePartialsAsync(String template) {
    if (partialResolver == null && store == null) {
      return java.util.concurrent.CompletableFuture.completedFuture(null);
    }

    java.util.Set<String> partialNames = identifyPartials(template);
    if (partialNames.isEmpty()) {
      return java.util.concurrent.CompletableFuture.completedFuture(null);
    }

    java.util.List<java.util.concurrent.CompletableFuture<Void>> futures =
        new java.util.ArrayList<>();

    for (String name : partialNames) {
      // Check if already registered
      if (templateLoader.templates.containsKey(name)) {
        continue;
      }

      java.util.concurrent.CompletableFuture<Void> resolution =
          java.util.concurrent.CompletableFuture.completedFuture(null);

      if (partialResolver != null) {
        resolution =
            partialResolver
                .resolve(name)
                .thenCompose(
                    content -> {
                      if (content != null) {
                        registerPartial(name, content);
                        // Recursively resolve partials in the content
                        return resolvePartialsAsync(content);
                      } else if (store != null) {
                        // Try store as fallback
                        return store
                            .loadPartial(name, null)
                            .thenCompose(
                                data -> {
                                  if (data != null && data.source() != null) {
                                    registerPartial(name, data.source());
                                    return resolvePartialsAsync(data.source());
                                  }
                                  return java.util.concurrent.CompletableFuture.completedFuture(
                                      null);
                                });
                      }
                      return java.util.concurrent.CompletableFuture.completedFuture(null);
                    });
      } else if (store != null) {
        resolution =
            store
                .loadPartial(name, null)
                .thenCompose(
                    data -> {
                      if (data != null && data.source() != null) {
                        registerPartial(name, data.source());
                        return resolvePartialsAsync(data.source());
                      }
                      return java.util.concurrent.CompletableFuture.completedFuture(null);
                    });
      }

      futures.add(resolution);
    }

    return java.util.concurrent.CompletableFuture.allOf(
        futures.toArray(new java.util.concurrent.CompletableFuture[0]));
  }

  /**
   * Identifies all partial references in a template.
   *
   * @param template The template to scan.
   * @return A set of partial names referenced in the template.
   */
  private java.util.Set<String> identifyPartials(String template) {
    java.util.Set<String> partials = new java.util.HashSet<>();
    // Match {{> partialName}} or {{> partialName context}}
    java.util.regex.Pattern pattern =
        java.util.regex.Pattern.compile("\\{\\{>\\s*([a-zA-Z0-9_-]+)");
    java.util.regex.Matcher matcher = pattern.matcher(template);
    while (matcher.find()) {
      partials.add(matcher.group(1));
    }
    return partials;
  }

  /** Internal render method used by compiled PromptFunction. */
  private RenderedPrompt renderWithTemplate(
      Template template,
      com.google.dotprompt.models.Prompt prompt,
      Map<String, Object> data,
      Map<String, Object> options)
      throws IOException {

    Map<String, Object> mergedData = new java.util.HashMap<>();

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
    Map<String, Object> contextData = new java.util.HashMap<>();
    if (data != null && data.containsKey("context")) {
      Map<String, Object> ctx = (Map<String, Object>) data.get("context");
      if (ctx.containsKey("state")) {
        contextData.put("state", ctx.get("state"));
      }
    }

    com.github.jknack.handlebars.Context context =
        com.github.jknack.handlebars.Context.newBuilder(mergedData).build();
    for (Map.Entry<String, Object> entry : contextData.entrySet()) {
      context.data(entry.getKey(), entry.getValue());
    }

    String renderedString = template.apply(context);

    List<Message> messages = toMessages(renderedString, mergedData);

    // Construct result config
    Map<String, Object> resultConfig = new java.util.HashMap<>();
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
   * Renders a prompt with the given data.
   *
   * @param templateName The name of the template to render.
   * @param data The data to use for rendering.
   * @return A future containing the rendered prompt.
   */
  public ListenableFuture<RenderedPrompt> render(String templateName, Map<String, Object> data) {
    return render(templateName, data, null);
  }

  /**
   * Renders a prompt with the given data and options.
   *
   * @param templateName The name of the template to render.
   * @param data The data to use for rendering.
   * @param options Additional options (overrides/defaults).
   * @return A future containing the rendered prompt.
   */
  public ListenableFuture<RenderedPrompt> render(
      String templateName, Map<String, Object> data, Map<String, Object> options) {
    return Futures.transform(
        promptLoader.load(templateName),
        prompt -> {
          try {
            Template template = handlebars.compileInline(prompt.template());

            // Merge defaults: File defaults -> Model Config -> Options defaults -> Data
            Map<String, Object> mergedData = new java.util.HashMap<>();

            // 0. Model Config
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

            // 1. File defaults and config
            mergeDefaults(mergedData, prompt.config());
            if (prompt.config() != null) {
              mergedData.putAll(prompt.config());
            }

            // 2. Options
            mergeDefaults(mergedData, options);
            if (options != null) {
              mergedData.putAll(options);
            }

            // 3. Data
            if (data != null) {
              mergedData.putAll(data);
            }

            // Handle context.state for @state access
            Map<String, Object> contextData = new java.util.HashMap<>();
            if (data != null && data.containsKey("context")) {
              Map<String, Object> ctx = (Map<String, Object>) data.get("context");
              if (ctx.containsKey("state")) {
                contextData.put("state", ctx.get("state"));
              }
            }

            com.github.jknack.handlebars.Context context =
                com.github.jknack.handlebars.Context.newBuilder(mergedData).build();
            for (Map.Entry<String, Object> entry : contextData.entrySet()) {
              context.data(entry.getKey(), entry.getValue());
            }

            String renderedString = template.apply(context);

            List<Message> messages = toMessages(renderedString, mergedData);

            // Construct result config: Model Config -> Prompt Config -> Options
            Map<String, Object> resultConfig = new java.util.HashMap<>();
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

            // Post-process schemas in config (input/output)
            processConfigSchemas(resultConfig);

            return new RenderedPrompt(resultConfig, messages);
          } catch (IOException e) {
            throw new RuntimeException("Failed to render template", e);
          }
        },
        MoreExecutors.directExecutor());
  }

  /** Registry for named Picoschema definitions. */
  private final java.util.concurrent.ConcurrentHashMap<String, Map<String, Object>> schemas =
      new java.util.concurrent.ConcurrentHashMap<>();

  public void registerSchema(String name, Map<String, Object> schema) {
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
        Map<String, Object> section = new java.util.HashMap<>((Map<String, Object>) val);
        if (section.containsKey("schema")) {
          Object schema = section.get("schema");
          // Use Picoschema to parse, using registered schemas as resolver
          try {
            section.put(
                "schema",
                Picoschema.parse(schema, SchemaResolver.fromSync(this.schemas::get)).get());
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
  // Parsing now supports new space-delimited formats for section and media.
  // section: <<<dotprompt:section NAME>>>
  // media: <<<dotprompt:media:url URL [TYPE]>>>
  private static final java.util.regex.Pattern MARKER_PATTERN =
      java.util.regex.Pattern.compile(
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

    List<MessageSource> messageSources = new java.util.ArrayList<>();
    // Initial message source
    MessageSource currentMessage = new MessageSource(Role.USER);
    messageSources.add(currentMessage);

    // Extract history messages from data if available
    List<Message> historyMessages = new java.util.ArrayList<>();
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
              List<Part> parts = new java.util.ArrayList<>();

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
    List<Message> historySources = transformMessagesToHistory(historyMessages);

    boolean historyInjected = false;
    java.util.regex.Matcher matcher = MARKER_PATTERN.matcher(renderedString);
    int lastEnd = 0;

    com.fasterxml.jackson.databind.ObjectMapper mapper =
        new com.fasterxml.jackson.databind.ObjectMapper();

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
            currentMessage = new MessageSource(role);
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
              MessageSource hSource = new MessageSource(hMsg.role());
              hSource.content.addAll(hMsg.content());
              messageSources.add(hSource);
            }

            currentMessage = new MessageSource(Role.MODEL);
            messageSources.add(currentMessage);
          } else {
            if (currentMessage.hasSource() || !currentMessage.content.isEmpty()) {
              currentMessage = new MessageSource(Role.MODEL);
              messageSources.add(currentMessage);
            }
          }
        } else if (markerContent.startsWith("media:")) {
          // Format: media:url URL [TYPE]
          String mediaPayload = markerContent.substring(6).trim();
          if (mediaPayload.startsWith("url ")) {
            String[] parts = mediaPayload.substring(4).split("\\s+");
            String url = parts[0];
            String contentType = parts.length > 1 ? parts[1] : ""; // Default or empty?
            // If content type is missing, should we guess or leave empty?
            // Canonical JS: `...${contentType ? ` ${contentType}` : ''}`
            currentMessage.addPart(new MediaPart(contentType, url));
          }
        } else if (markerContent.startsWith("section")) {
          // Format: section NAME
          // Treat section as a new part boundary AND preserve the marker text.
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

    List<Message> messages = new java.util.ArrayList<>();
    for (MessageSource source : messageSources) {
      List<Part> parts = source.toParts();
      if (!parts.isEmpty()) {
        messages.add(new Message(source.role, parts));
      }
    }

    boolean historyUsed = historyInjected;
    // Check if we have history but no marker was found
    if (!historyUsed && !historyMessages.isEmpty() && !messagesHaveHistory(messages)) {
      return insertHistory(messages, historyMessages);
    }

    // If marker was found, 'messages' already contains history content (injected in loop).
    return messages;
  }

  /**
   * Transforms raw messages into a history format if needed.
   *
   * @param messages The input messages.
   * @return A list of valid message objects.
   */
  private List<Message> transformMessagesToHistory(List<Message> messages) {
    // Assuming naive implementation first.
    return messages;
  }

  /**
   * Checks if the list of messages already contains history.
   *
   * @param messages The messages to check.
   * @return True if history is detected.
   */
  private boolean messagesHaveHistory(List<Message> messages) {
    return false; // Valid for current simplified Message model.
  }

  /**
   * Inserts history messages into the rendered message list.
   *
   * @param messages The rendered messages.
   * @param history The history messages to insert.
   * @return The combined list of messages.
   */
  private List<Message> insertHistory(List<Message> messages, List<Message> history) {
    if (history == null || history.isEmpty()) {
      return messages;
    }

    List<Message> result = new java.util.ArrayList<>();

    if (messages.isEmpty()) {
      result.addAll(history);
      return result;
    }

    Message lastMessage = messages.get(messages.size() - 1);
    if (lastMessage.role() == Role.USER) {
      // Insert history before the last user message
      result.addAll(messages.subList(0, messages.size() - 1));
      result.addAll(history);
      result.add(lastMessage);
    } else {
      result.addAll(messages);
      result.addAll(history);
    }
    return result;
  }

  /** Helper class to build messages from text fragments and parts. */
  private static class MessageSource {
    Role role;
    StringBuilder currentText = new StringBuilder();
    List<Part> content = new java.util.ArrayList<>();

    MessageSource(Role role) {
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
      return new java.util.ArrayList<>(content);
    }
  }

  // Helper to merge config maps
  private Map<String, Object> mergeConfigs(
      Map<String, Object> promptConfig, Map<String, Object> options) {
    if (options == null || options.isEmpty()) {
      return promptConfig;
    }
    // Simple shallow merge for top-level keys, favoring options
    Map<String, Object> result = new java.util.HashMap<>(promptConfig);
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
    private final Map<String, String> templates = new java.util.concurrent.ConcurrentHashMap<>();

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
}
