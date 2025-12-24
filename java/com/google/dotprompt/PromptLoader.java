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
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.dotprompt.models.Prompt;
import com.google.dotprompt.parser.Parser;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;

/**
 * Handles loading of prompt files from the classpath.
 *
 * <p>This class abstracts the retrieval of prompt source content. It currently supports loading
 * from standard classpath resources using a convention-based naming scheme ({@code name.prompt}).
 */
public class PromptLoader {
  /**
   * Regex pattern to extract YAML frontmatter and the template body. Matches content starting with
   * optional whitespace, a line of three dashes, the frontmatter content, a newline, and another
   * line of three dashes.
   */
  private static final Pattern FRONTMATTER_PATTERN =
      Pattern.compile("^\\s*---\\r?\\n(.*?)\\r?\\n---\\r?\\n", Pattern.DOTALL);

  /** Jackson ObjectMapper configured with YAMLFactory for parsing frontmatter. */
  private final ObjectMapper mapper;

  public PromptLoader() {
    this.mapper = new ObjectMapper(new YAMLFactory());
  }

  /**
   * Loads a prompt by name from the classpath.
   *
   * @param name The name of the prompt file (without extension).
   * @return A future containing the loaded Prompt.
   */
  public ListenableFuture<Prompt> load(String name) {
    try {
      String resourcePath = name + ".prompt";
      InputStream is = getClass().getClassLoader().getResourceAsStream(resourcePath);
      if (is == null) {
        return Futures.immediateFailedFuture(
            new IllegalArgumentException("Prompt not found: " + name));
      }
      String content = new String(is.readAllBytes(), StandardCharsets.UTF_8);
      return Futures.immediateFuture(parse(content));
    } catch (IOException e) {
      return Futures.immediateFailedFuture(e);
    }
  }

  /**
   * Parses a raw prompt string.
   *
   * @param content The raw string content of the prompt.
   * @return The parsed Prompt object.
   * @throws IOException If parsing fails.
   */
  public Prompt parse(String content) throws IOException {
    return Parser.parse(content);
  }
}
