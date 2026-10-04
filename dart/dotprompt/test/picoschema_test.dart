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

      test("returns schemas without a single type string unchanged", () {
        final schemas = <Map<String, dynamic>>[
          {
            "anyOf": [
              {"type": "string"},
              {"type": "null"},
            ],
          },
          {
            "oneOf": [
              {"type": "string"},
              {"type": "integer"},
            ],
          },
          {
            "allOf": [
              {"type": "object"},
            ],
          },
          {
            "enum": ["a", "b"],
          },
          {
            "type": ["string", "null"],
          },
          {
            r"$defs": {
              "A": {"type": "string"},
            },
            r"$ref": r"#/$defs/A",
          },
        ];
        for (final schema in schemas) {
          expect(Picoschema.toJsonSchema(schema), equals(schema), reason: "$schema");
        }
      });

      test("still parses Picoschema fields named like JSON Schema keywords", () {
        expect(
          Picoschema.toJsonSchema({"items": "string", "enum": "integer"}),
          equals({
            "type": "object",
            "properties": {
              "items": {"type": "string"},
              "enum": {"type": "integer"},
            },
            "additionalProperties": false,
            "required": ["items", "enum"],
          }),
        );
      });

      test("parses map-valued fields named like JSON Schema keywords as nested objects", () {
        final expected = {
          "type": "object",
          "properties": {
            "sku": {"type": "string"},
            "qty": {"type": "integer"},
          },
          "additionalProperties": false,
          "required": ["sku", "qty"],
        };
        for (final key in ["items", r"$defs"]) {
          expect(
            Picoschema.toJsonSchema({
              key: {"sku": "string", "qty": "integer"},
            }),
            equals({
              "type": "object",
              "properties": {key: expected},
              "additionalProperties": false,
              "required": [key],
            }),
            reason: key,
          );
        }
      });

      test("passes through JSON Schema with annotations and extension keys", () {
        final schemas = <Map<String, dynamic>>[
          {
            "type": "object",
            "title": "Person",
            "description": "a person",
            "properties": {
              "name": {"type": "string", "x-order": 1},
              "extra": <String, dynamic>{},
              "anything": true,
            },
            "required": ["name"],
            "examples": [
              {"name": "Ann"},
            ],
            "x-internal": true,
          },
          {"type": "string", "format": "email", "minLength": 3, "nullable": true},
          {"type": "string", "description": "a person, really"},
        ];
        for (final schema in schemas) {
          expect(Picoschema.toJsonSchema(schema), equals(schema), reason: "$schema");
        }
      });

      test("passes through nested JSON Schema subschemas", () {
        final schemas = <Map<String, dynamic>>[
          {
            "type": "object",
            "properties": {
              "tags": {
                "type": "array",
                "items": {"type": "string"},
              },
              "nick": {
                "anyOf": [
                  {"type": "string"},
                  {"type": "null"},
                ],
              },
              "meta": {
                "type": "object",
                "additionalProperties": {"type": "number"},
              },
            },
            "required": ["tags"],
          },
          {
            "type": "array",
            "items": [
              {"type": "string"},
              {"type": "integer"},
            ],
          },
        ];
        for (final schema in schemas) {
          expect(Picoschema.toJsonSchema(schema), equals(schema), reason: "$schema");
        }
      });

      test("returns a deep copy, not the input map", () {
        final schema = <String, dynamic>{
          "type": "object",
          "properties": {
            "a": {"type": "string"},
          },
        };
        final result = Picoschema.toJsonSchema(schema);
        result["description"] = "changed";
        (_props(result)["a"] as Map<String, dynamic>)["description"] = "changed";
        expect(
          schema,
          equals({
            "type": "object",
            "properties": {
              "a": {"type": "string"},
            },
          }),
        );
      });

      test("does not inspect values other than a top-level scalar type's siblings", () {
        // Type-name strings below the top level, or next to a non-scalar
        // `type`, are ordinary JSON Schema values.
        final schemas = <Map<String, dynamic>>[
          {
            "type": "object",
            "description": "string, the user",
            "properties": {
              "name": {"type": "string"},
            },
          },
          {
            "type": "object",
            "properties": {
              "a": {"type": "string", "description": "string", "default": "number"},
            },
          },
          {
            "type": "array",
            "title": "string",
            "items": {"type": "string", "title": "integer"},
          },
          {r"$ref": "#/defs/A", "description": "string"},
        ];
        for (final schema in schemas) {
          expect(Picoschema.toJsonSchema(schema), equals(schema), reason: "$schema");
        }
      });

      test(r"never reads $- and x- keys as Picoschema fields", () {
        for (final schema in <Map<String, dynamic>>[
          {"type": "string", r"$comment": "string"},
          {"type": "string", "x-kind": "string"},
        ]) {
          expect(Picoschema.toJsonSchema(schema), equals(schema), reason: "$schema");
        }
      });

      test("rejects Picoschema nested inside JSON Schema instead of passing it through", () {
        final schemas = <Map<String, dynamic>>[
          {
            "type": "object",
            "properties": {"a": "string"},
          },
          {
            "type": "object",
            "properties": {
              "a": {
                "type": "object",
                "properties": {"b": "string"},
              },
            },
          },
          {
            "type": "array",
            "items": {"sku": "string"},
          },
        ];
        for (final schema in schemas) {
          expect(
            () => Picoschema.toJsonSchema(schema),
            _throwsPicoschema("not recognized as JSON Schema"),
            reason: "$schema",
          );
        }
      });

      test("hints at JSON Schema when a schema of only JSON Schema keywords fails to parse", () {
        // No `type`, so these are Picoschema objects with fields named
        // `description`/`format`, whose values are not valid types.
        for (final schema in <Map<String, dynamic>>[
          {"description": "free form"},
          {"format": "date-time"},
        ]) {
          expect(
            () => Picoschema.toJsonSchema(schema),
            _throwsPicoschema("not recognized as JSON Schema"),
            reason: "$schema",
          );
        }
      });

      test("does not add the JSON Schema hint for Picoschema fields", () {
        expect(
          () => Picoschema.toJsonSchema({"type": "object", "name": "string"}),
          throwsA(
            isA<PicoschemaException>().having((e) => e.message, "message", isNot(contains("JSON Schema"))),
          ),
        );
      });
    });

    // Picoschema fields whose names coincide with JSON Schema keywords must be
    // converted, never passed through raw.
    group("fields named like JSON Schema keywords", () {
      test("treats a scalar-valued type field as Picoschema", () {
        for (final schema in <Map<String, dynamic>>[
          {"type": "string", "payload": "string"},
          {"type": "string", "title": "string"},
          {"type": "string", "description": "string, the description"},
        ]) {
          final result = Picoschema.toJsonSchema(schema);
          expect(result["type"], equals("object"), reason: "$schema");
          expect(_props(result).keys, equals(schema.keys), reason: "$schema");
          expect(_props(result)["type"], isA<Map<String, dynamic>>(), reason: "$schema");
        }
      });

      test("fails loudly instead of passing through a non-scalar type field", () {
        // `object` is not a Picoschema scalar, so this is invalid Picoschema
        // rather than JSON Schema with a stray `name` keyword.
        expect(
          () => Picoschema.toJsonSchema({"type": "object", "name": "string"}),
          _throwsPicoschema("unsupported scalar type 'object'"),
        );
      });

      test("treats Picoschema key syntax next to type as Picoschema", () {
        expect(
          Picoschema.toJsonSchema({"type": "string", "tags(array)": "string", "note?": "string"}),
          equals({
            "type": "object",
            "properties": {
              "type": {"type": "string"},
              "tags": {
                "type": "array",
                "items": {"type": "string"},
              },
              "note": {
                "type": ["string", "null"],
              },
            },
            "additionalProperties": false,
            "required": ["type", "tags"],
          }),
        );
      });

      test("treats a properties field with Picoschema values as Picoschema", () {
        for (final properties in <Map<String, dynamic>>[
          {"color": "string"},
          {
            "address": {"street": "string"},
          },
        ]) {
          final result = Picoschema.toJsonSchema({"properties": properties, "name": "string"});
          expect(_props(result).keys, equals(["properties", "name"]), reason: "$properties");
          expect(_props(result)["properties"], containsPair("type", "object"), reason: "$properties");
        }
      });

      test(r"treats a $type field next to other fields as a Picoschema field", () async {
        // `schema: string` is wrapped as {$type: string}; only that exact shape
        // is unwrapped, so other fields are never dropped.
        final metadata = await Dotprompt().renderMetadata(r"""
---
output:
  schema:
    $type: string
    name: string
---
hi
""");
        expect(_props(metadata.output!.schema!).keys, equals([r"$type", "name"]));
        expect(Picoschema.isPicoschema({r"$type": "string", "name": "string"}), isTrue);
      });

      test("converts type and properties fields from frontmatter", () async {
        final metadata = await Dotprompt().renderMetadata("""
---
output:
  schema:
    type: string, event kind
    properties:
      color: string
---
hi
""");
        expect(
          metadata.output?.schema,
          equals({
            "type": "object",
            "properties": {
              "type": {"type": "string", "description": "event kind"},
              "properties": {
                "type": "object",
                "properties": {
                  "color": {"type": "string"},
                },
                "additionalProperties": false,
                "required": ["color"],
              },
            },
            "additionalProperties": false,
            "required": ["type", "properties"],
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

      test("does not duplicate null for optional null fields", () {
        expect(_props(Picoschema.toJsonSchema({"x?": "null"}))["x"], equals({"type": "null"}));
      });

      test("rejects duplicate property names", () {
        for (final schema in <Map<String, dynamic>>[
          {"a": "string", "a?": "number"},
          {"a": "string", "a(array)": "number"},
          {
            "a?(enum)": ["X"],
            "a": "string",
          },
        ]) {
          expect(() => Picoschema.toJsonSchema(schema), _throwsPicoschema("duplicate property 'a'"), reason: "$schema");
        }
      });

      test("trims whitespace before the optional marker", () {
        expect(
          Picoschema.toJsonSchema({"a ?": "string", "b ?(array)": "string"}),
          equals({
            "type": "object",
            "properties": {
              "a": {
                "type": ["string", "null"],
              },
              "b": {
                "type": ["array", "null"],
                "items": {"type": "string"},
              },
            },
            "additionalProperties": false,
          }),
        );
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

      test("returns deep copies of registered schemas", () {
        final registered = <String, Map<String, dynamic>>{
          "Obj": {
            "type": "object",
            "properties": {
              "x": {"type": "string"},
            },
          },
        };
        final result = Picoschema.toJsonSchema({"o": "Obj"}, schemas: registered);
        _props(_props(result)["o"] as Map<String, dynamic>).remove("x");
        expect(_props(registered["Obj"]!).keys, equals(["x"]));
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

    test("adds the JSON Schema hint for unresolved names", () async {
      await expectLater(
        Picoschema.parse({"description": "Foo"}, schemaResolver: (_) async => null),
        _throwsPicoschema("not recognized as JSON Schema"),
      );
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
      expect(
        Picoschema.isPicoschema({
          "anyOf": [
            {"type": "string"},
          ],
        }),
        isFalse,
      );
    });

    test("passes JSON Schema from additionalMetadata through Dotprompt", () async {
      final schema = {
        "anyOf": [
          {"type": "string"},
          {"type": "integer"},
        ],
      };
      final metadata = await Dotprompt().renderMetadata("hi", PromptMetadata(output: OutputConfig(schema: schema)));
      expect(metadata.output!.schema, equals(schema));
    });
  });

  // https://github.com/genkit-ai/genkit-dart/issues/562
  group("genkit-dart#562: parenthetical qualifiers via Dotprompt", () {
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

    test("converts a top-level field named items instead of passing it through", () async {
      final metadata = await Dotprompt().renderMetadata("""
---
output:
  schema:
    items:
      sku: string
      qty: integer
---
hi
""");
      expect(
        metadata.output?.schema,
        equals({
          "type": "object",
          "properties": {
            "items": {
              "type": "object",
              "properties": {
                "sku": {"type": "string"},
                "qty": {"type": "integer"},
              },
              "additionalProperties": false,
              "required": ["sku", "qty"],
            },
          },
          "additionalProperties": false,
          "required": ["items"],
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

    test("resolves the input: Name / output: Name shorthand", () async {
      final metadata = await Dotprompt(
        const DotpromptOptions(
          schemas: {
            "Person": {"type": "object", "description": "a person"},
          },
        ),
      ).renderMetadata("---\ninput: Person\noutput: Person\n---\nhi");
      expect(metadata.input?.schema, equals({"type": "object", "description": "a person"}));
      expect(metadata.output?.schema, equals({"type": "object", "description": "a person"}));
    });

    test("rejects an unknown name in the output: Name shorthand", () async {
      await expectLater(
        Dotprompt().renderMetadata("---\noutput: Missing\n---\nhi"),
        _throwsPicoschema("could not find schema with name 'Missing'"),
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
