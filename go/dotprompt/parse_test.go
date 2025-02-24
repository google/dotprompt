// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"regexp"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestRoleAndHistoryMarkerRegex(t *testing.T) {
	t.Run("valid patterns", func(t *testing.T) {
		validPatterns := []string{
			"<<<dotprompt:role:user>>>",
			"<<<dotprompt:role:assistant>>>",
			"<<<dotprompt:role:system>>>",
			"<<<dotprompt:history>>>",
			"<<<dotprompt:role:bot>>>",
			"<<<dotprompt:role:human>>>",
			"<<<dotprompt:role:customer>>>",
		}

		for _, pattern := range validPatterns {
			t.Run(pattern, func(t *testing.T) {
				assert.True(t, RoleAndHistoryMarkerRegex.MatchString(pattern))
			})
		}
	})

	t.Run("invalid patterns", func(t *testing.T) {
		invalidPatterns := []string{
			"<<<dotprompt:role:USER>>>",        // uppercase not allowed
			"<<<dotprompt:role:assistant1>>>",   // numbers not allowed
			"<<<dotprompt:role:>>>",            // needs at least one letter
			"<<<dotprompt:role>>>",             // missing role value
			"<<<dotprompt:history123>>>",       // history should be exact
			"<<<dotprompt:HISTORY>>>",          // history must be lowercase
			"dotprompt:role:user",              // missing brackets
			"<<<dotprompt:role:user",           // incomplete closing
			"dotprompt:role:user>>>",           // incomplete opening
		}

		for _, pattern := range invalidPatterns {
			t.Run(pattern, func(t *testing.T) {
				assert.False(t, RoleAndHistoryMarkerRegex.MatchString(pattern))
			})
		}
	})

	t.Run("multiple occurrences", func(t *testing.T) {
		text := `
			<<<dotprompt:role:user>>> Hello
			<<<dotprompt:role:assistant>>> Hi there
			<<<dotprompt:history>>>
			<<<dotprompt:role:user>>> How are you?
		`
		matches := RoleAndHistoryMarkerRegex.FindAllString(text, -1)
		assert.Len(t, matches, 4)
	})
}

func TestMediaAndSectionMarkerRegex(t *testing.T) {
	t.Run("valid patterns", func(t *testing.T) {
		validPatterns := []string{
			"<<<dotprompt:media:url>>>",
			"<<<dotprompt:section>>>",
		}

		for _, pattern := range validPatterns {
			t.Run(pattern, func(t *testing.T) {
				assert.True(t, MediaAndSectionMarkerRegex.MatchString(pattern))
			})
		}
	})

	t.Run("matches in text", func(t *testing.T) {
		text := `
			<<<dotprompt:media:url>>> https://example.com/image.jpg
			<<<dotprompt:section>>> Section 1
			<<<dotprompt:media:url>>> https://example.com/video.mp4
			<<<dotprompt:section>>> Section 2
		`
		matches := MediaAndSectionMarkerRegex.FindAllString(text, -1)
		assert.Len(t, matches, 4)
	})
}

func TestSplitByRoleAndHistoryMarkers(t *testing.T) {
	t.Run("no markers", func(t *testing.T) {
		input := "Hello World"
		output := SplitByRoleAndHistoryMarkers(input)
		assert.Equal(t, []string{"Hello World"}, output)
	})

	t.Run("single marker", func(t *testing.T) {
		input := "Hello <<<dotprompt:role:assistant>>> world"
		output := SplitByRoleAndHistoryMarkers(input)
		assert.Equal(t, []string{"Hello ", "<<<dotprompt:role:assistant", " world"}, output)
	})

	t.Run("empty and whitespace", func(t *testing.T) {
		input := "  <<<dotprompt:role:system>>>   "
		output := SplitByRoleAndHistoryMarkers(input)
		assert.Equal(t, []string{"<<<dotprompt:role:system"}, output)
	})

	t.Run("adjacent markers", func(t *testing.T) {
		input := "<<<dotprompt:role:user>>><<<dotprompt:history>>>"
		output := SplitByRoleAndHistoryMarkers(input)
		assert.Equal(t, []string{"<<<dotprompt:role:user", "<<<dotprompt:history"}, output)
	})

	t.Run("invalid uppercase", func(t *testing.T) {
		input := "<<<dotprompt:ROLE:user>>>"
		output := SplitByRoleAndHistoryMarkers(input)
		assert.Equal(t, []string{"<<<dotprompt:ROLE:user>>>"}, output)
	})

	t.Run("multiple markers with text", func(t *testing.T) {
		input := "Start <<<dotprompt:role:user>>> middle <<<dotprompt:history>>> end"
		output := SplitByRoleAndHistoryMarkers(input)
		assert.Equal(t, []string{
			"Start ",
			"<<<dotprompt:role:user",
			" middle ",
			"<<<dotprompt:history",
			" end",
		}, output)
	})
}

