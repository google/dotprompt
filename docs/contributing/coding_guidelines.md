# Instructions for Gemini

You are an expert Python developer contributing to the Google Dotprompt project. When modifying or generating code, you must strictly adhere to the following guidelines.

## 1. Project Context
- **Target Python Version**: Python 3.10 or newer. Ensure code is compatible with Python 3.10+.
- **Language**: Python.
- **Environment Management**: Use `uv` for packaging and environment management.

### Python Libraries
- **JSON**: Use the built-in `json` module or `pydantic` for serialization.
- **Testing**: Use `pytest` and `unittest` for testing.

### Java Libraries
- **JSON**: Use **Jackson** for JSON parsing and serialization. Avoid Gson.
- **Testing**: Use **Google Truth** (`com.google.truth.Truth`) for assertions. Use JUnit 4/5 for test runners.
- **Utilities**: Use **Guava** for immutable collections and common utilities.
- **Dependency Injection**: Use **Dagger** for dependency injection.

### Java Style Guidelines
- **Imports**: Always use proper imports instead of fully qualified type names. Never write `com.github.jknack.handlebars.Context` inline; instead, add an `import` statement and use `Context`.
- **Formatting**: Use `google-java-format` for code formatting.
- **Javadoc**: Write comprehensive Javadoc for all public classes and methods.
- **Doc Sync**: Keep Javadoc comments in sync with the code. When modifying method signatures, parameters, or return types, update the corresponding Javadoc.
- **Method Chaining**: Fluent builder methods should return `this` for chaining.
- Please don't add section marker comments.

## 2. Typing & Style
- **Type Unions**: Use the pipe operator `|` (PEP 604) for union types (e.g., `int | str`) instead of `typing.Union`. Use `| None` for optional types.
- **Generics**: Use standard collection generics (PEP 585) like `list`, `dict`, `tuple` (lowercase) for type hints instead of `typing.List`, `typing.Dict`.
- **Imports**: Import deprecated typing types (`Callable`, `Awaitable`, etc.) from `collections.abc` instead of `typing`.
- **Strict Typing**: Apply type hints strictly to all function arguments and return values. Always include `-> None` for functions that do not return a value.
- **Type Aliases**: Use standard assignment or `TypeAlias` (from `typing`) for type aliases (e.g., `MyAlias = int | str`). Do NOT use the `type` keyword (PEP 695) as it requires Python 3.12+.
- **Enums**: Use `(str, Enum)` for string-based enums to maintain Python 3.10 compatibility. Do not use `StrEnum` until Python 3.10 support is dropped.
- **Interfaces**: Code against interfaces (Protocols), not implementations.
- **Design Patterns**: Use the adapter pattern for optional implementations.
- **Comments**:
  - Use proper punctuation.
  - Avoid comments explaining obvious code.
  - Add TODO comments in the format: `TODO: Fix this later.` when adding stub implementations.

## 3. Documentation
- **Docstrings**: Write comprehensive Google-style docstrings for all modules, classes, and functions.
- **Content Requirements**:
  - **Overview**: A one-line description followed by optional rationale.
  - **Key Operations**: Describe the purpose.
  - **Arguments**: Required for callables.
  - **Returns**: Required for callables.
  - **Examples**: Required for user-facing APIs.
  - **Caveats**: Note any limitations or side effects.

## 4. Formatting
- **Tools**: Format code using `ruff`. See the scripts/fmt script for more details.
- **Line Length**: Limit lines to 120 characters to distinguish vertical code flow.
- **Configuration**: Respect rules in `.editorconfig` or `pyproject.toml`.
- **Wrapping**: Wrap long lines and strings appropriately.

## 5. Testing
- **Frameworks**: Use `pytest` and `unittest`.
- **Docstrings**: Add docstrings to test modules, classes, and functions explaining their scope. Use the Google Python Style Guide for docstrings.
- **Execution**: Run tests via the scripts in `scripts/`.
- **Parity**: If porting tests from another language, maintain 1:1 logic parity; do not invent new behavior.
- **Purity**: Fix underlying code issues rather than special-casing tests.

## 6. Tooling & Ecosystem
- **Static Analysis**: Use `ty` for static type checking.
- **Logging**:
  - Use `structlog` for structured logging.
  - Use the async API (`await logger.ainfo(...)`) within coroutines.
  - Avoid f-strings in log calls; let `structlog` handle formatting (e.g. `logger.info("msg", var=val)`).
  - Use the sync API (`logger.exception(...)`) for exception handling.

## 7. Licensing
- **Header**: Include the following Apache 2.0 license header at the top of each file, ensuring the year is current (e.g., 2025):

```python
# Copyright 2025 Google LLC
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
