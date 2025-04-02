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

	"github.com/stretchr/testify/assert"
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
				assert.Nil(t, match, "Regex should not match for: %s", tc.source)
			} else {
				assert.NotNil(t, match, "Regex should match for: %s", tc.source)
				assert.Equal(t, 3, len(match), "Match should have 3 elements (full match + 2 groups)")
				frontmatter := match[1]
				body := match[2]
				assert.Equal(t, tc.expectedFrontmatter, frontmatter, "Frontmatter should match")
				assert.Equal(t, tc.expectedBody, body, "Body should match")
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
			assert.NotNil(t, RoleAndHistoryMarkerRegex.FindStringSubmatch(pattern),
				"Pattern should match: %s", pattern)
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
			assert.Nil(t, RoleAndHistoryMarkerRegex.FindStringSubmatch(pattern),
				"Pattern should not match: %s", pattern)
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
		assert.Equal(t, 4, len(matches))
	})
}

func TestMediaAndSectionMarkerRegex(t *testing.T) {
	t.Run("test valid patterns", func(t *testing.T) {
		validPatterns := []string{
			"<<<dotprompt:media:url>>>",
			"<<<dotprompt:section>>>",
		}

		for _, pattern := range validPatterns {
			assert.NotNil(t, MediaAndSectionMarkerRegex.FindStringSubmatch(pattern),
				"Pattern should match: %s", pattern)
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
		assert.Equal(t, 4, len(matches))
	})
}

func TestSplitByRegex(t *testing.T) {
	inputStr := "  one  ,  ,  two  ,  three  "
	output := splitByRegex(inputStr, regexp.MustCompile(`,`))
	assert.Equal(t, []string{"  one  ", "  two  ", "  three  "}, output)
}

func TestSplitByMediaAndSectionMarkers(t *testing.T) {
	t.Run("BasicMarker", func(t *testing.T) {
		inputStr := "<<<dotprompt:media:url>>> https://example.com/image.jpg"
		output := splitByMediaAndSectionMarkers(inputStr)
		expected := []string{
			"<<<dotprompt:media:url",
			" https://example.com/image.jpg",
		}

		assert.Equal(t, expected, output, "Split result should match expected output")
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

		assert.Equal(t, expected, output, "Split result should match expected output")
	})

	t.Run("NoMarkers", func(t *testing.T) {
		inputStr := "Hello World"
		output := splitByMediaAndSectionMarkers(inputStr)
		expected := []string{"Hello World"}

		assert.Equal(t, expected, output, "Split result should match expected output")
	})
}

func TestSplitByRoleAndHistoryMarkers(t *testing.T) {
	t.Run("NoMarkers", func(t *testing.T) {
		inputStr := "Hello World"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{"Hello World"}

		assert.Equal(t, expected, output, "Split result should match expected output")
	})

	t.Run("SingleMarker", func(t *testing.T) {
		inputStr := "Hello <<<dotprompt:role:model>>> world"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{
			"Hello ",
			"<<<dotprompt:role:model",
			" world",
		}

		assert.Equal(t, expected, output, "Split result should match expected output")
	})

	t.Run("FilterEmpty", func(t *testing.T) {
		inputStr := "  <<<dotprompt:role:system>>>   "
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{"<<<dotprompt:role:system"}

		assert.Equal(t, expected, output, "Split result should match expected output")
	})

	t.Run("AdjacentMarkers", func(t *testing.T) {
		inputStr := "<<<dotprompt:role:user>>><<<dotprompt:history>>>"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{
			"<<<dotprompt:role:user",
			"<<<dotprompt:history",
		}

		assert.Equal(t, expected, output, "Split result should match expected output")
	})

	t.Run("InvalidFormat", func(t *testing.T) {
		inputStr := "<<<dotprompt:ROLE:user>>>"
		output := splitByRoleAndHistoryMarkers(inputStr)
		expected := []string{"<<<dotprompt:ROLE:user>>>"}

		assert.Equal(t, expected, output, "Split result should match expected output")
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

		assert.Equal(t, expected, output, "Split result should match expected output")
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

		assert.Equal(t, expected, result)
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

		assert.Equal(t, expected, result)
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

		assert.Equal(t, expected, finalResult)
	})
}

func TestExtractFrontmatterAndBody(t *testing.T) {
	t.Run("should extract frontmatter and body", func(t *testing.T) {
		inputStr := "---\nfoo: bar\n---\nThis is the body."
		frontmatter, body := extractFrontmatterAndBody(inputStr)
		assert.Equal(t, "foo: bar", frontmatter)
		assert.Equal(t, "This is the body.", body)
	})

	t.Run("should extract frontmatter and body with empty frontmatter", func(t *testing.T) {
		inputStr := "---\n\n---\nThis is the body."
		frontmatter, body := extractFrontmatterAndBody(inputStr)
		assert.Equal(t, "", frontmatter)
		assert.Equal(t, "This is the body.", body)
	})

	t.Run("should return empty strings when there is no frontmatter marker", func(t *testing.T) {
		// TODO: May be change this behavior to return a matching body when
		// there is no frontmatter marker and we have a body. This may need to
		// be done across all the runtimes.
		inputStr := "Hello World"
		frontmatter, body := extractFrontmatterAndBody(inputStr)
		assert.Equal(t, "", frontmatter)
		assert.Equal(t, "", body)
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
		assert.NoError(t, err)
		assert.Equal(t, 2, len(result))

		for _, msg := range result {
			assert.Contains(t, msg.Metadata, "purpose")
			assert.Equal(t, "history", msg.Metadata["purpose"])
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
		assert.NoError(t, err)
		assert.Equal(t, 1, len(result))

		// Check that history purpose was added and existing metadata preserved
		assert.Contains(t, result[0].Metadata, "purpose")
		assert.Equal(t, "history", result[0].Metadata["purpose"])
		assert.Contains(t, result[0].Metadata, "foo")
		assert.Equal(t, "bar", result[0].Metadata["foo"])
	})

	t.Run("handle empty array", func(t *testing.T) {
		result, err := transformMessagesToHistory([]Message{})
		assert.NoError(t, err)
		assert.Equal(t, 0, len(result))
	})
}

func TestMessageSourcesToMessages(t *testing.T) {
	t.Run("should handle empty array", func(t *testing.T) {
		messageSources := []*MessageSource{}
		messages, err := messageSourcesToMessages(messageSources)
		assert.NoError(t, err)
		assert.Equal(t, 0, len(messages))
	})

	t.Run("should convert a single message source", func(t *testing.T) {
		messageSources := []*MessageSource{
			{
				Role:   RoleUser,
				Source: "Hello",
			},
		}

		messages, err := messageSourcesToMessages(messageSources)
		assert.NoError(t, err)
		assert.Equal(t, 1, len(messages))
		assert.Equal(t, []Message{
			{
				Role: RoleUser,
				Content: []Part{
					&TextPart{Text: "Hello"},
				},
			},
		}, messages)
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
		assert.NoError(t, err)
		assert.Equal(t, 1, len(messages))
		assert.Equal(t, []Message{
			{
				Role: RoleUser,
				Content: []Part{
					textPart,
				},
			},
		}, messages)
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
		assert.NoError(t, err)
		assert.Equal(t, 1, len(messages))
		assert.Equal(t, []Message{
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
		}, messages)
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
		assert.NoError(t, err)
		assert.Equal(t, 2, len(messages))

		// Check that the model message is included even with empty source
		assert.Equal(t, RoleModel, messages[0].Role)

		// Check that the user message is included
		assert.Equal(t, RoleUser, messages[1].Role)
		textPart, ok := messages[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Hello", textPart.Text)
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

		result := messagesHaveHistory(messages)
		assert.True(t, result)
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

		result := messagesHaveHistory(messages)
		assert.False(t, result)
	})
}

func TestToMessages(t *testing.T) {
	t.Run("should handle a simple string with no markers", func(t *testing.T) {
		renderedString := "Hello world"
		result, err := ToMessages(renderedString, nil)

		assert.NoError(t, err)
		assert.Equal(t, 1, len(result))
		assert.Equal(t, RoleUser, result[0].Role)

		textPart, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Hello world", textPart.Text)
	})

	t.Run("should handle a string with a single role marker", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:model>>>Hello world"
		result, err := ToMessages(renderedString, nil)

		assert.NoError(t, err)
		assert.Equal(t, 1, len(result))
		assert.Equal(t, RoleModel, result[0].Role)

		textPart, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Hello world", textPart.Text)
	})

	t.Run("should handle a string with multiple role markers", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:system>>>System instructions\n" +
			"<<<dotprompt:role:user>>>User query\n" +
			"<<<dotprompt:role:model>>>Model response"
		result, err := ToMessages(renderedString, nil)

		assert.NoError(t, err)
		assert.Equal(t, 3, len(result))

		assert.Equal(t, RoleSystem, result[0].Role)
		textPart0, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "System instructions\n", textPart0.Text)

		assert.Equal(t, RoleUser, result[1].Role)
		textPart1, ok := result[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "User query\n", textPart1.Text)

		assert.Equal(t, RoleModel, result[2].Role)
		textPart2, ok := result[2].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Model response", textPart2.Text)
	})

	t.Run("should update the role of an empty message instead of creating a new one", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>><<<dotprompt:role:model>>>Response"
		result, err := ToMessages(renderedString, nil)

		assert.NoError(t, err)
		// Should only have one message since the first role marker doesn't have content
		assert.Equal(t, 1, len(result))
		assert.Equal(t, RoleModel, result[0].Role)

		textPart, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Response", textPart.Text)
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

		assert.NoError(t, err)
		assert.Equal(t, 4, len(result))

		// First message is the user query
		assert.Equal(t, RoleUser, result[0].Role)
		textPart0, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Query", textPart0.Text)

		// Next two messages should be history messages with appropriate metadata
		assert.Equal(t, RoleUser, result[1].Role)
		assert.Contains(t, result[1].Metadata, "purpose")
		assert.Equal(t, "history", result[1].Metadata["purpose"])

		assert.Equal(t, RoleModel, result[2].Role)
		assert.Contains(t, result[2].Metadata, "purpose")
		assert.Equal(t, "history", result[2].Metadata["purpose"])

		// Last message is the follow-up
		assert.Equal(t, RoleModel, result[3].Role)
		textPart3, ok := result[3].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Follow-up", textPart3.Text)
	})

	t.Run("should handle empty history gracefully", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up"
		data := &DataArgument{Messages: []Message{}}
		result, err := ToMessages(renderedString, data)

		assert.NoError(t, err)
		assert.Equal(t, 2, len(result))

		assert.Equal(t, RoleUser, result[0].Role)
		textPart0, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Query", textPart0.Text)

		assert.Equal(t, RoleModel, result[1].Role)
		textPart1, ok := result[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Follow-up", textPart1.Text)
	})

	t.Run("should handle nil data gracefully", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>>Query<<<dotprompt:history>>>Follow-up"
		result, err := ToMessages(renderedString, nil)

		assert.NoError(t, err)
		assert.Equal(t, 2, len(result))

		assert.Equal(t, RoleUser, result[0].Role)
		textPart0, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Query", textPart0.Text)

		assert.Equal(t, RoleModel, result[1].Role)
		textPart1, ok := result[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Follow-up", textPart1.Text)
	})

	t.Run("should filter out empty messages", func(t *testing.T) {
		renderedString := "<<<dotprompt:role:user>>> " +
			"<<<dotprompt:role:system>>> " +
			"<<<dotprompt:role:model>>>Response"
		result, err := ToMessages(renderedString, nil)

		assert.NoError(t, err)
		assert.Equal(t, 1, len(result))
		assert.Equal(t, RoleModel, result[0].Role)

		textPart, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Response", textPart.Text)
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

		assert.NoError(t, err)
		assert.Equal(t, 4, len(result))

		assert.Contains(t, result[0].Metadata, "purpose")
		assert.Equal(t, "history", result[0].Metadata["purpose"])

		textPart1, ok := result[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "First", textPart1.Text)

		assert.Contains(t, result[2].Metadata, "purpose")
		assert.Equal(t, "history", result[2].Metadata["purpose"])

		textPart3, ok := result[3].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Second", textPart3.Text)
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

		assert.NoError(t, err)
		assert.Equal(t, 6, len(result))

		assert.Equal(t, RoleSystem, result[0].Role)
		textPart0, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Instructions\n", textPart0.Text)

		assert.Equal(t, RoleUser, result[1].Role)
		textPart1, ok := result[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Initial Query\n", textPart1.Text)

		assert.Equal(t, RoleUser, result[2].Role)
		assert.Contains(t, result[2].Metadata, "purpose")
		assert.Equal(t, "history", result[2].Metadata["purpose"])

		assert.Equal(t, RoleModel, result[3].Role)
		assert.Contains(t, result[3].Metadata, "purpose")
		assert.Equal(t, "history", result[3].Metadata["purpose"])

		assert.Equal(t, RoleUser, result[4].Role)
		textPart4, ok := result[4].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Follow-up Question\n", textPart4.Text)

		assert.Equal(t, RoleModel, result[5].Role)
		textPart5, ok := result[5].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Final Response", textPart5.Text)
	})

	t.Run("should handle an empty input string", func(t *testing.T) {
		result, err := ToMessages("", nil)

		assert.NoError(t, err)
		assert.Equal(t, 0, len(result))
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

		assert.NoError(t, err)
		// The resulting messages should have the history message inserted
		// before the user message by the insertHistory function
		assert.Equal(t, 2, len(result))

		assert.Equal(t, RoleUser, result[0].Role)
		textPart0, ok := result[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Previous", textPart0.Text)
		assert.Nil(t, result[0].Metadata) // insertHistory shouldn't add history metadata

		assert.Equal(t, RoleUser, result[1].Role)
		textPart1, ok := result[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Question", textPart1.Text)
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
		assert.NoError(t, err)
		assert.Equal(t, messages, result)
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
		assert.NoError(t, err)
		assert.Equal(t, messages, result)
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
		assert.NoError(t, err)
		assert.Equal(t, 3, len(result))

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

		assert.Equal(t, len(expected), len(result))
		for i := range expected {
			assert.Equal(t, expected[i].Role, result[i].Role)
			assert.Equal(t, expected[i].Metadata, result[i].Metadata)

			assert.Equal(t, len(expected[i].Content), len(result[i].Content))
			for j := range expected[i].Content {
				expectedPart, ok := expected[i].Content[j].(*TextPart)
				assert.True(t, ok)

				resultPart, ok := result[i].Content[j].(*TextPart)
				assert.True(t, ok)

				assert.Equal(t, expectedPart.Text, resultPart.Text)
			}
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
		assert.NoError(t, err)
		assert.Equal(t, 3, len(result))

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

		assert.Equal(t, len(expected), len(result))
		for i := range expected {
			assert.Equal(t, expected[i].Role, result[i].Role)
			assert.Equal(t, expected[i].Metadata, result[i].Metadata)

			assert.Equal(t, len(expected[i].Content), len(result[i].Content))
			for j := range expected[i].Content {
				expectedPart, ok := expected[i].Content[j].(*TextPart)
				assert.True(t, ok)

				resultPart, ok := result[i].Content[j].(*TextPart)
				assert.True(t, ok)

				assert.Equal(t, expectedPart.Text, resultPart.Text)
			}
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
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)

				switch expected := tc.expected.(type) {
				case *TextPart:
					actual, ok := result.(*TextPart)
					assert.True(t, ok)
					assert.Equal(t, expected.Text, actual.Text)
				case *MediaPart:
					actual, ok := result.(*MediaPart)
					assert.True(t, ok)
					assert.Equal(t, expected.Media.URL, actual.Media.URL)
					assert.Equal(t, expected.Media.ContentType, actual.Media.ContentType)
				case *PendingPart:
					actual, ok := result.(*PendingPart)
					assert.True(t, ok)
					assert.Equal(t, expected.Metadata["purpose"], actual.Metadata["purpose"])
					assert.Equal(t, expected.Metadata["pending"], actual.Metadata["pending"])
				}
			}
		})
	}
}

func TestParseMediaPiece(t *testing.T) {
	t.Run("parse media piece", func(t *testing.T) {
		piece := "<<<dotprompt:media:url>>> https://example.com/image.jpg"
		result, err := parseMediaPart(piece)
		assert.NoError(t, err)
		assert.Equal(t, "https://example.com/image.jpg", result.Media.URL)
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
		assert.NoError(t, err)
		assert.Equal(t, "test", result.Name)
		assert.Equal(t, "test description", result.Description)
		assert.Equal(t, "Template content", result.Template)

		assert.Contains(t, result.Ext, "foo")
		assert.Equal(t, "value", result.Ext["foo"]["bar"])

		assert.Equal(t, "test", result.Raw["name"])
		assert.Equal(t, "test description", result.Raw["description"])
		assert.Equal(t, "value", result.Raw["foo.bar"])
	})

	t.Run("handle document without frontmatter", func(t *testing.T) {
		source := "Just template content"

		result, err := ParseDocument(source)
		assert.NoError(t, err)
		assert.NotNil(t, result.Ext)
		assert.Equal(t, "Just template content", result.Template)
	})

	t.Run("handle invalid yaml frontmatter", func(t *testing.T) {
		source := `---
invalid: : yaml
---
Template content`

		result, err := ParseDocument(source)
		assert.NoError(t, err)
		assert.NotNil(t, result.Ext)
		// When YAML is invalid, return source as template
		assert.Equal(t, source, result.Template)
	})

	t.Run("handle empty frontmatter", func(t *testing.T) {
		source := `---
---
Template content`

		result, err := ParseDocument(source)
		assert.NoError(t, err)
		assert.NotNil(t, result.Ext)
		assert.Equal(t, "Template content", result.Template)
	})

	t.Run("handle multiple namespaced entries", func(t *testing.T) {
		source := `---
foo.bar: value1
foo.baz: value2
qux.quux: value3
---
Template content`

		result, err := ParseDocument(source)
		assert.NoError(t, err)

		assert.Contains(t, result.Ext, "foo")
		assert.Contains(t, result.Ext, "qux")
		assert.Equal(t, "value1", result.Ext["foo"]["bar"])
		assert.Equal(t, "value2", result.Ext["foo"]["baz"])
		assert.Equal(t, "value3", result.Ext["qux"]["quux"])
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
		assert.NoError(t, err)

		// Check that the result is a ParsedPrompt with the expected template
		assert.Equal(t, "Template content", result.Template)

		// Check that each reserved keyword field has the expected value
		// This is the equivalent of the commented-out section in the Python test
		assert.Equal(t, "value-name", result.Name)
		assert.Equal(t, "value-description", result.Description)
		assert.Equal(t, "value-variant", result.Variant)
		assert.Equal(t, "value-version", result.Version)

		// Check that raw contains all the reserved keywords
		for _, keyword := range ReservedMetadataKeywords {
			if keyword == "ext" {
				continue
			}
			assert.Contains(t, result.Raw, keyword)
			assert.Equal(t, "value-"+keyword, result.Raw[keyword])
		}
	})
}
