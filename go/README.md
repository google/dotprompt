# Go Dotprompt

Executable GenAI prompt templates in Go.

## Overview

This library provides a Go implementation of the Dotprompt format -- a
language-neutral executable prompt template format for Generative AI. It
passes all shared [spec tests](../spec/) for cross-language compatibility.

## Features

- YAML frontmatter for prompt metadata (model, config, input/output schemas)
- Handlebars templating with 7 built-in helpers (role, media, history,
  section, json, ifEquals, unlessEquals)
- Picoschema: compact schema notation with JSON Schema conversion
- Multi-message prompts with role markers
- Named partials with recursive resolution and cycle detection
- PromptStore interface with DirStore (file system) implementation
- Custom loaders and schema/tool resolvers
- Tools/functions and safety settings via config passthrough
- 200+ spec tests passing

## Installation

```bash
go get github.com/google/dotprompt/go/dotprompt
```

## Usage

```go
package main

import (
    "fmt"
    "github.com/google/dotprompt/go/dotprompt"
)

func main() {
    dp := dotprompt.New(nil)
    source := `---
model: gemini-2.0-flash
input:
  schema:
    name: string
---
Hello, {{name}}!`

    data := dotprompt.DataArgument{
        Input: map[string]any{"name": "World"},
    }
    rendered, err := dp.Render(source, data, nil)
    if err != nil {
        panic(err)
    }
    fmt.Println(rendered.Prompt.Messages[0].Content[0].Text)
}
```

## Listing prompts and partials

`DirStore.List` and `DirStore.ListPartials` return entries sorted by name and
variant. Set `Limit` to a positive value to request a page, then pass the returned
`Cursor` unchanged in the next call with the same variant filter. An empty cursor
in the result means there are no more entries. A zero or negative limit returns
all remaining entries.

Cursors represent offsets in the sorted, filtered listing; they do not preserve
a snapshot if files are added or removed between calls. Invalid cursors return
an error, and cursors beyond the current listing return an empty page.

## Building

```bash
go build ./...
```

## Testing

```bash
go test -v ./...
```

## Published Package

- **pkg.go.dev**: [github.com/google/dotprompt/go/dotprompt](https://pkg.go.dev/github.com/google/dotprompt/go/dotprompt)

## License

Apache-2.0
