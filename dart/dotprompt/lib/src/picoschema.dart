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

/// Picoschema to JSON Schema converter.
///
/// Picoschema is a compact, YAML-friendly schema format that compiles to JSON
/// Schema. This implementation follows the JavaScript reference
/// implementation and the spec in `spec/picoschema.yaml`. See
/// https://google.github.io/dotprompt/reference/picoschema/.
///
/// ```yaml
/// title: string, the article title       # scalar with description
/// subtitle?: string                      # optional (and nullable)
/// status?(enum, approval status): [PENDING, APPROVED]
/// tags(array, relevant tags): string     # array of scalars
/// authors(array):                        # array of objects
///   name: string
///   email?: string
/// metadata?(object, extra info):         # nested object
///   updatedAt?: string, ISO timestamp of last update
/// labels(object):
///   (*): string                          # wildcard -> additionalProperties
/// address: Address                       # named schema reference
/// ```
///
/// Scalar types are `string`, `number`, `integer`, `boolean`, `null` and
/// `any`. Any other type name is looked up as a named schema. The only
/// parenthetical types are `array`, `object` and `enum`; anything else in
/// parentheses is an error.
library;

import "error.dart";
import "store.dart" show SchemaResolver;

/// Looks up a named schema, throwing if it is unknown.
typedef _SchemaLookup = Map<String, dynamic> Function(String name);

/// Converts Picoschema definitions to JSON Schema.
///
/// ```dart
/// final schema = Picoschema.toJsonSchema({
///   'name': 'string, the name',
///   'steps(array)': {'number': 'integer', 'instruction': 'string'},
/// });
/// // {
/// //   "type": "object",
/// //   "properties": {
/// //     "name": {"type": "string", "description": "the name"},
/// //     "steps": {
/// //       "type": "array",
/// //       "items": {"type": "object", "properties": {...}, ...}
/// //     }
/// //   },
/// //   "additionalProperties": false,
/// //   "required": ["name", "steps"]
/// // }
/// ```
class Picoschema {
  Picoschema._();

  static const Set<String> _scalarTypes = {"any", "boolean", "integer", "null", "number", "string"};

  /// Top-level `type` values that mark a schema as already being JSON Schema.
  static const Set<String> _jsonSchemaTypes = {..._scalarTypes, "object", "array"};

  static const String _wildcardKey = "(*)";

  /// Splits `name?(type, description)` into `name?` and the parenthetical contents.
  static final RegExp _parentheticalKey = RegExp(r"^([^()]*)\((.*)\)$");

  /// Converts [picoschema] to JSON Schema synchronously.
  ///
  /// Named schema references are looked up in [schemas] only. Use [parse] to
  /// also consult an async [SchemaResolver]. Registered schemas must already
  /// be JSON Schema; they are inserted as-is, matching the other runtimes.
  ///
  /// Values that are already JSON Schema (see [isPicoschema]) are returned
  /// unchanged. A `null` input yields `{"type": "object"}`.
  ///
  /// Throws [PicoschemaException] if the schema is invalid or references an
  /// unknown named schema.
  static Map<String, dynamic> toJsonSchema(
    Object? picoschema, {
    Map<String, Map<String, dynamic>>? schemas,
  }) =>
      _convert(
        picoschema,
        (name) => schemas?[name] ?? (throw _unknownSchema(name, hasSchemaSource: schemas != null)),
      );

  /// Converts [picoschema] to JSON Schema, resolving named schemas from
  /// [schemas] first and then [schemaResolver] (same order as the JS
  /// implementation). Both must provide JSON Schema; it is inserted as-is.
  ///
  /// ```dart
  /// final schema = await Picoschema.parse(
  ///   {'address': 'Address, where to ship'},
  ///   schemaResolver: (name) async => lookupSchema(name),
  /// );
  /// ```
  static Future<Map<String, dynamic>> parse(
    Object? picoschema, {
    Map<String, Map<String, dynamic>>? schemas,
    SchemaResolver? schemaResolver,
  }) async {
    final resolved = <String, Map<String, dynamic>>{...?schemas};
    // The converter is sync, so names needing the async resolver are discovered
    // by converting, catching the first miss, resolving it and retrying. Each
    // retry resolves one more distinct name and Picoschema documents are small,
    // so this is cheaper to maintain than a separate reference-collecting walk.
    while (true) {
      try {
        return _convert(picoschema, (name) => resolved[name] ?? (throw _UnresolvedSchema(name)));
      } on _UnresolvedSchema catch (e) {
        final schema = await schemaResolver?.call(e.name);
        if (schema == null) {
          throw _unknownSchema(e.name, hasSchemaSource: schemas != null || schemaResolver != null);
        }
        resolved[e.name] = schema;
      }
    }
  }

