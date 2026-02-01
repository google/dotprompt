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

/// Unit tests for the Dotprompt class.
library;

import "package:dotprompt/dotprompt.dart";
import "package:test/test.dart";

void main() {
  group("Dotprompt", () {
    late Dotprompt dotprompt;

    setUp(() {
      dotprompt = Dotprompt();
    });

    group("parse", () {
      test("parses template without frontmatter", () {
        final parsed = dotprompt.parse("Hello {{name}}!");
        expect(parsed.template, equals("Hello {{name}}!"));
        expect(parsed.model, isNull);
      });

      test("parses template with frontmatter", () {
        final parsed = dotprompt.parse("""
---
model: gemini-pro
config:
  temperature: 0.7
---
Hello {{name}}!
""");
        expect(parsed.template, equals("Hello {{name}}!"));
        expect(parsed.model, equals("gemini-pro"));
        expect(parsed.config?["temperature"], equals(0.7));
      });

      test("handles empty template", () {
        final parsed = dotprompt.parse("");
        expect(parsed.template, equals(""));
        expect(parsed.model, isNull);
      });

      test("parses tools list", () {
        final parsed = dotprompt.parse("""
---
tools:
  - searchWeb
  - calculator
---
Use tools as needed.
""");
        expect(parsed.tools, equals(["searchWeb", "calculator"]));
      });
    });

    group("render", () {
      test("renders simple template", () async {
        final result = await dotprompt.render(
          "Hello {{name}}!",
          const DataArgument(input: {"name": "World"}),
        );
        expect(result.messages.length, equals(1));
        expect(result.messages.first.role, equals(Role.user));
        expect(result.messages.first.content.length, equals(1));
        expect(
          (result.messages.first.content.first as TextPart).text,
          equals("Hello World!"),
        );
      });

      test("uses default values when input missing", () async {
        final result = await dotprompt.render(
          """
---
input:
  default:
    name: User
---
Hello {{name}}!
""",
          const DataArgument(),
        );
        expect(
          (result.messages.first.content.first as TextPart).text.trim(),
          equals("Hello User!"),
        );
      });

      test("input overrides defaults", () async {
        final result = await dotprompt.render(
          """
---
input:
  default:
    name: User
---
Hello {{name}}!
""",
          const DataArgument(input: {"name": "Alice"}),
        );
        expect(
          (result.messages.first.content.first as TextPart).text.trim(),
          equals("Hello Alice!"),
        );
      });
    });

    group("partials", () {
      test("renders partial templates", () async {
        dotprompt.definePartial("greeting", "Hello, {{name}}!");
        final result = await dotprompt.render(
          "{{> greeting}}",
          const DataArgument(input: {"name": "World"}),
        );
        expect(
          (result.messages.first.content.first as TextPart).text,
          equals("Hello, World!"),
        );
      });

      test("uses partial resolver", () async {
        final dp = Dotprompt(
          DotpromptOptions(
            partialResolver: (name) async {
              if (name == "custom") {
                return "Custom partial content";
              }
              return null;
            },
          ),
        );
        final result = await dp.render("{{> custom}}", const DataArgument());
        expect(
          (result.messages.first.content.first as TextPart).text,
          equals("Custom partial content"),
        );
      });
    });

    group("tools", () {
      test("resolves defined tools", () async {
        dotprompt.defineTool(
          const ToolDefinition(name: "myTool", description: "A test tool"),
        );

        final metadata = await dotprompt.renderMetadata("""
---
tools:
  - myTool
---
Use the tool.
""");
        expect(metadata.toolDefs?.length, equals(1));
        expect(metadata.toolDefs?.first.name, equals("myTool"));
      });
    });
  });

  group("DotpromptOptions", () {
    test("applies default model", () async {
      final dp = Dotprompt(
        const DotpromptOptions(defaultModel: "my-default-model"),
      );
      final metadata = await dp.renderMetadata("Hello!");
      expect(metadata.model, equals("my-default-model"));
    });

    test("model config is merged", () async {
      final dp = Dotprompt(
        const DotpromptOptions(
          modelConfigs: {
            "gemini-pro": {"temperature": 0.5, "maxOutputTokens": 1000},
          },
        ),
      );
      final metadata = await dp.renderMetadata("""
---
model: gemini-pro
config:
  temperature: 0.8
---
Hello!
""");
      // Template config should override model config
      expect(metadata.config?["temperature"], equals(0.8));
      expect(metadata.config?["maxOutputTokens"], equals(1000));
    });
  });
}
