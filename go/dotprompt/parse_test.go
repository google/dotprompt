// Copyright 2025 Google LLC
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

package dotprompt

import (
	"regexp"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

func TestFrontmatterAndBodyRegex(t *testing.T) {
	testCases := []struct {
		name                string
		source              string
		expectedFrontmatter string
		expectedBody        string
		shouldMatch         bool
	}{
		{
			name:                "Document with CRLF line endings",
			source:              "---\r\nfoo: bar\r\n---\r\nThis is the body.\r\n",
			expectedFrontmatter: "foo: bar",
			expectedBody:        "This is the body.\r\n",
			shouldMatch:         true,
		},
		{
			name:                "Document with CR line endings",
			source:              "---\rfoo: bar\r---\rThis is the body.\r",
			expectedFrontmatter: "foo: bar",
			expectedBody:        "This is the body.\r",
			shouldMatch:         true,
		},
		{
			name:                "Document with LF line endings",
			source:              "---\nfoo: bar\n---\nThis is the body.\n",
			expectedFrontmatter: "foo: bar",
			expectedBody:        "This is the body.\n",
			shouldMatch:         true,
		},
		{
			name:                "Document with frontmatter and body",
			source:              "---\nfoo: bar\n---\nThis is the body.",
			expectedFrontmatter: "foo: bar",
			expectedBody:        "This is the body.",
			shouldMatch:         true,
		},
		{
			name:                "Document with empty frontmatter",
			source:              "---\n\n---\nBody only.",
			expectedFrontmatter: "",
			expectedBody:        "Body only.",
			shouldMatch:         true,
		},
		{
			name:                "Document with empty body",
			source:              "---\nfoo: bar\n---\n",
			expectedFrontmatter: "foo: bar",
			expectedBody:        "",
			shouldMatch:         true,
		},
		{
			name:                "Document with multiline frontmatter",
			source:              "---\nfoo: bar\nbaz: qux\n---\nThis is the body.",
			expectedFrontmatter: "foo: bar\nbaz: qux",
			expectedBody:        "This is the body.",
			shouldMatch:         true,
		},
		{
			name:                "Document with no frontmatter markers",
			source:              "Just a body.",
			expectedFrontmatter: "",
			expectedBody:        "",
			shouldMatch:         false,
		},
		{
			name:                "Document with incomplete frontmatter markers",
			source:              "---\nfoo: bar\nThis is the body.",
			expectedFrontmatter: "",
			expectedBody:        "",
			shouldMatch:         false,
		},
		{
			name:                "Document with extra frontmatter markers",
			source:              "---\nfoo: bar\n---\nThis is the body.\n---\nExtra section.",
			expectedFrontmatter: "foo: bar",
			expectedBody:        "This is the body.\n---\nExtra section.",
			shouldMatch:         true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			match := FrontmatterAndBodyRegex.FindStringSubmatch(tc.source)

			if !tc.shouldMatch {
				if match != nil {
					t.Errorf("Regex should not match for: %s", tc.source)
				}
			} else {
				if match == nil {
					t.Fatalf("Regex should match for: %s", tc.source)
				}
				if len(match) != 3 {
					t.Errorf("Match should have 3 elements (full match + 2 groups), got %d", len(match))
				}
				frontmatter := match[1]
				body := match[2]
				if frontmatter != tc.expectedFrontmatter {
					t.Errorf("Frontmatter = %q, want %q", frontmatter, tc.expectedFrontmatter)
				}
				if body != tc.expectedBody {
					t.Errorf("Body = %q, want %q", body, tc.expectedBody)
				}
			}
		})
	}
}

func TestRoleAndHistoryMarkerRegex(t *testing.T) {
	t.Run("test valid patterns", func(t *testing.T) {
		// NOTE: currently this doesn't validate the role.
		validPatterns := []string{
			"<<<dotprompt:role:user>>>",
			"<<<dotprompt:role:model>>>",
			"<<<dotprompt:role:system>>>",
			"<<<dotprompt:history>>>",
			"<<<dotprompt:role:bot>>>",
			"<<<dotprompt:role:human>>>",
			"<<<dotprompt:role:customer>>>",
		}

		for _, pattern := range validPatterns {
			if RoleAndHistoryMarkerRegex.FindStringSubmatch(pattern) == nil {
				t.Errorf("Pattern should match: %s", pattern)
			}
		}
	})

	t.Run("test invalid patterns", func(t *testing.T) {
		invalidPatterns := []string{
			"<<<dotprompt:role:USER>>>",   // uppercase not allowed
			"<<<dotprompt:role:model1>>>", // numbers not allowed
			"<<<dotprompt:role:>>>",       // needs at least one letter
			"<<<dotprompt:role>>>",        // missing role value
			"<<<dotprompt:history123>>>",  // history should be exact
			"<<<dotprompt:HISTORY>>>",     // history must be lowercase
			"dotprompt:role:user",         // missing brackets
			"<<<dotprompt:role:user",      // incomplete closing
			"dotprompt:role:user>>>",      // incomplete opening
		}

		for _, pattern := range invalidPatterns {
			if RoleAndHistoryMarkerRegex.FindStringSubmatch(pattern) != nil {
				t.Errorf("Pattern should not match: %s", pattern)
			}
		}
	})

	t.Run("multiple markers", func(t *testing.T) {
		text := `
		<<<dotprompt:role:user>>> Hello
		<<<dotprompt:role:model>>> Hi there
		<<<dotprompt:history>>>
		<<<dotprompt:role:user>>> How are you?
	`

		matches := RoleAndHistoryMarkerRegex.FindAllString(text, -1)
		if len(matches) != 4 {
			t.Errorf("len(matches) = %d, want 4", len(matches))
		}
	})
}

