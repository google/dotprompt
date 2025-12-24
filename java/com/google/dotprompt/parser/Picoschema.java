/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

package com.google.dotprompt.parser;

import com.google.dotprompt.resolvers.SchemaResolver;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * Picoschema parser and related helpers.
 *
 * <p>Picoschema is a compact, YAML-optimized schema definition format. This class compiles
 * Picoschema to JSON Schema.
 *
 * <p>Supported features:
 *
 * <ul>
 *   <li>Scalar types (any, boolean, integer, null, number, string)
 *   <li>Type descriptions (e.g. {@code name(string, The name)})
 *   <li>Optional fields (denoted by {@code ?})
 *   <li>Arrays ({@code items(string)})
 *   <li>Objects (nested maps)
 *   <li>Enums ({@code status(enum, [active, inactive])})
 *   <li>Wildcard properties ({@code (*)})
 * </ul>
 */
public class Picoschema {

  private static final Set<String> JSON_SCHEMA_SCALAR_TYPES =
      Set.of("any", "boolean", "integer", "null", "number", "string");

  private static final String WILDCARD_PROPERTY_NAME = "(*)";

  /** Checks if a schema is already in JSON Schema format. */
  public static boolean isJsonSchema(Object schema) {
    if (!(schema instanceof Map)) {
      return false;
    }
    Map<?, ?> map = (Map<?, ?>) schema;
    Object type = map.get("type");
    if (type == null) {
      return map.containsKey("properties");
    }
    String typeStr = (String) type;
    return JSON_SCHEMA_SCALAR_TYPES.contains(typeStr)
        || "object".equals(typeStr)
        || "array".equals(typeStr);
  }

  /**
   * Parses a Picoschema definition into a JSON Schema.
   *
   * @param schema The Picoschema definition (can be a Map or String).
   * @return A future containing the equivalent JSON Schema.
   */
  public static CompletableFuture<Map<String, Object>> parse(Object schema) {
    return parse(schema, null);
  }

  /**
   * Parses a Picoschema definition into a JSON Schema with reference resolution.
   *
   * @param schema The Picoschema definition.
   * @param resolver A function to resolve named schemas asynchronously.
   * @return A future containing the equivalent JSON Schema.
   */
  public static CompletableFuture<Map<String, Object>> parse(
      Object schema, SchemaResolver resolver) {
    if (schema == null) {
      return CompletableFuture.completedFuture(null);
    }

    if (schema instanceof String) {
      Description desc = extractDescription((String) schema);
      String typeName = desc.type;
      String description = desc.description;

      if (JSON_SCHEMA_SCALAR_TYPES.contains(typeName)) {
        Map<String, Object> out = new HashMap<>();
        if (!"any".equals(typeName)) {
          out.put("type", typeName);
        }
        if (description != null) {
          out.put("description", description);
        }
        return CompletableFuture.completedFuture(out);
      }

      // Resolve named schema asynchronously
      if (resolver != null) {
        return resolver
            .resolve(typeName)
            .thenApply(
                resolved -> {
                  if (resolved != null) {
                    Map<String, Object> out = new HashMap<>(resolved);
                    if (description != null) {
                      out.put("description", description);
                    }
                    return out;
                  }
                  throw new IllegalArgumentException("Unsupported scalar type: " + typeName);
                });
      }

      throw new IllegalArgumentException("Unsupported scalar type: " + typeName);
    }

    if (schema instanceof Map) {
      if (isJsonSchema(schema)) {
        Map<?, ?> map = (Map<?, ?>) schema;
        if (!map.containsKey("type") && map.containsKey("properties")) {
          Map<String, Object> newSchema = new HashMap<>((Map<String, Object>) schema);
          newSchema.put("type", "object");
          return CompletableFuture.completedFuture(newSchema);
        }
        return CompletableFuture.completedFuture((Map<String, Object>) schema);
      }
      return parsePico((Map<String, Object>) schema, resolver);
    }

    throw new IllegalArgumentException(
        "Picoschema must be a string or object. Got: " + schema.getClass());
  }

