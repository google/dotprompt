// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestHasMetadata(t *testing.T) {
	t.Run("test creating HasMetadata", func(t *testing.T) {
		hasMetadata := HasMetadata{
			Metadata: Metadata{
				"key": "value",
			},
		}
		assert.Equal(t, Metadata{
			"key": "value",
		}, hasMetadata.Metadata)
	})

	t.Run("test setting metadata", func(t *testing.T) {
		hasMetadata := HasMetadata{}
		hasMetadata.SetMetadata("key", "value")
		assert.Equal(t, Metadata{
			"key": "value",
		}, hasMetadata.Metadata)
	})

	t.Run("test getting metadata", func(t *testing.T) {
		hasMetadata := HasMetadata{
			Metadata: Metadata{
				"key": "value",
			},
		}
		assert.Equal(t, Metadata{
			"key": "value",
		}, hasMetadata.GetMetadata())
	})
}

func TestDerivedMetadata(t *testing.T) {
	t.Run("test derived metadata", func(t *testing.T) {
		type derivedMetadata struct {
			HasMetadata
		}
		d := derivedMetadata{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
		}
		assert.Equal(t, Metadata{
			"key": "value",
		}, d.GetMetadata())
		assert.Equal(t, Metadata{
			"key": "value",
		}, d.Metadata)

		d.SetMetadata("key2", "value2")
		assert.Equal(t, Metadata{
			"key":  "value",
			"key2": "value2",
		}, d.GetMetadata())
		assert.Equal(t, Metadata{
			"key":  "value",
			"key2": "value2",
		}, d.Metadata)
	})
}

func TestIsToolArgument(t *testing.T) {
	t.Run("test is valid tool argument", func(t *testing.T) {
		assert.True(t, IsToolArgument("tool"))
		assert.True(t, IsToolArgument(ToolDefinition{}))
	})

	t.Run("test is invalid tool argument", func(t *testing.T) {
		assert.False(t, IsToolArgument(1))
		assert.False(t, IsToolArgument(1.0))
		assert.False(t, IsToolArgument(true))
		assert.False(t, IsToolArgument(false))
		assert.False(t, IsToolArgument(nil))
		assert.False(t, IsToolArgument(map[string]any{}))
		assert.False(t, IsToolArgument([]any{}))
		assert.False(t, IsToolArgument(func() {}))
	})
}

func TestPendingPart(t *testing.T) {
	t.Run("test NewPendingPart", func(t *testing.T) {
		pendingPart := NewPendingPart()
		assert.NotNil(t, pendingPart)
		assert.NotNil(t, pendingPart.Metadata)
		assert.True(t, pendingPart.IsPending())
		assert.Equal(t, true, pendingPart.Metadata["pending"])
	})

	t.Run("test IsPending", func(t *testing.T) {
		// Test with pending set to true
		pendingPart := &PendingPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"pending": true,
				},
			},
		}
		assert.True(t, pendingPart.IsPending())

		// Test with pending set to false
		pendingPart = &PendingPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"pending": false,
				},
			},
		}
		assert.False(t, pendingPart.IsPending())

		// Test with pending not set
		pendingPart = &PendingPart{
			HasMetadata: HasMetadata{},
		}
		assert.False(t, pendingPart.IsPending())

		// Test with pending set to non-bool value
		pendingPart = &PendingPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"pending": "true",
				},
			},
		}
		assert.False(t, pendingPart.IsPending())
	})

	t.Run("test SetPending", func(t *testing.T) {
		pendingPart := &PendingPart{}

		// Test setting to true
		pendingPart.SetPending(true)
		assert.True(t, pendingPart.IsPending())
		assert.Equal(t, true, pendingPart.Metadata["pending"])

		// Test setting to false
		pendingPart.SetPending(false)
		assert.False(t, pendingPart.IsPending())
		assert.Equal(t, false, pendingPart.Metadata["pending"])
	})
}

func TestTextPart(t *testing.T) {
	t.Run("test TextPart creation and access", func(t *testing.T) {
		textPart := &TextPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
			Text: "Hello, world!",
		}

		assert.Equal(t, "Hello, world!", textPart.Text)
		assert.Equal(t, Metadata{"key": "value"}, textPart.GetMetadata())

		// Test Part interface compliance
		var part Part = textPart
		assert.Equal(t, Metadata{"key": "value"}, part.GetMetadata())
	})
}

