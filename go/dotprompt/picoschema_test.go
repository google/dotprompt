// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestPicoschema(t *testing.T) {
	t.Run("nil schema", func(t *testing.T) {
		result, err := Picoschema(nil, &PicoschemaOptions{})
		assert.NoError(t, err)
		assert.Nil(t, result)
	})

	t.Run("scalar type schema", func(t *testing.T) {
		result, err := Picoschema("string", &PicoschemaOptions{})
		assert.NoError(t, err)
		assert.Equal(t, JSONSchema{"type": "string"}, result)
	})

	t.Run("named schema", func(t *testing.T) {
		schemaResolver := func(name string) (JSONSchema, error) {
			if name == "MySchema" {
				return JSONSchema{"type": "object", "properties": map[string]any{"name": JSONSchema{"type": "string"}}}, nil
			}
			return nil, nil
		}
		result, err := Picoschema("MySchema", &PicoschemaOptions{SchemaResolver: schemaResolver})
		assert.NoError(t, err)
		assert.Equal(t, JSONSchema{"type": "object", "properties": map[string]any{"name": JSONSchema{"type": "string"}}}, result)
	})

	t.Run("invalid schema type", func(t *testing.T) {
		_, err := Picoschema(123, &PicoschemaOptions{})
		assert.Error(t, err)
	})
}

func TestPicoschemaParser_Parse(t *testing.T) {
	parser := NewPicoschemaParser(&PicoschemaOptions{})

	t.Run("nil schema", func(t *testing.T) {
		result, err := parser.Parse(nil)
		assert.NoError(t, err)
		assert.Nil(t, result)
	})

	t.Run("scalar type schema", func(t *testing.T) {
		result, err := parser.Parse("string")
		assert.NoError(t, err)
		assert.Equal(t, JSONSchema{"type": "string"}, result)
	})

	t.Run("object schema", func(t *testing.T) {
		schema := map[string]any{
			"type":       "object",
			"properties": map[string]any{"name": JSONSchema{"type": "string"}},
		}
		expectedSchema := JSONSchema{
			"type":       "object",
			"properties": map[string]any{"name": JSONSchema{"type": "string"}},
		}
		result, err := parser.Parse(schema)
		assert.NoError(t, err)
		assert.Equal(t, expectedSchema, result)
	})

	t.Run("invalid schema type", func(t *testing.T) {
		_, err := parser.Parse(123)
		assert.Error(t, err)
	})
}

func TestPicoschemaParser_parsePico(t *testing.T) {
	parser := NewPicoschemaParser(&PicoschemaOptions{})

	t.Run("scalar type", func(t *testing.T) {
		result, err := parser.parsePico("string")
		assert.NoError(t, err)
		assert.Equal(t, JSONSchema{"type": "string"}, result)
	})

	t.Run("object type", func(t *testing.T) {
		schema := map[string]any{
			"name": "string",
		}
		expected := JSONSchema{
			"type":                 "object",
			"properties":           map[string]any{"name": JSONSchema{"type": "string"}},
			"required":             []string{"name"},
			"additionalProperties": false,
		}
		result, err := parser.parsePico(schema)
		assert.NoError(t, err)
		assert.Equal(t, expected, result)
	})

	t.Run("array type", func(t *testing.T) {
		schema := map[string]any{
			"names(array)": "string",
		}
		expected := JSONSchema{
			"type": "object",
			"properties": map[string]any{
				"names": JSONSchema{
					"type":  "array",
					"items": JSONSchema{"type": "string"},
				},
			},
			"required":             []string{"names"},
			"additionalProperties": false,
		}
		result, err := parser.parsePico(schema)
		assert.NoError(t, err)
		assert.Equal(t, expected, result)
	})

	t.Run("nested array type", func(t *testing.T) {
		schema := map[string]any{
			"items(array)": map[string]any{"props(array)": "string"},
		}
		expected := JSONSchema{
			"type": "object",
			"properties": map[string]any{
				"items": JSONSchema{
					"type": "array",
					"items": JSONSchema{
						"type": "object",
						"properties": map[string]any{
							"props": JSONSchema{
								"type": "array",
								"items": JSONSchema{
									"type": "string",
								},
							},
						},
						"required":             []string{"props"},
						"additionalProperties": false,
					},
				},
			},
			"required":             []string{"items"},
			"additionalProperties": false,
		}
		result, err := parser.parsePico(schema)
		assert.NoError(t, err)
		assert.Equal(t, expected, result)
	})

	t.Run("enum type", func(t *testing.T) {
		schema := map[string]any{
			"status(enum)": []any{"active", "inactive"},
		}
		expected := JSONSchema{
			"type": "object",
			"properties": map[string]any{
				"status": JSONSchema{
					"enum": []any{"active", "inactive"},
				},
			},
			"required":             []string{"status"},
			"additionalProperties": false,
		}
		result, err := parser.parsePico(schema)
		assert.NoError(t, err)
		assert.Equal(t, expected, result)
	})
}

func TestExtractDescription(t *testing.T) {
	t.Run("no description", func(t *testing.T) {
		input := "string"
		expected := [2]string{"string", ""}
		result := extractDescription(input)
		assert.Equal(t, expected, result)
	})

	t.Run("with description", func(t *testing.T) {
		input := "string, a simple string"
		expected := [2]string{"string", "a simple string"}
		result := extractDescription(input)
		assert.Equal(t, expected, result)
	})
}

func TestContainsInterface(t *testing.T) {
	t.Run("contains item", func(t *testing.T) {
		slice := []any{"a", "b", "c"}
		item := "b"
		result := containsInterface(slice, item)
		assert.True(t, result)
	})

	t.Run("does not contain item", func(t *testing.T) {
		slice := []any{"a", "b", "c"}
		item := "d"
		result := containsInterface(slice, item)
		assert.False(t, result)
	})
}
