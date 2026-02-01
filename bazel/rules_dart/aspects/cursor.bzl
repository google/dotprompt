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

"""Cursor IDE integration aspect for Dart projects.

# ELI5 (Explain Like I'm 5)

## What is this?

Cursor is an AI-powered code editor. This aspect generates configuration files
so Cursor can understand your Dart project structure built with Bazel.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Cursor IDE Integration                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  bazel build //app:lib --aspects=@rules_dart//aspects:cursor.bzl%cursor    │
│                                                                             │
│  Generates:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  .cursor/                                                           │   │
│  │  ├── settings.json    (Dart SDK path, analysis settings)           │   │
│  │  ├── rules.json       (AI context rules for Dart)                  │   │
│  │  └── context.md       (Project context for AI)                     │   │
│  │                                                                     │   │
│  │  analysis_options.yaml (if not present)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
"""

# =============================================================================
# Cursor Settings Generation
# =============================================================================

def _generate_cursor_settings(dart_sdk_path, _package_name):
    """Generate Cursor settings.json content."""
    return '''{
  "dart.sdkPath": "%s",
  "dart.analysisExcludedFolders": [
    "bazel-bin",
    "bazel-out",
    "bazel-testlogs",
    ".dart_tool"
  ],
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "Dart-Code.dart-code",
  "dart.lineLength": 120,
  "dart.enableSdkFormatter": true,
  "files.watcherExclude": {
    "**/bazel-*/**": true,
    "**/.dart_tool/**": true
  },
  "search.exclude": {
    "**/bazel-*": true,
    "**/.dart_tool": true
  }
}''' % dart_sdk_path

def _generate_cursor_rules(package_name):
    """Generate Cursor AI rules for Dart projects."""
    return '''{
  "rules": [
    {
      "name": "Dart Style Guide",
      "description": "Follow the official Dart style guide",
      "pattern": "**/*.dart",
      "context": "Follow Effective Dart guidelines. Use lowerCamelCase for variables and methods, UpperCamelCase for types."
    },
    {
      "name": "Bazel Build System",
      "description": "This project uses Bazel for builds",
      "pattern": "BUILD.bazel",
      "context": "Use rules_dart macros: dart_library, dart_binary, dart_test. Dependencies should reference labels, not package names."
    },
    {
      "name": "Package: %s",
      "description": "Package-specific context",
      "pattern": "lib/**/*.dart",
      "context": "This is the %s package. Exports should be in lib/%s.dart."
    },
    {
      "name": "Tests",
      "description": "Test file conventions",
      "pattern": "test/**/*.dart",
      "context": "Use package:test for testing. Test files should end with _test.dart."
    }
  ]
}''' % (package_name, package_name, package_name)

def _generate_cursor_context(package_name, sources):
    """Generate Cursor AI context markdown."""
    source_list = "\n".join(["- " + s for s in sources[:20]])
    if len(sources) > 20:
        source_list += "\n- ... and %d more files" % (len(sources) - 20)

    return """# Project Context: %s

## Build System
This project uses **Bazel** with the `rules_dart` ruleset for hermetic builds.

## Structure
- `lib/` - Library source code
- `test/` - Test files
- `bin/` - Executable entry points
- `BUILD.bazel` - Bazel build definitions
- `pubspec.yaml` - Package manifest

## Source Files
%s

## Key Patterns
- Use `bazel build //...` to build
- Use `bazel test //...` to run tests
- Dependencies are managed via `pubspec.yaml` and resolved by Bazel

## Code Style
- Follow Effective Dart guidelines
- Max line length: 120 characters
- Use `dart format` for formatting
""" % (package_name, source_list)

# =============================================================================
# Aspect Implementation
# =============================================================================

CursorIdeInfo = provider(
    doc = "Cursor IDE configuration files.",
    fields = {
        "settings": "File: .cursor/settings.json",
        "rules": "File: .cursor/rules.json",
        "context": "File: .cursor/context.md",
    },
)

def _cursor_aspect_impl(_target, ctx):
    """Implementation of the Cursor IDE aspect."""

    # Only process Dart libraries
    if not hasattr(ctx.rule.attr, "srcs"):
        return []

    # Get package name
    package_name = getattr(ctx.rule.attr, "package_name", "") or ctx.label.name

    # Collect source file paths
    sources = []
    for src in ctx.rule.files.srcs:
        sources.append(src.short_path)

    # Get Dart SDK path (if available)
    dart_sdk_path = ""
    if hasattr(ctx.rule.attr, "dart_sdk") and ctx.rule.attr.dart_sdk:
        dart_bin = ctx.rule.files.dart_sdk
        if dart_bin:
            for f in dart_bin:
                dart_sdk_path = f.dirname
                break

    # Generate output files
    settings_file = ctx.actions.declare_file(".cursor/settings.json")
    rules_file = ctx.actions.declare_file(".cursor/rules.json")
    context_file = ctx.actions.declare_file(".cursor/context.md")

    # Write settings
    ctx.actions.write(
        output = settings_file,
        content = _generate_cursor_settings(dart_sdk_path, package_name),
    )

    # Write rules
    ctx.actions.write(
        output = rules_file,
        content = _generate_cursor_rules(package_name),
    )

    # Write context
    ctx.actions.write(
        output = context_file,
        content = _generate_cursor_context(package_name, sources),
    )

    return [
        OutputGroupInfo(
            cursor_ide = depset([settings_file, rules_file, context_file]),
        ),
        CursorIdeInfo(
            settings = settings_file,
            rules = rules_file,
            context = context_file,
        ),
    ]

cursor_aspect = aspect(
    implementation = _cursor_aspect_impl,
    doc = """Generates Cursor IDE configuration files for Dart targets.

Usage:
    bazel build //my:target --aspects=@rules_dart//aspects:cursor.bzl%cursor_aspect \\
        --output_groups=cursor_ide

This generates .cursor/ directory with settings and AI context.
""",
)

# =============================================================================
# Convenience Macro
# =============================================================================

def dart_cursor_project(name, target, visibility = None):
    """Generate Cursor IDE configuration for a Dart target.

    Args:
        name: Name of the genrule target.
        target: The dart_library or dart_binary to generate config for.
        visibility: Target visibility.
    """
    native.genrule(
        name = name,
        srcs = [],
        outs = [
            ".cursor/settings.json",
            ".cursor/rules.json",
            ".cursor/context.md",
        ],
        cmd = """
bazel build {target} --aspects=@rules_dart//aspects:cursor.bzl%cursor_aspect --output_groups=cursor_ide
cp -r bazel-bin/.cursor/* $(RULEDIR)/.cursor/
""".format(target = target),
        visibility = visibility,
    )