  /// Whether [schema] should be converted as Picoschema, i.e. it is not
  /// already JSON Schema. [toJsonSchema] and [parse] apply the same check, so
  /// calling this first is optional.
  ///
  /// JSON Schema is detected like in the JS and Python runtimes: a top-level
  /// `type` naming a JSON Schema type, or a `properties` map. A list-valued
  /// `type` or `anyOf`/`oneOf`/`allOf`/`enum`, `$schema` and `$ref` also count,
  /// so JSON Schema without a single `type` string is not misparsed.
  static bool isPicoschema(Map<String, dynamic> schema) => _wrappedTypeString(schema) != null || !_isJsonSchema(schema);

  static const Set<String> _jsonSchemaListKeywords = {"anyOf", "oneOf", "allOf", "enum"};

  // Deliberately shallow, like JS/Python: nothing below the top level is
  // inspected. So `{type: object, properties: {a: string}}` is passed through
  // as-is, and a Picoschema field named `type` with a JSON Schema type value
  // (`{type: string, name: string}`) makes the whole map JSON Schema.
  static bool _isJsonSchema(Map<String, dynamic> schema) {
    final type = schema["type"];
    return (type is String && _jsonSchemaTypes.contains(type)) ||
        (type is List && type.isNotEmpty && type.every(_jsonSchemaTypes.contains)) ||
        schema["properties"] is Map ||
        _jsonSchemaListKeywords.any((k) => schema[k] is List) ||
        schema.containsKey(r"$schema") ||
        schema.containsKey(r"$ref");
  }

  /// The type string of frontmatter like `schema: string`, which
  /// InputConfig/OutputConfig wrap as `{$type: "string"}`. Only a map whose
  /// sole key is `$type` counts, so a Picoschema object that happens to have a
  /// `$type` field is still parsed as an object.
  static String? _wrappedTypeString(Map<Object?, Object?> schema) {
    final wrapped = schema[r"$type"];
    return schema.length == 1 && wrapped is String ? wrapped : null;
  }

  static Map<String, dynamic> _deepCopy(Map<String, dynamic> map) =>
      map.map((key, value) => MapEntry(key, _deepCopyValue(value)));

  static Object? _deepCopyValue(Object? value) => switch (value) {
        final Map<Object?, Object?> m => _deepCopy(m.cast<String, dynamic>()),
        final List<Object?> l => [for (final e in l) _deepCopyValue(e)],
        _ => value,
      };

  static Map<String, dynamic> _convert(Object? schema, _SchemaLookup lookup) {
    if (schema == null) {
      return {"type": "object"};
    }
    if (schema is String) {
      return _parseTypeString(schema, lookup);
    }
    if (schema is Map) {
      final map = schema.cast<String, dynamic>();
      final wrapped = _wrappedTypeString(map);
      if (wrapped != null) {
        return _parseTypeString(wrapped, lookup);
      }
      if (_isJsonSchema(map)) {
        // Copied like named schemas, so callers never share nested maps with
        // the input. A bare `properties` map implies an object type.
        return {..._deepCopy(map), if (map["type"] == null && map["properties"] is Map) "type": "object"};
      }
      return _parseObject(map, lookup);
    }
    throw PicoschemaException("Picoschema: only consists of objects and strings. Got: $schema");
  }

  /// Parses `type[, description]`, where `type` is a scalar or a named schema.
  static Map<String, dynamic> _parseTypeString(String input, _SchemaLookup lookup) {
    final (type, description) = _extractDescription(input);
    final schema = switch (type) {
      // JS returns `{type: "any"}` for a top-level `any`, which is not valid
      // JSON Schema; `{}` (what JS returns for nested fields) is used everywhere.
      "any" => <String, dynamic>{},
      _ when _scalarTypes.contains(type) => <String, dynamic>{"type": type},
      // Deep copy so neither this converter nor callers editing the result can
      // change registered schemas.
      _ => _deepCopy(lookup(type)),
    };
    if (description != null) {
      schema["description"] = description;
    }
    return schema;
  }