  /**
   * Parses a Picoschema object definition asynchronously.
   *
   * @param obj The map representing the object schema.
   * @param resolver The schema resolver for named types.
   * @return A future containing the JSON Schema object definition.
   */
  @SuppressWarnings("unchecked")
  private static CompletableFuture<Map<String, Object>> parsePico(
      Map<String, Object> obj, SchemaResolver resolver) {

    Map<String, Object> schema = new HashMap<>();
    schema.put("type", "object");
    schema.put("properties", new HashMap<String, Object>());
    schema.put("additionalProperties", false);
    List<String> required = new ArrayList<>();
    schema.put("required", required);

    List<CompletableFuture<Void>> futures = new ArrayList<>();

    for (Map.Entry<String, Object> entry : obj.entrySet()) {
      String key = entry.getKey();
      Object value = entry.getValue();

      if (WILDCARD_PROPERTY_NAME.equals(key)) {
        futures.add(
            parse(value, resolver)
                .thenAccept(
                    parsed -> {
                      schema.put("additionalProperties", parsed);
                    }));
        continue;
      }

      String name;
      String typeInfo = null;
      int parenIndex = key.indexOf('(');
      if (parenIndex != -1 && key.endsWith(")")) {
        name = key.substring(0, parenIndex);
        typeInfo = key.substring(parenIndex + 1, key.length() - 1);
      } else {
        name = key;
      }

      boolean isOptional = name.endsWith("?");
      String propertyName = isOptional ? name.substring(0, name.length() - 1) : name;

      if (!isOptional) {
        required.add(propertyName);
      }

      final boolean finalIsOptional = isOptional;
      final String finalPropertyName = propertyName;

      if (typeInfo == null) {
        futures.add(
            parse(value, resolver)
                .thenAccept(
                    prop -> {
                      applyOptionalNullability(prop, finalIsOptional);
                      ((Map<String, Object>) schema.get("properties")).put(finalPropertyName, prop);
                    }));
      } else {
        Description typeDesc = extractDescription(typeInfo);
        String typeName = typeDesc.type;
        String description = typeDesc.description;

        if ("array".equals(typeName)) {
          futures.add(
              parse(value, resolver)
                  .thenAccept(
                      items -> {
                        Map<String, Object> prop = new HashMap<>();
                        prop.put(
                            "type", finalIsOptional ? Arrays.asList("array", "null") : "array");
                        prop.put("items", items);
                        if (description != null) {
                          prop.put("description", description);
                        }
                        ((Map<String, Object>) schema.get("properties"))
                            .put(finalPropertyName, prop);
                      }));
        } else if ("object".equals(typeName)) {
          futures.add(
              parse(value, resolver)
                  .thenAccept(
                      prop -> {
                        applyOptionalNullability(prop, finalIsOptional);
                        if (description != null) {
                          prop.put("description", description);
                        }
                        ((Map<String, Object>) schema.get("properties"))
                            .put(finalPropertyName, prop);
                      }));
        } else if ("enum".equals(typeName)) {
          Map<String, Object> prop = new HashMap<>();
          if (finalIsOptional && value instanceof List) {
            List<Object> enums = new ArrayList<>((List<?>) value);
            if (!enums.contains(null)) {
              enums.add(null);
            }
            prop.put("enum", enums);
          } else {
            prop.put("enum", value);
          }
          if (description != null) {
            prop.put("description", description);
          }
          ((Map<String, Object>) schema.get("properties")).put(finalPropertyName, prop);
        } else {
          throw new IllegalArgumentException(
              "Picoschema: parenthetical types must be 'object', 'array' or 'enum', got: "
                  + typeName);
        }
      }
    }

    return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
        .thenApply(
            v -> {
              if (required.isEmpty()) {
                schema.remove("required");
              }
              return schema;
            });
  }

  /** Applies nullability to optional properties. */
  @SuppressWarnings("unchecked")
  private static void applyOptionalNullability(Map<String, Object> prop, boolean isOptional) {
    if (!isOptional) return;

    Object currentType = prop.get("type");
    if (currentType instanceof String) {
      prop.put("type", Arrays.asList(currentType, "null"));
    } else if (prop.containsKey("enum")) {
      List<Object> enums = new ArrayList<>((List<?>) prop.get("enum"));
      if (!enums.contains(null)) {
        enums.add(null);
      }
      prop.put("enum", enums);
    }
  }

  /** Internal record for parsed type descriptions. */
  private record Description(String type, String description) {}

  /** Extracts type and description from a string like "string, The name". */
  private static Description extractDescription(String input) {
    if (!input.contains(",")) {
      return new Description(input, null);
    }
    int idx = input.indexOf(',');
    String type = input.substring(0, idx).trim();
    String desc = input.substring(idx + 1).trim();
    return new Description(type, desc);
  }
}
