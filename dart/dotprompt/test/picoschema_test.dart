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
///
/// Mirrors `js/src/picoschema.test.ts`; cross-runtime behavior is also covered
/// by `spec/picoschema.yaml` via `spec_test.dart`.
library;

import "package:dotprompt/dotprompt.dart";
import "package:test/test.dart";

Map<String, dynamic> _props(Map<String, dynamic> schema) => schema["properties"] as Map<String, dynamic>;

Matcher _throwsPicoschema(Pattern message) =>
    throwsA(isA<PicoschemaException>().having((e) => e.message, "message", contains(message)));

void main() {
  group("Picoschema.toJsonSchema", () {
    group("scalars", () {
      for (final type in ["string", "number", "integer", "boolean", "null"]) {
        test("converts $type", () {
          expect(Picoschema.toJsonSchema(type), equals({"type": type}));
        });
      }

      test("converts any to an empty schema", () {
        expect(Picoschema.toJsonSchema("any"), equals(<String, dynamic>{}));
        expect(Picoschema.toJsonSchema("any, anything"), equals({"description": "anything"}));
      });

      test("extracts description after the first comma", () {
        expect(
          Picoschema.toJsonSchema("number,  the description, with commas "),
          equals({"type": "number", "description": "the description, with commas"}),
        );
      });

      test("handles null input", () {
        expect(Picoschema.toJsonSchema(null), equals({"type": "object"}));
      });

      test("throws on unknown types without schemas", () {
        expect(() => Picoschema.toJsonSchema("UndefinedType"), _throwsPicoschema("unsupported scalar type"));
      });

      test("throws on non-standard type syntax", () {
        for (final type in ["string[]", "a | b", "str", "int", "String"]) {
          expect(() => Picoschema.toJsonSchema({"field": type}), throwsA(isA<PicoschemaException>()), reason: type);
        }
      });

      test("throws on invalid schema values", () {
        expect(() => Picoschema.toJsonSchema(123), _throwsPicoschema("only consists of objects and strings"));
        expect(
          () => Picoschema.toJsonSchema({
            "field": [1, 2],
          }),
          _throwsPicoschema("only consists of objects and strings"),
        );
      });
    });

    group("JSON Schema passthrough", () {
      test("returns schemas with a JSON Schema type unchanged", () {
        final schema = {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
          },
        };
        expect(Picoschema.toJsonSchema(schema), equals(schema));
        expect(Picoschema.toJsonSchema({"type": "string"}), equals({"type": "string"}));
      });

      test("adds type object when only properties is present", () {
        expect(
          Picoschema.toJsonSchema({
            "properties": {
              "name": {"type": "string"},
            },
          }),
          equals({
            "type": "object",
            "properties": {
              "name": {"type": "string"},
            },
          }),
        );
      });
    });

    group("objects", () {
      test("converts fields and marks them required", () {
        expect(
          Picoschema.toJsonSchema({"name": "string", "age": "integer, in years"}),
          equals({
            "type": "object",
            "properties": {
              "name": {"type": "string"},
              "age": {"type": "integer", "description": "in years"},
            },
            "additionalProperties": false,
            "required": ["name", "age"],
          }),
        );
      });

      test("makes optional fields nullable and not required", () {
        final result = Picoschema.toJsonSchema({"name": "string", "nickname?": "string"});
        expect(
          _props(result)["nickname"],
          equals({
            "type": ["string", "null"],
          }),
        );
        expect(result["required"], equals(["name"]));
      });

      test("omits required when every field is optional", () {
        expect(Picoschema.toJsonSchema({"a?": "string"}).containsKey("required"), isFalse);
      });

      test("converts nested objects without a qualifier", () {
        final result = Picoschema.toJsonSchema({
          "user": {"name": "string"},
        });
        expect(
          _props(result)["user"],
          equals({
            "type": "object",
            "properties": {
              "name": {"type": "string"},
            },
            "additionalProperties": false,
            "required": ["name"],
          }),
        );
      });

      test("converts (object) with description, optional", () {
        final result = Picoschema.toJsonSchema({
          "obj?(object, a nested object)": {"x": "integer"},
        });
        expect(
          _props(result)["obj"],
          equals({
            "type": ["object", "null"],
            "description": "a nested object",
            "properties": {
              "x": {"type": "integer"},
            },
            "additionalProperties": false,
            "required": ["x"],
          }),
        );
      });
    });

    group("arrays", () {
      test("converts (array) of scalars", () {
        expect(
          Picoschema.toJsonSchema({"names(array)": "string"}),
          equals({
            "type": "object",
            "properties": {
              "names": {
                "type": "array",
                "items": {"type": "string"},
              },
            },
            "additionalProperties": false,
            "required": ["names"],
          }),
        );
      });

      test("puts the qualifier description on the array and the value description on items", () {
        final result = Picoschema.toJsonSchema({"tags(array, list of tags)": "string, the tag"});
        expect(
          _props(result)["tags"],
          equals({
            "type": "array",
            "description": "list of tags",
            "items": {"type": "string", "description": "the tag"},
          }),
        );
      });

      test("makes optional arrays nullable", () {
        final result = Picoschema.toJsonSchema({"items?(array, list of items)": "string"});
        expect(
          _props(result)["items"],
          equals({
            "type": ["array", "null"],
            "description": "list of items",
            "items": {"type": "string"},
          }),
        );
        expect(result.containsKey("required"), isFalse);
      });

      test("converts arrays of objects and nested arrays", () {
        final result = Picoschema.toJsonSchema({
          "items(array)": {"props(array)": "string"},
        });
        final items = _props(result)["items"] as Map<String, dynamic>;
        expect(items["type"], equals("array"));
        final element = items["items"] as Map<String, dynamic>;
        expect(element["type"], equals("object"));
        expect(
          _props(element)["props"],
          equals({
            "type": "array",
            "items": {"type": "string"},
          }),
        );
      });
    });

    group("enums", () {
      test("converts (enum)", () {
        final result = Picoschema.toJsonSchema({
          "status(enum, the status)": ["A", "B"],
        });
        expect(
          _props(result)["status"],
          equals({
            "enum": ["A", "B"],
            "description": "the status",
          }),
        );
      });

      test("adds null to optional enums once", () {
        expect(
          _props(
            Picoschema.toJsonSchema({
              "c?(enum)": ["A"],
            }),
          )["c"],
          equals({
            "enum": ["A", null],
          }),
        );
        expect(
          _props(
            Picoschema.toJsonSchema({
              "c?(enum)": ["A", null],
            }),
          )["c"],
          equals({
            "enum": ["A", null],
          }),
        );
      });

      test("throws when enum values are not a list", () {
        expect(() => Picoschema.toJsonSchema({"c(enum)": "A"}), _throwsPicoschema("enum values must be a list"));
      });
    });

    group("wildcards", () {
      test("maps (*) to additionalProperties", () {
        expect(
          Picoschema.toJsonSchema({"other": "string", "(*)": "any, whatever you want"}),
          equals({
            "type": "object",
            "properties": {
              "other": {"type": "string"},
            },
            "additionalProperties": {"description": "whatever you want"},
            "required": ["other"],
          }),
        );
      });

      test("supports wildcard-only objects", () {
        expect(
          Picoschema.toJsonSchema({"(*)": "number, lucky number"}),
          equals({
            "type": "object",
            "properties": <String, dynamic>{},
            "additionalProperties": {"type": "number", "description": "lucky number"},
          }),
        );
      });
    });

    group("invalid parentheticals", () {
      test("rejects free-text descriptions in parentheses", () {
        expect(
          () => Picoschema.toJsonSchema({"email(User's email address)": "string"}),
          _throwsPicoschema("parenthetical types must be 'object', 'array' or 'enum', got: 'User's email address'"),
        );
      });

      test("rejects name(*)", () {
        expect(() => Picoschema.toJsonSchema({"wild(*)": "string"}), _throwsPicoschema("got: '*'"));
      });

      test("rejects malformed keys", () {
        expect(() => Picoschema.toJsonSchema({"bad(array": "string"}), _throwsPicoschema("invalid property name"));
        expect(() => Picoschema.toJsonSchema({"(array)": "string"}), _throwsPicoschema("invalid property name"));
      });
    });

    group("named schemas", () {
      final schemas = {
        "Foo": {"type": "number", "description": "a foo"},
      };

      test("resolves from schemas and overrides the description", () {
        expect(Picoschema.toJsonSchema("Foo", schemas: schemas), equals({"type": "number", "description": "a foo"}));
        expect(
          Picoschema.toJsonSchema("Foo, an overridden foo", schemas: schemas),
          equals({"type": "number", "description": "an overridden foo"}),
        );
      });

      test("makes optional references nullable without mutating the registered schema", () {
        final result = Picoschema.toJsonSchema({"foo?": "Foo"}, schemas: schemas);
        expect(
          _props(result)["foo"],
          equals({
            "type": ["number", "null"],
            "description": "a foo",
          }),
        );
        expect(schemas["Foo"], equals({"type": "number", "description": "a foo"}));
      });

      test("throws when a named schema is missing", () {
        expect(() => Picoschema.toJsonSchema("Bar", schemas: schemas), _throwsPicoschema("could not find schema"));
      });
    });
  });

  group("Picoschema.parse", () {
    test("resolves named schemas via the async resolver", () async {
      final requested = <String>[];
      final result = await Picoschema.parse(
        {"a": "AsyncType, first", "b?": "AsyncType", "c": "Other"},
        schemaResolver: (name) async {
          requested.add(name);
          return switch (name) {
            "AsyncType" => {"type": "number"},
            "Other" => {"type": "string"},
            _ => null,
          };
        },
      );
      expect(
        _props(result),
        equals({
          "a": {"type": "number", "description": "first"},
          "b": {
            "type": ["number", "null"],
          },
          "c": {"type": "string"},
        }),
      );
      expect(requested, equals(["AsyncType", "Other"]));
    });

    test("prefers schemas over the resolver", () async {
      final result = await Picoschema.parse(
        "Foo",
        schemas: {
          "Foo": {"type": "integer"},
        },
        schemaResolver: (_) async => fail("resolver should not be called"),
      );
      expect(result, equals({"type": "integer"}));
    });

    test("throws when the resolver returns null", () async {
      await expectLater(
        Picoschema.parse("Missing", schemaResolver: (_) async => null),
        _throwsPicoschema("could not find schema with name 'Missing'"),
      );
    });

    test("throws for unknown types without any schema source", () async {
      await expectLater(Picoschema.parse("Missing"), _throwsPicoschema("unsupported scalar type"));
    });
  });

  group("Picoschema.isPicoschema", () {
    test("returns true for Picoschema", () {
      expect(Picoschema.isPicoschema({"name": "string"}), isTrue);
      expect(Picoschema.isPicoschema({"name": "string, the name"}), isTrue);
      expect(
        Picoschema.isPicoschema({
          "obj(object)": {"x": "integer"},
        }),
        isTrue,
      );
      expect(
        Picoschema.isPicoschema({
          "status(enum)": ["A"],
        }),
        isTrue,
      );
      expect(Picoschema.isPicoschema({"(*)": "string"}), isTrue);
      expect(Picoschema.isPicoschema({r"$type": "string"}), isTrue);
    });

    test("returns false for JSON Schema", () {
      expect(Picoschema.isPicoschema({"type": "string"}), isFalse);
      expect(
        Picoschema.isPicoschema({
          "properties": {
            "a": {"type": "string"},
          },
        }),
        isFalse,
      );
      expect(Picoschema.isPicoschema({r"$schema": "http://json-schema.org/draft-07/schema#"}), isFalse);
      expect(Picoschema.isPicoschema({r"$ref": "#/defs/Foo"}), isFalse);
    });
  });

  // https://github.com/genkit-ai/genkit-dart/issues/562
  group("issue #562: parenthetical qualifiers via Dotprompt", () {
    test("renders (array), (object), (enum) and (*) per spec", () async {
      final metadata = await Dotprompt().renderMetadata("""
---
output:
  schema:
    tags(array): string
    tags3(array, the tags): string
    obj(object):
      x: integer
    status(enum): [A, B]
    steps(array):
      number: integer
      instruction: string
    (*): string
---
hi
""");
      expect(
        metadata.output?.schema,
        equals({
          "type": "object",
          "properties": {
            "tags": {
              "type": "array",
              "items": {"type": "string"},
            },
            "tags3": {
              "type": "array",
              "description": "the tags",
              "items": {"type": "string"},
            },
            "obj": {
              "type": "object",
              "properties": {
                "x": {"type": "integer"},
              },
              "additionalProperties": false,
              "required": ["x"],
            },
            "status": {
              "enum": ["A", "B"],
            },
            "steps": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "number": {"type": "integer"},
                  "instruction": {"type": "string"},
                },
                "additionalProperties": false,
                "required": ["number", "instruction"],
              },
            },
          },
          "additionalProperties": {"type": "string"},
          "required": ["tags", "tags3", "obj", "status", "steps"],
        }),
      );
    });

    test("resolves named schemas through DotpromptOptions.schemaResolver", () async {
      final dotprompt = Dotprompt(
        DotpromptOptions(
          schemaResolver: (name) async => name == "Address" ? {"type": "object", "description": "an address"} : null,
        ),
      );
      final metadata = await dotprompt.renderMetadata("""
---
input:
  schema:
    shipTo: Address
---
hi
""");
      expect(
        _props(metadata.input!.schema!)["shipTo"],
        equals({"type": "object", "description": "an address"}),
      );
    });

    test("rejects name(*)", () async {
      await expectLater(
        Dotprompt().renderMetadata("---\noutput:\n  schema:\n    wild(*): string\n---\nhi"),
        throwsA(isA<PicoschemaException>()),
      );
    });
  });
}
