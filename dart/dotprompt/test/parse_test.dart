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

/// Unit tests for the Parser class.
library;

import "package:dotprompt/dotprompt.dart";
import "package:test/test.dart";

void main() {
  group("Parser", () {
    group("parse", () {
      test("parses empty string", () {
        final result = Parser.parse("");
        expect(result.template, equals(""));
        expect(result.config, isEmpty);
      });

      test("parses template without frontmatter", () {
        final result = Parser.parse("Hello {{name}}!");
        expect(result.template, equals("Hello {{name}}!"));
        expect(result.config, isEmpty);
      });

      test("parses simple frontmatter", () {
        final result = Parser.parse("""
---
model: gemini-pro
---
Hello!
""");
        expect(result.template, equals("Hello!"));
        expect(result.config["model"], equals("gemini-pro"));
      });

      test("parses complex frontmatter", () {
        final result = Parser.parse("""
---
model: gemini-pro
config:
  temperature: 0.7
  maxOutputTokens: 1024
input:
  schema:
    name: string
    age: integer
  default:
    name: User
tools:
  - searchWeb
  - calculator
---
Hello {{name}}!
""");
        expect(result.config["model"], equals("gemini-pro"));
        expect((result.config["config"] as Map)["temperature"], equals(0.7));
        expect(
          (result.config["config"] as Map)["maxOutputTokens"],
          equals(1024),
        );
        expect(
          ((result.config["input"] as Map)["schema"] as Map)["name"],
          equals("string"),
        );
        expect(
          ((result.config["input"] as Map)["default"] as Map)["name"],
          equals("User"),
        );
        expect(result.config["tools"], equals(["searchWeb", "calculator"]));
      });

      test("throws on malformed frontmatter", () {
        expect(
          () => Parser.parse("""
---
model: gemini-pro
Hello!
"""),
          throwsA(isA<ParseException>()),
        );
      });

      test("handles frontmatter with no trailing newline", () {
        final result = Parser.parse("---\nmodel: test\n---\nContent");
        expect(result.config["model"], equals("test"));
        expect(result.template, equals("Content"));
      });

      test("handles empty frontmatter", () {
        final result = Parser.parse("---\n---\nContent");
        expect(result.config, isEmpty);
        expect(result.template, equals("Content"));
      });
    });

    group("parseDocument", () {
      test("returns ParsedPrompt with metadata", () {
        final result = Parser.parseDocument("""
---
model: gemini-pro
config:
  temperature: 0.5
---
Hello!
""");
        expect(result.model, equals("gemini-pro"));
        expect(result.config?["temperature"], equals(0.5));
        expect(result.template, equals("Hello!"));
      });

      test("handles extension fields", () {
        final result = Parser.parseDocument("""
---
model: test
ext1.foo: bar
ext2.baz: qux
---
Content
""");
        expect(result.ext?["ext1"]?["foo"], equals("bar"));
        expect(result.ext?["ext2"]?["baz"], equals("qux"));
      });
    });
  });
}