func TestMediaAndSectionMarkerRegex(t *testing.T) {
	t.Run("test valid patterns", func(t *testing.T) {
		validPatterns := []string{
			"<<<dotprompt:media:url>>>",
			"<<<dotprompt:section>>>",
		}

		for _, pattern := range validPatterns {
			if MediaAndSectionMarkerRegex.FindStringSubmatch(pattern) == nil {
				t.Errorf("Pattern should match: %s", pattern)
			}
		}
	})

	t.Run("multiple matches", func(t *testing.T) {
		text := `
		<<<dotprompt:media:url>>> https://example.com/image.jpg
		<<<dotprompt:section>>> Section 1
		<<<dotprompt:media:url>>> https://example.com/video.mp4
		<<<dotprompt:section>>> Section 2
	`

		matches := MediaAndSectionMarkerRegex.FindAllString(text, -1)
		if len(matches) != 4 {
			t.Errorf("len(matches) = %d, want 4", len(matches))
		}
	})
}

func TestSplitByRegex(t *testing.T) {
	inputStr := "  one  ,  ,  two  ,  three  "
	output := splitByRegex(inputStr, regexp.MustCompile(`,`))
	want := []string{"  one  ", "  two  ", "  three  "}
	if diff := cmp.Diff(want, output); diff != "" {
		t.Errorf("splitByRegex() mismatch (-want +got):\n%s", diff)
	}
}

