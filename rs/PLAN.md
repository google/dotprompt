## Plan for Rust `dotprompt` Implementation

The Rust implementation can mirror the structure and functionality of the TypeScript version, leveraging Rust's strengths in safety, performance, and concurrency.

**Phase 1: Core Parsing and Rendering Foundation**

1.  **Project Setup**:
    *   Initialize a new Rust library project using `cargo new dotprompt_rs --lib`.
    *   Configure `Cargo.toml` with initial dependencies (e.g., `serde` for deserialization, a YAML crate like `serde_yaml`, a Handlebars crate like `handlebars-rust`).
2.  **Type Definitions (`src/types.rs` or similar module)**:
    *   Translate TypeScript interfaces from `js/src/types.ts` into Rust structs and enums.
    *   Utilize `serde` derive macros (`Serialize`, `Deserialize`) for easy data conversion.
    *   Use standard Rust collections (e.g., `Vec<T>`, `HashMap<K, V>`) or crates like `im` for immutable collections if performance/safety benefits are identified.
3.  **Parsing Logic (`src/parse.rs` or `parser` module)**:
    *   Implement `parse_document`:
        *   Use `serde_yaml` to parse frontmatter.
        *   Replicate the logic from `js/src/parse.ts` for `extract_frontmatter_and_body`, handling reserved keywords and extension fields (`ext`).
    *   Implement `to_messages`:
        *   Adapt the marker-based string splitting logic (e.g., `split_by_role_and_history_markers`).
        *   Convert text pieces into `Message` and `Part` structs.
        *   Implement history insertion logic (`insert_history`, `messages_have_history`).
4.  **Handlebars Integration**:
    *   Integrate `handlebars-rust` for template rendering.
    *   Create Rust equivalents of the built-in Handlebars helpers found in `js/src/helpers.ts` (e.g., `JsonHelper`, `RoleHelper`, `HistoryHelper`, `MediaHelper`, `SectionHelper`, `IfEqualsHelper`, `UnlessEqualsHelper`) as custom Handlebars helpers in Rust.
5.  **`Dotprompt` Struct (Core Functionality - `src/lib.rs` or `src/dotprompt.rs`)**:
    *   Develop the main `Dotprompt` struct.
    *   The constructor (`Dotprompt::new()`) should initialize the Handlebars registry and register built-in and custom helpers/partials.
    *   Implement `parse(source: &str)`: Calls the Rust equivalent of `parse_document`.
    *   Implement `compile(source: &str)`:
        *   Parses the source.
        *   Resolves partials (initially, this can be synchronous or map-based).
        *   Compiles the Handlebars template.
        *   Returns a `PromptFunction` (which can be a Rust `Box<dyn Fn(...)>`).
    *   Implement `render(source: &str, data: DataArgument, options: PromptMetadata)`: Calls `compile` and then the resulting function.
    *   Initially, focus on synchronous operations for resolvers. Use `Result<T, E>` for error handling.

**Phase 2: Advanced Metadata, Schemas, and Tools**

1.  **PicoSchema Parser (`src/picoschema.rs` or `schema` module)**:
    *   Implement the logic to parse the Picoschema format and convert it into JSON Schema objects (e.g., using `serde_json::Value` or a dedicated JSON Schema crate).
    *   This will involve handling types, optional fields, descriptions, arrays, objects, enums, and wildcards.
    *   Integrate `SchemaResolver` functionality (likely a trait `SchemaResolver` with an `async fn resolve(&self, name: &str) -> Result<Option<JsonSchema>, Error>`).
2.  **`Dotprompt` Struct Enhancements**:
    *   Implement `render_metadata`.
    *   Implement internal methods for `resolve_metadata`, `resolve_tools`, and `render_picoschema` (which will use your `Picoschema` parser implementation).
    *   Add methods `define_tool(def: ToolDefinition)`, `define_helper(...)`, `define_partial(...)`.
    *   Incorporate `ToolResolver`, `SchemaResolver`, and `PartialResolver` (likely traits) into the metadata and compilation flows.

**Phase 3: Asynchronous Operations & DI (Rust-style)**

1.  **Asynchronous Operations with `async/await` and Tokio/async-std**:
    *   Refactor `PartialResolver`, `SchemaResolver`, and `ToolResolver` traits and their implementations to support asynchronous operations (e.g., returning `impl Future<Output = Result<...>>`). This is crucial if these resolvers need to fetch data from external sources (network, filesystem I/O).
    *   Use `async/await` syntax throughout the library where I/O is involved. Choose an async runtime (e.g., Tokio).
    *   Methods like `compile` and `render` might become `async fn compile(...)` and `async fn render(...)`.
