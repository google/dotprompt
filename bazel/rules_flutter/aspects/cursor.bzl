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

"""Cursor IDE integration aspect for Flutter projects.

This aspect generates Cursor-specific configuration files that provide
AI context for Flutter development.

## Generated Files

- `.cursor/settings.json` - Editor settings
- `.cursor/rules.json` - AI rules for Flutter patterns
- `.cursor/context.md` - Project context for AI
"""

# =============================================================================
# Cursor Settings Generation
# =============================================================================

def _generate_cursor_settings(flutter_sdk_path, _package_name):
    """Generate Cursor settings.json for Flutter."""
    return '''{
  "dart.flutterSdkPath": "%s",
  "dart.analysisExcludedFolders": [
    "bazel-bin",
    "bazel-out",
    "bazel-testlogs",
    ".dart_tool",
    "build"
  ],
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "Dart-Code.dart-code",
  "dart.lineLength": 120,
  "dart.enableSdkFormatter": true,
  "dart.previewFlutterUiGuides": true,
  "dart.previewFlutterUiGuidesCustomTracking": true,
  "files.watcherExclude": {
    "**/bazel-*/**": true,
    "**/.dart_tool/**": true,
    "**/build/**": true,
    "**/.flutter-plugins": true
  },
  "search.exclude": {
    "**/bazel-*": true,
    "**/.dart_tool": true,
    "**/build": true
  }
}''' % flutter_sdk_path

def _generate_cursor_rules(_package_name):
    """Generate Cursor AI rules for Flutter projects."""
    return '''{
  "rules": [
    {
      "name": "Flutter Widget Patterns",
      "description": "Follow Flutter widget best practices",
      "pattern": "**/*.dart",
      "context": "Use StatelessWidget when no state is needed. Use StatefulWidget sparingly. Prefer const constructors. Use BuildContext appropriately."
    },
    {
      "name": "Bazel Build System",
      "description": "This project uses Bazel for builds",
      "pattern": "BUILD.bazel",
      "context": "Use rules_flutter macros: flutter_library, flutter_application, flutter_test. Don't suggest 'flutter run' - use 'bazel run' instead."
    },
    {
      "name": "Widget Tree Structure",
      "description": "Keep widget trees clean",
      "pattern": "lib/**/*.dart",
      "context": "Extract widgets into separate files when they exceed 100 lines. Use composition over inheritance."
    },
    {
      "name": "Golden Tests",
      "description": "Widget screenshot testing",
      "pattern": "test/**/*_test.dart",
      "context": "Use matchesGoldenFile for visual regression testing. Golden files are in test/goldens/."
    },
    {
      "name": "State Management",
      "description": "State management patterns",
      "pattern": "lib/**/*.dart",
      "context": "Use Provider, Riverpod, or Bloc for state management. Keep business logic out of widgets."
    }
  ]
}'''

def _generate_cursor_context(package_name, sources, _is_flutter = True):
    """Generate Cursor AI context markdown for Flutter."""
    source_list = "\n".join(["- " + s for s in sources[:20]])
    if len(sources) > 20:
        source_list += "\n- ... and %d more files" % (len(sources) - 20)

    return """# Project Context: %s

## Framework
This is a **Flutter** project built with **Bazel** using `rules_flutter`.

## Build Commands
- Build: `bazel build //...`
- Test: `bazel test //...`
- Run: `bazel run //:app`
- Analyze: `bazel build //:analyze`
- DevTools: `bazel run //:devtools`

## Structure
- `lib/` - Application source code
- `lib/widgets/` - Reusable widgets  
- `lib/screens/` - Screen/page widgets
- `test/` - Widget and unit tests
- `test/goldens/` - Golden test images
- `assets/` - Images, fonts, etc.

## Source Files
%s

## Flutter Patterns

### Widget Structure
```dart
class MyWidget extends StatelessWidget {
  const MyWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return const Placeholder();
  }
}
```

### Testing Pattern
```dart
testWidgets('MyWidget displays correctly', (tester) async {
  await tester.pumpWidget(const MaterialApp(
    home: MyWidget(),
  ));
  expect(find.byType(MyWidget), findsOneWidget);
});
```

## Key Conventions
- Use `const` constructors where possible
- Extract widgets over 100 lines
- Keep build methods under 30 lines
- Use named parameters for clarity
""" % (package_name, source_list)

# =============================================================================
# Aspect Implementation
# =============================================================================

CursorFlutterInfo = provider(
    doc = "Cursor IDE configuration for Flutter.",
    fields = {
        "settings": "File: .cursor/settings.json",
        "rules": "File: .cursor/rules.json",
        "context": "File: .cursor/context.md",
    },
)

def _cursor_flutter_aspect_impl(_target, ctx):
    """Implementation of the Cursor IDE aspect for Flutter."""
    if not hasattr(ctx.rule.attr, "srcs"):
        return []

    package_name = getattr(ctx.rule.attr, "package_name", "") or ctx.label.name

    sources = []
    for src in ctx.rule.files.srcs:
        sources.append(src.short_path)

    flutter_sdk_path = ""
    if hasattr(ctx.rule.attr, "flutter_sdk") and ctx.rule.attr.flutter_sdk:
        flutter_bin = ctx.rule.files.flutter_sdk
        if flutter_bin:
            for f in flutter_bin:
                flutter_sdk_path = f.dirname
                break

    settings_file = ctx.actions.declare_file(".cursor/settings.json")
    rules_file = ctx.actions.declare_file(".cursor/rules.json")
    context_file = ctx.actions.declare_file(".cursor/context.md")

    ctx.actions.write(
        output = settings_file,
        content = _generate_cursor_settings(flutter_sdk_path, package_name),
    )

    ctx.actions.write(
        output = rules_file,
        content = _generate_cursor_rules(package_name),
    )

    ctx.actions.write(
        output = context_file,
        content = _generate_cursor_context(package_name, sources),
    )

    return [
        OutputGroupInfo(
            cursor_ide = depset([settings_file, rules_file, context_file]),
        ),
        CursorFlutterInfo(
            settings = settings_file,
            rules = rules_file,
            context = context_file,
        ),
    ]

cursor_flutter_aspect = aspect(
    implementation = _cursor_flutter_aspect_impl,
    doc = "Generates Cursor IDE configuration for Flutter targets.",
)
