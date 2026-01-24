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
import com.google.dotprompt.models.DataArgument;
import com.google.dotprompt.models.MediaContent;
import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.ParsedPrompt;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.PendingPart;
import com.google.dotprompt.models.Prompt;
import com.google.dotprompt.models.PromptMetadata;
import com.google.dotprompt.models.Role;
import com.google.dotprompt.models.TextPart;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Parses Dotprompt files into Prompt objects and rendered templates into messages.
 *
 * <p>This class handles:
 *
 * <ul>
 *   <li>Parsing YAML frontmatter and separating configuration from template body
 *   <li>Namespace expansion for extension fields
 *   <li>Converting rendered templates into structured messages
 *   <li>Processing role, history, media, and section markers
 *   <li>Handling chat history insertion
 * </ul>
 */
public class Parser {

  /** Prefix for role markers in the template. */
  public static final String ROLE_MARKER_PREFIX = "<<<dotprompt:role:";

  /** Prefix for history markers in the template. */
  public static final String HISTORY_MARKER_PREFIX = "<<<dotprompt:history";

  /** Prefix for media markers in the template. */
  public static final String MEDIA_MARKER_PREFIX = "<<<dotprompt:media:";

  /** Prefix for section markers in the template. */
  public static final String SECTION_MARKER_PREFIX = "<<<dotprompt:section";

  /**
   * Pattern to match YAML frontmatter in the input string.
   *
   * <p>Matches a YAML frontmatter block between "---" markers. Handles different line endings
   * (CRLF, LF, CR) and optional trailing whitespace on the marker lines. Allows blank lines and
   * license headers (lines starting with #) before the first --- marker.
   */
  private static final Pattern FRONTMATTER_PATTERN =
      Pattern.compile(
          "(?ms)^(?:(?:#[^\\n]*|[ \\t]*)\\n)*---[ \\t]*[\\r\\n]+(.*?)^[ \\t]*---[ \\t]*[\\r\\n]+");

  /**
   * Pattern to match role and history markers.
   *
   * <p>Examples: {@code <<<dotprompt:role:user>>>}, {@code <<<dotprompt:history>>>}
   */
  public static final Pattern ROLE_AND_HISTORY_MARKER_PATTERN =
      Pattern.compile("(<<<dotprompt:(?:role:[a-z]+|history))>>>");

  /**
   * Pattern to match media and section markers.
   *
   * <p>Examples: {@code <<<dotprompt:media:url>>>}, {@code <<<dotprompt:section>>>}
   */
  public static final Pattern MEDIA_AND_SECTION_MARKER_PATTERN =
      Pattern.compile("(<<<dotprompt:(?:media:url|section).*?)>>>");

  /** ObjectMapper for parsing YAML frontmatter. */
  private static final ObjectMapper mapper = new ObjectMapper(new YAMLFactory());

  /** Reserved metadata keywords that are handled specially, not moved to ext. */
  public static final Set<String> RESERVED_METADATA_KEYWORDS =
      Set.of(
          "config",
          "description",
          "ext",
          "input",
          "model",
          "name",
          "output",
          "raw",
          "toolDefs",
          "tools",
          "variant",
          "version");

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

