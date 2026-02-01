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

/// Unit tests for the Picoschema class.
library;

import "package:dotprompt/dotprompt.dart";
import "package:dotprompt/src/picoschema.dart";
import "package:test/test.dart";

void main() {
  group("Picoschema", () {
    group("toJsonSchema", () {
      test("converts simple string type", () {
        final result = Picoschema.toJsonSchema("string");
        expect(result, equals({"type": "string"}));
      });

      test("converts integer type", () {
        final result = Picoschema.toJsonSchema("integer");
        expect(result, equals({"type": "integer"}));
      });

      test("converts number type", () {
        final result = Picoschema.toJsonSchema("number");
        expect(result, equals({"type": "number"}));
      });

      test("converts boolean type", () {
        final result = Picoschema.toJsonSchema("boolean");
        expect(result, equals({"type": "boolean"}));
      });

      test("converts array type", () {
        final result = Picoschema.toJsonSchema("string[]");
        expect(
          result,
          equals({
            "type": "array",
            "items": {"type": "string"},
          }),
        );
      });

      test("converts nested array type", () {
        final result = Picoschema.toJsonSchema("integer[][]");
        expect(
          result,
          equals({
            "type": "array",
            "items": {
              "type": "array",
              "items": {"type": "integer"},
            },
          }),
        );
      });

      test("converts enum type", () {
        final result = Picoschema.toJsonSchema("foo | bar | baz");
        expect(
          result,
          equals({
            "type": "string",
            "enum": ["foo", "bar", "baz"],
          }),
        );
      });

      test("converts object schema", () {
        final result = Picoschema.toJsonSchema({
          "name": "string",
          "age": "integer",
        });
        expect(
          result,
          equals({
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "age": {"type": "integer"},
            },
            "additionalProperties": false,
            "required": ["name", "age"],
          }),
        );
      });

      test("handles optional fields", () {
        final result = Picoschema.toJsonSchema({
          "name": "string",
          "nickname?": "string",
        });
        expect(result["required"], equals(["name"]));
        expect((result["properties"] as Map).containsKey("nickname"), isTrue);
      });

      test("handles field descriptions", () {
        final result = Picoschema.toJsonSchema({
          "email(User's email address)": "string",
        });
        expect(
          (result["properties"] as Map)["email"],
          equals({"type": "string", "description": "User's email address"}),
        );
      });

      test("converts nested objects", () {
        final result = Picoschema.toJsonSchema({
          "user": {"name": "string", "email": "string"},
        });
        expect(
          ((result["properties"] as Map)["user"] as Map)["type"],
          equals("object"),
        );
        expect(
          (((result["properties"] as Map)["user"] as Map)["properties"] as Map)["name"],
          equals({"type": "string"}),
        );
      });

      test("handles null input", () {
        final result = Picoschema.toJsonSchema(null);
        expect(result, equals({"type": "object"}));
      });
    });

    group("isPicoschema", () {
      test("returns true for Picoschema", () {
        expect(Picoschema.isPicoschema({"name": "string"}), isTrue);
      });

      test(r"returns false for JSON Schema with $schema", () {
        expect(
          Picoschema.isPicoschema({
            r"$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
          }),
          isFalse,
        );
      });

      test("returns false for JSON Schema with type object and properties", () {
        expect(
          Picoschema.isPicoschema({
            "type": "object",
            "properties": {
              "name": {"type": "string"},
            },
          }),
          isFalse,
        );
      });
    });
  });
}