func TestDataPart(t *testing.T) {
	t.Run("test DataPart creation and access", func(t *testing.T) {
		dataPart := &DataPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
			Data: map[string]any{
				"name": "John",
				"age":  30,
			},
		}

		assert.Equal(t, map[string]any{"name": "John", "age": 30}, dataPart.Data)
		assert.Equal(t, Metadata{"key": "value"}, dataPart.GetMetadata())

		// Test Part interface compliance
		var part Part = dataPart
		assert.Equal(t, Metadata{"key": "value"}, part.GetMetadata())
	})
}

func TestMediaPart(t *testing.T) {
	t.Run("test MediaPart creation and access", func(t *testing.T) {
		mediaPart := &MediaPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
		}
		mediaPart.Media.URL = "https://example.com/image.jpg"
		mediaPart.Media.ContentType = "image/jpeg"

		assert.Equal(t, "https://example.com/image.jpg", mediaPart.Media.URL)
		assert.Equal(t, "image/jpeg", mediaPart.Media.ContentType)
		assert.Equal(t, Metadata{"key": "value"}, mediaPart.GetMetadata())

		// Test Part interface compliance
		var part Part = mediaPart
		assert.Equal(t, Metadata{"key": "value"}, part.GetMetadata())
	})
}

func TestToolRequestPart(t *testing.T) {
	t.Run("test ToolRequestPart creation and access", func(t *testing.T) {
		toolRequestPart := &ToolRequestPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
			ToolRequest: map[string]any{
				"name": "calculator",
				"args": map[string]any{
					"a": 1,
					"b": 2,
				},
			},
		}

		assert.Equal(t, map[string]any{
			"name": "calculator",
			"args": map[string]any{
				"a": 1,
				"b": 2,
			},
		}, toolRequestPart.ToolRequest)
		assert.Equal(t, Metadata{"key": "value"}, toolRequestPart.GetMetadata())

		// Test Part interface compliance
		var part Part = toolRequestPart
		assert.Equal(t, Metadata{"key": "value"}, part.GetMetadata())
	})
}

func TestToolResponsePart(t *testing.T) {
	t.Run("test ToolResponsePart creation and access", func(t *testing.T) {
		toolResponsePart := &ToolResponsePart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
			ToolResponse: map[string]any{
				"result": 3,
			},
		}

		assert.Equal(t, map[string]any{"result": 3}, toolResponsePart.ToolResponse)
		assert.Equal(t, Metadata{"key": "value"}, toolResponsePart.GetMetadata())

		// Test Part interface compliance
		var part Part = toolResponsePart
		assert.Equal(t, Metadata{"key": "value"}, part.GetMetadata())
	})
}

func TestMessage(t *testing.T) {
	t.Run("test Message creation and access", func(t *testing.T) {
		message := Message{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
			Role: RoleUser,
			Content: []Part{
				&TextPart{
					Text: "Hello, world!",
				},
			},
		}

		assert.Equal(t, RoleUser, message.Role)
		assert.Len(t, message.Content, 1)
		textPart, ok := message.Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Hello, world!", textPart.Text)
		assert.Equal(t, Metadata{"key": "value"}, message.GetMetadata())
	})

	t.Run("test predefined roles", func(t *testing.T) {
		assert.Equal(t, Role("user"), RoleUser)
		assert.Equal(t, Role("model"), RoleModel)
		assert.Equal(t, Role("tool"), RoleTool)
		assert.Equal(t, Role("system"), RoleSystem)
	})
}

func TestDocument(t *testing.T) {
	t.Run("test Document creation and access", func(t *testing.T) {
		document := Document{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"key": "value",
				},
			},
			Content: []Part{
				&TextPart{
					Text: "Document content",
				},
			},
		}

		assert.Len(t, document.Content, 1)
		textPart, ok := document.Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Document content", textPart.Text)
		assert.Equal(t, Metadata{"key": "value"}, document.GetMetadata())
	})
}

