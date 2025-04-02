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
	"github.com/invopop/jsonschema"
)

// Schema represents a generic schema definition.
type Schema any

// ToolDefinition defines a tool that can be used in a prompt.
type ToolDefinition struct {
	Name         string `json:"name"`
	Description  string `json:"description,omitempty"`
	InputSchema  Schema `json:"inputSchema"`
	OutputSchema Schema `json:"outputSchema,omitempty"`
}

// ToolArgument can be either a string or a ToolDefinition.
type ToolArgument any

// IsToolArgument returns true if the argument is a string or a ToolDefinition.
func IsToolArgument(arg any) bool {
	_, okString := arg.(string)
	if okString {
		return true
	}
	_, okDefinition := arg.(ToolDefinition)
	return okDefinition
}

// Metadata is a generic map of string keys to any values.
type Metadata map[string]any

// HasMetadata is a struct that can be embedded in other types to provide
// metadata.
type HasMetadata struct {
	Metadata Metadata `json:"metadata,omitempty"`
}

// SetMetadata sets the metadata for a struct that embeds HasMetadata.
func (h *HasMetadata) SetMetadata(key string, value any) {
	if h.Metadata == nil {
		h.Metadata = Metadata{}
	}
	h.Metadata[key] = value
}

// GetMetadata returns the metadata for a struct that embeds HasMetadata.
// This allows HasMetadata to be used with the Part interface.
func (h *HasMetadata) GetMetadata() Metadata {
	return h.Metadata
}

// PromptRef references a prompt in a store.
type PromptRef struct {
	Name    string `json:"name"`
	Variant string `json:"variant,omitempty"`
	Version string `json:"version,omitempty"`
}

// PromptData represents a prompt with its source content.
type PromptData struct {
	PromptRef
	Source string `json:"source"`
}

// ModelConfig represents model-specific configuration.
//
// See: Definition for ModelConfig as PromptMetadata generic type in types.d.ts
// for more information.
type ModelConfig map[string]any

// Input represents the configuration for input variables.
type PromptMetadataInput struct {
	Default map[string]any `json:"default,omitempty"`
	Schema  Schema         `json:"schema,omitempty"`
}

// Output represents the desired output format for a prompt.
type PromptMetadataOutput struct {
	Format string `json:"format,omitempty"`
	Schema Schema `json:"schema,omitempty"`
}

// PromptMetadata contains metadata about a prompt.
type PromptMetadata struct {
	HasMetadata
	// The name of the prompt.
	Name string `json:"name,omitempty"`
	// The variant name for the prompt.
	Variant string `json:"variant,omitempty"`
	// The version of the prompt.
	Version string `json:"version,omitempty"`
	// A description of the prompt.
	Description string `json:"description,omitempty"`
	// The name of the model to use for this prompt, e.g. `vertexai/gemini-1.0-pro`
	Model string `json:"model,omitempty"`
	// Names of tools (registered separately) to allow use of in this prompt.
	Tools []string `json:"tools,omitempty"`
	// Definitions of tools to allow use of in this prompt.
	ToolDefs []ToolDefinition `json:"toolDefs,omitempty"`
	// Model configuration. Not all models support all options.
	Config ModelConfig `json:"config,omitempty"`
	// Configuration for input variables.
	Input PromptMetadataInput `json:"input,omitempty"`
	// Defines the expected model output format.
	Output PromptMetadataOutput `json:"output,omitempty"`
	// This field will contain the raw frontmatter as parsed with no additional
	// processing or substitutions. If your implementation requires custom
	// fields they will be available here.
	Raw map[string]any `json:"raw,omitempty"`
	// Fields that contain a period will be considered "extension fields" in the
	// frontmatter and will be gathered by namespace. For example, `myext.foo:
	// 123` would be available at `parsedPrompt.ext.myext.foo`. Nested
	// namespaces will be flattened, so `myext.foo.bar: 123` would be available
	// at `parsedPrompt.ext["myext.foo"].bar`.
	Ext map[string]map[string]any `json:"ext,omitempty"`
}

// ParsedPrompt represents a parsed prompt template with metadata.
type ParsedPrompt struct {
	PromptMetadata
	// The source of the template with metadata / frontmatter already removed.
	Template string `json:"template"`
}

// Part represents a part of a message content.
type Part interface {
	// Each Part must embed HasMetadata
	GetMetadata() Metadata
}

// TextPart represents a text part of a message.
type TextPart struct {
	HasMetadata
	Text string `json:"text"`
}

// DataPart represents a data part of a message.
type DataPart struct {
	HasMetadata
	Data map[string]any `json:"data"`
}

// Media represents a media part of a message.
type Media struct {
	URL         string `json:"url"`
	ContentType string `json:"contentType,omitempty"`
}

// MediaPart represents a media part of a message.
type MediaPart struct {
	HasMetadata
	Media Media `json:"media"`
}

// ToolRequestPart represents a tool request part of a message.
type ToolRequestPart struct {
	HasMetadata
	ToolRequest map[string]any `json:"toolRequest"`
}

// ToolResponsePart represents a tool response part of a message.
type ToolResponsePart struct {
	HasMetadata
	ToolResponse map[string]any `json:"toolResponse"`
}

// PendingPart represents a pending part of a message.
type PendingPart struct {
	HasMetadata
}