func TestSplitByMediaAndSectionMarkers(t *testing.T) {
	t.Run("BasicMarker", func(t *testing.T) {
		inputStr := "<<<dotprompt:media:url>>> https://example.com/image.jpg"
		output := splitByMediaAndSectionMarkers(inputStr)
		expected := []string{
			"<<<dotprompt:media:url",
			" https://example.com/image.jpg",
		}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByMediaAndSectionMarkers() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("MultipleMarkers", func(t *testing.T) {
		inputStr := "Start <<<dotprompt:media:url>>> https://example.com/image.jpg End <<<dotprompt:section>>> Code"
		output := splitByMediaAndSectionMarkers(inputStr)
		expected := []string{
			"Start ",
			"<<<dotprompt:media:url",
			" https://example.com/image.jpg End ",
			"<<<dotprompt:section",
			" Code",
		}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByMediaAndSectionMarkers() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("NoMarkers", func(t *testing.T) {
		inputStr := "Hello World"
		output := splitByMediaAndSectionMarkers(inputStr)
		expected := []string{"Hello World"}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByMediaAndSectionMarkers() mismatch (-want +got):\n%s", diff)
		}
	})
}

func TestSplitByRoleAndHistoryMarkers(t *testing.T) {
	t.Run("NoMarkers", func(t *testing.T) {
		inputStr := "Hello World"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{"Hello World"}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByRoleAndHistoryMarkers() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("SingleMarker", func(t *testing.T) {
		inputStr := "Hello <<<dotprompt:role:model>>> world"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{
			"Hello ",
			"<<<dotprompt:role:model",
			" world",
		}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByRoleAndHistoryMarkers() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("FilterEmpty", func(t *testing.T) {
		inputStr := "  <<<dotprompt:role:system>>>   "
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{"<<<dotprompt:role:system"}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByRoleAndHistoryMarkers() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("AdjacentMarkers", func(t *testing.T) {
		inputStr := "<<<dotprompt:role:user>>><<<dotprompt:history>>>"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{
			"<<<dotprompt:role:user",
			"<<<dotprompt:history",
		}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByRoleAndHistoryMarkers() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("InvalidFormat", func(t *testing.T) {
		inputStr := "<<<dotprompt:ROLE:user>>>"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{"<<<dotprompt:ROLE:user>>>"}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByRoleAndHistoryMarkers() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("MultipleMarkers", func(t *testing.T) {
		inputStr := "Start <<<dotprompt:role:user>>> middle <<<dotprompt:history>>> end"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{
			"Start ",
			"<<<dotprompt:role:user",
			" middle ",
			"<<<dotprompt:history",
			" end",
		}

		if diff := cmp.Diff(expected, output); diff != "" {
			t.Errorf("splitByRoleAndHistoryMarkers() mismatch (-want +got):\n%s", diff)
		}
	})
}

func TestConvertNamespacedEntryToNestedObject(t *testing.T) {
	t.Run("test creating nested object", func(t *testing.T) {
		result := convertNamespacedEntryToNestedObject("foo.bar", "hello", nil)

		expected := map[string]map[string]any{
			"foo": {
				"bar": "hello",
			},
		}

		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("convertNamespacedEntryToNestedObject() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("test adding to existing namespace", func(t *testing.T) {
		existing := map[string]map[string]any{
			"foo": {
				"bar": "hello",
			},
		}

		result := convertNamespacedEntryToNestedObject("foo.baz", "world", existing)

		expected := map[string]map[string]any{
			"foo": {
				"bar": "hello",
				"baz": "world",
			},
		}

		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("convertNamespacedEntryToNestedObject() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("test handling multiple namespaces", func(t *testing.T) {
		result := convertNamespacedEntryToNestedObject("foo.bar", "hello", nil)
		finalResult := convertNamespacedEntryToNestedObject("baz.qux", "world", result)

		expected := map[string]map[string]any{
			"foo": {
				"bar": "hello",
			},
			"baz": {
				"qux": "world",
			},
		}

		if diff := cmp.Diff(expected, finalResult); diff != "" {
			t.Errorf("convertNamespacedEntryToNestedObject() mismatch (-want +got):\n%s", diff)
		}
	})
}

func TestExtractFrontmatterAndBody(t *testing.T) {
	t.Run("should extract frontmatter and body", func(t *testing.T) {
		inputStr := "---\nfoo: bar\n---\nThis is the body."
		frontmatter, body := extractFrontmatterAndBody(inputStr)
		if frontmatter != "foo: bar" {
			t.Errorf("frontmatter = %q, want %q", frontmatter, "foo: bar")
		}
		if body != "This is the body." {
			t.Errorf("body = %q, want %q", body, "This is the body.")
		}
	})

	t.Run("should extract frontmatter and body with empty frontmatter", func(t *testing.T) {
		inputStr := "---\n\n---\nThis is the body."
		frontmatter, body := extractFrontmatterAndBody(inputStr)
		if frontmatter != "" {
			t.Errorf("frontmatter = %q, want \"\"", frontmatter)
		}
		if body != "This is the body." {
			t.Errorf("body = %q, want %q", body, "This is the body.")
		}
	})

	t.Run("should return empty strings when there is no frontmatter marker", func(t *testing.T) {
		// TODO: May be change this behavior to return a matching body when
		// there is no frontmatter marker and we have a body. This may need to
		// be done across all the runtimes.
		inputStr := "Hello World"
		frontmatter, body := extractFrontmatterAndBody(inputStr)
		if frontmatter != "" {
			t.Errorf("frontmatter = %q, want \"\"", frontmatter)
		}
		if body != "" {
			t.Errorf("body = %q, want \"\"", body)
		}
	})
}

func TestTransformMessagesToHistory(t *testing.T) {
	t.Run("add history metadata to messages", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
			},
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Hi there"},
				},
			},
		}

		result, err := transformMessagesToHistory(messages)
		if err != nil {
			t.Errorf("transformMessagesToHistory() returned error: %v", err)
		}
		if len(result) != 2 {
			t.Errorf("len(result) = %d, want 2", len(result))
		}

		for i, msg := range result {
			if msg.Metadata["purpose"] != "history" {
				t.Errorf("result[%d].Metadata['purpose'] = %v, want \"history\"", i, msg.Metadata["purpose"])
			}
		}
	})

	t.Run("preserve existing metadata while adding history purpose", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"foo": "bar",
					},
				},
			},
		}

		result, err := transformMessagesToHistory(messages)
		if err != nil {
			t.Errorf("transformMessagesToHistory() returned error: %v", err)
		}
		if len(result) != 1 {
			t.Errorf("len(result) = %d, want 1", len(result))
		}

		// Check that history purpose was added and existing metadata preserved
		if result[0].Metadata["purpose"] != "history" {
			t.Errorf("Metadata['purpose'] = %v, want \"history\"", result[0].Metadata["purpose"])
		}
		if result[0].Metadata["foo"] != "bar" {
			t.Errorf("Metadata['foo'] = %v, want \"bar\"", result[0].Metadata["foo"])
		}
	})

	t.Run("handle empty array", func(t *testing.T) {
		result, err := transformMessagesToHistory([]Message{})
		if err != nil {
			t.Errorf("transformMessagesToHistory() returned error: %v", err)
		}
		if len(result) != 0 {
			t.Errorf("len(result) = %d, want 0", len(result))
		}
	})
}

func TestMessageSourcesToMessages(t *testing.T) {
	t.Run("should handle empty array", func(t *testing.T) {
		messageSources := []*MessageSource{}
		messages, err := messageSourcesToMessages(messageSources)
		if err != nil {
			t.Errorf("messageSourcesToMessages() returned error: %v", err)
		}
		if len(messages) != 0 {
			t.Errorf("len(messages) = %d, want 0", len(messages))
		}
	})

	t.Run("should convert a single message source", func(t *testing.T) {
		messageSources := []*MessageSource{
			{
				Role:   RoleUser,
				Source: "Hello",
			},
		}

		messages, err := messageSourcesToMessages(messageSources)
		if err != nil {
			t.Errorf("messageSourcesToMessages() returned error: %v", err)
		}
		if len(messages) != 1 {
			t.Errorf("len(messages) = %d, want 1", len(messages))
		}
		expected := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
			},
		}
		if diff := cmp.Diff(expected, messages); diff != "" {
			t.Errorf("messages mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("should handle message source with content", func(t *testing.T) {
		textPart := &TextPart{Text: "Existing content"}
		messageSources := []*MessageSource{
			{
				Role: RoleUser,
				Content: []Part{
					textPart,
				},
			},
		}

		messages, err := messageSourcesToMessages(messageSources)
		if err != nil {
			t.Errorf("messageSourcesToMessages() returned error: %v", err)
		}
		if len(messages) != 1 {
			t.Errorf("len(messages) = %d, want 1", len(messages))
		}
		expected := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					textPart,
				},
			},
		}
		if diff := cmp.Diff(expected, messages); diff != "" {
			t.Errorf("messages mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("should handle message source with metadata", func(t *testing.T) {
		textPart := &TextPart{Text: "Existing content"}
		messageSources := []*MessageSource{
			{
				Role: RoleUser,
				Content: []Part{
					textPart,
				},
				Metadata: map[string]any{
					"foo": "bar",
				},
			},
		}

		messages, err := messageSourcesToMessages(messageSources)
		if err != nil {
			t.Errorf("messageSourcesToMessages() returned error: %v", err)
		}
		if len(messages) != 1 {
			t.Errorf("len(messages) = %d, want 1", len(messages))
		}
		expected := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					textPart,
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"foo": "bar",
					},
				},
			},
		}
		if diff := cmp.Diff(expected, messages); diff != "" {
			t.Errorf("messages mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("should filter out message sources with empty source and content", func(t *testing.T) {
		messageSources := []*MessageSource{
			{
				Role:   RoleUser,
				Source: "",
			},
			{
				Role:    RoleModel,
				Source:  "  ",
				Content: []Part{}, // Empty content but still included
			},
			{
				Role:   RoleUser,
				Source: "Hello",
			},
		}

		messages, err := messageSourcesToMessages(messageSources)
		if err != nil {
			t.Errorf("messageSourcesToMessages() returned error: %v", err)
		}
		if len(messages) != 2 {
			t.Errorf("len(messages) = %d, want 2", len(messages))
		}

		// Check that the model message is included even with empty source
		if messages[0].Role != RoleModel {
			t.Errorf("messages[0].Role = %q, want %q", messages[0].Role, RoleModel)
		}

		// Check that the user message is included
		if messages[1].Role != RoleUser {
			t.Errorf("messages[1].Role = %q, want %q", messages[1].Role, RoleUser)
		}
		textPart, ok := messages[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("messages[1].Content[0] is not *TextPart, got %T", messages[1].Content[0])
		}
		if textPart.Text != "Hello" {
			t.Errorf("messages[1].Text = %q, want %q", textPart.Text, "Hello")
		}
	})
}

func TestMessagesHaveHistory(t *testing.T) {
	t.Run("should return true if messages have history metadata", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "history",
					},
				},
			},
		}

		if !messagesHaveHistory(messages) {
			t.Error("messagesHaveHistory(messages) = false, want true")
		}
	})

	t.Run("should return false if messages do not have history metadata", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
			},
		}

		if messagesHaveHistory(messages) {
			t.Error("messagesHaveHistory(messages) = true, want false")
		}
	})
}