      Map<String, Object> config = new HashMap<>();
      if (yaml != null && !yaml.trim().isEmpty()) {
        try {
          @SuppressWarnings("unchecked")
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

  /**
   * Parses a document containing YAML frontmatter and template content into a ParsedPrompt.
   *
   * @param source The source document containing frontmatter and template.
   * @return A ParsedPrompt with metadata and template content.
   * @throws IOException If parsing the YAML frontmatter fails.
   */
  public static ParsedPrompt parseDocument(String source) throws IOException {
    Prompt prompt = parse(source);
    PromptMetadata metadata = PromptMetadata.fromConfig(prompt.config());
    return ParsedPrompt.fromMetadata(prompt.template(), metadata);
  }

  /**
   * Splits a string by a regex pattern while filtering out empty/whitespace-only pieces.
   *
   * @param source The source string to split.
   * @param pattern The pattern to use for splitting.
   * @return A list of non-empty string pieces.
   */
  public static List<String> splitByRegex(String source, Pattern pattern) {
    if (source == null || source.isEmpty()) {
      return List.of();
    }

    List<String> result = new ArrayList<>();
    Matcher matcher = pattern.matcher(source);
    int lastEnd = 0;

    while (matcher.find()) {
      // Add text before the match
      if (matcher.start() > lastEnd) {
        String beforeMatch = source.substring(lastEnd, matcher.start());
        if (!beforeMatch.trim().isEmpty()) {
          result.add(beforeMatch);
        }
      }
      // Add the captured group (without the closing >>>)
      String captured = matcher.group(1);
      if (captured != null && !captured.trim().isEmpty()) {
        result.add(captured);
      }
      lastEnd = matcher.end();
    }

    // Add remaining text after last match
    if (lastEnd < source.length()) {
      String remaining = source.substring(lastEnd);
      if (!remaining.trim().isEmpty()) {
        result.add(remaining);
      }
    }

    return result;
  }

  /**
   * Splits a rendered template string by role and history markers.
   *
   * @param renderedString The template string to split.
   * @return List of non-empty string pieces.
   */
  public static List<String> splitByRoleAndHistoryMarkers(String renderedString) {
    return splitByRegex(renderedString, ROLE_AND_HISTORY_MARKER_PATTERN);
  }

  /**
   * Splits a source string by media and section markers.
   *
   * @param source The source string to split.
   * @return List of non-empty string pieces.
   */
  public static List<String> splitByMediaAndSectionMarkers(String source) {
    return splitByRegex(source, MEDIA_AND_SECTION_MARKER_PATTERN);
  }

  /**
   * Converts a rendered template string into a list of messages.
   *
   * <p>Processes role markers and history placeholders to structure the conversation.
   *
   * @param renderedString The rendered template string to convert.
   * @param data Optional data containing message history.
   * @return List of structured messages.
   */
  public static List<Message> toMessages(String renderedString, DataArgument data) {
    MessageSource currentMessage = new MessageSource(Role.USER, "");
    List<MessageSource> messageSources = new ArrayList<>();
    messageSources.add(currentMessage);

    for (String piece : splitByRoleAndHistoryMarkers(renderedString)) {
      if (piece.startsWith(ROLE_MARKER_PREFIX)) {
        String roleName = piece.substring(ROLE_MARKER_PREFIX.length());
        Role role = Role.fromString(roleName);

        if (currentMessage.source != null && !currentMessage.source.trim().isEmpty()) {
          // Current message has content, create a new message
          currentMessage = new MessageSource(role, "");
          messageSources.add(currentMessage);
        } else {
          // Update the role of the current empty message
          currentMessage.role = role;
        }
      } else if (piece.startsWith(HISTORY_MARKER_PREFIX)) {
        // Add the history messages to the message sources
        List<Message> historyMessages =
            transformMessagesToHistory(data != null ? data.messages() : List.of());
        for (Message msg : historyMessages) {
          messageSources.add(new MessageSource(msg.role(), msg.content(), msg.metadata()));
        }

        // Add a new message source for the model
        currentMessage = new MessageSource(Role.MODEL, "");
        messageSources.add(currentMessage);
      } else {
        // Add the piece to the current message source
        currentMessage.source =
            (currentMessage.source != null ? currentMessage.source : "") + piece;
      }
    }

    List<Message> messages = messageSourcesToMessages(messageSources);
    return insertHistory(messages, data != null ? data.messages() : null);
  }

  /**
   * Converts a rendered template string into a list of messages with no data context.
   *
   * @param renderedString The rendered template string to convert.
   * @return List of structured messages.
   */
  public static List<Message> toMessages(String renderedString) {
    return toMessages(renderedString, null);
  }

  /**
   * Transforms an array of messages by adding history metadata to each message.
   *
   * @param messages Array of messages to transform.
   * @return Array of messages with history metadata added.
   */
  public static List<Message> transformMessagesToHistory(List<Message> messages) {
    if (messages == null) {
      return List.of();
    }
    return messages.stream()
        .map(
            m -> {
              Map<String, Object> metadata = new HashMap<>();
              if (m.metadata() != null) {
                metadata.putAll(m.metadata());
              }
              metadata.put("purpose", "history");
              return new Message(m.role(), m.content(), metadata);
            })
        .collect(Collectors.toList());
  }

  /**
   * Checks if the messages have history metadata.
   *
   * @param messages The messages to check.
   * @return True if any message has history metadata.
   */
  public static boolean messagesHaveHistory(List<Message> messages) {
    if (messages == null) {
      return false;
    }
    return messages.stream()
        .anyMatch(m -> m.metadata() != null && "history".equals(m.metadata().get("purpose")));
  }

  /**
   * Inserts historical messages into the conversation at appropriate positions.
   *
   * <p>The history is inserted:
   *
   * <ul>
   *   <li>Before the last user message if there is a user message
   *   <li>At the end of the conversation if there is no history or no user message
   * </ul>
   *
   * @param messages Current array of messages.
   * @param history Historical messages to insert.
   * @return Messages with history inserted.
   */
  public static List<Message> insertHistory(List<Message> messages, List<Message> history) {
    // If we have no history or find an existing instance of history, return original
    if (history == null || history.isEmpty() || messagesHaveHistory(messages)) {
      return messages;
    }

    // If there are no messages, return the history
    if (messages == null || messages.isEmpty()) {
      return history;
    }

    Message lastMessage = messages.get(messages.size() - 1);
    if (lastMessage.role() == Role.USER) {
      // Insert history before the last user message
      List<Message> result = new ArrayList<>(messages.subList(0, messages.size() - 1));
      result.addAll(history);
      result.add(lastMessage);
      return result;
    }

    // Append history to the end
    List<Message> result = new ArrayList<>(messages);
    result.addAll(history);
    return result;
  }

  /**
   * Converts a source string into a list of parts, processing media and section markers.
   *
   * @param source The source string to convert into parts.
   * @return List of structured parts (text, media, or metadata).
   */
  public static List<Part> toParts(String source) {
    if (source == null || source.isEmpty()) {
      return List.of();
    }
    return splitByMediaAndSectionMarkers(source).stream()
        .map(Parser::parsePart)
        .collect(Collectors.toList());
  }

  /**
   * Parses a part from a string.
   *
   * @param piece The piece to parse.
   * @return Parsed part (TextPart, MediaPart, or PendingPart).
   */
  public static Part parsePart(String piece) {
    if (piece.startsWith(MEDIA_MARKER_PREFIX)) {
      return parseMediaPart(piece);
    }
    if (piece.startsWith(SECTION_MARKER_PREFIX)) {
      return parseSectionPart(piece);
    }
    return parseTextPart(piece);
  }

  /**
   * Parses a media part from a string.
   *
   * @param piece The piece to parse.
   * @return Parsed media part.
   * @throws IllegalArgumentException If the piece is not a valid media marker.
   */
  public static MediaPart parseMediaPart(String piece) {
    if (!piece.startsWith(MEDIA_MARKER_PREFIX)) {
      throw new IllegalArgumentException("Invalid media piece: " + piece);
    }
    String[] parts = piece.split(" ");
    String url = parts.length > 1 ? parts[1] : "";
    String contentType = parts.length > 2 ? parts[2] : null;

    MediaContent media =
        contentType != null && !contentType.trim().isEmpty()
            ? new MediaContent(url, contentType)
            : new MediaContent(url, null);
    return new MediaPart(media);
  }

  /**
   * Parses a section part from a string.
   *
   * @param piece The piece to parse.
   * @return Parsed pending part with section metadata.
   * @throws IllegalArgumentException If the piece is not a valid section marker.
   */
  public static PendingPart parseSectionPart(String piece) {
    if (!piece.startsWith(SECTION_MARKER_PREFIX)) {
      throw new IllegalArgumentException("Invalid section piece: " + piece);
    }
    String[] parts = piece.split(" ");
    String sectionType = parts.length > 1 ? parts[1] : "";
    Map<String, Object> metadata = new HashMap<>();
    metadata.put("purpose", sectionType);
    metadata.put("pending", true);
    return new PendingPart(metadata);
  }

  /**
   * Parses a text part from a string.
   *
   * @param piece The piece to parse.
   * @return Parsed text part.
   */
  public static TextPart parseTextPart(String piece) {
    return new TextPart(piece);
  }

  /**
   * Processes an array of message sources into an array of messages.
   *
   * @param messageSources List of message sources.
   * @return List of structured messages.
   */
  public static List<Message> messageSourcesToMessages(List<MessageSource> messageSources) {
    List<Message> messages = new ArrayList<>();
    for (MessageSource m : messageSources) {
      if (m.content != null || (m.source != null && !m.source.isEmpty())) {
        List<Part> content = m.content != null ? m.content : toParts(m.source);
        Message message = new Message(m.role, content, m.metadata);
        messages.add(message);
      }
    }
    return messages;
  }

  /**
   * Expands dot-separated keys in the configuration into nested maps.
   *
   * <p>Known top-level keys are preserved. Unknown keys are moved into an 'ext' map.
   *
   * @param input The raw configuration map.
   * @return A new map with namespaces expanded.
   */
  private static Map<String, Object> expandNamespacedKeys(Map<String, Object> input) {
    Map<String, Object> result = new HashMap<>();
    Map<String, Object> ext = new HashMap<>();

    for (Map.Entry<String, Object> entry : input.entrySet()) {
      String key = entry.getKey();
      Object value = entry.getValue();

      if (RESERVED_METADATA_KEYWORDS.contains(key)) {
        result.put(key, value);
      } else {
        // Expand namespace into ext
        addNested(ext, key, value);
      }
    }

    if (!ext.isEmpty()) {
      result.put("ext", ext);
    }

    return result;
  }

  /**
   * Adds a namespaced key to a map structure using "last dot" flattening logic.
   *
   * <p>e.g. "a.b.c" -> { "a.b": { "c": value } }
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
        root.put(parentKey, new HashMap<String, Object>());
      }
      ((Map<String, Object>) root.get(parentKey)).put(childKey, value);
    }
  }
}