// NewPendingPart creates a new PendingPart with the pending flag set to true.
func NewPendingPart() *PendingPart {
	return &PendingPart{
		HasMetadata: HasMetadata{
			Metadata: map[string]any{
				"pending": true,
			},
		},
	}
}

// IsPending returns true if the pending flag is set to true.
func (p *PendingPart) IsPending() bool {
	pendingValue, ok := p.Metadata["pending"]
	if !ok {
		return false
	}
	pending, ok := pendingValue.(bool)
	if !ok {
		return false
	}
	return pending
}

// SetPending sets the pending flag to the given value.
func (p *PendingPart) SetPending(enabled bool) {
	if p.Metadata == nil {
		p.Metadata = Metadata{}
	}
	p.Metadata["pending"] = enabled
}

// Role represents the role of a message in a conversation.
type Role string

// Predefined roles.
const (
	RoleModel  Role = "model"
	RoleSystem Role = "system"
	RoleTool   Role = "tool"
	RoleUser   Role = "user"
)

// Message represents a message in a conversation.
type Message struct {
	HasMetadata
	Role    Role   `json:"role"`
	Content []Part `json:"content"`
}

// Document represents a document with content parts.
type Document struct {
	HasMetadata
	Content []Part `json:"content"`
}

// DataArgument provides all of the information necessary to render a template
// at runtime.
type DataArgument struct {
	// Input variables for the prompt template.
	Input map[string]any `json:"input,omitempty"`
	// Relevant documents.
	Docs []Document `json:"docs,omitempty"`
	// Previous messages in the history of a multi-turn conversation.
	Messages []Message `json:"messages,omitempty"`
	// Items in the context argument are exposed as `@` variables, e.g.
	// `context: {state: {...}}` is exposed as `@state`.
	Context map[string]any `json:"context,omitempty"`
}

// SchemaResolver is a function that resolves a schema name to a JSON schema.
type SchemaResolver func(schemaName string) (*jsonschema.Schema, error)

// ToolResolver is a function that resolves a tool name to a tool definition.
type ToolResolver func(toolName string) (ToolDefinition, error)

// RenderedPrompt is the final result of rendering a Dotprompt template.
type RenderedPrompt struct {
	PromptMetadata
	Messages []Message `json:"messages"`
}

// PromptFunction is a function that takes runtime data/context and returns a
// rendered prompt.
type PromptFunction func(data *DataArgument, options *PromptMetadata) (RenderedPrompt, error)

// PromptRefFunction is a function that takes runtime data/context and returns a
// rendered prompt after loading a prompt via reference.
type PromptRefFunction func(data DataArgument, options PromptMetadata) (RenderedPrompt, error)

// PaginatedResponse represents a paginated response.
type PaginatedResponse struct {
	Cursor string `json:"cursor,omitempty"`
}

// PartialRef references a partial in a store.
type PartialRef struct {
	Name    string `json:"name"`
	Variant string `json:"variant,omitempty"`
	Version string `json:"version,omitempty"`
}

// PartialData represents a partial with its source content.
type PartialData struct {
	PartialRef
	Source string `json:"source"`
}

// ListPromptsOptions represents options for listing prompts or partials.
type ListPromptsOptions struct {
	Cursor string
	Limit  int
}

// ListPromptsResult represents a list of items and a cursor.
type ListPromptsResult[T any] struct {
	Items  []T
	Cursor string `json:"cursor,omitempty"`
}

// ListPartialsOptions represents options for listing partials.
type ListPartialsOptions struct {
	Cursor string
	Limit  int
}

// ListPartialsResult represents a list of partials and a cursor.
type ListPartialsResult[T any] struct {
	Items  []T
	Cursor string `json:"cursor,omitempty"`
}

// LoadPromptOptions represents options for loading a prompt.
type LoadPromptOptions struct {
	Variant string
	Version string
}

// LoadPartialOptions represents options for loading a partial.
type LoadPartialOptions struct {
	Variant string
	Version string
}

// PromptStore is an interface for storing and retrieving prompts.
type PromptStore interface {
	// List returns a list of all prompts in the store (optionally paginated).
	List(options ListPromptsOptions) (ListPromptsResult[PromptRef], error)

	// ListPartials returns a list of partial names available in this store.
	ListPartials(options ListPartialsOptions) (ListPartialsResult[PartialRef], error)

	// Load retrieves a prompt from the store.
	Load(name string, options LoadPromptOptions) (PromptData, error)

	// LoadPartial retrieves a partial from the store.
	LoadPartial(name string, options LoadPartialOptions) (PartialData, error)
}

// PromptStoreDeleteOptions represents options for deleting a prompt or partial.
type PromptStoreDeleteOptions struct {
	Variant string
}

// PromptStoreWritable is a PromptStore that also has built-in methods for
// writing prompts.
type PromptStoreWritable interface {
	PromptStore

	// Save saves a prompt in the store. May be destructive for prompt stores
	// without versioning.
	Save(prompt PromptData) error

	// Delete deletes a prompt from the store.
	Delete(name string, options PromptStoreDeleteOptions) error
}

// PromptBundle represents a bundle of prompts and partials.
type PromptBundle struct {
	Partials []PartialData `json:"partials"`
	Prompts  []PromptData  `json:"prompts"`
}