func TestToMessages(t *testing.T) {
	t.Run("should handle a simple string with no markers", func(t *testing.T) {
		renderedString := "Hello world"
		result, err := ToMessages(renderedString, nil)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 1 {
			t.Errorf("len(result) = %d, want 1", len(result))
		}
		if result[0].Role != RoleUser {
			t.Errorf("Role = %q, want %q", result[0].Role, RoleUser)
		}

		textPart, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart.Text != "Hello world" {
			t.Errorf("Text = %q, want %q", textPart.Text, "Hello world")
		}
	})

	t.Run("should handle a string with a single role marker", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:model>>>Hello world"
		result, err := ToMessages(renderedString, nil)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 1 {
			t.Errorf("len(result) = %d, want 1", len(result))
		}
		if result[0].Role != RoleModel {
			t.Errorf("Role = %q, want %q", result[0].Role, RoleModel)
		}

		textPart, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart.Text != "Hello world" {
			t.Errorf("Text = %q, want %q", textPart.Text, "Hello world")
		}
	})

	t.Run("should handle a string with multiple role markers", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:system>>>System instructions\n" +
			"<<<dotprompt:role:user>>>User query\n" +
			"<<<dotprompt:role:model>>>Model response"
		result, err := ToMessages(renderedString, nil)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 3 {
			t.Errorf("len(result) = %d, want 3", len(result))
		}

		if result[0].Role != RoleSystem {
			t.Errorf("result[0].Role = %q, want %q", result[0].Role, RoleSystem)
		}
		textPart0, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[0].Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart0.Text != "System instructions\n" {
			t.Errorf("result[0].Text = %q, want %q", textPart0.Text, "System instructions\n")
		}

		if result[1].Role != RoleUser {
			t.Errorf("result[1].Role = %q, want %q", result[1].Role, RoleUser)
		}
		textPart1, ok := result[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[1].Content[0] is not *TextPart, got %T", result[1].Content[0])
		}
		if textPart1.Text != "User query\n" {
			t.Errorf("result[1].Text = %q, want %q", textPart1.Text, "User query\n")
		}

		if result[2].Role != RoleModel {
			t.Errorf("result[2].Role = %q, want %q", result[2].Role, RoleModel)
		}
		textPart2, ok := result[2].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[2].Content[0] is not *TextPart, got %T", result[2].Content[0])
		}
		if textPart2.Text != "Model response" {
			t.Errorf("result[2].Text = %q, want %q", textPart2.Text, "Model response")
		}
	})

	t.Run("should update the role of an empty message instead of creating a new one", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>><<<dotprompt:role:model>>>Response"
		result, err := ToMessages(renderedString, nil)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		// Should only have one message since the first role marker doesn't have content
		if len(result) != 1 {
			t.Errorf("len(result) = %d, want 1", len(result))
		}
		if result[0].Role != RoleModel {
			t.Errorf("Role = %q, want %q", result[0].Role, RoleModel)
		}

		textPart, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart.Text != "Response" {
			t.Errorf("Text = %q, want %q", textPart.Text, "Response")
		}
	})

	t.Run("should handle history markers and add metadata", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up"
		historyMessages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Previous question"},
				},
			},
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Previous answer"},
				},
			},
		}

		data := &DataArgument{Messages: historyMessages}
		result, err := ToMessages(renderedString, data)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 4 {
			t.Errorf("len(result) = %d, want 4", len(result))
		}

		// First message is the user query
		if result[0].Role != RoleUser {
			t.Errorf("result[0].Role = %q, want %q", result[0].Role, RoleUser)
		}
		textPart0, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[0].Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart0.Text != "Query" {
			t.Errorf("result[0].Text = %q, want %q", textPart0.Text, "Query")
		}

		// Next two messages should be history messages with appropriate metadata
		if result[1].Role != RoleUser {
			t.Errorf("result[1].Role = %q, want %q", result[1].Role, RoleUser)
		}
		if result[1].Metadata["purpose"] != "history" {
			t.Errorf("result[1].Metadata['purpose'] = %v, want \"history\"", result[1].Metadata["purpose"])
		}

		if result[2].Role != RoleModel {
			t.Errorf("result[2].Role = %q, want %q", result[2].Role, RoleModel)
		}
		if result[2].Metadata["purpose"] != "history" {
			t.Errorf("result[2].Metadata['purpose'] = %v, want \"history\"", result[2].Metadata["purpose"])
		}

		// Last message is the follow-up
		if result[3].Role != RoleModel {
			t.Errorf("result[3].Role = %q, want %q", result[3].Role, RoleModel)
		}
		textPart3, ok := result[3].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[3].Content[0] is not *TextPart, got %T", result[3].Content[0])
		}
		if textPart3.Text != "Follow-up" {
			t.Errorf("result[3].Text = %q, want %q", textPart3.Text, "Follow-up")
		}
	})

	t.Run("should handle empty history gracefully", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up"
		data := &DataArgument{Messages: []Message{}}
		result, err := ToMessages(renderedString, data)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 2 {
			t.Errorf("len(result) = %d, want 2", len(result))
		}

		if result[0].Role != RoleUser {
			t.Errorf("result[0].Role = %q, want %q", result[0].Role, RoleUser)
		}
		textPart0, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[0].Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart0.Text != "Query" {
			t.Errorf("result[0].Text = %q, want %q", textPart0.Text, "Query")
		}

		if result[1].Role != RoleModel {
			t.Errorf("result[1].Role = %q, want %q", result[1].Role, RoleModel)
		}
		textPart1, ok := result[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[1].Content[0] is not *TextPart, got %T", result[1].Content[0])
		}
		if textPart1.Text != "Follow-up" {
			t.Errorf("result[1].Text = %q, want %q", textPart1.Text, "Follow-up")
		}
	})

	t.Run("should handle nil data gracefully", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up"
		result, err := ToMessages(renderedString, nil)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 2 {
			t.Errorf("len(result) = %d, want 2", len(result))
		}

		if result[0].Role != RoleUser {
			t.Errorf("result[0].Role = %q, want %q", result[0].Role, RoleUser)
		}
		textPart0, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[0].Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart0.Text != "Query" {
			t.Errorf("result[0].Text = %q, want %q", textPart0.Text, "Query")
		}

		if result[1].Role != RoleModel {
			t.Errorf("result[1].Role = %q, want %q", result[1].Role, RoleModel)
		}
		textPart1, ok := result[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[1].Content[0] is not *TextPart, got %T", result[1].Content[0])
		}
		if textPart1.Text != "Follow-up" {
			t.Errorf("result[1].Text = %q, want %q", textPart1.Text, "Follow-up")
		}
	})

	t.Run("should filter out empty messages", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>> " +
			"<<<dotprompt:role:system>>> " +
			"<<<dotprompt:role:model>>>Response"
		result, err := ToMessages(renderedString, nil)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 1 {
			t.Errorf("len(result) = %d, want 1", len(result))
		}
		if result[0].Role != RoleModel {
			t.Errorf("Role = %q, want %q", result[0].Role, RoleModel)
		}

		textPart, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart.Text != "Response" {
			t.Errorf("Text = %q, want %q", textPart.Text, "Response")
		}
	})

	t.Run("should handle multiple history markers by treating each as a separate insertion point", func(t *testing.T) {
		renderedString := "<<<dotprompt:history>>>First<<<dotprompt:history>>>Second"
		historyMessages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Previous"},
				},
			},
		}

		data := &DataArgument{Messages: historyMessages}
		result, err := ToMessages(renderedString, data)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 4 {
			t.Errorf("len(result) = %d, want 4", len(result))
		}

		if result[0].Metadata["purpose"] != "history" {
			t.Errorf("result[0].Metadata['purpose'] = %v, want \"history\"", result[0].Metadata["purpose"])
		}

		textPart1, ok := result[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[1].Content[0] is not *TextPart, got %T", result[1].Content[0])
		}
		if textPart1.Text != "First" {
			t.Errorf("result[1].Text = %q, want %q", textPart1.Text, "First")
		}

		if result[2].Metadata["purpose"] != "history" {
			t.Errorf("result[2].Metadata['purpose'] = %v, want \"history\"", result[2].Metadata["purpose"])
		}

		textPart3, ok := result[3].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[3].Content[0] is not *TextPart, got %T", result[3].Content[0])
		}
		if textPart3.Text != "Second" {
			t.Errorf("result[3].Text = %q, want %q", textPart3.Text, "Second")
		}
	})

	t.Run("should support complex interleaving of role and history markers", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:system>>>Instructions\n" +
			"<<<dotprompt:role:user>>>Initial Query\n" +
			"<<<dotprompt:history>>>\n" +
			"<<<dotprompt:role:user>>>Follow-up Question\n" +
			"<<<dotprompt:role:model>>>Final Response"

		historyMessages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Previous question"},
				},
			},
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Previous answer"},
				},
			},
		}

		data := &DataArgument{Messages: historyMessages}
		result, err := ToMessages(renderedString, data)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 6 {
			t.Errorf("len(result) = %d, want 6", len(result))
		}

		if result[0].Role != RoleSystem {
			t.Errorf("result[0].Role = %q, want %q", result[0].Role, RoleSystem)
		}
		textPart0, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[0].Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart0.Text != "Instructions\n" {
			t.Errorf("result[0].Text = %q, want %q", textPart0.Text, "Instructions\n")
		}

		if result[1].Role != RoleUser {
			t.Errorf("result[1].Role = %q, want %q", result[1].Role, RoleUser)
		}
		textPart1, ok := result[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[1].Content[0] is not *TextPart, got %T", result[1].Content[0])
		}
		if textPart1.Text != "Initial Query\n" {
			t.Errorf("result[1].Text = %q, want %q", textPart1.Text, "Initial Query\n")
		}

		if result[2].Role != RoleUser {
			t.Errorf("result[2].Role = %q, want %q", result[2].Role, RoleUser)
		}
		if result[2].Metadata["purpose"] != "history" {
			t.Errorf("result[2].Metadata['purpose'] = %v, want \"history\"", result[2].Metadata["purpose"])
		}

		if result[3].Role != RoleModel {
			t.Errorf("result[3].Role = %q, want %q", result[3].Role, RoleModel)
		}
		if result[3].Metadata["purpose"] != "history" {
			t.Errorf("result[3].Metadata['purpose'] = %v, want \"history\"", result[3].Metadata["purpose"])
		}

		if result[4].Role != RoleUser {
			t.Errorf("result[4].Role = %q, want %q", result[4].Role, RoleUser)
		}
		textPart4, ok := result[4].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[4].Content[0] is not *TextPart, got %T", result[4].Content[0])
		}
		if textPart4.Text != "Follow-up Question\n" {
			t.Errorf("result[4].Text = %q, want %q", textPart4.Text, "Follow-up Question\n")
		}

		if result[5].Role != RoleModel {
			t.Errorf("result[5].Role = %q, want %q", result[5].Role, RoleModel)
		}
		textPart5, ok := result[5].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[5].Content[0] is not *TextPart, got %T", result[5].Content[0])
		}
		if textPart5.Text != "Final Response" {
			t.Errorf("result[5].Text = %q, want %q", textPart5.Text, "Final Response")
		}
	})

	t.Run("should handle an empty input string", func(t *testing.T) {
		result, err := ToMessages("", nil)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		if len(result) != 0 {
			t.Errorf("len(result) = %d, want 0", len(result))
		}
	})

	t.Run("should properly call insertHistory with data.messages", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>>Question"
		historyMessages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Previous"},
				},
			},
		}

		data := &DataArgument{Messages: historyMessages}
		result, err := ToMessages(renderedString, data)

		if err != nil {
			t.Errorf("ToMessages() returned error: %v", err)
		}
		// The resulting messages should have the history message inserted
		// before the user message by the insertHistory function
		if len(result) != 2 {
			t.Errorf("len(result) = %d, want 2", len(result))
		}

		if result[0].Role != RoleUser {
			t.Errorf("result[0].Role = %q, want %q", result[0].Role, RoleUser)
		}
		textPart0, ok := result[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[0].Content[0] is not *TextPart, got %T", result[0].Content[0])
		}
		if textPart0.Text != "Previous" {
			t.Errorf("result[0].Text = %q, want %q", textPart0.Text, "Previous")
		}
		if result[0].Metadata != nil {
			t.Errorf("result[0].Metadata should be nil, got %v", result[0].Metadata)
		}

		if result[1].Role != RoleUser {
			t.Errorf("result[1].Role = %q, want %q", result[1].Role, RoleUser)
		}
		textPart1, ok := result[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("result[1].Content[0] is not *TextPart, got %T", result[1].Content[0])
		}
		if textPart1.Text != "Question" {
			t.Errorf("result[1].Text = %q, want %q", textPart1.Text, "Question")
		}
	})
}

