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

import static com.google.common.truth.Truth.assertThat;

import com.google.dotprompt.models.DataArgument;
import com.google.dotprompt.models.MediaPart;
import com.google.dotprompt.models.Message;
import com.google.dotprompt.models.Part;
import com.google.dotprompt.models.PendingPart;
import com.google.dotprompt.models.Prompt;
import com.google.dotprompt.models.Role;
import com.google.dotprompt.models.TextPart;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Tests for the Parser class. */
@RunWith(JUnit4.class)
public class ParserTest {

  @Test
  public void testParseWithFrontmatter() throws IOException {
    String content =
        "---\n"
            + "input:\n"
            + "  schema:\n"
            + "    type: object\n"
            + "---\n"
            + "Start of the template.";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Start of the template.");
    assertThat(prompt.config()).containsKey("input");
  }

  @Test
  public void testParseWithoutFrontmatter() throws IOException {
    String content = "Just a template.";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Just a template.");
    assertThat(prompt.config()).isEmpty();
  }

  @Test
  public void testParseEmptyFrontmatter() throws IOException {
    String content = "---\n---\nTemplate";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Template");
    assertThat(prompt.config()).isEmpty();
  }

  @Test
  public void testParseWhitespacePreservation() throws IOException {
    String content = "---\nfoo: bar\n---\n  Indented.\n";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("  Indented.\n");
  }

