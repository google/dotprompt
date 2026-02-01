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

"""IDE integration aspects for Flutter.

This module provides aspects for generating IDE project files, following
patterns from rules_go (go_ide_aspect) and rules_kotlin (kt_ide).

## Supported IDEs

- IntelliJ IDEA / Android Studio
- VS Code
- Vim/Neovim (via LSP)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IDE Aspect Flow                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  bazel build :app --aspects=@rules_flutter//aspects:ide.bzl%flutter_ide     │
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  Flutter Rules  │───▶│  IDE Aspect     │───▶│  IDE Files      │         │
│  │  (providers)    │    │  (collects info)│    │  (generated)    │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
│  Collected Info:                  Generated Files:                         │
│  • Source roots                   • .idea/ (IntelliJ)                      │
│  • Test roots                     • .vscode/ (VS Code)                     │
│  • Asset directories              • analysis_options.yaml                  │
│  • Dependencies                   • launch.json                            │
│  • SDK path                       • settings.json                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```bash
# Generate IntelliJ project files
bazel build :app --aspects=@rules_flutter//aspects:ide.bzl%flutter_intellij_aspect \
    --output_groups=intellij

# Generate VS Code workspace
bazel build :app --aspects=@rules_flutter//aspects:ide.bzl%flutter_vscode_aspect \
    --output_groups=vscode
```
"""

# =============================================================================
# Providers
# =============================================================================

FlutterIdeInfo = provider(
    doc = "IDE integration information for Flutter targets.",
    fields = {
        "source_roots": "Depset of source root directories.",
        "test_roots": "Depset of test root directories.",
        "asset_roots": "Depset of asset directories.",
        "package_name": "String: Package name from pubspec.yaml.",
        "package_uri": "String: Package URI (package:name/).",
        "sdk_path": "String: Path to Flutter SDK.",
        "dart_sdk_path": "String: Path to Dart SDK.",
        "analysis_options": "File: analysis_options.yaml if present.",
        "pubspec": "File: pubspec.yaml.",
        "dependencies": "List of package dependencies.",
        "dev_dependencies": "List of dev dependencies.",
    },
)

# =============================================================================
# IntelliJ Aspect
# =============================================================================

def _collect_flutter_ide_info(_target, ctx):
    """Collect IDE info from a Flutter target.

    Args:
        _target: The target being analyzed (unused, required by aspect API).
        ctx: The rule context.

    Returns:
        FlutterIdeInfo provider with collected information.
    """
    source_roots = []
    test_roots = []
    asset_roots = []
    package_name = ""
    pubspec = None
    analysis_options = None

    # Check for FlutterLibraryInfo
    if hasattr(ctx.rule.attr, "srcs"):
        for src in ctx.rule.files.srcs:
            # Determine root from file path
            if "/lib/" in src.path:
                root = src.path.split("/lib/")[0] + "/lib"
                source_roots.append(root)
            elif "/test/" in src.path:
                root = src.path.split("/test/")[0] + "/test"
                test_roots.append(root)

    if hasattr(ctx.rule.attr, "assets"):
        for asset in ctx.rule.files.assets:
            if "/assets/" in asset.path:
                root = asset.path.split("/assets/")[0] + "/assets"
                asset_roots.append(root)

    if hasattr(ctx.rule.attr, "pubspec") and ctx.rule.attr.pubspec:
        pubspec = ctx.rule.file.pubspec

        # Extract package name from pubspec path
        package_name = pubspec.dirname.split("/")[-1]

    return FlutterIdeInfo(
        source_roots = depset(source_roots),
        test_roots = depset(test_roots),
        asset_roots = depset(asset_roots),
        package_name = package_name,
        package_uri = "package:{}/".format(package_name) if package_name else "",
        sdk_path = "",  # Filled by toolchain
        dart_sdk_path = "",
        analysis_options = analysis_options,
        pubspec = pubspec,
        dependencies = [],
        dev_dependencies = [],
    )

