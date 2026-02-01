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

/// Spec-based conformance tests for Dotprompt Dart implementation.
///
/// This test file reads YAML spec files and runs the defined test cases
/// against the Dart implementation to ensure cross-runtime compatibility.
library;

import "dart:io";

import "package:dotprompt/dotprompt.dart";
import "package:test/test.dart";
import "package:yaml/yaml.dart";

void main() {
  var specRelativePaths = <String>[];
  final envSpecFile = Platform.environment["SPEC_FILE"];
  final workspaceRoot = _findWorkspaceRoot();

  if (envSpecFile != null && envSpecFile.isNotEmpty) {
    specRelativePaths.add(envSpecFile);
  } else {
    // recursively find all yaml files in spec/ directory
    final specDir = Directory("$workspaceRoot/spec");
    if (specDir.existsSync()) {
      specRelativePaths = specDir
          .listSync(recursive: true)
          .where((e) => e is File && e.path.endsWith(".yaml"))
          .map((e) => e.path.substring(workspaceRoot.length + 1))
          .toList()
        // Sort for deterministic execution order
        ..sort();
    } else {
      // ignore: avoid_print
      print("Warning: Spec directory not found at $workspaceRoot/spec. Skipping default discovery.");
    }
  }

  if (specRelativePaths.isEmpty) {
    // ignore: avoid_print
    print("Warning: No spec files found. Skipping.");
  }

  for (final specFile in specRelativePaths) {
    // path might be absolute or relative depending on how we got it
    // If it came from env, it's relative to CWD usually, but here we treat it as workspace relative if we found it via scan?
    // Wait, envSpecFile logic was: path relative to CWD in Bazel script?
    // In Bazel script: export SPEC_FILE="../../{spec_path}" which is relative to test binary CWD.
    // Spec paths found via listSync are absolute.
    // I need to handle both cases.

    String specPath;
    if (File(specFile).isAbsolute) {
      specPath = specFile;
    } else {
      // If relative, assume relative to workspace root (for parity with manual list usage)
      // BUT Bazel script passes `../../spec/...` which is relative to CWD.
      // If I use `File(specFile).exists()`, it checks relative to CWD.
      if (File(specFile).existsSync()) {
        specPath = specFile;
      } else {
        specPath = "$workspaceRoot/$specFile";
      }
    }

    final file = File(specPath);

    if (!file.existsSync()) {
      // ignore: avoid_print
      print("Warning: Spec file not found: $specPath. Skipping.");
      continue;
    }

    final content = file.readAsStringSync();
    final specs = loadYaml(content) as YamlList;

    for (final spec in specs) {
      final specMap = _convertYamlMap(spec as YamlMap);
      final specName = specMap["name"] as String;
      final template = specMap["template"] as String?;
      final tests = specMap["tests"] as List?;
      final partials = specMap["partials"] as Map<String, dynamic>?;
      final resolverPartials = specMap["resolverPartials"] as Map<String, dynamic>?;

      if (tests == null) continue;

      group(specName, () {
        // Scenario-level data
        final scenarioData = specMap["data"] as Map<String, dynamic>?;

        for (final testCase in tests) {
          final testMap = _convertYamlValue(testCase) as Map<String, dynamic>;
          final desc = testMap["desc"] as String;
          // Merge scenario-level data with test-level data (test overrides scenario)
          final testData = testMap["data"] as Map<String, dynamic>?;
          final data = <String, dynamic>{...?scenarioData, ...?testData};
          final options = testMap["options"] as Map<String, dynamic>?;
          final expected = testMap["expect"] as Map<String, dynamic>;

          test(desc, () async {
            // Build options with partials
            final dotpromptOptions = DotpromptOptions(
              partials: {...?partials?.cast<String, String>()},
              partialResolver: resolverPartials != null ? (name) async => resolverPartials[name] as String? : null,
            );

            final dotprompt = Dotprompt(dotpromptOptions);

            // Build data argument
            final dataArg = DataArgument(
              input:
                  data.containsKey("input") ? data["input"] as Map<String, dynamic>? : (data.isNotEmpty ? data : null),
              context: data.containsKey("context")
                  ? ContextData.fromJson(
                      (data["context"] as Map).cast<String, dynamic>(),
                    )
                  : null,
              messages: data.containsKey("messages")
                  ? (data["messages"] as List)
                      .map(
                        (m) => Message.fromJson(
                          (m as Map).cast<String, dynamic>(),
                        ),
                      )
                      .toList()
                  : null,
            );

            // Render the template
            final result = await dotprompt.render(
              template ?? "",
              dataArg,
              options,
            );

            // Check expected messages
            if (expected.containsKey("messages")) {
              final expectedMessages = expected["messages"] as List;
              expect(result.messages.length, equals(expectedMessages.length));

              for (var i = 0; i < expectedMessages.length; i++) {
                final expectedMsg = expectedMessages[i] as Map<String, dynamic>;
                final actualMsg = result.messages[i];

                // Check role
                if (expectedMsg.containsKey("role")) {
                  expect(actualMsg.role.value, equals(expectedMsg["role"]));
                }

                // Check content
                if (expectedMsg.containsKey("content")) {
                  final expectedContent = expectedMsg["content"] as List;
                  expect(
                    actualMsg.content.length,
                    equals(expectedContent.length),
                  );

                  for (var j = 0; j < expectedContent.length; j++) {
                    final expectedPart = expectedContent[j] as Map<String, dynamic>;
                    final actualPart = actualMsg.content[j];

                    if (expectedPart.containsKey("text")) {
                      expect(actualPart, isA<TextPart>());
                      expect(
                        (actualPart as TextPart).text,
                        equals(expectedPart["text"]),
                      );
                    } else if (expectedPart.containsKey("media")) {
                      expect(actualPart, isA<MediaPart>());
                      final actualMedia = (actualPart as MediaPart).media;
                      final expectedMedia = expectedPart["media"] as Map<String, dynamic>;
                      expect(actualMedia.url, equals(expectedMedia["url"]));
                      if (expectedMedia.containsKey("contentType")) {
                        expect(
                          actualMedia.contentType,
                          equals(expectedMedia["contentType"]),
                        );
                      }
                    }
                  }
                }
              }
            }

            // Check other expected fields
            if (expected.containsKey("model")) {
              expect(result.model, equals(expected["model"]));
            }

            if (expected.containsKey("config")) {
              final expectedConfig = expected["config"] as Map<String, dynamic>;
              for (final entry in expectedConfig.entries) {
                expect(
                  result.config[entry.key],
                  equals(entry.value),
                  reason: "Config key '${entry.key}' mismatch",
                );
              }
            }

            if (expected.containsKey("raw")) {
              final expectedRaw = expected["raw"] as Map<String, dynamic>;
              final actualRaw = result.raw;
              expect(actualRaw, isNotNull);
              for (final entry in expectedRaw.entries) {
                expect(
                  _deepEquals(actualRaw![entry.key], entry.value),
                  isTrue,
                  reason: "Raw key '${entry.key}' mismatch",
                );
              }
            }

            if (expected.containsKey("ext")) {
              final expectedExt = expected["ext"] as Map<String, dynamic>;
              final actualExt = result.ext;
              expect(actualExt, isNotNull);
              for (final entry in expectedExt.entries) {
                expect(
                  _deepEquals(actualExt![entry.key], entry.value),
                  isTrue,
                  reason: "Ext key '${entry.key}' mismatch",
                );
              }
            }

            if (expected.containsKey("input")) {
              final expectedInput = expected["input"] as Map<String, dynamic>;
              final actualInput = result.input;
              expect(actualInput, isNotNull);
              for (final entry in expectedInput.entries) {
                expect(
                  _deepEquals(actualInput![entry.key], entry.value),
                  isTrue,
                  reason: "Input key '${entry.key}' mismatch",
                );
              }
            }
          });
        }
      });
    }
  }
}