func TestInsertHistory(t *testing.T) {
	t.Run("should return original messages if history is undefined", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
			},
		}

		result, err := insertHistory(messages, nil)
		if err != nil {
			t.Errorf("insertHistory() returned error: %v", err)
		}
		if diff := cmp.Diff(messages, result); diff != "" {
			t.Errorf("insertHistory() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("should return original messages if history purpose already exists", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "history",
					},
				},
			},
		}

		history := []Message{
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Previous"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "history",
					},
				},
			},
		}

		result, err := insertHistory(messages, history)
		if err != nil {
			t.Errorf("insertHistory() returned error: %v", err)
		}
		if diff := cmp.Diff(messages, result); diff != "" {
			t.Errorf("insertHistory() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("should insert history before the last user message", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleSystem,
				Content: []Part{
					&TextPart{Text: "System prompt"},
				},
			},
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Current question"},
				},
			},
		}

		history := []Message{
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Previous"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "history",
					},
				},
			},
		}

		result, err := insertHistory(messages, history)
		if err != nil {
			t.Errorf("insertHistory() returned error: %v", err)
		}
		if len(result) != 3 {
			t.Errorf("len(result) = %d, want 3", len(result))
		}

		expected := []Message{
			{
				Role: RoleSystem,
				Content: []Part{
					&TextPart{Text: "System prompt"},
				},
			},
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Previous"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "history",
					},
				},
			},
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Current question"},
				},
			},
		}

		if len(expected) != len(result) {
			t.Fatalf("Expected length %d, got %d", len(expected), len(result))
		}

		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("insertHistory() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("should append history at the end if no user message is last", func(t *testing.T) {
		messages := []Message{
			{
				Role: RoleSystem,
				Content: []Part{
					&TextPart{Text: "System prompt"},
				},
			},
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Model message"},
				},
			},
		}

		history := []Message{
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Previous"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "history",
					},
				},
			},
		}

		result, err := insertHistory(messages, history)
		if err != nil {
			t.Errorf("insertHistory() returned error: %v", err)
		}
		if len(result) != 3 {
			t.Errorf("len(result) = %d, want 3", len(result))
		}

		expected := []Message{
			{
				Role: RoleSystem,
				Content: []Part{
					&TextPart{Text: "System prompt"},
				},
			},
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Model message"},
				},
			},
			{
				Role: RoleModel,
				Content: []Part{
					&TextPart{Text: "Previous"},
				},
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "history",
					},
				},
			},
		}

		if len(expected) != len(result) {
			t.Fatalf("Expected length %d, got %d", len(expected), len(result))
		}

		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("insertHistory() mismatch (-want +got):\n%s", diff)
		}
	})
}