def _flutter_intellij_aspect_impl(target, ctx):
    """Implementation of IntelliJ IDE aspect."""
    ide_info = _collect_flutter_ide_info(target, ctx)

    # Generate IntelliJ module file (.iml)
    iml_file = ctx.actions.declare_file("{}.iml".format(ctx.label.name))

    iml_content = """<?xml version="1.0" encoding="UTF-8"?>
<module type="JAVA_MODULE" version="4">
  <component name="NewModuleRootManager" inherit-compiler-output="true">
    <exclude-output />
    <content url="file://$MODULE_DIR$">
{source_folders}
{test_folders}
{asset_folders}
      <excludeFolder url="file://$MODULE_DIR$/build" />
      <excludeFolder url="file://$MODULE_DIR$/.dart_tool" />
    </content>
    <orderEntry type="inheritedJdk" />
    <orderEntry type="sourceFolder" forTests="false" />
    <orderEntry type="library" name="Dart SDK" level="project" />
    <orderEntry type="library" name="Flutter SDK" level="project" />
  </component>
</module>
"""

    source_folders = "\n".join([
        '      <sourceFolder url="file://$MODULE_DIR$/lib" isTestSource="false" />'
        for _ in ide_info.source_roots.to_list()[:1]  # Just one lib folder
    ]) or '      <sourceFolder url="file://$MODULE_DIR$/lib" isTestSource="false" />'

    test_folders = "\n".join([
        '      <sourceFolder url="file://$MODULE_DIR$/test" isTestSource="true" />'
        for _ in ide_info.test_roots.to_list()[:1]
    ]) or ""

    asset_folders = "\n".join([
        '      <sourceFolder url="file://$MODULE_DIR$/assets" isTestSource="false" type="java-resource" />'
        for _ in ide_info.asset_roots.to_list()[:1]
    ]) or ""

    ctx.actions.write(
        output = iml_file,
        content = iml_content.format(
            source_folders = source_folders,
            test_folders = test_folders,
            asset_folders = asset_folders,
        ),
    )

    # Generate run configuration
    run_config = ctx.actions.declare_file(".idea/runConfigurations/{}_debug.xml".format(ctx.label.name))

    run_config_content = """<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="{name} (Debug)" type="FlutterRunConfigurationType" factoryName="Flutter">
    <option name="filePath" value="$PROJECT_DIR$/lib/main.dart" />
    <option name="buildMode" value="debug" />
    <method v="2" />
  </configuration>
</component>
""".format(name = ctx.label.name)

    ctx.actions.write(output = run_config, content = run_config_content)

    return [
        OutputGroupInfo(
            intellij = depset([iml_file, run_config]),
        ),
        ide_info,
    ]

flutter_intellij_aspect = aspect(
    implementation = _flutter_intellij_aspect_impl,
    doc = "Generates IntelliJ IDEA / Android Studio project files.",
    attr_aspects = ["deps"],
)

# =============================================================================
# VS Code Aspect
# =============================================================================

