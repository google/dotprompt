# Rust Dotprompt

Executable `GenAI` prompt templates in Rust.

## Overview

This library provides a Rust implementation of the dotprompt format - a language-neutral executable prompt template format for Generative AI.

## Features

- YAML frontmatter for prompt metadata
- Handlebars templating engine
- Picoschema to JSON Schema conversion
- Built-in helpers for common prompt patterns
- Type-safe prompt rendering

## Usage

```rust
use dotprompt::{Dotprompt, DataArgument, RenderedPrompt};

let dotprompt = Dotprompt::new(None);
let template = r#"---
model: gemini-pro
---
Hello {{name}}!"#;

let mut data = DataArgument::default();
data.input = Some(serde_json::json!({"name": "World"}));

let rendered: RenderedPrompt = dotprompt.render(template, data, None)?;
```

## License

Apache 2.0
