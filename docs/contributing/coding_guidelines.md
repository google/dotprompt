# Dotprompt Development Guidelines

## Overview

Dotprompt is a multi-language library implementing an executable prompt template file format
for Generative AI. The codebase supports **Go**, **Python**, **JavaScript/TypeScript**,
**Java**, and **Rust** implementations.

## Code Quality & Linting

* **Run Linting**: Always run `./scripts/lint` from the repo root for Python code changes,
  and the language-specific check scripts for other languages.
  0 diagnostics should be reported for all blocking checks.
* **Treat Warnings as Errors**: Do not ignore warnings from linters or type checkers
  unless there is a compelling, documented reason.
* **Check Licenses**: Run `./scripts/check_license` to ensure all files have proper
  license headers.

***

## Python Development

### Target Environment

* **Python Version**: Target Python 3.10 or newer.
* **Environment**: Use `uv` for packaging and environment management.

### Type Checking

Two type checkers are configured (both blocking, must pass with zero errors):

* **ty** (Astral/Ruff) - Fast type checker from the Ruff team
* **pyrefly** (Meta) - Static type checker from Meta

Run type checks with:

```bash
cd python
uv run ty check
uv run pyrefly check
```

Or use the lint script which runs both:

```bash
./scripts/lint
```

### Type Checker Configuration

Both type checkers are configured in `python/pyproject.toml`.

**pyrefly** (`[tool.pyrefly]`):

* `project_includes`: Specifies which directories to check (`dotpromptz`, `handlebarrz`, `tests`)
* `untyped_def_behavior = "check-and-infer-return-type"`: Check untyped functions
  and infer return types
* `python_version = "3.10"`: Matches ruff.target-version

**ty** (`[[tool.ty.overrides]]`):

* Uses overrides to ignore `unresolved-import` errors in `samples/` directory
  (external dependencies not installed in the workspace)
* ty still type-checks all code in samples, just tolerates missing third-party imports

### Error Suppression Policy

Avoid ignoring warnings from the type checker (`# type: ignore`, `# pyrefly: ignore`, etc.)
unless there is a compelling, documented reason.

* **Try to fix first**: Before suppressing, try to rework the code to avoid the
  warning entirely. Use explicit type annotations, asserts for type narrowing,
  local variables to capture narrowed types in closures, or refactor the logic.
* **Acceptable suppressions**: Only suppress when the warning is due to:
  * Type checker limitations (e.g., closure narrowing issues)
  * External library type stub issues
  * Intentional design choices
* **Minimize surface area**: Suppress on the specific line, not globally in config.
* **Always add a comment**: Explain why the suppression is needed.
* **Be specific**: Use the exact error code when possible (e.g., `# pyrefly: ignore[missing-attribute]`).

### Typing & Style

* **Syntax**:
  * Use `|` for union types instead of `Union`.
  * Use `| None` instead of `Optional`.
  * Use lowercase `list`, `dict` for type hints (avoid `List`, `Dict`).
  * Use modern generics (PEP 585, 695).
* **Imports**: Import types like `Callable`, `Awaitable` from `collections.abc`,
  not standard library `typing`.
* **Strictness**: Apply type hints strictly, including `-> None` for void functions.

### Formatting

* **Tool**: Format code using `ruff` (or `./scripts/fmt`).
* **Line Length**: Max 120 characters.
* **Config**: Refer to `.editorconfig` or `python/pyproject.toml` for rules.

### Testing

* **Framework**: Use `pytest`.
* **Execution**: Run via `uv run pytest .` in the `python` directory.
* **Coverage**: Aim for 85% or higher coverage.

### Docstrings

* **Format**: Write comprehensive Google-style docstrings for modules, classes,
  and functions.
* **Required Sections**:
  * **Overview**: One-liner description followed by rationale.
  * **Args/Attributes**: Required for callables/classes.
  * **Returns**: Required for callables.
  * **Examples**: Required for user-facing API.

***

## JavaScript/TypeScript Development

### Target Environment

* **Node.js Version**: Support Node.js 20, 21, 22, 23, and 24.
* **Package Manager**: Use `pnpm` for dependency management.

### Type Checking

TypeScript's built-in type checker (`tsc`) is used. The project also supports
the native TypeScript compiler (`tsgo`).

```bash
pnpm -C js build       # Build with tsc
pnpm -C js build:native # Build with tsgo
```

### Linting & Formatting

* **Linter**: Biome is used for linting JavaScript/TypeScript code.
* **Formatter**: Biome is also used for formatting.
* **Config**: See `biome.json` in the repo root.

```bash
pnpm dlx @biomejs/biome check --formatter-enabled=true js/
```

### Testing

* **Framework**: Vitest is used for testing.
* **Execution**: Run `pnpm -C js test`.

***

## Go Development

### Target Environment

* **Go Version**: Support Go 1.24 and 1.25.

### Linting

* **golangci-lint**: Primary linter for Go code.
* **go vet**: Standard Go static analysis.
* **govulncheck**: Vulnerability scanning.

```bash
cd go
golangci-lint run ./...
go vet -v ./...
govulncheck ./...
```

### Formatting

* **Tool**: Use `gofmt` for formatting.
* **Check**: Run `gofmt -l go/` to list unformatted files.
* **Fix**: Run `gofmt -w go/` or `./scripts/format_go_files`.

### Testing

```bash
go test -C go -v ./...
```

Or use the comprehensive check script:

```bash
./scripts/run_go_checks
```

***

## Rust Development

### Target Environment

