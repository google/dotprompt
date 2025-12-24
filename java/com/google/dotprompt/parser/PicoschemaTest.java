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

import static com.google.common.truth.Truth.assertThat;
import static org.junit.Assert.assertThrows;

import com.google.dotprompt.resolvers.SchemaResolver;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/** Comprehensive tests for the Picoschema parser. */
@RunWith(JUnit4.class)
public class PicoschemaTest {

  private static Map<String, Object> parseSync(Object schema)
      throws ExecutionException, InterruptedException {
    return Picoschema.parse(schema).get();
  }

  private static Map<String, Object> parseSync(Object schema, SchemaResolver resolver)
      throws ExecutionException, InterruptedException {
    return Picoschema.parse(schema, resolver).get();
  }

  @Test
  public void parse_nullSchema_returnsNull() throws Exception {
    assertThat(Picoschema.parse(null).get()).isNull();
  }

  @Test
  public void parse_scalarTypeSchema() throws Exception {
    assertThat(parseSync("string")).isEqualTo(Map.of("type", "string"));
  }

  @Test
  public void parse_scalarTypeNumber() throws Exception {
    assertThat(parseSync("number")).isEqualTo(Map.of("type", "number"));
  }

  @Test
  public void parse_scalarTypeInteger() throws Exception {
    assertThat(parseSync("integer")).isEqualTo(Map.of("type", "integer"));
  }

  @Test
  public void parse_scalarTypeBoolean() throws Exception {
    assertThat(parseSync("boolean")).isEqualTo(Map.of("type", "boolean"));
  }

  @Test
  public void parse_scalarTypeNull() throws Exception {
    assertThat(parseSync("null")).isEqualTo(Map.of("type", "null"));
  }

  @Test
  public void parse_anyType_noTypeField() throws Exception {
    // 'any' type should produce an empty schema (no type field)
    assertThat(parseSync("any")).isEqualTo(Map.of());
  }

  @Test
  public void parse_objectSchema() throws Exception {
    Map<String, Object> schema =
        Map.of("type", "object", "properties", Map.of("name", Map.of("type", "string")));
    assertThat(parseSync(schema)).isEqualTo(schema);
  }

  @Test
  public void parse_invalidSchemaType() {
    assertThrows(IllegalArgumentException.class, () -> parseSync(123));
  }

  @Test
  public void parse_namedSchema() throws Exception {
    SchemaResolver resolver =
        SchemaResolver.fromSync(
            name -> {
              if ("CustomType".equals(name)) return Map.of("type", "integer");
              return null;
            });
    Map<String, Object> result = parseSync("CustomType", resolver);
    assertThat(result).isEqualTo(Map.of("type", "integer"));
  }

  @Test
  public void parse_namedSchemaWithDescription() throws Exception {
    SchemaResolver resolver =
        SchemaResolver.fromSync(
            name -> {
              if ("DescribedType".equals(name)) return Map.of("type", "boolean");
              return null;
            });
    Map<String, Object> result = parseSync("DescribedType, this is a description", resolver);
    assertThat(result).isEqualTo(Map.of("type", "boolean", "description", "this is a description"));
  }

  @Test
  public void parse_namedSchemaNotFound_throwsError() {
    SchemaResolver resolver = SchemaResolver.fromSync(name -> null);
    ExecutionException exception =
        assertThrows(ExecutionException.class, () -> parseSync("NonExistentSchema", resolver));
    assertThat(exception.getCause()).isInstanceOf(IllegalArgumentException.class);
    assertThat(exception.getCause().getMessage()).contains("Unsupported scalar type");
  }

  @Test
  public void parse_namedSchemaNoResolver_throwsError() {
    assertThrows(IllegalArgumentException.class, () -> parseSync("CustomSchema"));
  }

  @Test
  public void parse_scalarTypeSchemaWithDescription() throws Exception {
    assertThat(parseSync("string, a string"))
        .isEqualTo(Map.of("type", "string", "description", "a string"));
  }

  @Test
  public void parse_anyTypeWithDescription() throws Exception {
    assertThat(parseSync("any, can be any type"))
        .isEqualTo(Map.of("description", "can be any type"));
  }

