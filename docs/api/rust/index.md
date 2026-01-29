# Rust API

The `dotprompt` crate is the Rust implementation of the Dotprompt file format.

## Installation

Add to your `Cargo.toml`:

```toml
[dependencies]
dotprompt = "0.1"
```

## Quick Start

```rust
use dotprompt::{Dotprompt, DataArgument, RenderedPrompt};
use serde_json::json;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let source = r#"
---
model: gemini-pro
input:
  schema:
    name: string
---
Hello, {{name}}!
"#;

    let dotprompt = Dotprompt::new(None);

    let mut data = DataArgument::default();
    data.input = Some(json!({"name": "World"}));

    let rendered: RenderedPrompt = dotprompt.render(source, data, None)?;

    for message in &rendered.messages {
        println!("{:?}: {:?}", message.role, message.content);
    }

    Ok(())
}
```

## Core Types

### Dotprompt

The main entry point for working with Dotprompt templates.

```rust
impl Dotprompt {
    /// Create a new Dotprompt instance with optional configuration.
    pub fn new(options: Option<DotpromptOptions>) -> Self;

    /// Parse a template string into a ParsedPrompt.
    pub fn parse(&self, source: &str) -> Result<ParsedPrompt, DotpromptError>;

    /// Compile a template into a reusable PromptFunction.
    pub fn compile(&self, source: &str) -> Result<PromptFunction, DotpromptError>;

    /// Parse, compile, and render a template in one step.
    pub fn render(
        &self,
        source: &str,
        data: DataArgument,
        options: Option<PromptMetadata>,
    ) -> Result<RenderedPrompt, DotpromptError>;

    /// Register a custom Handlebars helper.
    pub fn define_helper<F>(&mut self, name: &str, helper: F) -> &mut Self
    where
        F: Fn(&[Value], &HelperOptions) -> String + Send + Sync + 'static;

    /// Register a partial template.
    pub fn define_partial(&mut self, name: &str, source: &str) -> &mut Self;

    /// Register a tool definition.
    pub fn define_tool(&mut self, definition: ToolDefinition) -> &mut Self;
}
```

### DotpromptOptions

```rust
pub struct DotpromptOptions {
    pub default_model: Option<String>,
    pub model_configs: Option<HashMap<String, Value>>,
    pub helpers: Option<HashMap<String, HelperFn>>,
    pub partials: Option<HashMap<String, String>>,
    pub tools: Option<HashMap<String, ToolDefinition>>,
    pub tool_resolver: Option<Box<dyn ToolResolver>>,
    pub schemas: Option<HashMap<String, JsonSchema>>,
    pub schema_resolver: Option<Box<dyn SchemaResolver>>,
    pub partial_resolver: Option<Box<dyn PartialResolver>>,
}
```

## Types

### ParsedPrompt

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParsedPrompt {
    pub template: String,
    pub name: Option<String>,
    pub description: Option<String>,
    pub variant: Option<String>,
    pub version: Option<String>,
    pub model: Option<String>,
    pub config: Option<Value>,
    pub input: Option<PromptInputConfig>,
    pub output: Option<PromptOutputConfig>,
    pub tools: Option<Vec<String>>,
    pub tool_defs: Option<Vec<ToolDefinition>>,
    pub ext: Option<HashMap<String, HashMap<String, Value>>>,
    pub raw: Option<HashMap<String, Value>>,
}
```

### RenderedPrompt

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RenderedPrompt {
    #[serde(flatten)]
    pub metadata: PromptMetadata,
    pub messages: Vec<Message>,
}
```

### Message

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: Role,
    pub content: Vec<Part>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, Value>>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    User,
    Model,
    Tool,
    System,
}
```

### Part

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Part {
    Text(TextPart),
    Media(MediaPart),
    Data(DataPart),
    ToolRequest(ToolRequestPart),
    ToolResponse(ToolResponsePart),
    Pending(PendingPart),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextPart {
    pub text: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, Value>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaPart {
    pub media: MediaContent,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<HashMap<String, Value>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MediaContent {
    pub url: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content_type: Option<String>,
}
```

### DataArgument

```rust
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct DataArgument {
    pub input: Option<Value>,
    pub docs: Option<Vec<Document>>,
    pub messages: Option<Vec<Message>>,
    pub context: Option<HashMap<String, Value>>,
}
```

### ToolDefinition

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolDefinition {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub input_schema: JsonSchema,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub output_schema: Option<JsonSchema>,
}
```

## Error Handling

```rust
#[derive(Debug, thiserror::Error)]
pub enum DotpromptError {
    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("Render error: {0}")]
    RenderError(String),

    #[error("Schema error: {0}")]
    SchemaError(String),

    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
}
```

## Stores

### DirStore

Load prompts from a filesystem directory.

```rust
use dotprompt::stores::{DirStore, DirStoreOptions, PromptStore};

let store = DirStore::new(DirStoreOptions {
    directory: "./prompts".into(),
});

let prompt = store.load("greeting", None).await?;
```

### DirStoreSync

Synchronous version.

```rust
use dotprompt::stores::{DirStoreSync, DirStoreOptions, PromptStoreSync};

let store = DirStoreSync::new(DirStoreOptions {
    directory: "./prompts".into(),
});

let prompt = store.load("greeting", None)?;
```

## Picoschema

Convert Picoschema to JSON Schema.

```rust
use dotprompt::picoschema::picoschema_to_json_schema;
use serde_json::json;

let schema = json!({
    "name": "string",
    "age?": "integer, The person's age"
});

let json_schema = picoschema_to_json_schema(schema, None).await?;
```

## Built-in Helpers

| Helper | Description | Example |
|--------|-------------|---------|
| `role` | Set message role | `{{role "system"}}` |
| `media` | Insert media content | `{{media url="..." contentType="image/png"}}` |
| `history` | Insert message history | `{{history}}` |
| `section` | Create a content section | `{{section "code"}}` |
| `json` | Serialize to JSON | `{{json data indent=2}}` |
| `ifEquals` | Conditional equality | `{{#ifEquals a b}}...{{/ifEquals}}` |
| `unlessEquals` | Conditional inequality | `{{#unlessEquals a b}}...{{/unlessEquals}}` |

## External Documentation

* [docs.rs](https://docs.rs/dotprompt)
* [crates.io](https://crates.io/crates/dotprompt)
* [GitHub source](https://github.com/google/dotprompt/tree/main/rs)
