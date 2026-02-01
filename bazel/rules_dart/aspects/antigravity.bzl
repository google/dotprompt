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

"""Antigravity IDE integration aspect for Dart projects.

# ELI5 (Explain Like I'm 5)

## What is this?

Antigravity is Google's agentic AI-powered code assistant. This aspect generates
configuration files so Antigravity can understand your Dart project structure
and provide accurate, context-aware assistance.

## Why Antigravity?

Antigravity uses GEMINI.md files for project-specific guidance. By generating
these files from build metadata, the AI assistant has accurate knowledge of:
- Project structure and dependencies
- Build system (Bazel with rules_dart)
- Code conventions and patterns
- Available tooling

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Antigravity IDE Integration                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  bazel build //app:lib --aspects=@rules_dart//aspects:antigravity.bzl%...  │
│                                                                             │
│  Generates:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  .gemini/                                                           │   │
│  │  └── GEMINI.md        (Project context for AI assistant)           │   │
│  │                                                                     │   │
│  │  GEMINI.md            (Root project guidance)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
"""

# =============================================================================
# GEMINI.md Content Generation
# =============================================================================

def _generate_gemini_md(package_name, sources, deps, is_flutter = False):
    """Generate GEMINI.md content for Antigravity context."""
    source_list = "\n".join(["- `" + s + "`" for s in sources[:30]])
    if len(sources) > 30:
        source_list += "\n- ... and %d more files" % (len(sources) - 30)

    dep_list = "\n".join(["- `" + d + "`" for d in deps[:20]])
    if len(deps) > 20:
        dep_list += "\n- ... and %d more dependencies" % (len(deps) - 20)

    framework = "Flutter" if is_flutter else "Dart"

    return """# {package_name} Development Guidelines

## Overview

This is a **{framework}** project built with **Bazel** using the `rules_dart` ruleset.
Antigravity should use this context to provide accurate assistance.

## Build System

* **Build Tool**: Bazel with `rules_dart`
* **Package Manager**: pub (managed by Bazel)
* **SDK Version**: Dart 3.x

### Common Commands

| Command | Description |
|---------|-------------|
| `bazel build //...` | Build all targets |
| `bazel test //...` | Run all tests |
| `bazel run //:main` | Run the main application |
| `bazel build //:analyze` | Run static analysis |
| `bazel build //:format_check` | Check code formatting |

## Project Structure

```
{package_name}/
\342\224\234\342\224\200\342\224\200 lib/           # Library source code
\342\224\202   \342\224\224\342\224\200\342\224\200 src/       # Private implementation
\342\224\234\342\224\200\342\224\200 test/          # Unit and widget tests
\342\224\234\342\224\200\342\224\200 bin/           # Executable entry points
\342\224\234\342\224\200\342\224\200 BUILD.bazel    # Bazel build definitions
\342\224\234\342\224\200\342\224\200 pubspec.yaml   # Package manifest
\342\224\224\342\224\200\342\224\200 GEMINI.md      # This file (AI context)
```

## Source Files

{source_list}

## Dependencies

{dep_list}

## Code Style

* **Formatter**: `dart format` with 120-character line limit
* **Linter**: Standard Dart lints from `package:lints`
* **Style Guide**: Follow [Effective Dart](https://dart.dev/guides/language/effective-dart)

### Key Conventions

1. Use `lowerCamelCase` for variables, functions, and parameters
2. Use `UpperCamelCase` for types, classes, and enums
3. Use `lowercase_with_underscores` for libraries and file names
4. Prefer `final` over `var` when values don't change
5. Use async/await over raw Futures

## Testing

* **Framework**: `package:test`
* **Test Files**: Named `*_test.dart` in `test/` directory
* **Run Tests**: `bazel test //...`

### Test Patterns

```dart
import 'package:test/test.dart';
import 'package:{package_name}/{package_name}.dart';

void main() {{
  group('{package_name}', () {{
    test('should work', () {{
      expect(true, isTrue);
    }});
  }});
}}
```

## Bazel Rules Reference

| Rule | Purpose |
|------|---------|
| `dart_library` | Create a reusable library |
| `dart_binary` | Create an executable |
| `dart_test` | Create a test target |
| `dart_native_binary` | Compile to native executable |
| `dart_analyze` | Run static analysis |
| `dart_format_check` | Validate formatting |

## AI Assistant Guidelines

When helping with this project:

1. **Use Bazel for builds** - Don't suggest `dart run` or `flutter run` directly
2. **Follow existing patterns** - Match the code style in existing files
3. **Prefer immutability** - Use `final`, `const`, and immutable collections
4. **Document public APIs** - Add doc comments to public members
5. **Write tests** - Suggest tests for new functionality
6. **Handle errors** - Use Result types or proper exception handling

## Common Tasks

### Adding a New File

1. Create the file in `lib/src/`
2. Export from `lib/{package_name}.dart` if public
3. Update `BUILD.bazel` if needed (usually auto-included via glob)

### Adding a Dependency

1. Add to `pubspec.yaml`
2. Run `bazel build //:pub_get` or `dart pub get`
3. Use in code with `import 'package:dep_name/...';`

### Running in Development

```bash
# Build and run
bazel run //:main

# Run with arguments
bazel run //:main -- --arg1 --arg2
```
""".format(
        package_name = package_name,
        framework = framework,
        source_list = source_list,
        dep_list = dep_list,
    )

