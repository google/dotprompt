# Dotprompt JetBrains Plugin

Language support for Dotprompt (`.prompt`) files in JetBrains IDEs (IntelliJ IDEA, PyCharm, GoLand, WebStorm, etc.).

## Features

- **Syntax Highlighting**: YAML frontmatter, Handlebars templates, Dotprompt markers
- **LSP Integration**: Real-time diagnostics, formatting, and hover documentation (via LSP4IJ)
- **Code Comments**: Block comment support using `{{! ... }}`

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
   - Select `build/distributions/dotprompt-intellij-0.1.0.zip`

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

## LSP Features

When `promptly` is installed and in your PATH, you get:

| Feature | Description |
|---------|-------------|
| Diagnostics | Real-time YAML and Handlebars error detection |
| Formatting | Format with `Code` → `Reformat Code` |
| Hover | Documentation for helpers and frontmatter fields |

## Configuration

The plugin automatically finds `promptly` in:
1. System PATH
2. `~/.cargo/bin/promptly`

## Architecture

This plugin uses [LSP4IJ](https://github.com/redhat-developer/lsp4ij) to connect to the `promptly` LSP server, providing a rich editing experience without duplicating the language server logic.
