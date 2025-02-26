package dotprompt

type Schema map[string]interface{}

type ToolDefinition struct {
	Name         string `json:"name"`
	Description  string `json:"description,omitempty"`
	InputSchema  Schema `json:"inputSchema"`
	OutputSchema Schema `json:"outputSchema,omitempty"`
}

type ToolArgument interface{}

type HasMetadata struct {
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

type PromptRef struct {
	Name    string `json:"name"`
	Variant string `json:"variant,omitempty"`
	Version string `json:"version,omitempty"`
}

type PromptData struct {
	PromptRef PromptRef `json:"promptRef"`
	Source    string    `json:"source"`
}

type PromptMetadata struct {
	HasMetadata HasMetadata            `json:"metadata,omitempty"`
	Name        string                 `json:"name,omitempty"`
	Variant     string                 `json:"variant,omitempty"`
	Version     string                 `json:"version,omitempty"`
	Description string                 `json:"description,omitempty"`
	Model       string                 `json:"model,omitempty"`
	Tools       []string               `json:"tools,omitempty"`
	ToolDefs    []ToolDefinition       `json:"toolDefs,omitempty"`
	Config      map[string]interface{} `json:"config,omitempty"`
	Input       struct {
		Default map[string]interface{} `json:"default,omitempty"`
		Schema  Schema                 `json:"schema,omitempty"`
	} `json:"input,omitempty"`
	Output struct {
		Format string `json:"format,omitempty"`
		Schema Schema `json:"schema,omitempty"`
	} `json:"output,omitempty"`
	Raw map[string]interface{}            `json:"raw,omitempty"`
	Ext map[string]map[string]interface{} `json:"ext,omitempty"`
}

type ParsedPrompt struct {
	PromptMetadata PromptMetadata
	Template       string `json:"template"`
}

type EmptyPart struct {
	HasMetadata HasMetadata             `json:"metadata,omitempty"`
	Text        *string                 `json:"text,omitempty"`
	Data        *map[string]interface{} `json:"data,omitempty"`
	Media       *struct {
		URL         string `json:"url"`
		ContentType string `json:"contentType,omitempty"`
	} `json:"media,omitempty"`
	ToolRequest *struct {
		Name  string      `json:"name"`
		Input interface{} `json:"input,omitempty"`
		Ref   string      `json:"ref,omitempty"`
	} `json:"toolRequest,omitempty"`
	ToolResponse *struct {
		Name   string      `json:"name"`
		Output interface{} `json:"output,omitempty"`
		Ref    string      `json:"ref,omitempty"`
	} `json:"toolResponse,omitempty"`
}

type Part struct {
	Text         TextPart               `json:"textpart,omitempty"`
	Data         DataPart               `json:"datapart,omitempty"`
	Media        MediaPart              `json:"mediapart,omitempty"`
	ToolRequest  ToolRequestPart        `json:"toolRequestpart,omitempty"`
	ToolResponse ToolResponsePart       `json:"toolResponsepart,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

type TextPart struct {
	Text string `json:"text"`
}

type DataPart struct {
	Data map[string]interface{} `json:"data"`
}

type MediaType struct {
	URL         string `json:"url"`
	ContentType string `json:"contentType,omitempty"`
}

type MediaPart struct {
	Media MediaType `json:"media"`
}

type ToolRequest struct {
	Name  string      `json:"name"`
	Input interface{} `json:"input,omitempty"`
	Ref   string      `json:"ref,omitempty"`
}

type ToolRequestPart struct {
	ToolRequest ToolRequest `json:"toolRequest"`
}

type ToolResponse struct {
	Name   string      `json:"name"`
	Output interface{} `json:"output,omitempty"`
	Ref    string      `json:"ref,omitempty"`
}

type ToolResponsePart struct {
	ToolResponse ToolResponse `json:"toolResponse"`
}

type Message struct {
	HasMetadata HasMetadata `json:"metadata,omitempty"`
	Role        string      `json:"role"`
	Content     []Part      `json:"content"`
}

type Document struct {
	HasMetadata HasMetadata `json:"metadata,omitempty"`
	Content     []Part      `json:"content"`
}

type DataArgument struct {
	Input    map[string]interface{} `json:"input,omitempty"`
	Docs     []Document             `json:"docs,omitempty"`
	Messages []Message              `json:"messages,omitempty"`
	Context  map[string]interface{} `json:"context,omitempty"`
}

type JSONSchema map[string]interface{}

type SchemaResolver func(schemaName string) (JSONSchema, error)

type ToolResolver func(toolName string) (ToolDefinition, error)

type RenderedPrompt struct {
	PromptMetadata
	Messages []Message `json:"messages"`
}

type PromptFunction func(data DataArgument, options *PromptMetadata) (RenderedPrompt, error)

type PromptRefFunction func(data DataArgument, options *PromptMetadata) (RenderedPrompt, error)

type PaginatedResponse struct {
	Cursor string `json:"cursor,omitempty"`
}

type PartialRef struct {
	Name    string `json:"name"`
	Variant string `json:"variant,omitempty"`
	Version string `json:"version,omitempty"`
}

type PartialData struct {
	PartialRef
	Source string `json:"source"`
}

type PromptStore interface {
	List(options *ListOptions) (ListResponse, error)
	ListPartials(options *ListOptions) (ListPartialsResponse, error)
	Load(name string, options *LoadOptions) (PromptData, error)
	LoadPartial(name string, options *LoadOptions) (PromptData, error)
}

type PromptStoreWritable interface {
	PromptStore
	Save(prompt PromptData) error
	Delete(name string, options *DeleteOptions) error
}

type PromptBundle struct {
	Partials []PartialData `json:"partials"`
	Prompts  []PromptData  `json:"prompts"`
}

type ListOptions struct {
	Cursor string `json:"cursor,omitempty"`
	Limit  int    `json:"limit,omitempty"`
}

type ListResponse struct {
	Prompts []PromptRef `json:"prompts"`
	Cursor  string      `json:"cursor,omitempty"`
}

type ListPartialsResponse struct {
	Partials []PartialRef `json:"partials"`
	Cursor   string       `json:"cursor,omitempty"`
}

type LoadOptions struct {
	Variant string `json:"variant,omitempty"`
	Version string `json:"version,omitempty"`
}

type DeleteOptions struct {
	Variant string `json:"variant,omitempty"`
}