/// Finds the workspace root by looking for MODULE.bazel.
String _findWorkspaceRoot() {
  var dir = Directory.current;
  while (dir.path != dir.parent.path) {
    if (File("${dir.path}/MODULE.bazel").existsSync()) {
      return dir.path;
    }
    dir = dir.parent;
  }
  return Directory.current.path;
}

/// Converts a YamlMap to a Dart Map.
Map<String, dynamic> _convertYamlMap(YamlMap yaml) {
  final result = <String, dynamic>{};
  for (final entry in yaml.entries) {
    result[entry.key as String] = _convertYamlValue(entry.value);
  }
  return result;
}

/// Converts a YAML value to a Dart value.
dynamic _convertYamlValue(dynamic value) {
  if (value is YamlMap) {
    return _convertYamlMap(value);
  } else if (value is YamlList) {
    return value.map(_convertYamlValue).toList();
  }
  return value;
}

/// Deep equality check for nested structures.
bool _deepEquals(dynamic a, dynamic b) {
  if (a == b) return true;
  if (a == null || b == null) return false;

  if (a is Map && b is Map) {
    if (a.length != b.length) return false;
    for (final key in a.keys) {
      if (!b.containsKey(key)) return false;
      if (!_deepEquals(a[key], b[key])) return false;
    }
    return true;
  }

  if (a is List && b is List) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (!_deepEquals(a[i], b[i])) return false;
    }
    return true;
  }

  return a.toString() == b.toString();
}