func TestDataArgument(t *testing.T) {
	t.Run("test DataArgument creation and access", func(t *testing.T) {
		dataArg := DataArgument{
			Input: map[string]any{
				"query": "How to make pancakes?",
			},
			Docs: []Document{
				{
					Content: []Part{
						&TextPart{Text: "Pancake recipe"},
					},
				},
			},
			Messages: []Message{
				{
					Role: RoleUser,
					Content: []Part{
						&TextPart{Text: "I want to make pancakes"},
					},
				},
			},
			Context: map[string]any{
				"state": "cooking",
			},
		}

		assert.Equal(t, "How to make pancakes?", dataArg.Input["query"])
		assert.Len(t, dataArg.Docs, 1)
		assert.Len(t, dataArg.Messages, 1)
		assert.Equal(t, "cooking", dataArg.Context["state"])

		// Check document content
		textPart, ok := dataArg.Docs[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Pancake recipe", textPart.Text)

		// Check message content
		assert.Equal(t, RoleUser, dataArg.Messages[0].Role)
		msgTextPart, ok := dataArg.Messages[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "I want to make pancakes", msgTextPart.Text)
	})
}

func TestPromptRef(t *testing.T) {
	t.Run("test PromptRef creation and access", func(t *testing.T) {
		promptRef := PromptRef{
			Name:    "test-prompt",
			Variant: "v1",
			Version: "1.0.0",
		}

		assert.Equal(t, "test-prompt", promptRef.Name)
		assert.Equal(t, "v1", promptRef.Variant)
		assert.Equal(t, "1.0.0", promptRef.Version)
	})
}

func TestPromptData(t *testing.T) {
	t.Run("test PromptData creation and access", func(t *testing.T) {
		promptData := PromptData{
			PromptRef: PromptRef{
				Name:    "test-prompt",
				Variant: "v1",
				Version: "1.0.0",
			},
			Source: "This is a test prompt template",
		}

		assert.Equal(t, "test-prompt", promptData.Name)
		assert.Equal(t, "v1", promptData.Variant)
		assert.Equal(t, "1.0.0", promptData.Version)
		assert.Equal(t, "This is a test prompt template", promptData.Source)
	})
}

func TestPartialRef(t *testing.T) {
	t.Run("test PartialRef creation and access", func(t *testing.T) {
		partialRef := PartialRef{
			Name:    "test-partial",
			Variant: "v1",
			Version: "1.0.0",
		}

		assert.Equal(t, "test-partial", partialRef.Name)
		assert.Equal(t, "v1", partialRef.Variant)
		assert.Equal(t, "1.0.0", partialRef.Version)
	})
}

func TestPartialData(t *testing.T) {
	t.Run("test PartialData creation and access", func(t *testing.T) {
		partialData := PartialData{
			PartialRef: PartialRef{
				Name:    "test-partial",
				Variant: "v1",
				Version: "1.0.0",
			},
			Source: "This is a test partial template",
		}

		assert.Equal(t, "test-partial", partialData.Name)
		assert.Equal(t, "v1", partialData.Variant)
		assert.Equal(t, "1.0.0", partialData.Version)
		assert.Equal(t, "This is a test partial template", partialData.Source)
	})
}

func TestRenderedPrompt(t *testing.T) {
	t.Run("test RenderedPrompt creation and access", func(t *testing.T) {
		renderedPrompt := RenderedPrompt{
			PromptMetadata: PromptMetadata{
				Name:        "test-prompt",
				Description: "A test prompt",
				Model:       "test-model",
			},
			Messages: []Message{
				{
					Role: RoleUser,
					Content: []Part{
						&TextPart{Text: "Hello"},
					},
				},
				{
					Role: RoleModel,
					Content: []Part{
						&TextPart{Text: "Hi there!"},
					},
				},
			},
		}

		assert.Equal(t, "test-prompt", renderedPrompt.Name)
		assert.Equal(t, "A test prompt", renderedPrompt.Description)
		assert.Equal(t, "test-model", renderedPrompt.Model)
		assert.Len(t, renderedPrompt.Messages, 2)

		// Check first message
		assert.Equal(t, RoleUser, renderedPrompt.Messages[0].Role)
		userTextPart, ok := renderedPrompt.Messages[0].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Hello", userTextPart.Text)

		// Check second message
		assert.Equal(t, RoleModel, renderedPrompt.Messages[1].Role)
		modelTextPart, ok := renderedPrompt.Messages[1].Content[0].(*TextPart)
		assert.True(t, ok)
		assert.Equal(t, "Hi there!", modelTextPart.Text)
	})
}

func TestPromptBundle(t *testing.T) {
	t.Run("test PromptBundle creation and access", func(t *testing.T) {
		bundle := PromptBundle{
			Partials: []PartialData{
				{
					PartialRef: PartialRef{
						Name: "test-partial",
					},
					Source: "Partial content",
				},
			},
			Prompts: []PromptData{
				{
					PromptRef: PromptRef{
						Name: "test-prompt",
					},
					Source: "Prompt content",
				},
			},
		}

		assert.Len(t, bundle.Partials, 1)
		assert.Len(t, bundle.Prompts, 1)
		assert.Equal(t, "test-partial", bundle.Partials[0].Name)
		assert.Equal(t, "Partial content", bundle.Partials[0].Source)
		assert.Equal(t, "test-prompt", bundle.Prompts[0].Name)
		assert.Equal(t, "Prompt content", bundle.Prompts[0].Source)
	})
}
