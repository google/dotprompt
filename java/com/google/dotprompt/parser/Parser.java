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

package com.google.dotprompt.parser;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.dotprompt.models.Prompt;
import java.io.IOException;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Parses Dotprompt files into Prompt objects.
 *
 * <p>This class handles the parsing of YAML frontmatter and the separation of configuration from
 * the template body. It also manages namespace expansion for extension fields.
 */
public class Parser {

  /**
   * The pattern used to match YAML frontmatter in the input string.
   *
   * <p>This pattern matches a YAML frontmatter block, which is a block of YAML content between
   * "---" markers. The pattern is designed to be flexible enough to handle different line endings
   * (CRLF, LF, CR) and optional trailing newlines. It also allows for trailing whitespace on the
   * marker lines.
   *
   * <p>Uses (?m) for multiline anchors (^) and (?s) for dot matching newlines.
   */
  private static final Pattern FRONTMATTER_PATTERN =
      Pattern.compile("(?ms)^\\s*---[ \\t]*[\\r\\n]+(.*?)^[ \\t]*---[ \\t]*[\\r\\n]+");

  /**
   * The ObjectMapper used to parse YAML frontmatter.
   *
   * <p>This ObjectMapper is configured to use the YAMLFactory, which is specifically designed for
   * parsing YAML content. It is used to convert the YAML frontmatter into a Map of configuration
   * values.
   */
  private static final ObjectMapper mapper = new ObjectMapper(new YAMLFactory());

  /**
   * Parses a Dotprompt template string into a Prompt object.
   *
   * @param content The raw string content of the prompt file (including frontmatter).
   * @return The parsed Prompt object containing the template and configuration.
   * @throws IOException If parsing the YAML frontmatter fails.
   */
  public static Prompt parse(String content) throws IOException {
    if (content == null || content.trim().isEmpty()) {
      return new Prompt("", Map.of());
    }

    Matcher matcher = FRONTMATTER_PATTERN.matcher(content);
    if (matcher.find()) {
      String yaml = matcher.group(1);
      String template = content.substring(matcher.end());

      Map<String, Object> config = Map.of();
      if (yaml != null && !yaml.trim().isEmpty()) {
        try {
          Map<String, Object> rawConfig = mapper.readValue(yaml, Map.class);
          config = expandNamespacedKeys(rawConfig);
          config.put("raw", rawConfig);
        } catch (IOException e) {
          throw e;
        }
      }
      return new Prompt(template, config);
    } else {
      return new Prompt(content, Map.of());
    }
  }

  private static final java.util.Set<String> KNOWN_KEYS =
      java.util.Set.of(
          "name", "description", "version", "model", "tools", "input", "output", "config", "meta");

  /**
   * Expands dot-separated keys in the configuration into nested maps.
   *
   * <p>Known top-level keys are preserved. Unknown keys are moved into an 'ext' map.
   *
   * @param input The raw configuration map.
   * @return A new map with namespaces expanded.
   */
  private static Map<String, Object> expandNamespacedKeys(Map<String, Object> input) {
    Map<String, Object> result = new java.util.HashMap<>();
    Map<String, Object> ext = new java.util.HashMap<>();

    for (Map.Entry<String, Object> entry : input.entrySet()) {
      String key = entry.getKey();
      Object value = entry.getValue();

      if (KNOWN_KEYS.contains(key)) {
        result.put(key, value);
      } else {
        // Expand namespace into ext
        // e.g. foo.bar -> ext.put("foo", {bar: value})
        // Handle multiple levels: a.b.c
        addNested(ext, key, value);
      }
    }

    if (!ext.isEmpty()) {
      result.put("ext", ext);
    }

    return result;
  }

  /**
   * Adds a namespaced key to a map structure using "last dot" flattening logic. e.g. "a.b.c" -> {
   * "a.b": { "c": value } }
   *
   * @param root The root map to add to.
   * @param key The dot-separated key (e.g., "a.b.c").
   * @param value The value to set.
   */
  @SuppressWarnings("unchecked")
  private static void addNested(Map<String, Object> root, String key, Object value) {
    int lastDot = key.lastIndexOf('.');
    if (lastDot == -1) {
      root.put(key, value);
    } else {
      String parentKey = key.substring(0, lastDot);
      String childKey = key.substring(lastDot + 1);

      if (!root.containsKey(parentKey) || !(root.get(parentKey) instanceof Map)) {
        root.put(parentKey, new java.util.HashMap<String, Object>());
      }
      ((Map<String, Object>) root.get(parentKey)).put(childKey, value);
    }
  }
}
