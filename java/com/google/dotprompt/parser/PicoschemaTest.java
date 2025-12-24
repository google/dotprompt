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
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

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
  public void parse_scalarTypeSchema() throws Exception {
    assertThat(parseSync("string")).isEqualTo(Map.of("type", "string"));
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
  public void parse_scalarTypeSchemaWithDescription() throws Exception {
    assertThat(parseSync("string, a string"))
        .isEqualTo(Map.of("type", "string", "description", "a string"));
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
}
