<!-- Code Quality & Security -->

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/google/dotprompt/badge)](https://scorecard.dev/viewer/?uri=github.com/google/dotprompt)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10359/badge)](https://www.bestpractices.dev/projects/10359)
[![codecov](https://codecov.io/gh/google/dotprompt/graph/badge.svg)](https://codecov.io/gh/google/dotprompt)
[![License](https://img.shields.io/github/license/google/dotprompt)](https://github.com/google/dotprompt/blob/main/LICENSE)

<!-- Repository Stats -->

[![GitHub stars](https://img.shields.io/github/stars/google/dotprompt?style=social)](https://github.com/google/dotprompt)
[![GitHub forks](https://img.shields.io/github/forks/google/dotprompt?style=social)](https://github.com/google/dotprompt/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/google/dotprompt?style=social)](https://github.com/google/dotprompt)
[![GitHub contributors](https://img.shields.io/github/contributors/google/dotprompt)](https://github.com/google/dotprompt/graphs/contributors)
[![GitHub last commit](https://img.shields.io/github/last-commit/google/dotprompt)](https://github.com/google/dotprompt/commits/main)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/google/dotprompt)](https://github.com/google/dotprompt/pulse)

[![OSS Insight](https://img.shields.io/badge/OSS%20Insight-google%2Fdotprompt-blue?logo=github)](https://ossinsight.io/analyze/google/dotprompt)
[![Discord](https://img.shields.io/discord/1029867111234740224?logo=discord&label=Discord)](https://discord.gg/qXt5zzQKpc)
[![View Code Wiki](https://www.gstatic.com/_/boq-sdlc-agents-ui/_/r/YUi5dj2UWvE.svg)](https://codewiki.google/github.com/google/dotprompt)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/google/dotprompt)

[![Star History Chart](https://api.star-history.com/svg?repos=google/dotprompt&type=Date)](https://star-history.com/#google/dotprompt&Date)

# Dotprompt: Executable GenAI Prompt Templates

**Dotprompt** is an executable prompt template file format for Generative AI. It
is designed to be agnostic to programming language and model provider to allow
for maximum flexibility in usage. Dotprompt extends the popular
[Handlebars](https://handlebarsjs.com) templating language with GenAI-specific
features.

## Package Versions

| Package | Version | Registry |
|---------|---------|----------|
| **Core Libraries** |||
| `dotprompt` (JS/TS) | [![npm](https://img.shields.io/npm/v/dotprompt)](https://www.npmjs.com/package/dotprompt) | [npm](https://www.npmjs.com/package/dotprompt) |
| `dotpromptz` (Python) | [![PyPI](https://img.shields.io/pypi/v/dotpromptz)](https://pypi.org/project/dotpromptz/) | [PyPI](https://pypi.org/project/dotpromptz/) |
| `dotpromptz-handlebars` (Python) | [![PyPI](https://img.shields.io/pypi/v/dotpromptz-handlebars)](https://pypi.org/project/dotpromptz-handlebars/) | [PyPI](https://pypi.org/project/dotpromptz-handlebars/) |
| `dotprompt-go` (Go) | [![Go](https://img.shields.io/github/v/tag/google/dotprompt?filter=dotprompt-go*&label=version)](https://pkg.go.dev/github.com/google/dotprompt/go/dotprompt) | [pkg.go.dev](https://pkg.go.dev/github.com/google/dotprompt/go/dotprompt) |
| `dotprompt-rs` (Rust) | [![crates.io](https://img.shields.io/crates/v/dotprompt)](https://crates.io/crates/dotprompt) | [crates.io](https://crates.io/crates/dotprompt) |
| `dotprompt-java` (Java) | [![Maven Central](https://img.shields.io/maven-central/v/com.google.dotprompt/dotprompt)](https://central.sonatype.com/artifact/com.google.dotprompt/dotprompt) | [Maven Central](https://central.sonatype.com/artifact/com.google.dotprompt/dotprompt) |
| **IDE Extensions** |||
| `dotprompt-vscode` | [![VS Marketplace](https://img.shields.io/visual-studio-marketplace/v/google.dotprompt-vscode)](https://marketplace.visualstudio.com/items?itemName=google.dotprompt-vscode) | [VS Marketplace](https://marketplace.visualstudio.com/items?itemName=google.dotprompt-vscode) |
| `dotprompt-jetbrains` | [![JetBrains](https://img.shields.io/jetbrains/plugin/v/com.google.dotprompt)](https://plugins.jetbrains.com/plugin/com.google.dotprompt) | [JetBrains](https://plugins.jetbrains.com/plugin/com.google.dotprompt) |
| `dotprompt-vim` | - | [GitHub](https://github.com/google/dotprompt/tree/main/packages/vim) |
| `dotprompt-emacs` | - | [GitHub](https://github.com/google/dotprompt/tree/main/packages/emacs) |
| **Web Editors** |||
| `dotprompt-monaco` | [![npm](https://img.shields.io/npm/v/dotprompt-monaco)](https://www.npmjs.com/package/dotprompt-monaco) | [npm](https://www.npmjs.com/package/dotprompt-monaco) |
| `dotprompt-codemirror` | [![npm](https://img.shields.io/npm/v/dotprompt-codemirror)](https://www.npmjs.com/package/dotprompt-codemirror) | [npm](https://www.npmjs.com/package/dotprompt-codemirror) |
| **Tools** |||
| `tree-sitter-dotprompt` | [![npm](https://img.shields.io/npm/v/tree-sitter-dotprompt)](https://www.npmjs.com/package/tree-sitter-dotprompt) | [npm](https://www.npmjs.com/package/tree-sitter-dotprompt) |
| `promptly` | [![npm](https://img.shields.io/npm/v/promptly-cli)](https://www.npmjs.com/package/promptly-cli) | [npm](https://www.npmjs.com/package/promptly-cli) |

## CI Status

| Workflow | Status | Description |
|----------|--------|-------------|
| **Language Tests** |||
| Go | [![Go](https://github.com/google/dotprompt/actions/workflows/go.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/go.yml) | Go library tests |
| Python | [![Python](https://github.com/google/dotprompt/actions/workflows/python.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/python.yml) | Python dotpromptz tests |
| JavaScript | [![JavaScript](https://github.com/google/dotprompt/actions/workflows/js.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/js.yml) | JS/TS library tests |
| Java | [![Java](https://github.com/google/dotprompt/actions/workflows/java.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/java.yml) | Java library tests |
| Rust | [![Rust](https://github.com/google/dotprompt/actions/workflows/rust.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/rust.yml) | Rust library tests |
| Bazel | [![Bazel](https://github.com/google/dotprompt/actions/workflows/bazel.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/bazel.yml) | Bazel build & test |
| Handlebarrz | [![Handlebarrz](https://github.com/google/dotprompt/actions/workflows/handlebarrz-tests.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/handlebarrz-tests.yml) | Python Handlebars tests |
| **IDE & Editor Plugins** |||
| VS Code | [![VS Code](https://github.com/google/dotprompt/actions/workflows/vscode_extension.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/vscode_extension.yml) | VS Code extension |
| IDE Plugins | [![IDE Plugins](https://github.com/google/dotprompt/actions/workflows/ide_plugins.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/ide_plugins.yml) | Vim, Emacs, JetBrains |
| Web Editors | [![Web Editors](https://github.com/google/dotprompt/actions/workflows/web_editors.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/web_editors.yml) | Monaco, CodeMirror |
| Tree-sitter | [![Tree-sitter](https://github.com/google/dotprompt/actions/workflows/treesitter.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/treesitter.yml) | Grammar & parser |
| **Code Quality** |||
| Go Lint | [![Go Lint](https://github.com/google/dotprompt/actions/workflows/golangci-lint.yml/badge.svg)](https://github.com/google/dotprompt/actions/workflows/golangci-lint.yml) | golangci-lint |

## What's an executable prompt template?

An executable prompt template is a file that contains not only the text of a
prompt but also metadata and instructions for how to use that prompt with a
generative AI model. Here's what makes Dotprompt files executable:

* **Metadata Inclusion**: Dotprompt files include metadata about model
  configuration, input requirements, and expected output format. This
  information is typically stored in a YAML frontmatter section at the beginning
  of the file.

* **Self-Contained Entity**: Because a Dotprompt file contains all the necessary
  information to execute a prompt, it can be treated as a self-contained entity.
  This means you can "run" a Dotprompt file directly, without needing additional
  configuration or setup in your code.

* **Model Configuration**: The file specifies which model to use and how to
  configure it (e.g., temperature, max tokens).

* **Input Schema**: It defines the structure of the input data expected by the
  prompt, allowing for validation and type-checking.

* **Output Format**: The file can specify the expected format of the model's
  output, which can be used for parsing and validation.

* **Templating**: The prompt text itself uses Handlebars syntax, allowing for
  dynamic content insertion based on input variables.

This combination of features makes it possible to treat a Dotprompt file as an
executable unit, streamlining the process of working with AI models and ensuring
consistency across different uses of the same prompt.

## Example `.prompt` file

Here's an example of a Dotprompt file that extracts structured data from
provided text:

```handlebars
---
model: googleai/gemini-1.5-pro
input:
  schema:
    text: string
output:
  format: json
  schema:
    name?: string, the full name of the person
    age?: number, the age of the person
    occupation?: string, the person's occupation
---

Extract the requested information from the given text. If a piece of information
is not present, omit that field from the output.

Text: {{text}}
```

This Dotprompt file:

1. Specifies the use of the `googleai/gemini-1.5-pro` model.
2. Defines an input schema expecting a `text` string.
3. Specifies that the output should be in JSON format.
4. Provides a schema for the expected output, including fields for name, age,
   and occupation.
5. Uses Handlebars syntax (`{{text}}`) to insert the input text into the prompt.

When executed, this prompt would take a text input, analyze it using the
specified AI model, and return a structured JSON object with the extracted
information.

## Installation

The remainder of this getting started guide will use the reference Dotprompt
implementation included as part of the [Firebase
Genkit](https://github.com/firebase/genkit) GenAI SDK. To use other
implementations of Dotprompt, see the [list of
Implementations](third_party/docsite/src/content/docs/implementations.mdx).

First, install the necessary packages using NPM. Here we'll be using the [Gemini
API](https://ai.google.dev/gemini-api) from Google as our model implementation:

```bash
npm i genkit @genkit-ai/googleai
```

After installation, you'll need to set up your environment and initialize the
Dotprompt system. Here's a basic setup:

```typescript
import { genkit } from "genkit";
import { googleAI } from "@genkit-ai/googleai";

// Configure Genkit with the GoogleAI provider and Dotprompt plugin
const ai = genkit({
  plugins: [googleAI()],
  // promptDir: 'prompts', /* this is the default value */
});

// Now you're ready to use Dotprompt!
```

**Note:** You will need to set your Google AI API key to the `GOOGLE_API_KEY`
environment variable or pass it as an option to the `googleAI()` plugin
configuration.

With this setup, you can now create `.prompt` files in your project and use them
in your code. For example, if you have a file named `extractInfo.prompt` with
the content from the earlier example, you can use it like this:

```typescript
const extractInfo = ai.prompt("extractInfo");

const { output } = await extractInfo({
  text: "John Doe is a 35-year-old software engineer living in New York.",
});

console.log(output);
// Output: { "name": "John Doe", "age": 35, "occupation": "software engineer" }
```

This setup allows you to leverage the power of Dotprompt, making your AI
interactions more structured, reusable, and maintainable.

By following these steps, you'll have a basic Dotprompt setup ready to go. From
here, you can create more complex prompts, integrate them into your application,
and start harnessing the full power of generative AI in a structured,
template-driven way.

## Contributing

We welcome contributions! Please see our [Development Guidelines](GEMINI.md) for:

* Code style and linting requirements for each language
* Testing requirements
* Git commit message conventions

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) with package
names as scopes:

```bash
feat(dotpromptz): add new helper function
fix(dotprompt-go): resolve parsing edge case
docs(dotprompt-java): update API documentation
```

| Scope | Package |
|-------|---------|
| `dotprompt` | JavaScript/TypeScript (`js/`) |
| `dotpromptz` | Python dotpromptz (`python/dotpromptz/`) |
| `dotpromptz-handlebars` | Python Handlebars (`python/handlebarrz/`) |
| `dotprompt-go` | Go (`go/`) |
| `dotprompt-rs` | Rust (`rs/`) |
| `dotprompt-java` | Java (`java/`) |
| `dotprompt-vscode` | VS Code extension |
| `dotprompt-jetbrains` | JetBrains plugin |
| `tree-sitter-dotprompt` | Tree-sitter grammar |
| `promptly` | CLI tool for .prompt files |

See [GEMINI.md](GEMINI.md) for the complete list of scopes and guidelines.