  @Test
  public void parse_propertiesObjectShorthand() throws Exception {
    Map<String, Object> schema = Map.of("name", "string");
    Map<String, Object> expected =
        Map.of(
            "type",
            "object",
            "properties",
            Map.of("name", Map.of("type", "string")),
            "required",
            List.of("name"),
            "additionalProperties",
            false);
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_propertiesObjectShorthandMultipleFields() throws Exception {
    // Using HashMap because Map.of doesn't guarantee order
    Map<String, Object> schema = new HashMap<>();
    schema.put("name", "string");
    schema.put("age", "integer");

    Map<String, Object> result = parseSync(schema);

    assertThat(result).containsEntry("type", "object");
    assertThat(result).containsKey("properties");
    @SuppressWarnings("unchecked")
    Map<String, Object> props = (Map<String, Object>) result.get("properties");
    assertThat(props).containsKey("name");
    assertThat(props).containsKey("age");
  }

  @Test
  public void parse_picoArrayType() throws Exception {
    Map<String, Object> schema = Map.of("names(array)", "string");
    Map<String, Object> expected =
        Map.of(
            "type",
            "object",
            "properties",
            Map.of("names", Map.of("type", "array", "items", Map.of("type", "string"))),
            "required",
            List.of("names"),
            "additionalProperties",
            false);
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_picoArrayTypeWithDescription() throws Exception {
    Map<String, Object> schema = Map.of("items(array, list of items)", "string");
    Map<String, Object> result = parseSync(schema);

    assertThat(result).containsEntry("type", "object");
    @SuppressWarnings("unchecked")
    Map<String, Object> props = (Map<String, Object>) result.get("properties");
    @SuppressWarnings("unchecked")
    Map<String, Object> itemsProp = (Map<String, Object>) props.get("items");
    assertThat(itemsProp).containsEntry("type", "array");
    assertThat(itemsProp).containsEntry("description", "list of items");
  }

  @Test
  public void parse_picoOptionalArrayWithDescription() throws Exception {
    Map<String, Object> schema = Map.of("items?(array, list of items)", "string");
    Map<String, Object> result = parseSync(schema);

    assertThat(result).containsEntry("type", "object");
    @SuppressWarnings("unchecked")
    Map<String, Object> props = (Map<String, Object>) result.get("properties");
    @SuppressWarnings("unchecked")
    Map<String, Object> itemsProp = (Map<String, Object>) props.get("items");
    assertThat(itemsProp).containsEntry("type", Arrays.asList("array", "null"));
    assertThat(itemsProp).containsEntry("description", "list of items");
    // Optional properties should not be in required
    assertThat(result).doesNotContainKey("required");
  }

  @Test
  public void parse_picoNestedArray() throws Exception {
    // Nested array: items(array) containing props(array)
    Map<String, Object> innerSchema = Map.of("props(array)", "string");
    Map<String, Object> schema = Map.of("items(array)", innerSchema);
    Map<String, Object> result = parseSync(schema);

    assertThat(result).containsEntry("type", "object");
    @SuppressWarnings("unchecked")
    Map<String, Object> props = (Map<String, Object>) result.get("properties");
    @SuppressWarnings("unchecked")
    Map<String, Object> itemsProp = (Map<String, Object>) props.get("items");
    assertThat(itemsProp).containsEntry("type", "array");
    @SuppressWarnings("unchecked")
    Map<String, Object> itemsItems = (Map<String, Object>) itemsProp.get("items");
    assertThat(itemsItems).containsEntry("type", "object");
    @SuppressWarnings("unchecked")
    Map<String, Object> innerProps = (Map<String, Object>) itemsItems.get("properties");
    assertThat(innerProps).containsKey("props");
  }

  @Test
  public void parse_picoEnumType() throws Exception {
    Map<String, Object> schema = Map.of("status(enum)", List.of("active", "inactive"));
    Map<String, Object> expected =
        Map.of(
            "type",
            "object",
            "properties",
            Map.of("status", Map.of("enum", List.of("active", "inactive"))),
            "required",
            List.of("status"),
            "additionalProperties",
            false);
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_picoEnumWithDescription() throws Exception {
    Map<String, Object> schema = Map.of("status(enum, the status)", List.of("active", "inactive"));
    Map<String, Object> result = parseSync(schema);

    assertThat(result).containsEntry("type", "object");
    @SuppressWarnings("unchecked")
    Map<String, Object> props = (Map<String, Object>) result.get("properties");
    @SuppressWarnings("unchecked")
    Map<String, Object> statusProp = (Map<String, Object>) props.get("status");
    assertThat(statusProp).containsEntry("enum", List.of("active", "inactive"));
    assertThat(statusProp).containsEntry("description", "the status");
  }

  @Test
  public void parse_picoEnumWithOptionalAndNull() throws Exception {
    Map<String, Object> schema = Map.of("status?(enum)", List.of("active", "inactive"));
    Map<String, Object> expected =
        Map.of(
            "type",
            "object",
            "properties",
            Map.of("status", Map.of("enum", Arrays.asList("active", "inactive", null))),
            "additionalProperties",
            false);
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_picoOptionalProperty() throws Exception {
    Map<String, Object> schema = Map.of("name?", "string");
    Map<String, Object> expected =
        Map.of(
            "type",
            "object",
            "properties",
            Map.of("name", Map.of("type", Arrays.asList("string", "null"))),
            "additionalProperties",
            false);
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_picoWildcardProperty() throws Exception {
    Map<String, Object> schema = Map.of("(*)", "string");
    Map<String, Object> expected =
        Map.of(
            "type", "object",
            "properties", Map.of(),
            "additionalProperties", Map.of("type", "string"));
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_picoNestedObject() throws Exception {
    Map<String, Object> schema = Map.of("address(object)", Map.of("street", "string"));
    Map<String, Object> expected =
        Map.of(
            "type",
            "object",
            "properties",
            Map.of(
                "address",
                Map.of(
                    "type",
                    "object",
                    "properties",
                    Map.of("street", Map.of("type", "string")),
                    "required",
                    List.of("street"),
                    "additionalProperties",
                    false)),
            "required",
            List.of("address"),
            "additionalProperties",
            false);
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_picoNestedObjectWithDescription() throws Exception {
    Map<String, Object> schema = Map.of("address(object, the address)", Map.of("street", "string"));
    Map<String, Object> result = parseSync(schema);

    @SuppressWarnings("unchecked")
    Map<String, Object> props = (Map<String, Object>) result.get("properties");
    @SuppressWarnings("unchecked")
    Map<String, Object> addressProp = (Map<String, Object>) props.get("address");
    assertThat(addressProp).containsEntry("type", "object");
    assertThat(addressProp).containsEntry("description", "the address");
  }

  @Test
  public void parse_picoDescriptionOnType() throws Exception {
    Map<String, Object> schema = Map.of("name", "string, a name");
    Map<String, Object> expected =
        Map.of(
            "type",
            "object",
            "properties",
            Map.of("name", Map.of("type", "string", "description", "a name")),
            "required",
            List.of("name"),
            "additionalProperties",
            false);
    assertThat(parseSync(schema)).isEqualTo(expected);
  }

  @Test
  public void parse_picoDescriptionOnCustomSchema() throws Exception {
    SchemaResolver resolver =
        SchemaResolver.fromSync(
            name -> {
              if ("CustomSchema".equals(name)) return Map.of("type", "string");
              return null;
            });
    Map<String, Object> schema = Map.of("field1", "CustomSchema, a custom field");
    Map<String, Object> result = parseSync(schema, resolver);

    @SuppressWarnings("unchecked")
    Map<String, Object> props = (Map<String, Object>) result.get("properties");
    @SuppressWarnings("unchecked")
    Map<String, Object> field1Prop = (Map<String, Object>) props.get("field1");
    assertThat(field1Prop).containsEntry("type", "string");
    assertThat(field1Prop).containsEntry("description", "a custom field");
  }

  @Test
  public void parse_asyncResolver() throws Exception {
    SchemaResolver asyncResolver =
        name -> {
          // Simulate async operation
          return CompletableFuture.supplyAsync(
              () -> {
                if ("AsyncType".equals(name)) return Map.of("type", "number");
                return null;
              });
        };
    Map<String, Object> result = parseSync("AsyncType", asyncResolver);
    assertThat(result).isEqualTo(Map.of("type", "number"));
  }

  @Test
  public void parse_jsonSchemaPassthrough() throws Exception {
    Map<String, Object> jsonSchema =
        Map.of("type", "object", "properties", Map.of("name", Map.of("type", "string")));
    assertThat(parseSync(jsonSchema)).isEqualTo(jsonSchema);
  }

  @Test
  public void parse_jsonSchemaWithPropertiesOnly_addsType() throws Exception {
    // If 'properties' is present but 'type' is not, add type: object
    Map<String, Object> schema = Map.of("properties", Map.of("name", Map.of("type", "string")));
    Map<String, Object> result = parseSync(schema);
    assertThat(result).containsEntry("type", "object");
  }

  @Test
  public void isJsonSchema_withTypeObject() {
    assertThat(Picoschema.isJsonSchema(Map.of("type", "object"))).isTrue();
  }

  @Test
  public void isJsonSchema_withTypeString() {
    assertThat(Picoschema.isJsonSchema(Map.of("type", "string"))).isTrue();
  }

  @Test
  public void isJsonSchema_withTypeArray() {
    assertThat(Picoschema.isJsonSchema(Map.of("type", "array"))).isTrue();
  }

  @Test
  public void isJsonSchema_withPropertiesOnly() {
    assertThat(Picoschema.isJsonSchema(Map.of("properties", Map.of()))).isTrue();
  }

  @Test
  public void isJsonSchema_picoschemaObject() {
    assertThat(Picoschema.isJsonSchema(Map.of("name", "string"))).isFalse();
  }

  @Test
  public void isJsonSchema_nonMap() {
    assertThat(Picoschema.isJsonSchema("string")).isFalse();
  }
}
