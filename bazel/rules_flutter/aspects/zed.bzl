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

"""Zed editor integration aspect for Flutter projects.

This aspect generates Zed-specific configuration files for Flutter development.

## Generated Files

- `.zed/settings.json` - Editor and LSP settings
- `.zed/tasks.json` - Build and run tasks
"""

# =============================================================================
# Zed Settings Generation
# =============================================================================

def _generate_zed_settings(flutter_sdk_path, _package_name):
    """Generate Zed settings.json for Flutter."""
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
        "flutterOutline": true
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
    "**/build/**",
    "**/.flutter-plugins",
    "**/.flutter-plugins-dependencies"
  ],
  "project_panel": {
    "file_icons": true,
    "folder_icons": true,
    "git_status": true
  }
}''' % flutter_sdk_path

def _generate_zed_tasks(_package_name):
    """Generate Zed tasks.json for Flutter."""
    return '''{
  "tasks": [
    {
      "label": "Build All",
      "command": "bazel",
      "args": ["build", "//..."],
      "cwd": "${workspaceFolder}",
      "reveal": "always"
    },
    {
      "label": "Test All",
      "command": "bazel",
      "args": ["test", "//..."],
      "cwd": "${workspaceFolder}",
      "reveal": "always"
    },
    {
      "label": "Run App",
      "command": "bazel",
      "args": ["run", "//:app"],
      "cwd": "${workspaceFolder}",
      "reveal": "always"
    },
    {
      "label": "Run DevTools",
      "command": "bazel",
      "args": ["run", "//:devtools"],
      "cwd": "${workspaceFolder}",
      "reveal": "always"
    },
    {
      "label": "Update Goldens",
      "command": "bazel",
      "args": ["run", "//:update_goldens"],
      "cwd": "${workspaceFolder}",
      "reveal": "always"
    },
    {
      "label": "Analyze",
      "command": "bazel",
      "args": ["build", "//:analyze"],
      "cwd": "${workspaceFolder}",
      "reveal": "always"
    },
    {
      "label": "Pub Get",
      "command": "flutter",
      "args": ["pub", "get"],
      "cwd": "${workspaceFolder}",
      "reveal": "always"
    }
  ]
}'''

# =============================================================================
# Aspect Implementation
# =============================================================================

ZedFlutterInfo = provider(
    doc = "Zed editor configuration for Flutter.",
    fields = {
        "settings": "File: .zed/settings.json",
        "tasks": "File: .zed/tasks.json",
    },
)

def _zed_flutter_aspect_impl(_target, ctx):
    """Implementation of the Zed editor aspect for Flutter."""
    if not hasattr(ctx.rule.attr, "srcs"):
        return []

    package_name = getattr(ctx.rule.attr, "package_name", "") or ctx.label.name

    flutter_sdk_path = ""
    if hasattr(ctx.rule.attr, "flutter_sdk") and ctx.rule.attr.flutter_sdk:
        flutter_bin = ctx.rule.files.flutter_sdk
        if flutter_bin:
            for f in flutter_bin:
                flutter_sdk_path = f.dirname
                break

    settings_file = ctx.actions.declare_file(".zed/settings.json")
    tasks_file = ctx.actions.declare_file(".zed/tasks.json")

    ctx.actions.write(
        output = settings_file,
        content = _generate_zed_settings(flutter_sdk_path, package_name),
    )

    ctx.actions.write(
        output = tasks_file,
        content = _generate_zed_tasks(package_name),
    )

    return [
        OutputGroupInfo(
            zed_ide = depset([settings_file, tasks_file]),
        ),
        ZedFlutterInfo(
            settings = settings_file,
            tasks = tasks_file,
        ),
    ]

zed_flutter_aspect = aspect(
    implementation = _zed_flutter_aspect_impl,
    doc = "Generates Zed editor configuration for Flutter targets.",
)
