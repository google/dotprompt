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
	"testing"

	"github.com/google/go-cmp/cmp"
)

func TestHasMetadata(t *testing.T) {
	t.Run("test creating HasMetadata", func(t *testing.T) {
		hasMetadata := HasMetadata{
			Metadata: Metadata{
				"key": "value",
			},
		}
		want := Metadata{"key": "value"}
		if diff := cmp.Diff(want, hasMetadata.Metadata); diff != "" {
			t.Errorf("Metadata mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("test setting metadata", func(t *testing.T) {
		hasMetadata := HasMetadata{}
		hasMetadata.SetMetadata("key", "value")
		want := Metadata{"key": "value"}
		if diff := cmp.Diff(want, hasMetadata.Metadata); diff != "" {
			t.Errorf("Metadata mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("test getting metadata", func(t *testing.T) {
		hasMetadata := HasMetadata{
			Metadata: Metadata{
				"key": "value",
			},
		}
		want := Metadata{"key": "value"}
		if diff := cmp.Diff(want, hasMetadata.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}
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
		want := Metadata{"key": "value"}
		if diff := cmp.Diff(want, d.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}
		if diff := cmp.Diff(want, d.Metadata); diff != "" {
			t.Errorf("Metadata mismatch (-want +got):\n%s", diff)
		}

		d.SetMetadata("key2", "value2")
		want2 := Metadata{
			"key":  "value",
			"key2": "value2",
		}
		if diff := cmp.Diff(want2, d.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() after SetMetadata mismatch (-want +got):\n%s", diff)
		}
		if diff := cmp.Diff(want2, d.Metadata); diff != "" {
			t.Errorf("Metadata after SetMetadata mismatch (-want +got):\n%s", diff)
		}
	})
}

func TestIsToolArgument(t *testing.T) {
	t.Run("test is valid tool argument", func(t *testing.T) {
		if !IsToolArgument("tool") {
			t.Error("IsToolArgument(\"tool\") = false, want true")
		}
		if !IsToolArgument(ToolDefinition{}) {
			t.Error("IsToolArgument(ToolDefinition{}) = false, want true")
		}
	})

	t.Run("test is invalid tool argument", func(t *testing.T) {
		invalidArgs := []any{
			1,
			1.0,
			true,
			false,
			nil,
			map[string]any{},
			[]any{},
			func() {},
		}
		for _, arg := range invalidArgs {
			if IsToolArgument(arg) {
				t.Errorf("IsToolArgument(%v) = true, want false", arg)
			}
		}
	})
}

func TestPendingPart(t *testing.T) {
	t.Run("test NewPendingPart", func(t *testing.T) {
		pendingPart := NewPendingPart()
		if pendingPart == nil {
			t.Fatal("NewPendingPart() returned nil")
		}
		if pendingPart.Metadata == nil {
			t.Fatal("NewPendingPart().Metadata is nil")
		}
		if !pendingPart.IsPending() {
			t.Error("IsPending() = false, want true")
		}
		if got := pendingPart.Metadata["pending"]; got != true {
			t.Errorf("Metadata['pending'] = %v, want true", got)
		}
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
		if !pendingPart.IsPending() {
			t.Error("IsPending() = false, want true")
		}

		// Test with pending set to false
		pendingPart = &PendingPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"pending": false,
				},
			},
		}
		if pendingPart.IsPending() {
			t.Error("IsPending() = true, want false")
		}

		// Test with pending not set
		pendingPart = &PendingPart{
			HasMetadata: HasMetadata{},
		}
		if pendingPart.IsPending() {
			t.Error("IsPending() = true, want false")
		}

		// Test with pending set to non-bool value
		pendingPart = &PendingPart{
			HasMetadata: HasMetadata{
				Metadata: Metadata{
					"pending": "true",
				},
			},
		}
		if pendingPart.IsPending() {
			t.Error("IsPending() = true, want false")
		}
	})

	t.Run("test SetPending", func(t *testing.T) {
		pendingPart := &PendingPart{}

		// Test setting to true
		pendingPart.SetPending(true)
		if !pendingPart.IsPending() {
			t.Error("IsPending() = false, want true")
		}
		if got := pendingPart.Metadata["pending"]; got != true {
			t.Errorf("Metadata['pending'] = %v, want true", got)
		}

		// Test setting to false
		pendingPart.SetPending(false)
		if pendingPart.IsPending() {
			t.Error("IsPending() = true, want false")
		}
		if got := pendingPart.Metadata["pending"]; got != false {
			t.Errorf("Metadata['pending'] = %v, want false", got)
		}
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

		if textPart.Text != "Hello, world!" {
			t.Errorf("Text = %q, want %q", textPart.Text, "Hello, world!")
		}
		wantMeta := Metadata{"key": "value"}
		if diff := cmp.Diff(wantMeta, textPart.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}

		// Test Part interface compliance
		var part Part = textPart
		if diff := cmp.Diff(wantMeta, part.GetMetadata()); diff != "" {
			t.Errorf("part.GetMetadata() mismatch (-want +got):\n%s", diff)
		}
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

		wantData := map[string]any{"name": "John", "age": 30}
		if diff := cmp.Diff(wantData, dataPart.Data); diff != "" {
			t.Errorf("Data mismatch (-want +got):\n%s", diff)
		}
		wantMeta := Metadata{"key": "value"}
		if diff := cmp.Diff(wantMeta, dataPart.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}

		// Test Part interface compliance
		var part Part = dataPart
		if diff := cmp.Diff(wantMeta, part.GetMetadata()); diff != "" {
			t.Errorf("part.GetMetadata() mismatch (-want +got):\n%s", diff)
		}
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

		if mediaPart.Media.URL != "https://example.com/image.jpg" {
			t.Errorf("URL = %q, want %q", mediaPart.Media.URL, "https://example.com/image.jpg")
		}
		if mediaPart.Media.ContentType != "image/jpeg" {
			t.Errorf("ContentType = %q, want %q", mediaPart.Media.ContentType, "image/jpeg")
		}
		wantMeta := Metadata{"key": "value"}
		if diff := cmp.Diff(wantMeta, mediaPart.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}

		// Test Part interface compliance
		var part Part = mediaPart
		if diff := cmp.Diff(wantMeta, part.GetMetadata()); diff != "" {
			t.Errorf("part.GetMetadata() mismatch (-want +got):\n%s", diff)
		}
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

		wantRequest := map[string]any{
			"name": "calculator",
			"args": map[string]any{
				"a": 1,
				"b": 2,
			},
		}
		if diff := cmp.Diff(wantRequest, toolRequestPart.ToolRequest); diff != "" {
			t.Errorf("ToolRequest mismatch (-want +got):\n%s", diff)
		}
		wantMeta := Metadata{"key": "value"}
		if diff := cmp.Diff(wantMeta, toolRequestPart.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}

		// Test Part interface compliance
		var part Part = toolRequestPart
		if diff := cmp.Diff(wantMeta, part.GetMetadata()); diff != "" {
			t.Errorf("part.GetMetadata() mismatch (-want +got):\n%s", diff)
		}
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

		wantResponse := map[string]any{"result": 3}
		if diff := cmp.Diff(wantResponse, toolResponsePart.ToolResponse); diff != "" {
			t.Errorf("ToolResponse mismatch (-want +got):\n%s", diff)
		}
		wantMeta := Metadata{"key": "value"}
		if diff := cmp.Diff(wantMeta, toolResponsePart.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}

		// Test Part interface compliance
		var part Part = toolResponsePart
		if diff := cmp.Diff(wantMeta, part.GetMetadata()); diff != "" {
			t.Errorf("part.GetMetadata() mismatch (-want +got):\n%s", diff)
		}
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

		if message.Role != RoleUser {
			t.Errorf("Role = %q, want %q", message.Role, RoleUser)
		}
		if len(message.Content) != 1 {
			t.Errorf("len(Content) = %d, want 1", len(message.Content))
		}
		textPart, ok := message.Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Content[0] is not *TextPart, got %T", message.Content[0])
		}
		if textPart.Text != "Hello, world!" {
			t.Errorf("Text = %q, want %q", textPart.Text, "Hello, world!")
		}
		wantMeta := Metadata{"key": "value"}
		if diff := cmp.Diff(wantMeta, message.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("test predefined roles", func(t *testing.T) {
		if Role("user") != RoleUser {
			t.Errorf("RoleUser mismatch")
		}
		if Role("model") != RoleModel {
			t.Errorf("RoleModel mismatch")
		}
		if Role("tool") != RoleTool {
			t.Errorf("RoleTool mismatch")
		}
		if Role("system") != RoleSystem {
			t.Errorf("RoleSystem mismatch")
		}
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

		if len(document.Content) != 1 {
			t.Errorf("len(Content) = %d, want 1", len(document.Content))
		}
		textPart, ok := document.Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Content[0] is not *TextPart, got %T", document.Content[0])
		}
		if textPart.Text != "Document content" {
			t.Errorf("Text = %q, want %q", textPart.Text, "Document content")
		}
		wantMeta := Metadata{"key": "value"}
		if diff := cmp.Diff(wantMeta, document.GetMetadata()); diff != "" {
			t.Errorf("GetMetadata() mismatch (-want +got):\n%s", diff)
		}
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

		if dataArg.Input["query"] != "How to make pancakes?" {
			t.Errorf("Input['query'] = %q, want %q", dataArg.Input["query"], "How to make pancakes?")
		}
		if len(dataArg.Docs) != 1 {
			t.Errorf("len(Docs) = %d, want 1", len(dataArg.Docs))
		}
		if len(dataArg.Messages) != 1 {
			t.Errorf("len(Messages) = %d, want 1", len(dataArg.Messages))
		}
		if dataArg.Context["state"] != "cooking" {
			t.Errorf("Context['state'] = %q, want %q", dataArg.Context["state"], "cooking")
		}

		// Check document content
		textPart, ok := dataArg.Docs[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Docs[0].Content[0] is not *TextPart, got %T", dataArg.Docs[0].Content[0])
		}
		if textPart.Text != "Pancake recipe" {
			t.Errorf("Docs text = %q, want %q", textPart.Text, "Pancake recipe")
		}

		// Check message content
		if dataArg.Messages[0].Role != RoleUser {
			t.Errorf("Message Role = %q, want %q", dataArg.Messages[0].Role, RoleUser)
		}
		msgTextPart, ok := dataArg.Messages[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Messages[0].Content[0] is not *TextPart, got %T", dataArg.Messages[0].Content[0])
		}
		if msgTextPart.Text != "I want to make pancakes" {
			t.Errorf("Message text = %q, want %q", msgTextPart.Text, "I want to make pancakes")
		}
	})
}

func TestPromptRef(t *testing.T) {
	t.Run("test PromptRef creation and access", func(t *testing.T) {
		promptRef := PromptRef{
			Name:    "test-prompt",
			Variant: "v1",
			Version: "1.0.0",
		}

		if promptRef.Name != "test-prompt" {
			t.Errorf("Name = %q, want %q", promptRef.Name, "test-prompt")
		}
		if promptRef.Variant != "v1" {
			t.Errorf("Variant = %q, want %q", promptRef.Variant, "v1")
		}
		if promptRef.Version != "1.0.0" {
			t.Errorf("Version = %q, want %q", promptRef.Version, "1.0.0")
		}
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

		if promptData.Name != "test-prompt" {
			t.Errorf("Name = %q, want %q", promptData.Name, "test-prompt")
		}
		if promptData.Variant != "v1" {
			t.Errorf("Variant = %q, want %q", promptData.Variant, "v1")
		}
		if promptData.Version != "1.0.0" {
			t.Errorf("Version = %q, want %q", promptData.Version, "1.0.0")
		}
		if promptData.Source != "This is a test prompt template" {
			t.Errorf("Source = %q, want %q", promptData.Source, "This is a test prompt template")
		}
	})
}

func TestPartialRef(t *testing.T) {
	t.Run("test PartialRef creation and access", func(t *testing.T) {
		partialRef := PartialRef{
			Name:    "test-partial",
			Variant: "v1",
			Version: "1.0.0",
		}

		if partialRef.Name != "test-partial" {
			t.Errorf("Name = %q, want %q", partialRef.Name, "test-partial")
		}
		if partialRef.Variant != "v1" {
			t.Errorf("Variant = %q, want %q", partialRef.Variant, "v1")
		}
		if partialRef.Version != "1.0.0" {
			t.Errorf("Version = %q, want %q", partialRef.Version, "1.0.0")
		}
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

		if partialData.Name != "test-partial" {
			t.Errorf("Name = %q, want %q", partialData.Name, "test-partial")
		}
		if partialData.Variant != "v1" {
			t.Errorf("Variant = %q, want %q", partialData.Variant, "v1")
		}
		if partialData.Version != "1.0.0" {
			t.Errorf("Version = %q, want %q", partialData.Version, "1.0.0")
		}
		if partialData.Source != "This is a test partial template" {
			t.Errorf("Source = %q, want %q", partialData.Source, "This is a test partial template")
		}
	})
}

func TestRenderedPrompt(t *testing.T) {
	t.Run("test RenderedPrompt creation and access", func(t *testing.T) {
		renderedPrompt := RenderedPrompt{
			PromptMetadata: PromptMetadata{
				Name:        "test-prompt",
				Description: "A test prompt",
				Model:       "test-model",
				MaxTurns:    5,
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

		if renderedPrompt.Name != "test-prompt" {
			t.Errorf("Name = %q, want %q", renderedPrompt.Name, "test-prompt")
		}
		if renderedPrompt.Description != "A test prompt" {
			t.Errorf("Description = %q, want %q", renderedPrompt.Description, "A test prompt")
		}
		if renderedPrompt.Model != "test-model" {
			t.Errorf("Model = %q, want %q", renderedPrompt.Model, "test-model")
		}
		if renderedPrompt.MaxTurns != 5 {
			t.Errorf("MaxTurns = %d, want 5", renderedPrompt.MaxTurns)
		}
		if len(renderedPrompt.Messages) != 2 {
			t.Errorf("len(Messages) = %d, want 2", len(renderedPrompt.Messages))
		}

		// Check first message
		if renderedPrompt.Messages[0].Role != RoleUser {
			t.Errorf("Messages[0].Role = %q, want %q", renderedPrompt.Messages[0].Role, RoleUser)
		}
		userTextPart, ok := renderedPrompt.Messages[0].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Messages[0].Content[0] is not *TextPart, got %T", renderedPrompt.Messages[0].Content[0])
		}
		if userTextPart.Text != "Hello" {
			t.Errorf("Messages[0].Text = %q, want %q", userTextPart.Text, "Hello")
		}

		// Check second message
		if renderedPrompt.Messages[1].Role != RoleModel {
			t.Errorf("Messages[1].Role = %q, want %q", renderedPrompt.Messages[1].Role, RoleModel)
		}
		modelTextPart, ok := renderedPrompt.Messages[1].Content[0].(*TextPart)
		if !ok {
			t.Fatalf("Messages[1].Content[0] is not *TextPart, got %T", renderedPrompt.Messages[1].Content[0])
		}
		if modelTextPart.Text != "Hi there!" {
			t.Errorf("Messages[1].Text = %q, want %q", modelTextPart.Text, "Hi there!")
		}
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

		if len(bundle.Partials) != 1 {
			t.Errorf("len(Partials) = %d, want 1", len(bundle.Partials))
		}
		if len(bundle.Prompts) != 1 {
			t.Errorf("len(Prompts) = %d, want 1", len(bundle.Prompts))
		}
		if bundle.Partials[0].Name != "test-partial" {
			t.Errorf("Partials[0].Name = %q, want %q", bundle.Partials[0].Name, "test-partial")
		}
		if bundle.Partials[0].Source != "Partial content" {
			t.Errorf("Partials[0].Source = %q, want %q", bundle.Partials[0].Source, "Partial content")
		}
		if bundle.Prompts[0].Name != "test-prompt" {
			t.Errorf("Prompts[0].Name = %q, want %q", bundle.Prompts[0].Name, "test-prompt")
		}
		if bundle.Prompts[0].Source != "Prompt content" {
			t.Errorf("Prompts[0].Source = %q, want %q", bundle.Prompts[0].Source, "Prompt content")
		}
	})
}
