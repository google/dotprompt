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

"""IDE integration aspects for Dart.

This module provides Bazel aspects that generate IDE-specific metadata
for IntelliJ, VSCode, and other IDEs.

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         IDE Integration Aspects                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  bazel build //... --aspects=@rules_dart//:aspects.bzl%dart_ide_info         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  For each dart_library/dart_binary/dart_test:                          │ │
│  │                                                                         │ │
│  │  1. Collect source files                                               │ │
│  │  2. Resolve dependencies                                               │ │
│  │  3. Generate IDE metadata JSON                                         │ │
│  │                                                                         │ │
│  │  Output: target.dart-info.json                                         │ │
│  │  {                                                                      │ │
│  │    "sources": ["lib/main.dart", ...],                                  │ │
│  │    "package_root": "dart/dotprompt",                                   │ │
│  │    "dependencies": ["@pub_deps//http", ...],                           │ │
│  │    "analysis_options": "analysis_options.yaml"                         │ │
│  │  }                                                                      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  IDE plugins consume this to provide:                                        │
│  - Code navigation                                                           │
│  - Auto-completion                                                           │
│  - Dependency resolution                                                     │
│  - Error highlighting                                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Usage:
    # Generate IDE info for all Dart targets
    bazel build //... --aspects=@rules_dart//:aspects.bzl%dart_ide_info \\
        --output_groups=dart_ide_info

    # IntelliJ plugin integration
    # The Bazel IntelliJ plugin uses these aspects automatically
"""

# Provider for IDE information
DartIdeInfo = provider(
    doc = "IDE information for a Dart target.",
    fields = {
        "sources": "Depset of source files",
        "package_root": "String: package root directory",
        "dependencies": "List of dependency labels",
        "analysis_options": "File: analysis_options.yaml if present",
        "pubspec": "File: pubspec.yaml if present",
        "is_test": "Boolean: whether this is a test target",
        "output_file": "File: the generated IDE info JSON",
    },
)

def _dart_ide_info_impl(target, ctx):
    """Aspect implementation for collecting Dart IDE information."""

    # Check if this is a Dart target
    if not hasattr(ctx.rule.attr, "srcs"):
        return []

    # Collect sources
    sources = []
    if hasattr(ctx.rule.attr, "srcs"):
        for src in ctx.rule.attr.srcs:
            sources.extend(src.files.to_list())

    # Get main file if present
    main_file = None
    if hasattr(ctx.rule.attr, "main"):
        main_file = ctx.rule.attr.main

    # Determine package root
    package_root = ctx.label.package

    # Collect dependencies
    deps = []
    if hasattr(ctx.rule.attr, "deps"):
        for dep in ctx.rule.attr.deps:
            deps.append(str(dep.label))

    # Check for analysis_options.yaml
    analysis_options = None
    for f in sources:
        if f.basename == "analysis_options.yaml":
            analysis_options = f
            break

    # Check for pubspec.yaml
    pubspec = None
    if hasattr(ctx.rule.attr, "pubspec") and ctx.rule.attr.pubspec:
        pubspec = ctx.rule.attr.pubspec

    # Determine if this is a test target
    is_test = ctx.rule.kind.endswith("_test")

    # Generate IDE info JSON
    output_file = ctx.actions.declare_file(ctx.label.name + ".dart-info.json")

    ide_info = {
        "label": str(ctx.label),
        "kind": ctx.rule.kind,
        "package_root": package_root,
        "sources": [f.path for f in sources],
        "dependencies": deps,
        "is_test": is_test,
    }

    if main_file:
        ide_info["main"] = main_file.files.to_list()[0].path if hasattr(main_file, "files") else str(main_file)

    if analysis_options:
        ide_info["analysis_options"] = analysis_options.path

    if pubspec:
        ide_info["pubspec"] = pubspec.files.to_list()[0].path if hasattr(pubspec, "files") else str(pubspec)

    # Write JSON
    ctx.actions.write(
        output = output_file,
        content = json.encode(ide_info),
    )

    return [
        DartIdeInfo(
            sources = depset(sources),
            package_root = package_root,
            dependencies = deps,
            analysis_options = analysis_options,
            pubspec = pubspec,
            is_test = is_test,
            output_file = output_file,
        ),
        OutputGroupInfo(
            dart_ide_info = depset([output_file]),
        ),
    ]

dart_ide_info = aspect(
    implementation = _dart_ide_info_impl,
    doc = "Collects IDE information for Dart targets.",
    attr_aspects = ["deps"],
)

# VSCode-specific settings generator
def generate_vscode_settings(dart_targets):
    """Generate VSCode settings for Dart project.

    Args:
        dart_targets: List of DartIdeInfo providers

    Returns:
        Dict suitable for .vscode/settings.json
    """
    return {
        "dart.sdkPath": "${workspaceFolder}/bazel-bin/external/dart_sdk",
        "dart.analysisExcludedFolders": [
            "bazel-bin",
            "bazel-out",
            "bazel-testlogs",
        ],
        "dart.enableCompletionCommitCharacters": True,
    }

# IntelliJ-specific settings generator
def generate_intellij_facet(dart_targets):
    """Generate IntelliJ Dart facet configuration.

    Args:
        dart_targets: List of DartIdeInfo providers

    Returns:
        Dict suitable for .idea facet configuration
    """
    return {
        "type": "Dart",
        "configuration": {
            "sdkPath": "bazel-bin/external/dart_sdk",
        },
    }
