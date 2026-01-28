// Copyright 2025 Google LLC
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

package dotprompt

import (
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/google/go-cmp/cmp/cmpopts"
	"github.com/invopop/jsonschema"
	orderedmap "github.com/wk8/go-ordered-map/v2"
)

var TEST_PROPERTY = orderedmap.New[string, *jsonschema.Schema]()

func TestPicoschema(t *testing.T) {
	TEST_PROPERTY.Set("name", &jsonschema.Schema{Type: "string"})
	t.Run("nil schema", func(t *testing.T) {
		result, err := Picoschema(nil, &PicoschemaOptions{})
		if err != nil {
			t.Errorf("Picoschema(nil) returned error: %v", err)
		}
		if result != nil {
			t.Errorf("Picoschema(nil) = %v, want nil", result)
		}
	})

	t.Run("scalar type schema", func(t *testing.T) {
		result, err := Picoschema("string", &PicoschemaOptions{})
		if err != nil {
			t.Errorf("Picoschema(\"string\") returned error: %v", err)
		}
		want := &jsonschema.Schema{Type: "string"}
		if diff := cmp.Diff(want, result, cmpopts.IgnoreUnexported(jsonschema.Schema{})); diff != "" {
			t.Errorf("Picoschema(\"string\") mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("named schema", func(t *testing.T) {
		schemaResolver := func(name string) (*jsonschema.Schema, error) {
			if name == "MySchema" {
				return &jsonschema.Schema{Type: "object", Properties: TEST_PROPERTY}, nil
			}
			return nil, nil
		}
		result, err := Picoschema("MySchema", &PicoschemaOptions{SchemaResolver: schemaResolver})
		if err != nil {
			t.Errorf("Picoschema(\"MySchema\") returned error: %v", err)
		}
		want := &jsonschema.Schema{Type: "object", Properties: TEST_PROPERTY}
		if diff := cmp.Diff(want, result, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
			t.Errorf("Picoschema(\"MySchema\") mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("invalid schema type", func(t *testing.T) {
		_, err := Picoschema(123, &PicoschemaOptions{})
		if err == nil {
			t.Error("Picoschema(123) expected error, got nil")
		}
	})
}

func TestPicoschemaParser_Parse(t *testing.T) {
	parser := NewPicoschemaParser(&PicoschemaOptions{})

	t.Run("nil schema", func(t *testing.T) {
		result, err := parser.Parse(nil)
		if err != nil {
			t.Errorf("Parse(nil) returned error: %v", err)
		}
		if result != nil {
			t.Errorf("Parse(nil) = %v, want nil", result)
		}
	})

	t.Run("scalar type schema", func(t *testing.T) {
		result, err := parser.Parse("string")
		if err != nil {
			t.Errorf("Parse(\"string\") returned error: %v", err)
		}
		want := &jsonschema.Schema{Type: "string"}
		if diff := cmp.Diff(want, result, cmpopts.IgnoreUnexported(jsonschema.Schema{})); diff != "" {
			t.Errorf("Parse(\"string\") mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("object schema", func(t *testing.T) {
		schema := map[string]any{
			"type":       "object",
			"properties": TEST_PROPERTY,
		}
		expectedSchema := &jsonschema.Schema{
			Type:       "object",
			Properties: TEST_PROPERTY,
		}
		result, err := parser.Parse(schema)
		if err != nil {
			t.Errorf("Parse(schema) returned error: %v", err)
		}
		if diff := cmp.Diff(expectedSchema, result, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
			t.Errorf("Parse(schema) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("invalid schema type", func(t *testing.T) {
		_, err := parser.Parse(123)
		if err == nil {
			t.Error("Parse(123) expected error, got nil")
		}
	})
}

func TestPicoschemaParser_parsePico(t *testing.T) {
	parser := NewPicoschemaParser(&PicoschemaOptions{})

	t.Run("scalar type", func(t *testing.T) {
		result, err := parser.parsePico("string")
		if err != nil {
			t.Errorf("parsePico(\"string\") returned error: %v", err)
		}
		want := &jsonschema.Schema{Type: "string"}
		if diff := cmp.Diff(want, result, cmpopts.IgnoreUnexported(jsonschema.Schema{})); diff != "" {
			t.Errorf("parsePico(\"string\") mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("object type", func(t *testing.T) {
		schema := map[string]any{
			"name": "string",
		}
		expected := &jsonschema.Schema{
			Type:       "object",
			Properties: TEST_PROPERTY,
			Required:   []string{"name"},
		}
		result, err := parser.parsePico(schema)
		if err != nil {
			t.Errorf("parsePico(schema) returned error: %v", err)
		}
		if diff := cmp.Diff(expected, result, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
			t.Errorf("parsePico(schema) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("array type", func(t *testing.T) {
		schema := map[string]any{
			"names(array)": "string",
		}
		property := orderedmap.New[string, *jsonschema.Schema]()
		property.Set("names", &jsonschema.Schema{
			Type:  "array",
			Items: &jsonschema.Schema{Type: "string"},
		})
		expected := &jsonschema.Schema{
			Type:       "object",
			Properties: property,
			Required:   []string{"names"},
		}
		result, err := parser.parsePico(schema)
		if err != nil {
			t.Errorf("parsePico(schema) returned error: %v", err)
		}
		if diff := cmp.Diff(expected, result, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
			t.Errorf("parsePico(schema) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("nested array type", func(t *testing.T) {
		schema := map[string]any{
			"items(array)": map[string]any{"props(array)": "string"},
		}
		itemsProperty := orderedmap.New[string, *jsonschema.Schema]()
		itemsProperty.Set("props", &jsonschema.Schema{
			Type: "array",
			Items: &jsonschema.Schema{
				Type: "string",
			},
		})
		property := orderedmap.New[string, *jsonschema.Schema]()
		property.Set("items", &jsonschema.Schema{
			Type: "array",
			Items: &jsonschema.Schema{
				Type:       "object",
				Properties: itemsProperty,
				Required:   []string{"props"},
			},
		})

		expected := &jsonschema.Schema{
			Type:       "object",
			Properties: property,
			Required:   []string{"items"},
		}
		result, err := parser.parsePico(schema)
		if err != nil {
			t.Errorf("parsePico(schema) returned error: %v", err)
		}
		if diff := cmp.Diff(expected, result, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
			t.Errorf("parsePico(schema) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("description on optionl array type", func(t *testing.T) {
		schema := map[string]any{
			"items?(array, list of items)": "string",
		}

		property := orderedmap.New[string, *jsonschema.Schema]()
		property.Set("items", &jsonschema.Schema{
			Type:        "",
			Items:       &jsonschema.Schema{Type: "string"},
			Description: "list of items",
			AnyOf:       []*jsonschema.Schema{{Type: "array"}, {Type: "null"}},
		})
		expected := &jsonschema.Schema{
			Type:       "object",
			Properties: property,
			Required:   []string{},
		}
		result, err := parser.parsePico(schema)
		if err != nil {
			t.Errorf("parsePico(schema) returned error: %v", err)
		}
		if diff := cmp.Diff(expected, result, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
			t.Errorf("parsePico(schema) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("enum type", func(t *testing.T) {
		schema := map[string]any{
			"status(enum)": []any{"active", "inactive"},
		}
		property := orderedmap.New[string, *jsonschema.Schema]()
		property.Set("status", &jsonschema.Schema{
			Enum: []any{"active", "inactive"},
		})
		expected := &jsonschema.Schema{
			Type:       "object",
			Properties: property,
			Required:   []string{"status"},
		}
		result, err := parser.parsePico(schema)
		if err != nil {
			t.Errorf("parsePico(schema) returned error: %v", err)
		}
		if diff := cmp.Diff(expected, result, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
			t.Errorf("parsePico(schema) mismatch (-want +got):\n%s", diff)
		}
	})
}

func TestExtractDescription(t *testing.T) {
	t.Run("no description", func(t *testing.T) {
		input := "string"
		expected := [2]string{"string", ""}
		result := extractDescription(input)
		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("extractDescription(%q) mismatch (-want +got):\n%s", input, diff)
		}
	})

	t.Run("with description", func(t *testing.T) {
		input := "string, a simple string"
		expected := [2]string{"string", "a simple string"}
		result := extractDescription(input)
		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("extractDescription(%q) mismatch (-want +got):\n%s", input, diff)
		}
	})
}