  /// Parses the value side of an object field.
  static Map<String, dynamic> _parseValue(Object? value, String key, _SchemaLookup lookup) {
    if (value is String) {
      return _parseTypeString(value, lookup);
    }
    if (value is Map) {
      return _parseObject(value.cast<String, dynamic>(), lookup);
    }
    // `field:` with no value is an empty object, as in JS.
    if (value == null) {
      return _parseObject(const {}, lookup);
    }
    throw PicoschemaException("Picoschema: only consists of objects and strings. Got: $value (in '$key')");
  }

  static Map<String, dynamic> _parseObject(Map<String, dynamic> obj, _SchemaLookup lookup) {
    final properties = <String, dynamic>{};
    final required = <String>[];
    Object additionalProperties = false;

    for (final MapEntry(:key, :value) in obj.entries) {
      if (key == _wildcardKey) {
        additionalProperties = _parseValue(value, key, lookup);
        continue;
      }

      final match = _parentheticalKey.firstMatch(key);
      if (match == null && (key.contains("(") || key.contains(")"))) {
        throw PicoschemaException("Picoschema: invalid property name '$key'");
      }
      final name = (match?.group(1) ?? key).trim();
      final isOptional = name.endsWith("?");
      // Trimmed again so `a ?` is `a`, not `a ` (JS keeps the space).
      final propertyName = (isOptional ? name.substring(0, name.length - 1) : name).trim();
      if (propertyName.isEmpty) {
        throw PicoschemaException("Picoschema: invalid property name '$key'");
      }
      // `a` and `a?` (or `a(array)`) map to the same property. JS lets the last
      // key win and leaves `required` inconsistent; reject it instead.
      if (properties.containsKey(propertyName)) {
        throw PicoschemaException("Picoschema: duplicate property '$propertyName' (in '$key')");
      }
      if (!isOptional) {
        required.add(propertyName);
      }

      final parenthetical = match?.group(2);
      if (parenthetical == null) {
        final prop = _parseValue(value, key, lookup);
        properties[propertyName] = isOptional ? _nullable(prop) : prop;
        continue;
      }

      final (type, description) = _extractDescription(parenthetical);
      final prop = switch (type) {
        "array" => <String, dynamic>{
            "type": isOptional ? ["array", "null"] : "array",
            "items": _parseValue(value, key, lookup),
          },
        "object" when isOptional => _nullable(_parseValue(value, key, lookup)),
        "object" => _parseValue(value, key, lookup),
        "enum" => _enumSchema(value, key, isOptional: isOptional),
        _ => throw PicoschemaException(
            "Picoschema: parenthetical types must be 'object', 'array' or 'enum', got: '$type' (in '$key')",
          ),
      };
      if (description != null) {
        prop["description"] = description;
      }
      properties[propertyName] = prop;
    }

    return {
      "type": "object",
      "properties": properties,
      "additionalProperties": additionalProperties,
      if (required.isNotEmpty) "required": required,
    };
  }

  static Map<String, dynamic> _enumSchema(Object? value, String key, {required bool isOptional}) {
    if (value is! List) {
      throw PicoschemaException("Picoschema: enum values must be a list (in '$key')");
    }
    return {
      "enum": [...value, if (isOptional && !value.contains(null)) null],
    };
  }

  /// Optional fields are also nullable. Only a single string `type` is widened,
  /// matching the other runtimes.
  static Map<String, dynamic> _nullable(Map<String, dynamic> schema) {
    final type = schema["type"];
    if (type is String && type != "null") {
      schema["type"] = [type, "null"];
    }
    return schema;
  }

  /// Splits `type, description` on the first comma. The description is null
  /// when there is no comma or nothing after it.
  static (String, String?) _extractDescription(String input) {
    final comma = input.indexOf(",");
    if (comma < 0) {
      return (input.trim(), null);
    }
    final description = input.substring(comma + 1).trim();
    return (input.substring(0, comma).trim(), description.isEmpty ? null : description);
  }

  static PicoschemaException _unknownSchema(String name, {required bool hasSchemaSource}) => PicoschemaException(
        hasSchemaSource
            ? "Picoschema: could not find schema with name '$name'"
            : "Picoschema: unsupported scalar type '$name'.",
      );
}

/// Signals a named schema that [Picoschema.parse] still has to resolve.
class _UnresolvedSchema implements Exception {
  const _UnresolvedSchema(this.name);

  final String name;
}
