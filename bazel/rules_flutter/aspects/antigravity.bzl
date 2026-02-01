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

"""Antigravity IDE integration aspect for Flutter projects.

This aspect generates GEMINI.md and context files for Google's Antigravity
AI-powered code assistant, providing Flutter-specific context.

## Generated Files

- `GEMINI.md` - Project development guidelines
- `.gemini/context.json` - Structured project context
"""

# =============================================================================
# GEMINI.md Generation for Flutter
# =============================================================================

def _generate_gemini_md(package_name, sources, deps):
    """Generate GEMINI.md for Flutter projects."""
    source_list = "\n".join(["- `" + s + "`" for s in sources[:30]])
    if len(sources) > 30:
        source_list += "\n- ... and %d more files" % (len(sources) - 30)

    dep_list = "\n".join(["- `" + d + "`" for d in deps[:20]])
    if len(deps) > 20:
        dep_list += "\n- ... and %d more dependencies" % (len(deps) - 20)

    return '''# {package_name} Flutter Development Guidelines

## Overview

This is a **Flutter** application built with **Bazel** using `rules_flutter`.
Antigravity should use this context for accurate Flutter-specific assistance.

## Build System

* **Build Tool**: Bazel with `rules_flutter`
* **Package Manager**: pub (managed by Bazel)
* **Flutter SDK**: Hermetically managed via Bazel

### Common Commands

| Command | Description |
|---------|-------------|
| `bazel build //...` | Build all targets |
| `bazel test //...` | Run all tests |
| `bazel run //:app` | Run the application |
| `bazel run //:devtools` | Launch DevTools |
| `bazel run //:update_goldens` | Update golden test images |
| `bazel build //:analyze` | Run static analysis |

## Project Structure

```
{package_name}/
├── lib/
│   ├── main.dart          # Entry point
│   ├── app.dart           # App widget
│   ├── screens/           # Screen widgets
│   ├── widgets/           # Reusable widgets
│   ├── models/            # Data models
│   └── services/          # Business logic
├── test/
│   ├── widget_test.dart   # Widget tests
│   └── goldens/           # Golden test images
├── assets/
│   ├── images/            # Image assets
│   └── fonts/             # Custom fonts
├── BUILD.bazel            # Bazel build file
├── pubspec.yaml           # Package manifest
└── GEMINI.md              # This file
```

## Source Files

{source_list}

## Dependencies

{dep_list}

## Flutter Patterns

### Widget Creation
```dart
class MyWidget extends StatelessWidget {{
  const MyWidget({{
    super.key,
    required this.title,
  }});

  final String title;

  @override
  Widget build(BuildContext context) {{
    return Text(title);
  }}
}}
```

### State Management
- Use `Provider`, `Riverpod`, or `Bloc` for state
- Keep widgets "dumb" - move logic to services
- Use `ChangeNotifier` for simple reactive state

### Testing
```dart
testWidgets('MyWidget test', (tester) async {{
  await tester.pumpWidget(const MaterialApp(
    home: MyWidget(title: 'Test'),
  ));

  expect(find.text('Test'), findsOneWidget);
}});
```

### Golden Tests
```dart
testWidgets('MyWidget golden', (tester) async {{
  await tester.pumpWidget(const MyWidget());
  await expectLater(
    find.byType(MyWidget),
    matchesGoldenFile('goldens/my_widget.png'),
  );
}});
```

## Bazel Rules Reference

| Rule | Purpose |
|------|---------|
| `flutter_library` | Create a reusable library |
| `flutter_application` | Build the main app |
| `flutter_test` | Run widget tests |
| `flutter_golden_test` | Run golden tests |
| `flutter_devtools` | Launch DevTools |
| `flutter_analyze` | Static analysis |

## AI Assistant Guidelines

When helping with this Flutter project:

1. **Use Bazel commands** - Not `flutter run` directly
2. **Prefer const widgets** - Use `const` constructors
3. **Extract widgets** - Keep files under 300 lines
4. **Write tests** - Add widget tests for new UI
5. **Use golden tests** - For visual regression testing
6. **Follow Material 3** - Use Material 3 design patterns

## Common Tasks

### Adding a New Screen

1. Create `lib/screens/new_screen.dart`
2. Add route in app router
3. Create widget test in `test/screens/`
4. Add golden test for visual regression

### Adding Assets

1. Add file to `assets/` directory
2. Update `pubspec.yaml` assets section
3. Use `AssetImage` or `Image.asset`

### Hot Reload During Development

For hot reload, use flutter directly:
```bash
cd $(bazel info workspace)
flutter run
```
'''.format(
        package_name = package_name,
        source_list = source_list,
        dep_list = dep_list,
    )

def _generate_antigravity_context(package_name):
    """Generate .gemini/context.json for Flutter."""
    return '''{
  "project": {
    "name": "%s",
    "type": "flutter",
    "build_system": "bazel",
    "ruleset": "rules_flutter"
  },
  "flutter": {
    "platforms": ["android", "ios", "web", "macos", "linux", "windows"],
    "material_version": 3,
    "null_safety": true
  },
  "conventions": {
    "line_length": 120,
    "indentation": 2,
    "prefer_const": true,
    "trailing_commas": true
  },
  "ai_hints": [
    "Use Bazel for builds, not flutter CLI directly",
    "Prefer StatelessWidget over StatefulWidget",
    "Use const constructors where possible",
    "Keep widget files under 300 lines",
    "Write golden tests for visual regression",
    "Use Provider/Riverpod for state management"
  ],
  "exclude_patterns": [
    "bazel-*/**",
    ".dart_tool/**",
    "build/**",
    ".flutter-plugins"
  ]
}''' % package_name

# =============================================================================
# Aspect Implementation
# =============================================================================

AntigravityFlutterInfo = provider(
    doc = "Antigravity IDE configuration for Flutter.",
    fields = {
        "gemini_md": "File: GEMINI.md",
        "context_json": "File: .gemini/context.json",
    },
)

def _antigravity_flutter_aspect_impl(_target, ctx):
    """Implementation of the Antigravity IDE aspect for Flutter."""
    if not hasattr(ctx.rule.attr, "srcs"):
        return []

    package_name = getattr(ctx.rule.attr, "package_name", "") or ctx.label.name

    sources = []
    for src in ctx.rule.files.srcs:
        sources.append(src.short_path)

    deps = []
    if hasattr(ctx.rule.attr, "deps"):
        for dep in ctx.rule.attr.deps:
            deps.append(str(dep.label))

    gemini_file = ctx.actions.declare_file("GEMINI.md")
    context_file = ctx.actions.declare_file(".gemini/context.json")

    ctx.actions.write(
        output = gemini_file,
        content = _generate_gemini_md(package_name, sources, deps),
    )

    ctx.actions.write(
        output = context_file,
        content = _generate_antigravity_context(package_name),
    )

    return [
        OutputGroupInfo(
            antigravity_ide = depset([gemini_file, context_file]),
        ),
        AntigravityFlutterInfo(
            gemini_md = gemini_file,
            context_json = context_file,
        ),
    ]

antigravity_flutter_aspect = aspect(
    implementation = _antigravity_flutter_aspect_impl,
    doc = "Generates Antigravity IDE configuration for Flutter targets.",
)
