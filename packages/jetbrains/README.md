# Dotprompt JetBrains Plugin

Language support for Dotprompt (`.prompt`) files in JetBrains IDEs (IntelliJ IDEA, PyCharm, GoLand, WebStorm, etc.).

## Features

- **Syntax Highlighting**: YAML frontmatter, Handlebars templates, Dotprompt markers
- **LSP Integration**: Real-time diagnostics, formatting, and hover documentation (via LSP4IJ)
- **Live Templates**: Type `role`, `if`, `each`, `json` + Tab for quick insertions
- **Code Comments**: Block comment support using `{{! ... }}`
- **Settings UI**: Configure promptly path and format on save

## Requirements

- JetBrains IDE 2024.1 or later
- [LSP4IJ plugin](https://plugins.jetbrains.com/plugin/23257-lsp4ij) (installed automatically as dependency)
- `promptly` CLI for LSP features

## Installation

### From JetBrains Marketplace (Coming Soon)

1. Open your IDE
2. Go to **Settings/Preferences** → **Plugins** → **Marketplace**
3. Search for "Dotprompt"
4. Click **Install**

### From Source (Gradle)

1. **Prerequisites**: Ensure you have Gradle and JDK 17+ installed

2. **Build the plugin**:
   ```bash
   cd packages/jetbrains
   ./gradlew buildPlugin
   ```

3. **Install**:
   - Go to **Settings/Preferences** → **Plugins** → **⚙️** → **Install Plugin from Disk...**
   - Select `build/distributions/dotprompt-intellij-0.2.0.zip`

### From Source (Bazel)

You can also build the core plugin library with Bazel:

```bash
bazel build //packages/jetbrains:dotprompt-intellij
```

This produces `bazel-bin/packages/jetbrains/dotprompt-intellij.jar`.

> **Note**: For full plugin packaging (with plugin.xml, icons, LSP4IJ integration), 
> use the Gradle build. The Bazel target is useful for incremental compilation 
> during development and IDE integration.

### Install promptly for LSP Features

```bash
cargo install --path rs/promptly
# or
cargo build --release -p promptly
```

## Building

```bash
# Build the plugin
./gradlew buildPlugin

# Run IDE with plugin for testing
./gradlew runIde

# Run tests
./gradlew test
```

## Live Templates

Type these abbreviations and press Tab to expand:

| Abbreviation | Expands To |
|--------------|------------|
| `role` | Role block with customizable role name |
| `system` | System role block |
| `user` | User role block |
| `model` | Model role block |
| `if` | Handlebars if block |
| `ifelse` | Handlebars if-else block |
| `unless` | Handlebars unless block |
| `each` | Handlebars each loop |
| `with` | Handlebars with block |
| `json` | JSON serialization helper |
| `media` | Media embedding helper |
| `history` | History insertion |
| `section` | Named section block |
| `partial` | Partial template inclusion |
| `comment` | Handlebars comment |
| `prompt` | Complete prompt template |
| `frontmatter` | YAML frontmatter |

## LSP Features

When `promptly` is installed and in your PATH, you get:

| Feature | Description |
|---------|-------------|
| Diagnostics | Real-time YAML and Handlebars error detection |
| Formatting | Format with `Code` → `Reformat Code` |
| Hover | Documentation for helpers and frontmatter fields |

## Configuration

### Settings UI

Go to **Settings/Preferences** → **Languages & Frameworks** → **Dotprompt**:

- **Promptly path**: Custom path to the promptly executable
- **Enable LSP features**: Toggle diagnostics, formatting, hover
- **Format on save**: Automatically format when saving

### Auto-Detection

The plugin automatically finds `promptly` in:
1. User-configured path (Settings)
2. System PATH
3. `~/.cargo/bin/promptly`

## Architecture

This plugin uses [LSP4IJ](https://github.com/redhat-developer/lsp4ij) to connect to the `promptly` LSP server, providing a rich editing experience without duplicating the language server logic.
