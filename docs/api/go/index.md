# Go API

The `dotprompt` package is the Go implementation of the Dotprompt file format.

## Installation

```bash
go get github.com/google/dotprompt/go/dotprompt
```

## Quick Start

```go
package main

import (
    "context"
    "fmt"
    "log"

    "github.com/google/dotprompt/go/dotprompt"
)

func main() {
    source := `
---
model: gemini-pro
input:
  schema:
    name: string
---
Hello, {{name}}!
`

    dp := dotprompt.New()

    rendered, err := dp.Render(context.Background(), source, dotprompt.DataArgument{
        Input: map[string]any{"name": "World"},
    })
    if err != nil {
        log.Fatal(err)
    }

    for _, msg := range rendered.Messages {
        fmt.Printf("%s: %v\n", msg.Role, msg.Content)
    }
}
```

## Core Types

### Dotprompt

The main entry point for working with Dotprompt templates.

```go
// New creates a new Dotprompt instance with default options.
func New(opts ...Option) *Dotprompt

// NewWithOptions creates a new Dotprompt instance with the given options.
func NewWithOptions(options DotpromptOptions) *Dotprompt
```

#### Options

```go
type DotpromptOptions struct {
    DefaultModel    string
    ModelConfigs    map[string]any
    Helpers         map[string]HelperFn
    Partials        map[string]string
    Tools           map[string]ToolDefinition
    ToolResolver    ToolResolver
    Schemas         map[string]JsonSchema
    SchemaResolver  SchemaResolver
    PartialResolver PartialResolver
}
```

### Methods

#### Parse

```go
// Parse parses a Dotprompt template string into a ParsedPrompt.
func (d *Dotprompt) Parse(source string) (*ParsedPrompt, error)
```

#### Compile

```go
// Compile compiles a template into a reusable PromptFunction.
func (d *Dotprompt) Compile(ctx context.Context, source string) (PromptFunction, error)
```

#### Render

```go
// Render parses, compiles, and renders a template in one step.
func (d *Dotprompt) Render(
    ctx context.Context,
    source string,
    data DataArgument,
    options ...PromptMetadata,
) (*RenderedPrompt, error)
```

#### DefineHelper

```go
// DefineHelper registers a custom Handlebars helper.
func (d *Dotprompt) DefineHelper(name string, fn HelperFn) *Dotprompt
```

#### DefinePartial

```go
// DefinePartial registers a partial template.
func (d *Dotprompt) DefinePartial(name string, source string) *Dotprompt
```

#### DefineTool

```go
// DefineTool registers a tool definition.
func (d *Dotprompt) DefineTool(definition ToolDefinition) *Dotprompt
```

## Types

### ParsedPrompt

```go
type ParsedPrompt struct {
    Template    string
    Name        string
    Description string
    Variant     string
    Version     string
    Model       string
    Config      any
    Input       *PromptInputConfig
    Output      *PromptOutputConfig
    Tools       []string
    ToolDefs    []ToolDefinition
    Ext         map[string]map[string]any
    Raw         map[string]any
}
```

### RenderedPrompt

```go
type RenderedPrompt struct {
    PromptMetadata
    Messages []Message
}
```

### Message

```go
type Message struct {
    Role     Role
    Content  []Part
    Metadata map[string]any
}

type Role string

const (
    RoleUser   Role = "user"
    RoleModel  Role = "model"
    RoleTool   Role = "tool"
    RoleSystem Role = "system"
)
```

### Part

```go
type Part interface {
    isPart()
}

type TextPart struct {
    Text     string
    Metadata map[string]any
}

type MediaPart struct {
    Media    MediaContent
    Metadata map[string]any
}

type MediaContent struct {
    URL         string
    ContentType string
}

type DataPart struct {
    Data     map[string]any
    Metadata map[string]any
}
```

### DataArgument

```go
type DataArgument struct {
    Input    map[string]any
    Docs     []Document
    Messages []Message
    Context  map[string]any
}
```

### ToolDefinition

```go
type ToolDefinition struct {
    Name         string
    Description  string
    InputSchema  JsonSchema
    OutputSchema JsonSchema
}
```

## Stores

### DirStore

Load prompts from a filesystem directory.

```go
import "github.com/google/dotprompt/go/dotprompt"

store := dotprompt.NewDirStore(dotprompt.DirStoreOptions{
    Directory: "./prompts",
})

prompt, err := store.Load(ctx, "greeting", nil)
if err != nil {
    log.Fatal(err)
}
```

### DirStoreSync

Synchronous version of DirStore.

```go
store := dotprompt.NewDirStoreSync(dotprompt.DirStoreOptions{
    Directory: "./prompts",
})

prompt, err := store.Load("greeting", nil)
```

## Picoschema

Convert Picoschema to JSON Schema.

```go
schema := map[string]any{
    "name":  "string",
    "age?": "integer, The person's age",
}

jsonSchema, err := dotprompt.PicoschemaToJSONSchema(ctx, schema, nil)
```

## External Documentation

* [pkg.go.dev](https://pkg.go.dev/github.com/google/dotprompt/go/dotprompt)
* [GitHub source](https://github.com/google/dotprompt/tree/main/go)
