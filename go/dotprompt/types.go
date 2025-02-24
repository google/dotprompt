// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

// Schema represents a generic dictionary schema
type Schema = map[string]interface{}

// ToolDefinition defines a tool with its name, description, and schemas
type ToolDefinition struct {
	Name         string  `json:"name"`
	Description  *string `json:"description,omitempty"`
	InputSchema  Schema  `json:"inputSchema"`
	OutputSchema *Schema `json:"outputSchema,omitempty"`
}

// ToolArgument can be either a string or a ToolDefinition
type ToolArgument interface{} // string | *ToolDefinition

// HasMetadata provides metadata functionality
type HasMetadata struct {
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// PromptRef contains reference information for a prompt
type PromptRef struct {
	Name    string  `json:"name"`
	Variant *string `json:"variant,omitempty"`
	Version *string `json:"version,omitempty"`
}

// PromptData extends PromptRef with source information
type PromptData struct {
	PromptRef
	Source string `json:"source"`
}

// PromptMetadata contains metadata for a prompt
type PromptMetadata[ModelConfig any] struct {
	HasMetadata
	Name        *string          `json:"name,omitempty"`
	Variant     *string          `json:"variant,omitempty"`
	Version     *string          `json:"version,omitempty"`
	Description *string          `json:"description,omitempty"`
	Model       *string          `json:"model,omitempty"`
	Tools       []string         `json:"tools,omitempty"`
	ToolDefs    []ToolDefinition `json:"toolDefs,omitempty"`
	Config      *ModelConfig     `json:"config,omitempty"`
	Input       *struct {
		Default *map[string]interface{} `json:"default,omitempty"`
		Schema  *Schema                 `json:"schema,omitempty"`
	} `json:"input,omitempty"`
	Output *struct {
		Format *string `json:"format,omitempty"` // 'json' | 'text' | string
		Schema *Schema `json:"schema,omitempty"`
	} `json:"output,omitempty"`
	Raw map[string]interface{}            `json:"raw,omitempty"`
	Ext map[string]map[string]interface{} `json:"ext,omitempty"`
}

// ParsedPrompt extends PromptMetadata with a template
type ParsedPrompt[ModelConfig any] struct {
	PromptMetadata[ModelConfig]
	Template string `json:"template"`
}

// EmptyPart represents a base part with no content
type EmptyPart struct {
	HasMetadata
	Text         interface{} `json:"-"`
	Data         interface{} `json:"-"`
	Media        interface{} `json:"-"`
	ToolRequest  interface{} `json:"-"`
	ToolResponse interface{} `json:"-"`
}

// TextPart represents text content
type TextPart struct {
	HasMetadata
	Text string `json:"text"`
}

// DataPart represents structured data content
type DataPart struct {
	HasMetadata
	Data map[string]interface{} `json:"data"`
}

// MediaPart represents media content
type MediaPart struct {
	HasMetadata
	Media struct {
		URL         string  `json:"url"`
		ContentType *string `json:"contentType,omitempty"`
	} `json:"media"`
}

// ToolRequestPart represents a tool request
type ToolRequestPart[Input any] struct {
	HasMetadata
	ToolRequest struct {
		Name  string  `json:"name"`
		Input *Input  `json:"input,omitempty"`
		Ref   *string `json:"ref,omitempty"`
	} `json:"toolRequest"`
}

// ToolResponsePart represents a tool response
type ToolResponsePart[Output any] struct {
	HasMetadata
	ToolResponse struct {
		Name   string  `json:"name"`
		Output *Output `json:"output,omitempty"`
		Ref    *string `json:"ref,omitempty"`
	} `json:"toolResponse"`
}

// PendingPart represents a pending operation
type PendingPart struct {
	HasMetadata
	Metadata struct {
		Pending bool                   `json:"pending"`
		Extra   map[string]interface{} `json:",inline"`
	} `json:"metadata"`
}

// Part represents different types of content parts
type Part interface {
	HasMetadata
	IsPart() bool
}

// Ensure all part types implement Part interface
func (*EmptyPart) IsPart()           { return true }
func (*TextPart) IsPart()            { return true }
func (*DataPart) IsPart()            { return true }
func (*MediaPart) IsPart()           { return true }
func (*PendingPart) IsPart()         { return true }
func (*ToolRequestPart[_]) IsPart()  { return true }
func (*ToolResponsePart[_]) IsPart() { return true }

// Role represents different roles in a conversation
type Role string

const (
	RoleUser   Role = "user"
	RoleModel  Role = "model"
	RoleTool   Role = "tool"
	RoleSystem Role = "system"
)

// Message represents a conversation message
type Message struct {
	HasMetadata
	Role    Role   `json:"role"`
	Content []Part `json:"content"`
}

// Document represents a document with content parts
type Document struct {
	HasMetadata
	Content []Part `json:"content"`
}

// DataArgument provides information for template rendering
type DataArgument[Variables any, State any] struct {
	Input    *Variables             `json:"input,omitempty"`
	Docs     []Document             `json:"docs,omitempty"`
	Messages []Message              `json:"messages,omitempty"`
	Context  map[string]interface{} `json:"context,omitempty"`
}

// JSONSchema represents a generic JSON schema
type JSONSchema = interface{}

// SchemaResolver resolves schema names to JSON schemas
type SchemaResolver interface {
	Resolve(schemaName string) (*JSONSchema, error)
}

// ToolResolver resolves tool names to ToolDefinitions
type ToolResolver interface {
	Resolve(toolName string) (*ToolDefinition, error)
}

// RenderedPrompt represents the final result of rendering a template
type RenderedPrompt[ModelConfig any] struct {
	PromptMetadata[ModelConfig]
	Messages []Message `json:"messages"`
}

// PromptFunction defines the interface for prompt rendering
type PromptFunction[ModelConfig any] interface {
	GetPrompt() ParsedPrompt[ModelConfig]
	Render(data DataArgument[interface{}, interface{}], options *PromptMetadata[ModelConfig]) (RenderedPrompt[ModelConfig], error)
}

// PromptRefFunction defines the interface for prompt rendering via reference
type PromptRefFunction[ModelConfig any] interface {
	GetPromptRef() PromptRef
	Render(data DataArgument[interface{}, interface{}], options *PromptMetadata[ModelConfig]) (RenderedPrompt[ModelConfig], error)
}

// PaginatedResponse represents a paginated response
type PaginatedResponse struct {
	Cursor *string `json:"cursor,omitempty"`
}

// PartialRef contains reference information for a partial
type PartialRef struct {
	Name    string  `json:"name"`
	Variant *string `json:"variant,omitempty"`
	Version *string `json:"version,omitempty"`
}

// PartialData extends PartialRef with source information
type PartialData struct {
	PartialRef
	Source string `json:"source"`
}

// PromptBundle contains collections of partials and prompts
type PromptBundle struct {
	Partials []PartialData `json:"partials"`
	Prompts  []PromptData  `json:"prompts"`
}

// PromptStore defines the interface for prompt storage operations
type PromptStore interface {
	// List returns all prompts in the store (optionally paginated)
	List(options *struct {
		Cursor *string `json:"cursor,omitempty"`
		Limit  *int    `json:"limit,omitempty"`
	}) (*struct {
		Prompts []PromptRef `json:"prompts"`
		Cursor  *string     `json:"cursor,omitempty"`
	}, error)

	// ListPartials returns a list of partial names available in this store
	ListPartials(options *struct {
		Cursor *string `json:"cursor,omitempty"`
		Limit  *int    `json:"limit,omitempty"`
	}) (*struct {
		Partials []PartialRef `json:"partials"`
		Cursor   *string      `json:"cursor,omitempty"`
	}, error)

	// Load retrieves a prompt from the store
	Load(name string, options *struct {
		Variant *string `json:"variant,omitempty"`
		Version *string `json:"version,omitempty"`
	}) (*PromptData, error)

	// LoadPartial retrieves a partial from the store
	LoadPartial(name string, options *struct {
		Variant *string `json:"variant,omitempty"`
		Version *string `json:"version,omitempty"`
	}) (*PromptData, error)
}

// PromptStoreWritable extends PromptStore with write operations
type PromptStoreWritable interface {
	PromptStore
	Save(prompt PromptData) error
	Delete(name string, options *struct {
		Variant *string `json:"variant,omitempty"`
	}) error
}

// ModelConfig represents configuration for the model.
type ModelConfig struct {
	Model       string                 `json:"model"`
	Parameters  map[string]interface{} `json:"parameters,omitempty"`
	MaxTokens   *int                  `json:"max_tokens,omitempty"`
	Temperature *float64              `json:"temperature,omitempty"`
}

// Role constants
const (
	RoleUser      = "user"
	RoleModel     = "model"
	RoleSystem    = "system"
	RoleAssistant = "assistant"
	RoleBot       = "bot"
	RoleHuman     = "human"
	RoleCustomer  = "customer"
)
