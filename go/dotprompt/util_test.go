// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestStringOrEmpty(t *testing.T) {
	assert.Equal(t, "", stringOrEmpty(nil))
	assert.Equal(t, "", stringOrEmpty(""))
	assert.Equal(t, "test", stringOrEmpty("test"))
}

func TestGetMapOrNil(t *testing.T) {
	// Create a test map with a nested map
	testMap := map[string]any{
		"mapKey": map[string]any{
			"key": "value",
		},
		"notAMap":  "string value",
		"nilValue": nil,
	}

	t.Run("should return nested map for existing key", func(t *testing.T) {
		result := getMapOrNil(testMap, "mapKey")
		assert.Equal(t, map[string]any{"key": "value"}, result)
	})

	t.Run("should return nil for nil map", func(t *testing.T) {
		result := getMapOrNil(nil, "key")
		assert.Nil(t, result)
	})

	t.Run("should return nil for non-existent key", func(t *testing.T) {
		result := getMapOrNil(testMap, "nonExistentKey")
		assert.Nil(t, result)
	})

	t.Run("should return nil for value that's not a map", func(t *testing.T) {
		result := getMapOrNil(testMap, "notAMap")
		assert.Nil(t, result)
	})

	t.Run("should return nil for nil value", func(t *testing.T) {
		result := getMapOrNil(testMap, "nilValue")
		assert.Nil(t, result)
	})
}

func TestCopyMapping(t *testing.T) {
	original := map[string]any{
		"key1": "value1",
		"key2": "value2",
	}

	copy := copyMapping(original)

	assert.Equal(t, original, copy)
}
func TestMergeMaps(t *testing.T) {
	t.Run("both maps are nil", func(t *testing.T) {
		result := MergeMaps(nil, nil)
		assert.Equal(t, map[string]any{}, result)
	})

	t.Run("first map is nil", func(t *testing.T) {
		map2 := map[string]any{"key1": "value1"}
		result := MergeMaps(nil, map2)
		assert.Equal(t, map2, result)
	})

	t.Run("second map is nil", func(t *testing.T) {
		map1 := map[string]any{"key1": "value1"}
		result := MergeMaps(map1, nil)
		assert.Equal(t, map1, result)
	})

	t.Run("both maps are non-nil", func(t *testing.T) {
		map1 := map[string]any{"key1": "value1"}
		map2 := map[string]any{"key2": "value2"}
		expected := map[string]any{"key1": "value1", "key2": "value2"}
		result := MergeMaps(map1, map2)
		assert.Equal(t, expected, result)
	})

	t.Run("overlapping keys", func(t *testing.T) {
		map1 := map[string]any{"key1": "value1"}
		map2 := map[string]any{"key1": "newValue1", "key2": "value2"}
		expected := map[string]any{"key1": "newValue1", "key2": "value2"}
		result := MergeMaps(map1, map2)
		assert.Equal(t, expected, result)
	})
}

func TestTrimUnicodeSpacesExceptNewlines(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"Hello, world!", "Hello, world!"},
		{"  Hello, world!  ", "Hello, world!"},
		{"\tHello,\tworld!\t", "Hello,world!"},
		{"\nHello,\nworld!\n", "\nHello,\nworld!\n"},
		{"\rHello,\rworld!\r", "\rHello,\rworld!\r"},
		{"\n\t Hello, \t\n world! \t\n", "\n Hello, \n world! \n"},
		{"\u2003Hello,\u2003world!\u2003", "Hello,world!"},
		{"\u2003\nHello,\n\u2003world!\n\u2003", "\nHello,\nworld!\n"},
	}

	for _, test := range tests {
		result := trimUnicodeSpacesExceptNewlines(test.input)
		assert.Equal(t, test.expected, result)
	}
}