* **Toolchains**: Support both stable and nightly toolchains.
* **Stable is blocking**: Nightly failures are allowed but logged.

### Linting

* **Clippy**: Primary linter with strict settings.
* **Workspace lints**: Configured in `Cargo.toml` at the workspace level.

```bash
cargo clippy --all-targets --workspace -- -D warnings
```

Key lint settings (from `Cargo.toml`):

* `unsafe_code = "forbid"` - No unsafe code allowed
* `missing_docs = "deny"` - All public items must be documented
* All clippy categories enabled: `pedantic`, `nursery`, `correctness`, etc.

### Formatting

```bash
cargo fmt --all -- --check
```

### Testing

```bash
cargo test --all-targets --workspace
```

Or use the comprehensive check script:

```bash
./scripts/run_rust_checks
```

***

## Java Development

### Target Environment

* **JDK Version**: Support JDK 17, 21, 23, and 24.
* **Build System**: Bazel.

### Formatting

* **Tool**: google-java-format
* **Check**:

```bash
java -jar google-java-format.jar --dry-run --set-exit-if-changed $(find java -name "*.java")
```

### Testing

```bash
bazel test --test_output=errors //java/com/google/dotprompt/...
```

***

## Cross-Language Specifications

The `spec/` directory contains YAML specification files that define expected
behavior across all language implementations. These specs are used for
conformance testing:

* `spec/helpers/` - Helper function specifications
* `spec/metadata.yaml` - Metadata parsing specifications
* `spec/partials.yaml` - Partial template specifications
* `spec/picoschema.yaml` - Picoschema specifications
* `spec/variables.yaml` - Variable substitution specifications

All language implementations should pass these specification tests.

***

## Licensing

Include the Apache 2.0 license header at the top of each file (update year as needed):

### Python/Bash/YAML

```python
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
```

### JavaScript/TypeScript/Java/Rust

```javascript
// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0
```

***

## Git Commit Message Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/) format with the
package name as the scope. This ensures release-please correctly attributes
commits to packages and generates accurate changelogs.

### Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Changes that do not affect the meaning of the code |
| `refactor` | A code change that neither fixes a bug nor adds a feature |
| `perf` | A code change that improves performance |
| `test` | Adding missing tests or correcting existing tests |
| `build` | Changes that affect the build system or external dependencies |
| `ci` | Changes to CI configuration files and scripts |
| `chore` | Other changes that don't modify src or test files |

### Commit Scopes (Package Names)

**IMPORTANT**: Use the exact scope from the table below. These match the package
names in `.release-please-config.json` and are used to generate release PRs.

| Scope | Package/Directory | Description |
|-------|-------------------|-------------|
| `dotprompt` | `js/` | JavaScript/TypeScript library |
| `dotpromptz` | `python/dotpromptz/` | Python dotpromptz package |
| `dotpromptz-handlebars` | `python/handlebarrz/` | Python Handlebars bindings (PyPI: dotpromptz-handlebars) |
| `dotprompt-go` | `go/` | Go implementation |
| `dotprompt-rs` | `rs/` | Rust implementation |
| `dotprompt-java` | `java/` | Java implementation |
| `dotprompt-vscode` | `packages/vscode/` | VS Code extension |
| `dotprompt-vim` | `packages/vim/` | Vim plugin |
| `dotprompt-emacs` | `packages/emacs/` | Emacs mode |
| `dotprompt-monaco` | `packages/monaco/` | Monaco editor integration |
| `dotprompt-codemirror` | `packages/codemirror/` | CodeMirror integration |
| `dotprompt-jetbrains` | `packages/jetbrains/` | JetBrains IDE plugin |
| `tree-sitter-dotprompt` | `packages/treesitter/` | Tree-sitter grammar |
| `promptly` | `packages/promptly/` | CLI tool for .prompt files |

### Examples

```bash
# Feature in Python dotpromptz package
feat(dotpromptz): add support for custom helpers

# Bug fix in handlebarrz (Python Handlebars bindings)
fix(dotpromptz-handlebars): correct template escaping behavior

# Documentation for Go implementation
docs(dotprompt-go): add usage examples to README

# CI change for Rust
ci(dotprompt-rs): add nightly toolchain testing

# Cross-cutting change (no scope)
chore: update dependencies across all packages
```

### Guidelines

* Add a rationale paragraph in the body explaining the why and what.
* Keep the subject line under 72 characters.
* Use imperative mood ("add" not "added", "fix" not "fixed").
* Do not include absolute file paths as links in commit messages.
* Reference issue numbers in the footer (e.g., `Fixes #123`).

***

## Available Scripts

| Script | Description |
|--------|-------------|
| `scripts/lint` | Run Python linting (ruff, ty, pyrefly) |
| `scripts/fmt` | Format all code |
| `scripts/check_license` | Check license headers |
| `scripts/run_go_checks` | Run all Go checks and tests |
| `scripts/run_rust_checks` | Run all Rust checks and tests |
| `scripts/run_js_checks` | Run all JS/TS checks and tests |
| `scripts/run_python_checks` | Run Python checks |
| `scripts/run_python_security_checks` | Run security scanning |
| `scripts/build_dists` | Build distribution packages |

***

## CI/CD

All pull requests trigger GitHub Actions workflows for each language:

* `.github/workflows/python.yml` - Python checks
* `.github/workflows/go.yml` - Go checks
* `.github/workflows/js.yml` - JavaScript/TypeScript checks
* `.github/workflows/java.yml` - Java checks
* `.github/workflows/rust.yml` - Rust checks

All checks must pass before merging.