func TestParsePart(t *testing.T) {
	testCases := []struct {
		name     string
		piece    string
		expected Part
		hasError bool
	}{
		{
			name:     "Text part",
			piece:    "Hello World",
			expected: &TextPart{Text: "Hello World"},
			hasError: false,
		},
		{
			name:  "Media part",
			piece: "<<<dotprompt:media:url>>> https://example.com/image.jpg",
			expected: &MediaPart{
				Media: struct {
					URL         string `json:"url"`
					ContentType string `json:"contentType,omitempty"`
				}{
					URL: "https://example.com/image.jpg",
				},
			},
			hasError: false,
		},
		{
			name:  "Media part with content type",
			piece: "<<<dotprompt:media:url>>> https://example.com/image.jpg image/jpeg",
			expected: &MediaPart{
				Media: struct {
					URL         string `json:"url"`
					ContentType string `json:"contentType,omitempty"`
				}{
					URL:         "https://example.com/image.jpg",
					ContentType: "image/jpeg",
				},
			},
			hasError: false,
		},
		{
			name:  "Section part",
			piece: "<<<dotprompt:section>>> code",
			expected: &PendingPart{
				HasMetadata: HasMetadata{
					Metadata: map[string]any{
						"purpose": "code",
						"pending": true,
					},
				},
			},
			hasError: false,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result, err := parsePart(tc.piece)

			if tc.hasError {
				if err == nil {
					t.Errorf("parsePart(%q) expected error, got nil", tc.piece)
				}
			} else {
				if err != nil {
					t.Errorf("parsePart(%q) expected no error, got %v", tc.piece, err)
				}

				switch expected := tc.expected.(type) {
				case *TextPart:
					actual, ok := result.(*TextPart)
					if !ok {
						t.Fatalf("result is not *TextPart, got %T", result)
					}
					if actual.Text != expected.Text {
						t.Errorf("Text = %q, want %q", actual.Text, expected.Text)
					}
				case *MediaPart:
					actual, ok := result.(*MediaPart)
					if !ok {
						t.Fatalf("result is not *MediaPart, got %T", result)
					}
					if actual.Media.URL != expected.Media.URL {
						t.Errorf("URL = %q, want %q", actual.Media.URL, expected.Media.URL)
					}
					if actual.Media.ContentType != expected.Media.ContentType {
						t.Errorf("ContentType = %q, want %q", actual.Media.ContentType, expected.Media.ContentType)
					}
				case *PendingPart:
					actual, ok := result.(*PendingPart)
					if !ok {
						t.Fatalf("result is not *PendingPart, got %T", result)
					}
					if diff := cmp.Diff(expected.Metadata["purpose"], actual.Metadata["purpose"]); diff != "" {
						t.Errorf("Metadata['purpose'] mismatch (-want +got):\n%s", diff)
					}
					if diff := cmp.Diff(expected.Metadata["pending"], actual.Metadata["pending"]); diff != "" {
						t.Errorf("Metadata['pending'] mismatch (-want +got):\n%s", diff)
					}
				}
			}
		})
	}
}