def _generate_antigravity_context(package_name, _sources):
    """Generate .gemini/context.json for additional AI context."""
    return '''{
  "project": {
    "name": "%s",
    "type": "dart",
    "build_system": "bazel",
    "ruleset": "rules_dart"
  },
  "conventions": {
    "line_length": 120,
    "indentation": 2,
    "quotes": "single",
    "trailing_commas": true
  },
  "ai_hints": [
    "This project uses Bazel, not pub run directly",
    "Dependencies are managed via pubspec.yaml but resolved by Bazel",
    "Use dart_library, dart_binary, dart_test rules",
    "Follow Effective Dart guidelines",
    "Tests go in test/ directory with _test.dart suffix"
  ],
  "exclude_patterns": [
    "bazel-*/**",
    ".dart_tool/**",
    "build/**"
  ]
}''' % package_name

# =============================================================================
# Aspect Implementation
# =============================================================================

AntigravityInfo = provider(
    doc = "Antigravity IDE configuration files.",
    fields = {
        "gemini_md": "File: GEMINI.md project guidance",
        "context_json": "File: .gemini/context.json",
    },
)

def _antigravity_aspect_impl(_target, ctx):
    """Implementation of the Antigravity IDE aspect."""

    # Only process Dart libraries
    if not hasattr(ctx.rule.attr, "srcs"):
        return []

    # Get package name
    package_name = getattr(ctx.rule.attr, "package_name", "") or ctx.label.name

    # Collect source file paths
    sources = []
    for src in ctx.rule.files.srcs:
        sources.append(src.short_path)

    # Collect dependency labels
    deps = []
    if hasattr(ctx.rule.attr, "deps"):
        for dep in ctx.rule.attr.deps:
            deps.append(str(dep.label))

    # Check if Flutter (has flutter-specific attributes)
    is_flutter = hasattr(ctx.rule.attr, "assets") or "flutter" in package_name.lower()

    # Generate output files
    gemini_file = ctx.actions.declare_file("GEMINI.md")
    context_file = ctx.actions.declare_file(".gemini/context.json")

    # Write GEMINI.md
    ctx.actions.write(
        output = gemini_file,
        content = _generate_gemini_md(package_name, sources, deps, is_flutter),
    )

    # Write context.json
    ctx.actions.write(
        output = context_file,
        content = _generate_antigravity_context(package_name, sources),
    )

    return [
        OutputGroupInfo(
            antigravity_ide = depset([gemini_file, context_file]),
        ),
        AntigravityInfo(
            gemini_md = gemini_file,
            context_json = context_file,
        ),
    ]

antigravity_aspect = aspect(
    implementation = _antigravity_aspect_impl,
    doc = """Generates Antigravity IDE configuration files for Dart targets.

Usage:
    bazel build //my:target --aspects=@rules_dart//aspects:antigravity.bzl%antigravity_aspect \\
        --output_groups=antigravity_ide

This generates GEMINI.md and .gemini/context.json for AI assistant context.
""",
)

# =============================================================================
# Convenience Macro
# =============================================================================

def dart_antigravity_project(name, target, visibility = None):
    """Generate Antigravity IDE configuration for a Dart target.

    Args:
        name: Name of the genrule target.
        target: The dart_library or dart_binary to generate config for.
        visibility: Target visibility.
    """
    native.genrule(
        name = name,
        srcs = [],
        outs = [
            "GEMINI.md",
            ".gemini/context.json",
        ],
        cmd = """
bazel build {target} --aspects=@rules_dart//aspects:antigravity.bzl%antigravity_aspect --output_groups=antigravity_ide
cp bazel-bin/GEMINI.md $(RULEDIR)/
mkdir -p $(RULEDIR)/.gemini
cp bazel-bin/.gemini/context.json $(RULEDIR)/.gemini/
""".format(target = target),
        visibility = visibility,
    )