func TestConvertNamespacedEntryToNestedObject(t *testing.T) {
	t.Run("create nested object", func(t *testing.T) {
		result := ConvertNamespacedEntryToNestedObject("foo.bar", "hello", nil)
		assert.Equal(t, map[string]map[string]interface{}{
			"foo": {"bar": "hello"},
		}, result)
	})

	t.Run("add to existing namespace", func(t *testing.T) {
		existing := map[string]map[string]interface{}{
			"foo": {"bar": "hello"},
		}
		result := ConvertNamespacedEntryToNestedObject("foo.baz", "world", existing)
		assert.Equal(t, map[string]map[string]interface{}{
			"foo": {
				"bar": "hello",
				"baz": "world",
			},
		}, result)
	})

	t.Run("multiple namespaces", func(t *testing.T) {
		result := ConvertNamespacedEntryToNestedObject("foo.bar", "hello", nil)
		finalResult := ConvertNamespacedEntryToNestedObject("baz.qux", "world", result)
		assert.Equal(t, map[string]map[string]interface{}{
			"foo": {"bar": "hello"},
			"baz": {"qux": "world"},
		}, finalResult)
	})
}

func TestFrontmatterAndBodyRegex(t *testing.T) {
	t.Run("match document with frontmatter", func(t *testing.T) {
		source := "---\nfoo: bar\n---\nThis is the body."
		match := FrontmatterAndBodyRegex.FindStringSubmatch(source)
		assert.NotNil(t, match)
		assert.Equal(t, source, match[0])
		assert.Equal(t, "foo: bar", match[1])
		assert.Equal(t, "This is the body.", match[2])
	})

	t.Run("match with extra spaces", func(t *testing.T) {
		source := "---   \n   title: Test   \n---   \nContent here."
		match := FrontmatterAndBodyRegex.FindStringSubmatch(source)
		assert.NotNil(t, match)
		assert.Equal(t, source, match[0])
		assert.Equal(t, "   title: Test   ", match[1])
		assert.Equal(t, "Content here.", match[2])
	})

	t.Run("no frontmatter", func(t *testing.T) {
		source := "No frontmatter here."
		match := FrontmatterAndBodyRegex.FindStringSubmatch(source)
		assert.Nil(t, match)
	})
}

func TestExtractFrontmatterAndBody(t *testing.T) {
	t.Run("extract both parts", func(t *testing.T) {
		source := "---\nfoo: bar\n---\nThis is the body."
		frontmatter, body := ExtractFrontmatterAndBody(source)
		assert.Equal(t, "foo: bar", frontmatter)
		assert.Equal(t, "This is the body.", body)
	})

	t.Run("no frontmatter", func(t *testing.T) {
		source := "No frontmatter here."
		frontmatter, body := ExtractFrontmatterAndBody(source)
		assert.Equal(t, "", frontmatter)
		assert.Equal(t, "", body)
	})
}

func TestSplitByMediaAndSectionMarkers(t *testing.T) {
	t.Run("no markers", func(t *testing.T) {
		source := "This is a test string."
		parts := SplitByMediaAndSectionMarkers(source)
		assert.Equal(t, []string{"This is a test string."}, parts)
	})

	t.Run("with markers", func(t *testing.T) {
		source := "Hello <<<dotprompt:media:url>>> World <<<dotprompt:section>>>!"
		parts := SplitByMediaAndSectionMarkers(source)
		assert.Equal(t, []string{
			"Hello ",
			"<<<dotprompt:media:url",
			" World ",
			"<<<dotprompt:section",
			"!",
		}, parts)
	})
}