func TestParseMediaPiece(t *testing.T) {
	t.Run("parse media piece", func(t *testing.T) {
		piece := "<<<dotprompt:media:url>>> https://example.com/image.jpg"
		result, err := parseMediaPart(piece)
		if err != nil {
			t.Errorf("parseMediaPart() returned error: %v", err)
		}
		if result.Media.URL != "https://example.com/image.jpg" {
			t.Errorf("URL = %q, want %q", result.Media.URL, "https://example.com/image.jpg")
		}
	})
}

func TestParseDocument(t *testing.T) {
	t.Run("parse document with frontmatter and template", func(t *testing.T) {
		source := `---
name: test
description: test description
foo.bar: value
---
Template content`

		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}
		if result.Name != "test" {
			t.Errorf("Name = %q, want %q", result.Name, "test")
		}
		if result.Description != "test description" {
			t.Errorf("Description = %q, want %q", result.Description, "test description")
		}
		if result.Template != "Template content" {
			t.Errorf("Template = %q, want %q", result.Template, "Template content")
		}

		if result.Ext["foo"] == nil {
			t.Error("Ext['foo'] is nil")
		} else if result.Ext["foo"]["bar"] != "value" {
			t.Errorf("Ext['foo']['bar'] = %q, want \"value\"", result.Ext["foo"]["bar"])
		}

		if result.Raw["name"] != "test" {
			t.Errorf("Raw['name'] = %q, want \"test\"", result.Raw["name"])
		}
		if result.Raw["description"] != "test description" {
			t.Errorf("Raw['description'] = %q, want \"test description\"", result.Raw["description"])
		}
		if result.Raw["foo.bar"] != "value" {
			t.Errorf("Raw['foo.bar'] = %q, want \"value\"", result.Raw["foo.bar"])
		}
	})

	t.Run("handle document without frontmatter", func(t *testing.T) {
		source := "Just template content"

		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}
		if result.Ext == nil {
			t.Error("Ext is nil")
		}
		if result.Template != "Just template content" {
			t.Errorf("Template = %q, want \"Just template content\"", result.Template)
		}
	})

	t.Run("handle invalid yaml frontmatter", func(t *testing.T) {
		source := `---
invalid: : yaml
---
Template content`

		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}
		if result.Ext == nil {
			t.Error("Ext is nil")
		}
		// When YAML is invalid, return source as template
		if result.Template != source {
			t.Errorf("Template = %q, want %q", result.Template, source)
		}
	})

	t.Run("handle empty frontmatter", func(t *testing.T) {
		source := `---
---
Template content`

		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}
		if result.Ext == nil {
			t.Error("Ext is nil")
		}
		if result.Template != "Template content" {
			t.Errorf("Template = %q, want \"Template content\"", result.Template)
		}
	})

	t.Run("handle multiple namespaced entries", func(t *testing.T) {
		source := `---
foo.bar: value1
foo.baz: value2
qux.quux: value3
---
Template content`

		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}

		if result.Ext["foo"] == nil {
			t.Error("Ext['foo'] is nil")
		}
		if result.Ext["qux"] == nil {
			t.Error("Ext['qux'] is nil")
		}
		if result.Ext["foo"]["bar"] != "value1" {
			t.Errorf("Ext['foo']['bar'] = %q, want \"value1\"", result.Ext["foo"]["bar"])
		}
		if result.Ext["foo"]["baz"] != "value2" {
			t.Errorf("Ext['foo']['baz'] = %q, want \"value2\"", result.Ext["foo"]["baz"])
		}
		if result.Ext["qux"]["quux"] != "value3" {
			t.Errorf("Ext['qux']['quux'] = %q, want \"value3\"", result.Ext["qux"]["quux"])
		}
	})

	t.Run("handle reserved keywords", func(t *testing.T) {
		// Create frontmatter with all reserved keywords except 'ext'
		var frontmatterParts []string
		for _, keyword := range ReservedMetadataKeywords {
			if keyword == "ext" {
				continue
			}
			frontmatterParts = append(frontmatterParts, keyword+": value-"+keyword)
		}

		// Create source with frontmatter and template
		source := "---\n" + strings.Join(frontmatterParts, "\n") + "\n---\nTemplate content"

		// Parse the document
		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}

		// Check that the result is a ParsedPrompt with the expected template
		if result.Template != "Template content" {
			t.Errorf("Template = %q, want \"Template content\"", result.Template)
		}

		// Check that each reserved keyword field has the expected value
		if result.Name != "value-name" {
			t.Errorf("Name = %q, want \"value-name\"", result.Name)
		}
		if result.Description != "value-description" {
			t.Errorf("Description = %q, want \"value-description\"", result.Description)
		}
		if result.Variant != "value-variant" {
			t.Errorf("Variant = %q, want \"value-variant\"", result.Variant)
		}
		if result.Version != "value-version" {
			t.Errorf("Version = %q, want \"value-version\"", result.Version)
		}

		// Check that raw contains all the reserved keywords
		for _, keyword := range ReservedMetadataKeywords {
			if keyword == "ext" {
				continue
			}
			if result.Raw[keyword] == nil {
				t.Errorf("Raw[%q] is nil", keyword)
			}
			expectedValue := "value-" + keyword
			if result.Raw[keyword] != expectedValue {
				t.Errorf("Raw[%q] = %q, want %q", keyword, result.Raw[keyword], expectedValue)
			}
		}
	})

	t.Run("should handle license header before frontmatter", func(t *testing.T) {
		source := "# Copyright 2025 Google LLC\n# License: Apache 2.0\n---\nmodel: gemini-pro\n---\nHello!"
		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}
		if result.Model != "gemini-pro" {
			t.Errorf("Model = %q, want \"gemini-pro\"", result.Model)
		}
		if result.Template != "Hello!" {
			t.Errorf("Template = %q, want \"Hello!\"", result.Template)
		}
	})

	t.Run("should handle shebang before frontmatter", func(t *testing.T) {
		source := "#!/usr/bin/env promptly\n---\nmodel: gemini-flash\n---\nHello shebang!"
		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}
		if result.Model != "gemini-flash" {
			t.Errorf("Model = %q, want \"gemini-flash\"", result.Model)
		}
		if result.Template != "Hello shebang!" {
			t.Errorf("Template = %q, want \"Hello shebang!\"", result.Template)
		}
	})

	t.Run("should handle shebang and license header before frontmatter", func(t *testing.T) {
		source := "#!/usr/bin/env promptly\n# Copyright 2025 Google\n# SPDX: Apache-2.0\n---\nmodel: gemini-2.0\n---\nHello combined!"
		result, err := ParseDocument(source)
		if err != nil {
			t.Errorf("ParseDocument() returned error: %v", err)
		}
		if result.Model != "gemini-2.0" {
			t.Errorf("Model = %q, want \"gemini-2.0\"", result.Model)
		}
		if result.Template != "Hello combined!" {
			t.Errorf("Template = %q, want \"Hello combined!\"", result.Template)
		}
	})
}