2.  **Dependency Injection (Rust-style)**:
    *   Rust typically achieves DI through:
        *   **Constructor Injection**: Pass dependencies (like resolver implementations) to `Dotprompt::new()`.
        *   **Trait Objects**: Use `Box<dyn Trait>` for dynamic dispatch if different resolver implementations are needed at runtime.
        *   **Generics**: Use generic type parameters bounded by traits for static dispatch.
    *   For resolvers, passing trait objects or using generics in `Dotprompt::new()` is a common pattern.
3.  **Logging with `log` crate and a backend (e.g., `env_logger`, `tracing`)**:
    *   Integrate the `log` crate facade for structured logging throughout the library, especially for parsing issues, resolver activity, and rendering steps.
    *   Users of the library can then choose their preferred logging backend.

**Phase 4: Prompt Storage and LLM Adapters**

1.  **PromptStore Implementation (`src/stores/directory.rs`)**:
    *   Create a Rust version of the `DirStore` from `js/src/stores/dir.ts` for filesystem-based prompt and partial management.
    *   This includes file I/O using `std::fs` (or async equivalents like `tokio::fs`), directory scanning, and content-based versioning (e.g., using a SHA1 crate like `sha1`).
2.  **LLM Adapters (`src/adapters/gemini.rs`, `src/adapters/openai.rs`, etc.)**:
    *   Translate the TypeScript adapters. These structs/functions will take a `RenderedPrompt` object and convert it into the specific request format required by different LLM providers.
    *   Use an HTTP client crate like `reqwest` for making API calls (likely in async contexts).

**Phase 5: Testing, Error Handling, and Polish**

1.  **Unit and Integration Testing**:
    *   Write comprehensive tests using Rust's built-in testing framework (`#[test]`).
    *   Organize tests in `tests` directory for integration tests and inline for unit tests.
    *   Ensure edge cases and error conditions are well-covered.
2.  **Error Handling with `Result<T, E>`**:
    *   Use Rust's `Result<T, E>` enum extensively for error handling. Define custom error types (e.g., using `thiserror` crate) for better error reporting.
3.  **Clippy for Linting**:
    *   Regularly run `cargo clippy` to catch common Rust pitfalls and improve code style.
4.  **Code Style and Reviews**:
    *   Adhere to idiomatic Rust style (use `cargo fmt`).
    *   Conduct thorough code reviews.
    *   Refactor for clarity, performance, and maintainability.

## Publishing to Crates.io

**I. Prerequisites & Setup**

1.  **Crates.io Account**:
    *   Create an account on crates.io.
2.  **Cargo Login**:
    *   Log in to crates.io using `cargo login <API_TOKEN>`.

**II. `Cargo.toml` Configuration**

1.  **Manifest Details**:
    *   Ensure `[package]` section in `Cargo.toml` is complete and accurate:
        *   `name`: e.g., `dotprompt` (must be unique on crates.io)
        *   `version`: e.g., `0.1.0` (follow SemVer)
        *   `authors`: `["Your Name <you@example.com>"]`
        *   `edition`: e.g., `2021`
        *   `description`: A short description of the library.
        *   `readme`: e.g., `README.md`
        *   `repository`: URL of the Git repository.
        *   `license`: SPDX license identifier (e.g., `Apache-2.0`).
        *   `keywords`: Relevant keywords (e.g., `["genai", "prompt", "templating", "llm"]`).
        *   `categories`: Relevant categories from crates.io.
2.  **Dependencies**:
    *   List all public dependencies.
    *   Ensure versions are appropriate (e.g., using caret `^` or tilde `~` requirements).

**III. Documentation and Readme**

1.  **API Documentation**:
    *   Write comprehensive /// Rustdoc comments for all public APIs.
    *   Generate documentation using `cargo doc --open`.
2.  **README.md**:
    *   Create a `README.md` file with an overview, usage examples, and installation instructions.

**IV. Building and Testing**

1.  **Build Release Version**:
    *   `cargo build --release`
2.  **Run Tests**:
    *   `cargo test --all-features`
3.  **Check Formatting and Lints**:
    *   `cargo fmt --all --check`
    *   `cargo clippy --all-targets --all-features -- -D warnings`

**V. Publishing**

1.  **Dry Run (Recommended)**:
    *   `cargo publish --dry-run`
    *   This will check for common issues without actually publishing.
2.  **Publish**:
    *   `cargo publish`

**VI. Post-Publishing**

1.  **Tag Release**:
    *   Create a Git tag for the released version (e.g., `v0.1.0`).
2.  **Announce**:
    *   Consider announcing the release if appropriate.