func TestTransformMessagesToHistory(t *testing.T) {
	t.Run("add history purpose", func(t *testing.T) {
		messages := []Message{
			{Content: []Part{&TextPart{Text: "Hello"}}},
			{Content: []Part{&TextPart{Text: "World"}}},
		}
		result := transformMessagesToHistory(messages)
		assert.Len(t, result, 2)
		assert.Equal(t, "history", result[0].Metadata["purpose"])
		assert.Equal(t, "history", result[1].Metadata["purpose"])
	})

	t.Run("preserve existing metadata", func(t *testing.T) {
		messages := []Message{
			{
				Content:  []Part{&TextPart{Text: "Test"}},
				Metadata: map[string]interface{}{"foo": "bar"},
			},
		}
		result := transformMessagesToHistory(messages)
		assert.Len(t, result, 1)
		assert.Equal(t, "bar", result[0].Metadata["foo"])
		assert.Equal(t, "history", result[0].Metadata["purpose"])
	})

	t.Run("empty array", func(t *testing.T) {
		result := transformMessagesToHistory(nil)
		assert.Empty(t, result)
	})
}

func TestSplitByRegex(t *testing.T) {
	t.Run("split and filter", func(t *testing.T) {
		source := "  one  ,  ,  two  ,  three  "
		result := SplitByRegex(source, regexp.MustCompile(`,`))
		assert.Equal(t, []string{"  one  ", "  two  ", "  three  "}, result)
	})

	t.Run("no matches", func(t *testing.T) {
		source := "no matches here"
		result := SplitByRegex(source, regexp.MustCompile(`,`))
		assert.Equal(t, []string{"no matches here"}, result)
	})

	t.Run("empty string", func(t *testing.T) {
		result := SplitByRegex("", regexp.MustCompile(`,`))
		assert.Empty(t, result)
	})
}

func TestInsertHistory(t *testing.T) {
	t.Run("with existing history marker", func(t *testing.T) {
		messages := []Message{
			{Role: RoleUser, Content: []Part{&TextPart{Text: "first"}}},
			{
				Role:     RoleModel,
				Content:  []Part{&TextPart{Text: "second"}},
				Metadata: map[string]interface{}{"purpose": "history"},
			},
			{Role: RoleUser, Content: []Part{&TextPart{Text: "third"}}},
		}
		history := []Message{
			{Role: RoleUser, Content: []Part{&TextPart{Text: "past1"}}},
			{Role: RoleModel, Content: []Part{&TextPart{Text: "past2"}}},
		}
		result := InsertHistory(messages, history)
		assert.Equal(t, messages, result)
	})

	t.Run("empty history", func(t *testing.T) {
		messages := []Message{
			{Role: RoleUser, Content: []Part{&TextPart{Text: "first"}}},
			{Role: RoleUser, Content: []Part{&TextPart{Text: "second"}}},
		}
		result := InsertHistory(messages, nil)
		assert.Equal(t, messages, result)
	})

	t.Run("append history without trailing user", func(t *testing.T) {
		messages := []Message{
			{Role: RoleUser, Content: []Part{&TextPart{Text: "first"}}},
			{Role: RoleModel, Content: []Part{&TextPart{Text: "second"}}},
		}
		history := []Message{
			{Role: RoleUser, Content: []Part{&TextPart{Text: "past1"}}},
			{Role: RoleModel, Content: []Part{&TextPart{Text: "past2"}}},
		}
		result := InsertHistory(messages, history)
		expected := append(messages, history...)
		assert.Equal(t, expected, result)
	})
}

func TestToParts(t *testing.T) {
	t.Run("no markers", func(t *testing.T) {
		source := "This is a test string."
		parts := ToParts(source)
		assert.Len(t, parts, 1)
		textPart, ok := parts[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "This is a test string.", textPart.Text)
	})

	t.Run("media marker", func(t *testing.T) {
		source := "<<<dotprompt:media:url>>> https://example.com/image.jpg image/jpeg"
		parts := ToParts(source)
		assert.Len(t, parts, 1)
		mediaPart, ok := parts[0].(*MediaPart)
		assert.True(t, ok)
		assert.Equal(t, "https://example.com/image.jpg", mediaPart.Media.URL)
		assert.Equal(t, "image/jpeg", *mediaPart.Media.ContentType)
	})

	t.Run("section marker", func(t *testing.T) {
		source := "<<<dotprompt:section>>> test"
		parts := ToParts(source)
		assert.Len(t, parts, 1)
		pendingPart, ok := parts[0].(*PendingPart)
		assert.True(t, ok)
		assert.True(t, pendingPart.Metadata["pending"].(bool))
	})
}
