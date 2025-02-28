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
				return JSONSchema{"type": "object", "properties": map[string]interface{}{"name": JSONSchema{"type": "string"}}}, nil
			}
			return nil, nil
		}
		result, err := Picoschema("MySchema", &PicoschemaOptions{SchemaResolver: schemaResolver})
		assert.NoError(t, err)
		assert.Equal(t, JSONSchema{"type": "object", "properties": map[string]interface{}{"name": JSONSchema{"type": "string"}}}, result)
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
		schema := map[string]interface{}{
			"type":       "object",
			"properties": map[string]interface{}{"name": JSONSchema{"type": "string"}},
		}
		expectedSchema := JSONSchema{
			"type":       "object",
			"properties": map[string]interface{}{"name": JSONSchema{"type": "string"}},
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
		schema := map[string]interface{}{
			"name": "string",
		}
		expected := JSONSchema{
			"type":                 "object",
			"properties":           map[string]interface{}{"name": JSONSchema{"type": "string"}},
			"required":             []string{"name"},
			"additionalProperties": false,
		}
		result, err := parser.parsePico(schema)
		assert.NoError(t, err)
		assert.Equal(t, expected, result)
	})

	t.Run("array type", func(t *testing.T) {
		schema := map[string]interface{}{
			"names(array)": "string",
		}
		expected := JSONSchema{
			"type": "object",
			"properties": map[string]interface{}{
				"names": JSONSchema{
					"type":  []interface{}{"array"},
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

	t.Run("enum type", func(t *testing.T) {
		schema := map[string]interface{}{
			"status(enum)": []interface{}{"active", "inactive"},
		}
		expected := JSONSchema{
			"type": "object",
			"properties": map[string]interface{}{
				"status": JSONSchema{
					"enum": []interface{}{"active", "inactive"},
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
		slice := []interface{}{"a", "b", "c"}
		item := "b"
		result := containsInterface(slice, item)
		assert.True(t, result)
	})

	t.Run("does not contain item", func(t *testing.T) {
		slice := []interface{}{"a", "b", "c"}
		item := "d"
		result := containsInterface(slice, item)
		assert.False(t, result)
	})
}
