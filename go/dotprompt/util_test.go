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

func TestContains(t *testing.T) {
	testCases := []struct {
		name     string
		keyword  string
		expected bool
	}{
		{
			name:     "name",
			keyword:  "name",
			expected: true,
		},
		{
			name:     "description",
			keyword:  "description",
			expected: true,
		},
		{
			name:     "variant",
			keyword:  "variant",
			expected: true,
		},
		{
			name:     "version",
			keyword:  "version",
			expected: true,
		},
		{
			name:     "ext",
			keyword:  "ext",
			expected: true,
		},
		{
			name:     "foo",
			keyword:  "foo",
			expected: false,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			assert.Equal(t, tc.expected, contains(ReservedMetadataKeywords, tc.keyword))
		})
	}
}

func TestMergeMaps(t *testing.T) {
	t.Run("both maps are nil", func(t *testing.T) {
		result := MergeMaps(nil, nil)
		assert.Equal(t, map[string]interface{}{}, result)
	})

	t.Run("first map is nil", func(t *testing.T) {
		map2 := map[string]interface{}{"key1": "value1"}
		result := MergeMaps(nil, map2)
		assert.Equal(t, map2, result)
	})

	t.Run("second map is nil", func(t *testing.T) {
		map1 := map[string]interface{}{"key1": "value1"}
		result := MergeMaps(map1, nil)
		assert.Equal(t, map1, result)
	})

	t.Run("both maps are non-nil", func(t *testing.T) {
		map1 := map[string]interface{}{"key1": "value1"}
		map2 := map[string]interface{}{"key2": "value2"}
		expected := map[string]interface{}{"key1": "value1", "key2": "value2"}
		result := MergeMaps(map1, map2)
		assert.Equal(t, expected, result)
	})

	t.Run("overlapping keys", func(t *testing.T) {
		map1 := map[string]interface{}{"key1": "value1"}
		map2 := map[string]interface{}{"key1": "newValue1", "key2": "value2"}
		expected := map[string]interface{}{"key1": "newValue1", "key2": "value2"}
		result := MergeMaps(map1, map2)
		assert.Equal(t, expected, result)
	})
}

func TestTrimSpaces(t *testing.T) {
	t.Run("no leading or trailing spaces", func(t *testing.T) {
		input := "Hello, world!"
		expected := "Hello, world!"
		result := trimSpaces(input)
		assert.Equal(t, expected, result)
	})

	t.Run("leading spaces", func(t *testing.T) {
		input := "   Hello, world!"
		expected := "Hello, world!"
		result := trimSpaces(input)
		assert.Equal(t, expected, result)
	})

	t.Run("trailing spaces", func(t *testing.T) {
		input := "Hello, world!   "
		expected := "Hello, world!"
		result := trimSpaces(input)
		assert.Equal(t, expected, result)
	})

	t.Run("leading and trailing spaces", func(t *testing.T) {
		input := "   Hello, world!   "
		expected := "Hello, world!"
		result := trimSpaces(input)
		assert.Equal(t, expected, result)
	})

	t.Run("spaces and newlines", func(t *testing.T) {
		input := "   Hello, \nworld!   "
		expected := "Hello, \nworld!"
		result := trimSpaces(input)
		assert.Equal(t, expected, result)
	})
}