  @Test
  public void testParseCRLF() throws IOException {
    String content = "---\r\nfoo: bar\r\n---\r\nBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    @SuppressWarnings("unchecked")
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseMultilineFrontmatter() throws IOException {
    String content = "---\nfoo: bar\nbaz: qux\n---\nBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    @SuppressWarnings("unchecked")
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
    assertThat(ext).containsEntry("baz", "qux");
  }

  @Test
  public void testParseExtraMarkers() throws IOException {
    String content = "---\nfoo: bar\n---\nBody\n---\nExtra";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body\n---\nExtra");
    @SuppressWarnings("unchecked")
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseWithCR() throws IOException {
    String content = "---\rfoo: bar\r---\rBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    @SuppressWarnings("unchecked")
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseFrontmatterWithExtraSpaces() throws IOException {
    String content = "---   \nfoo: bar\n---   \nBody";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Body");
    @SuppressWarnings("unchecked")
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");
    assertThat(ext).containsEntry("foo", "bar");
  }

  @Test
  public void testParseNamespacedKeys() throws IOException {
    String content = "---\na.b.c: val\n---\nBody";
    Prompt prompt = Parser.parse(content);
    @SuppressWarnings("unchecked")
    Map<String, Object> ext = (Map<String, Object>) prompt.config().get("ext");

    // Expect: { "a.b": { "c": "val" } }
    assertThat(ext).containsKey("a.b");
    @SuppressWarnings("unchecked")
    Map<String, Object> ab = (Map<String, Object>) ext.get("a.b");
    assertThat(ab).containsEntry("c", "val");
  }

  @Test
  public void testParseIncompleteFrontmatter() throws IOException {
    String content = "---\nfoo: bar\nBody"; // Missing second marker
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo(content);
    assertThat(prompt.config()).isEmpty();
  }

  @Test
  public void testRoleAndHistoryMarkerPattern_validPatterns() {
    String[] validPatterns = {
      "<<<dotprompt:role:user>>>",
      "<<<dotprompt:role:model>>>",
      "<<<dotprompt:role:system>>>",
      "<<<dotprompt:history>>>",
      "<<<dotprompt:role:bot>>>",
      "<<<dotprompt:role:human>>>"
    };

    for (String pattern : validPatterns) {
      assertThat(Parser.ROLE_AND_HISTORY_MARKER_PATTERN.matcher(pattern).find()).isTrue();
    }
  }

  @Test
  public void testRoleAndHistoryMarkerPattern_invalidPatterns() {
    String[] invalidPatterns = {
      "<<<dotprompt:role:USER>>>", // uppercase not allowed
      "<<<dotprompt:role:model1>>>", // numbers not allowed
      "<<<dotprompt:role:>>>", // needs at least one letter
      "<<<dotprompt:role>>>", // missing role value
      "<<<dotprompt:history123>>>", // history should be exact
      "<<<dotprompt:HISTORY>>>", // history must be lowercase
      "dotprompt:role:user", // missing brackets
      "<<<dotprompt:role:user", // incomplete closing
      "dotprompt:role:user>>>", // incomplete opening
    };

    for (String pattern : invalidPatterns) {
      assertThat(Parser.ROLE_AND_HISTORY_MARKER_PATTERN.matcher(pattern).find()).isFalse();
    }
  }

  @Test
  public void testSplitByRoleAndHistoryMarkers_noMarkers() {
    List<String> result = Parser.splitByRoleAndHistoryMarkers("Hello World");
    assertThat(result).containsExactly("Hello World");
  }

  @Test
  public void testSplitByRoleAndHistoryMarkers_singleMarker() {
    List<String> result =
        Parser.splitByRoleAndHistoryMarkers("Hello <<<dotprompt:role:model>>> world");
    assertThat(result).containsExactly("Hello ", "<<<dotprompt:role:model", " world");
  }

  @Test
  public void testSplitByRoleAndHistoryMarkers_filterEmptyPieces() {
    List<String> result = Parser.splitByRoleAndHistoryMarkers("  <<<dotprompt:role:system>>>   ");
    assertThat(result).containsExactly("<<<dotprompt:role:system");
  }

  @Test
  public void testSplitByRoleAndHistoryMarkers_adjacentMarkers() {
    List<String> result =
        Parser.splitByRoleAndHistoryMarkers("<<<dotprompt:role:user>>><<<dotprompt:history>>>");
    assertThat(result).containsExactly("<<<dotprompt:role:user", "<<<dotprompt:history");
  }

  @Test
  public void testSplitByRoleAndHistoryMarkers_multipleMarkers() {
    List<String> result =
        Parser.splitByRoleAndHistoryMarkers(
            "Start <<<dotprompt:role:user>>> middle <<<dotprompt:history>>> end");
    assertThat(result)
        .containsExactly(
            "Start ", "<<<dotprompt:role:user", " middle ", "<<<dotprompt:history", " end");
  }

  @Test
  public void testSplitByMediaAndSectionMarkers_noMarkers() {
    List<String> result = Parser.splitByMediaAndSectionMarkers("Hello World");
    assertThat(result).containsExactly("Hello World");
  }

  @Test
  public void testSplitByMediaAndSectionMarkers_mediaMarker() {
    List<String> result =
        Parser.splitByMediaAndSectionMarkers(
            "<<<dotprompt:media:url>>> https://example.com/image.jpg");
    assertThat(result).containsExactly("<<<dotprompt:media:url", " https://example.com/image.jpg");
  }

  @Test
  public void testToMessages_simpleStringNoMarkers() {
    List<Message> result = Parser.toMessages("Hello world");

    assertThat(result).hasSize(1);
    assertThat(result.get(0).role()).isEqualTo(Role.USER);
    assertThat(result.get(0).content()).hasSize(1);
    assertThat(((TextPart) result.get(0).content().get(0)).text()).isEqualTo("Hello world");
  }

  @Test
  public void testToMessages_singleRoleMarker() {
    List<Message> result = Parser.toMessages("<<<dotprompt:role:model>>>Hello world");

    assertThat(result).hasSize(1);
    assertThat(result.get(0).role()).isEqualTo(Role.MODEL);
    assertThat(((TextPart) result.get(0).content().get(0)).text()).isEqualTo("Hello world");
  }

  @Test
  public void testToMessages_multipleRoleMarkers() {
    String renderedString =
        "<<<dotprompt:role:system>>>System instructions\n"
            + "<<<dotprompt:role:user>>>User query\n"
            + "<<<dotprompt:role:model>>>Model response";
    List<Message> result = Parser.toMessages(renderedString);

    assertThat(result).hasSize(3);

    assertThat(result.get(0).role()).isEqualTo(Role.SYSTEM);
    assertThat(((TextPart) result.get(0).content().get(0)).text())
        .isEqualTo("System instructions\n");

    assertThat(result.get(1).role()).isEqualTo(Role.USER);
    assertThat(((TextPart) result.get(1).content().get(0)).text()).isEqualTo("User query\n");

    assertThat(result.get(2).role()).isEqualTo(Role.MODEL);
    assertThat(((TextPart) result.get(2).content().get(0)).text()).isEqualTo("Model response");
  }

  @Test
  public void testToMessages_updatesRoleOfEmptyMessage() {
    String renderedString = "<<<dotprompt:role:user>>><<<dotprompt:role:model>>>Response";
    List<Message> result = Parser.toMessages(renderedString);

    // Should only have one message since first role marker has no content
    assertThat(result).hasSize(1);
    assertThat(result.get(0).role()).isEqualTo(Role.MODEL);
    assertThat(((TextPart) result.get(0).content().get(0)).text()).isEqualTo("Response");
  }

  @Test
  public void testToMessages_emptyInputString() {
    List<Message> result = Parser.toMessages("");
    assertThat(result).isEmpty();
  }

  @Test
  public void testToMessages_historyMarkersAddMetadata() {
    String renderedString = "<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up";
    List<Message> historyMessages =
        List.of(
            new Message(Role.USER, List.of(new TextPart("Previous question")), null),
            new Message(Role.MODEL, List.of(new TextPart("Previous answer")), null));

    DataArgument data = new DataArgument(null, null, historyMessages, null);
    List<Message> result = Parser.toMessages(renderedString, data);

    assertThat(result).hasSize(4);

    // First message is the user query
    assertThat(result.get(0).role()).isEqualTo(Role.USER);
    assertThat(((TextPart) result.get(0).content().get(0)).text()).isEqualTo("Query");

    // Next two messages are history with metadata
    assertThat(result.get(1).role()).isEqualTo(Role.USER);
    assertThat(result.get(1).metadata()).containsEntry("purpose", "history");

    assertThat(result.get(2).role()).isEqualTo(Role.MODEL);
    assertThat(result.get(2).metadata()).containsEntry("purpose", "history");

    // Last message is the follow-up
    assertThat(result.get(3).role()).isEqualTo(Role.MODEL);
    assertThat(((TextPart) result.get(3).content().get(0)).text()).isEqualTo("Follow-up");
  }

  @Test
  public void testToMessages_emptyHistory() {
    String renderedString = "<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up";
    DataArgument data = new DataArgument(null, null, List.of(), null);
    List<Message> result = Parser.toMessages(renderedString, data);

    assertThat(result).hasSize(2);
    assertThat(result.get(0).role()).isEqualTo(Role.USER);
    assertThat(result.get(1).role()).isEqualTo(Role.MODEL);
  }

  @Test
  public void testTransformMessagesToHistory_addsMetadata() {
    List<Message> messages =
        List.of(
            new Message(Role.USER, List.of(new TextPart("Hello")), null),
            new Message(Role.MODEL, List.of(new TextPart("Hi there")), null));

    List<Message> result = Parser.transformMessagesToHistory(messages);

    assertThat(result).hasSize(2);
    assertThat(result.get(0).metadata()).containsEntry("purpose", "history");
    assertThat(result.get(1).metadata()).containsEntry("purpose", "history");
  }

  @Test
  public void testTransformMessagesToHistory_preservesExistingMetadata() {
    List<Message> messages =
        List.of(new Message(Role.USER, List.of(new TextPart("Hello")), Map.of("foo", "bar")));

    List<Message> result = Parser.transformMessagesToHistory(messages);

    assertThat(result).hasSize(1);
    assertThat(result.get(0).metadata()).containsEntry("foo", "bar");
    assertThat(result.get(0).metadata()).containsEntry("purpose", "history");
  }

  @Test
  public void testTransformMessagesToHistory_emptyArray() {
    List<Message> result = Parser.transformMessagesToHistory(List.of());
    assertThat(result).isEmpty();
  }

  @Test
  public void testMessagesHaveHistory_true() {
    List<Message> messages =
        List.of(
            new Message(Role.USER, List.of(new TextPart("Hello")), Map.of("purpose", "history")));

    assertThat(Parser.messagesHaveHistory(messages)).isTrue();
  }

  @Test
  public void testMessagesHaveHistory_false() {
    List<Message> messages = List.of(new Message(Role.USER, List.of(new TextPart("Hello")), null));

    assertThat(Parser.messagesHaveHistory(messages)).isFalse();
  }

  @Test
  public void testInsertHistory_returnsOriginalIfNoHistory() {
    List<Message> messages = List.of(new Message(Role.USER, List.of(new TextPart("Hello")), null));

    List<Message> result = Parser.insertHistory(messages, List.of());

    assertThat(result).isEqualTo(messages);
  }

  @Test
  public void testInsertHistory_returnsOriginalIfHistoryExists() {
    List<Message> messages =
        List.of(
            new Message(Role.USER, List.of(new TextPart("Hello")), Map.of("purpose", "history")));

    List<Message> history =
        List.of(
            new Message(
                Role.MODEL, List.of(new TextPart("Previous")), Map.of("purpose", "history")));

    List<Message> result = Parser.insertHistory(messages, history);

    assertThat(result).isEqualTo(messages);
  }

  @Test
  public void testInsertHistory_insertsBeforeLastUserMessage() {
    List<Message> messages =
        List.of(
            new Message(Role.SYSTEM, List.of(new TextPart("System prompt")), null),
            new Message(Role.USER, List.of(new TextPart("Current question")), null));

    List<Message> history =
        List.of(
            new Message(
                Role.MODEL, List.of(new TextPart("Previous")), Map.of("purpose", "history")));

    List<Message> result = Parser.insertHistory(messages, history);

    assertThat(result).hasSize(3);
    assertThat(result.get(0).role()).isEqualTo(Role.SYSTEM);
    assertThat(result.get(1).role()).isEqualTo(Role.MODEL);
    assertThat(result.get(1).metadata()).containsEntry("purpose", "history");
    assertThat(result.get(2).role()).isEqualTo(Role.USER);
  }

  @Test
  public void testInsertHistory_appendsIfNoUserMessageIsLast() {
    List<Message> messages =
        List.of(
            new Message(Role.SYSTEM, List.of(new TextPart("System prompt")), null),
            new Message(Role.MODEL, List.of(new TextPart("Model message")), null));

    List<Message> history =
        List.of(
            new Message(
                Role.MODEL, List.of(new TextPart("Previous")), Map.of("purpose", "history")));

    List<Message> result = Parser.insertHistory(messages, history);

    assertThat(result).hasSize(3);
    assertThat(result.get(0).role()).isEqualTo(Role.SYSTEM);
    assertThat(result.get(1).role()).isEqualTo(Role.MODEL);
    assertThat(result.get(2).role()).isEqualTo(Role.MODEL);
    assertThat(result.get(2).metadata()).containsEntry("purpose", "history");
  }

  @Test
  public void testToParts_simpleText() {
    List<Part> result = Parser.toParts("Hello World");
    assertThat(result).hasSize(1);
    assertThat(result.get(0)).isInstanceOf(TextPart.class);
    assertThat(((TextPart) result.get(0)).text()).isEqualTo("Hello World");
  }

  @Test
  public void testToParts_emptyString() {
    List<Part> result = Parser.toParts("");
    assertThat(result).isEmpty();
  }

  @Test
  public void testParsePart_textPart() {
    Part result = Parser.parsePart("Hello World");
    assertThat(result).isInstanceOf(TextPart.class);
    assertThat(((TextPart) result).text()).isEqualTo("Hello World");
  }

  @Test
  public void testParsePart_mediaPart() {
    Part result = Parser.parsePart("<<<dotprompt:media:url>>> https://example.com/image.jpg");
    assertThat(result).isInstanceOf(MediaPart.class);
    assertThat(((MediaPart) result).media().url()).isEqualTo("https://example.com/image.jpg");
  }

  @Test
  public void testParsePart_sectionPart() {
    Part result = Parser.parsePart("<<<dotprompt:section>>> code");
    assertThat(result).isInstanceOf(PendingPart.class);
    assertThat(((PendingPart) result).metadata()).containsEntry("purpose", "code");
    assertThat(((PendingPart) result).metadata()).containsEntry("pending", true);
  }

  @Test
  public void testParseMediaPart_basic() {
    MediaPart result =
        Parser.parseMediaPart("<<<dotprompt:media:url>>> https://example.com/image.jpg");
    assertThat(result.media().url()).isEqualTo("https://example.com/image.jpg");
    assertThat(result.media().contentType()).isNull();
  }

  @Test
  public void testParseMediaPart_withContentType() {
    MediaPart result =
        Parser.parseMediaPart("<<<dotprompt:media:url>>> https://example.com/image.jpg image/jpeg");
    assertThat(result.media().url()).isEqualTo("https://example.com/image.jpg");
    assertThat(result.media().contentType()).isEqualTo("image/jpeg");
  }

  @Test(expected = IllegalArgumentException.class)
  public void testParseMediaPart_invalidPrefix() {
    Parser.parseMediaPart("https://example.com/image.jpg");
  }

  @Test
  public void testParseSectionPart_basic() {
    PendingPart result = Parser.parseSectionPart("<<<dotprompt:section>>> code");
    assertThat(result.metadata()).containsEntry("purpose", "code");
    assertThat(result.metadata()).containsEntry("pending", true);
  }

  @Test(expected = IllegalArgumentException.class)
  public void testParseSectionPart_invalidPrefix() {
    Parser.parseSectionPart("code");
  }

  @Test
  public void testParseTextPart() {
    TextPart result = Parser.parseTextPart("Hello World");
    assertThat(result.text()).isEqualTo("Hello World");
  }

  @Test
  public void testMessageSourcesToMessages_emptyArray() {
    List<Message> result = Parser.messageSourcesToMessages(List.of());
    assertThat(result).isEmpty();
  }

  @Test
  public void testMessageSourcesToMessages_singleSource() {
    List<MessageSource> sources = List.of(new MessageSource(Role.USER, "Hello"));
    List<Message> result = Parser.messageSourcesToMessages(sources);

    assertThat(result).hasSize(1);
    assertThat(result.get(0).role()).isEqualTo(Role.USER);
    assertThat(((TextPart) result.get(0).content().get(0)).text()).isEqualTo("Hello");
  }

  @Test
  public void testMessageSourcesToMessages_withContent() {
    List<MessageSource> sources =
        List.of(new MessageSource(Role.USER, List.of(new TextPart("Existing content")), null));
    List<Message> result = Parser.messageSourcesToMessages(sources);

    assertThat(result).hasSize(1);
    assertThat(((TextPart) result.get(0).content().get(0)).text()).isEqualTo("Existing content");
  }

  @Test
  public void testMessageSourcesToMessages_withMetadata() {
    List<MessageSource> sources =
        List.of(new MessageSource(Role.USER, List.of(new TextPart("Hello")), Map.of("foo", "bar")));
    List<Message> result = Parser.messageSourcesToMessages(sources);

    assertThat(result).hasSize(1);
    assertThat(result.get(0).metadata()).containsEntry("foo", "bar");
  }

  @Test
  public void testMessageSourcesToMessages_multipleMessages() {
    List<MessageSource> sources =
        List.of(
            new MessageSource(Role.USER, "Hello"),
            new MessageSource(Role.MODEL, "Hi there!"),
            new MessageSource(Role.USER, "How are you?"));
    List<Message> result = Parser.messageSourcesToMessages(sources);

    assertThat(result).hasSize(3);
    assertThat(((TextPart) result.get(0).content().get(0)).text()).isEqualTo("Hello");
    assertThat(((TextPart) result.get(1).content().get(0)).text()).isEqualTo("Hi there!");
    assertThat(((TextPart) result.get(2).content().get(0)).text()).isEqualTo("How are you?");
  }

  @Test
  public void testParseDocument_withFrontmatterAndTemplate() throws IOException {
    String source = "---\nname: test\ndescription: test description\n---\nTemplate content";

    var result = Parser.parseDocument(source);

    assertThat(result.name()).isEqualTo("test");
    assertThat(result.description()).isEqualTo("test description");
    assertThat(result.template()).isEqualTo("Template content");
  }

  @Test
  public void testParseDocument_withExtensionFields() throws IOException {
    String source = "---\nfoo.bar: value\n---\nTemplate content";

    var result = Parser.parseDocument(source);

    assertThat(result.template()).isEqualTo("Template content");
    assertThat(result.ext()).isNotNull();
    @SuppressWarnings("unchecked")
    Map<String, Object> foo = (Map<String, Object>) result.ext().get("foo");
    assertThat(foo).containsEntry("bar", "value");
  }

  @Test
  public void testParseDocument_withoutFrontmatter() throws IOException {
    String source = "Just template content";

    var result = Parser.parseDocument(source);

    assertThat(result.template()).isEqualTo("Just template content");
    assertThat(result.name()).isNull();
  }

  @Test
  public void testParseDocument_emptyFrontmatter() throws IOException {
    String source = "---\n---\nTemplate content";

    var result = Parser.parseDocument(source);

    assertThat(result.template()).isEqualTo("Template content");
    assertThat(result.name()).isNull();
  }

  @Test
  public void testParseDocument_withModelConfig() throws IOException {
    String source = "---\nmodel: gemini-2.5-pro\n---\nTemplate content";

    var result = Parser.parseDocument(source);

    assertThat(result.model()).isEqualTo("gemini-2.5-pro");
    assertThat(result.template()).isEqualTo("Template content");
  }

  @Test
  public void testParseWithLicenseHeader() throws IOException {
    String content =
        "# Copyright 2025 Google LLC\n"
            + "# License: Apache 2.0\n"
            + "---\n"
            + "model: gemini-pro\n"
            + "---\n"
            + "Hello!";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Hello!");
    assertThat(prompt.config()).containsEntry("model", "gemini-pro");
  }

  @Test
  public void testParseWithShebang() throws IOException {
    String content =
        "#!/usr/bin/env promptly\n"
            + "---\n"
            + "model: gemini-flash\n"
            + "---\n"
            + "Hello shebang!";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Hello shebang!");
    assertThat(prompt.config()).containsEntry("model", "gemini-flash");
  }

  @Test
  public void testParseWithShebangAndLicenseHeader() throws IOException {
    String content =
        "#!/usr/bin/env promptly\n"
            + "# Copyright 2025 Google\n"
            + "# SPDX: Apache-2.0\n"
            + "---\n"
            + "model: gemini-2.5-flash\n"
            + "---\n"
            + "Hello combined!";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Hello combined!");
    assertThat(prompt.config()).containsEntry("model", "gemini-2.5-flash");
  }

  @Test
  public void testParseWithBlankLinesBeforeFrontmatter() throws IOException {
    String content =
        "# License header\n"
            + "\n"
            + "# More comments\n"
            + "\n"
            + "---\n"
            + "model: gemini-pro\n"
            + "---\n"
            + "Hello!";
    Prompt prompt = Parser.parse(content);
    assertThat(prompt.template()).isEqualTo("Hello!");
    assertThat(prompt.config()).containsEntry("model", "gemini-pro");
  }
}