def _flutter_vscode_aspect_impl(target, ctx):
    """Implementation of VS Code IDE aspect."""
    ide_info = _collect_flutter_ide_info(target, ctx)

    # Generate launch.json
    launch_json = ctx.actions.declare_file(".vscode/launch.json")
    launch_content = """{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flutter: Debug",
            "type": "dart",
            "request": "launch",
            "program": "lib/main.dart",
            "flutterMode": "debug"
        },
        {
            "name": "Flutter: Profile",
            "type": "dart",
            "request": "launch",
            "program": "lib/main.dart",
            "flutterMode": "profile"
        },
        {
            "name": "Flutter: Release",
            "type": "dart",
            "request": "launch",
            "program": "lib/main.dart",
            "flutterMode": "release"
        }
    ]
}
"""
    ctx.actions.write(output = launch_json, content = launch_content)

    # Generate settings.json
    settings_json = ctx.actions.declare_file(".vscode/settings.json")
    settings_content = """{
    "dart.flutterSdkPath": "${env:FLUTTER_SDK}",
    "dart.lineLength": 120,
    "dart.enableSdkFormatter": true,
    "dart.previewFlutterUiGuides": true,
    "dart.previewFlutterUiGuidesCustomTracking": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        "source.organizeImports": "explicit"
    },
    "[dart]": {
        "editor.formatOnSave": true,
        "editor.formatOnType": true,
        "editor.rulers": [120],
        "editor.selectionHighlight": false,
        "editor.tabCompletion": "onlySnippets",
        "editor.wordBasedSuggestions": "off"
    }
}
"""
    ctx.actions.write(output = settings_json, content = settings_content)

    # Generate tasks.json for Bazel integration
    tasks_json = ctx.actions.declare_file(".vscode/tasks.json")
    tasks_content = """{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Bazel: Build",
            "type": "shell",
            "command": "bazel",
            "args": ["build", "//..."],
            "group": "build",
            "problemMatcher": []
        },
        {
            "label": "Bazel: Test",
            "type": "shell",
            "command": "bazel",
            "args": ["test", "//..."],
            "group": "test",
            "problemMatcher": []
        },
        {
            "label": "Flutter: Pub Get",
            "type": "shell",
            "command": "flutter",
            "args": ["pub", "get"],
            "problemMatcher": []
        },
        {
            "label": "Flutter: Analyze",
            "type": "shell",
            "command": "flutter",
            "args": ["analyze"],
            "problemMatcher": "$dart-analyze"
        }
    ]
}
"""
    ctx.actions.write(output = tasks_json, content = tasks_content)

    # Generate extensions.json with recommended extensions
    extensions_json = ctx.actions.declare_file(".vscode/extensions.json")
    extensions_content = """{
    "recommendations": [
        "Dart-Code.dart-code",
        "Dart-Code.flutter",
        "BazelBuild.vscode-bazel",
        "esbenp.prettier-vscode"
    ]
}
"""
    ctx.actions.write(output = extensions_json, content = extensions_content)

    return [
        OutputGroupInfo(
            vscode = depset([launch_json, settings_json, tasks_json, extensions_json]),
        ),
        ide_info,
    ]

flutter_vscode_aspect = aspect(
    implementation = _flutter_vscode_aspect_impl,
    doc = "Generates VS Code workspace files.",
    attr_aspects = ["deps"],
)

# =============================================================================
# Combined IDE Aspect
# =============================================================================

def _flutter_ide_aspect_impl(target, ctx):
    """Combined IDE aspect generating files for all supported IDEs."""
    ide_info = _collect_flutter_ide_info(target, ctx)

    outputs = []

    # IntelliJ files
    iml_file = ctx.actions.declare_file("{}.iml".format(ctx.label.name))
    ctx.actions.write(
        output = iml_file,
        content = """<?xml version="1.0" encoding="UTF-8"?>
<module type="JAVA_MODULE" version="4">
  <component name="NewModuleRootManager" inherit-compiler-output="true">
    <content url="file://$MODULE_DIR$">
      <sourceFolder url="file://$MODULE_DIR$/lib" isTestSource="false" />
      <sourceFolder url="file://$MODULE_DIR$/test" isTestSource="true" />
      <excludeFolder url="file://$MODULE_DIR$/build" />
    </content>
    <orderEntry type="inheritedJdk" />
    <orderEntry type="sourceFolder" forTests="false" />
  </component>
</module>
""",
    )
    outputs.append(iml_file)

    # VS Code launch.json
    launch_json = ctx.actions.declare_file("{}_launch.json".format(ctx.label.name))
    ctx.actions.write(
        output = launch_json,
        content = """{
    "version": "0.2.0",
    "configurations": [
        {"name": "Debug", "type": "dart", "request": "launch", "program": "lib/main.dart"}
    ]
}
""",
    )
    outputs.append(launch_json)

    return [
        OutputGroupInfo(
            ide = depset(outputs),
            intellij = depset([iml_file]),
            vscode = depset([launch_json]),
        ),
        ide_info,
    ]

flutter_ide_aspect = aspect(
    implementation = _flutter_ide_aspect_impl,
    doc = "Generates IDE project files for IntelliJ and VS Code.",
    attr_aspects = ["deps"],
)
