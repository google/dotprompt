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

"""Zed editor integration aspect for Dart projects.

# ELI5 (Explain Like I'm 5)

## What is this?

Zed is a high-performance code editor built in Rust. This aspect generates
configuration files so Zed can understand your Dart project built with Bazel.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Zed Editor Integration                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  bazel build //app:lib --aspects=@rules_dart//aspects:zed.bzl%zed_aspect   │
│                                                                             │
│  Generates:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  .zed/                                                              │   │
│  │  ├── settings.json    (Dart SDK path, formatting)                  │   │
│  │  └── tasks.json       (Build and test tasks)                       │   │
│  │                                                                     │   │
│  │  analysis_options.yaml (if not present)                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Zed Configuration

Zed uses a simple JSON configuration format. Key settings include:
- Language server configuration
- Formatter settings
- Task definitions for builds and tests
"""

# =============================================================================
# Zed Settings Generation
# =============================================================================

def _generate_zed_settings(dart_sdk_path, _package_name):
    """Generate Zed settings.json content."""
    return '''{
  "lsp": {
    "dart": {
      "binary": {
        "path": "%s/bin/dart",
        "arguments": ["language-server", "--protocol=lsp"]
      },
      "initialization_options": {
        "onlyAnalyzeProjectsWithOpenFiles": false,
        "suggestFromUnimportedLibraries": true,
        "closingLabels": true,
        "outline": true,
        "flutterOutline": false
      }
    }
  },
  "languages": {
    "Dart": {
      "tab_size": 2,
      "formatter": "language_server",
      "format_on_save": "on",
      "preferred_line_length": 120
    }
  },
  "file_scan_exclusions": [
    "**/bazel-*/**",
    "**/.dart_tool/**",
    "**/build/**"
  ],
  "project_panel": {
    "file_icons": true,
    "folder_icons": true,
    "git_status": true
  }
}''' % dart_sdk_path

def _generate_zed_tasks(package_name):
    """Generate Zed tasks.json content."""
    return '''{
  "tasks": [
    {
      "label": "Build All",
      "command": "bazel",
      "args": ["build", "//..."],
      "cwd": "${workspaceFolder}",
      "use_new_terminal": false,
      "allow_concurrent_runs": false,
      "reveal": "always"
    },
    {
      "label": "Test All",
      "command": "bazel",
      "args": ["test", "//..."],
      "cwd": "${workspaceFolder}",
      "use_new_terminal": false,
      "allow_concurrent_runs": false,
      "reveal": "always"
    },
    {
      "label": "Build Current Package",
      "command": "bazel",
      "args": ["build", "//:%s"],
      "cwd": "${workspaceFolder}",
      "use_new_terminal": false,
      "reveal": "always"
    },
    {
      "label": "Run Analyzer",
      "command": "bazel",
      "args": ["build", "//:analyze"],
      "cwd": "${workspaceFolder}",
      "use_new_terminal": false,
      "reveal": "always"
    },
    {
      "label": "Format Check",
      "command": "bazel",
      "args": ["build", "//:format_check"],
      "cwd": "${workspaceFolder}",
      "use_new_terminal": false,
      "reveal": "always"
    },
    {
      "label": "Pub Get",
      "command": "dart",
      "args": ["pub", "get"],
      "cwd": "${workspaceFolder}",
      "use_new_terminal": false,
      "reveal": "always"
    },
    {
      "label": "Clean Build",
      "command": "bazel",
      "args": ["clean"],
      "cwd": "${workspaceFolder}",
      "use_new_terminal": false,
      "reveal": "always"
    }
  ]
}''' % package_name

def _generate_zed_keymap():
    """Generate Zed keymap.json content with Dart-specific bindings."""
    return '''{
  "bindings": {
    "ctrl-shift-b": "task::Spawn",
    "ctrl-shift-t": ["task::Spawn", { "task_name": "Test All" }],
    "ctrl-shift-f": "editor::Format",
    "f5": ["task::Spawn", { "task_name": "Build All" }]
  }
}'''

# =============================================================================
# Aspect Implementation
# =============================================================================

ZedIdeInfo = provider(
    doc = "Zed editor configuration files.",
    fields = {
        "settings": "File: .zed/settings.json",
        "tasks": "File: .zed/tasks.json",
        "keymap": "File: .zed/keymap.json",
    },
)

def _zed_aspect_impl(_target, ctx):
    """Implementation of the Zed editor aspect."""

    # Only process Dart libraries
    if not hasattr(ctx.rule.attr, "srcs"):
        return []

    # Get package name
    package_name = getattr(ctx.rule.attr, "package_name", "") or ctx.label.name

    # Get Dart SDK path (if available)
    dart_sdk_path = ""
    if hasattr(ctx.rule.attr, "dart_sdk") and ctx.rule.attr.dart_sdk:
        dart_bin = ctx.rule.files.dart_sdk
        if dart_bin:
            for f in dart_bin:
                dart_sdk_path = f.dirname
                break

    # Generate output files
    settings_file = ctx.actions.declare_file(".zed/settings.json")
    tasks_file = ctx.actions.declare_file(".zed/tasks.json")
    keymap_file = ctx.actions.declare_file(".zed/keymap.json")

    # Write settings
    ctx.actions.write(
        output = settings_file,
        content = _generate_zed_settings(dart_sdk_path, package_name),
    )

    # Write tasks
    ctx.actions.write(
        output = tasks_file,
        content = _generate_zed_tasks(package_name),
    )

    # Write keymap
    ctx.actions.write(
        output = keymap_file,
        content = _generate_zed_keymap(),
    )

    return [
        OutputGroupInfo(
            zed_ide = depset([settings_file, tasks_file, keymap_file]),
        ),
        ZedIdeInfo(
            settings = settings_file,
            tasks = tasks_file,
            keymap = keymap_file,
        ),
    ]

zed_aspect = aspect(
    implementation = _zed_aspect_impl,
    doc = """Generates Zed editor configuration files for Dart targets.

Usage:
    bazel build //my:target --aspects=@rules_dart//aspects:zed.bzl%zed_aspect \\
        --output_groups=zed_ide

This generates .zed/ directory with settings, tasks, and keymaps.
""",
)

# =============================================================================
# Convenience Macro
# =============================================================================

def dart_zed_project(name, target, visibility = None):
    """Generate Zed editor configuration for a Dart target.

    Args:
        name: Name of the genrule target.
        target: The dart_library or dart_binary to generate config for.
        visibility: Target visibility.
    """
    native.genrule(
        name = name,
        srcs = [],
        outs = [
            ".zed/settings.json",
            ".zed/tasks.json",
            ".zed/keymap.json",
        ],
        cmd = """
bazel build {target} --aspects=@rules_dart//aspects:zed.bzl%zed_aspect --output_groups=zed_ide
cp -r bazel-bin/.zed/* $(RULEDIR)/.zed/
""".format(target = target),
        visibility = visibility,
    )
