// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"strings"
	"unicode"
)

// stringOrEmpty returns the string value of an any or an empty string if it's not a string.
func stringOrEmpty(value any) string {
	if value == nil {
		return ""
	}

	if strValue, ok := value.(string); ok {
		return strValue
	}

	return ""
}

// getMapOrNil returns the map value of an any or nil if it's not a map.
func getMapOrNil(m map[string]any, key string) map[string]any {
	if value, ok := m[key]; ok {
		if mapValue, isMap := value.(map[string]any); isMap {
			return mapValue
		}
	}

	return nil
}

// copyMapping copies a map.
func copyMapping[K comparable, V any](mapping map[K]V) map[K]V {
	newMapping := make(map[K]V)
	for k, v := range mapping {
		newMapping[k] = v
	}
	return newMapping
}

// MergeMaps merges two map[string]any objects and handles nil maps.
func MergeMaps(map1, map2 map[string]any) map[string]any {
	// If map1 is nil, initialize it as an empty map
	if map1 == nil {
		map1 = make(map[string]any)
	}

	// If map2 is nil, return map1 as is
	if map2 == nil {
		return map1
	}

	// Merge map2 into map1
	for key, value := range map2 {
		map1[key] = value
	}

	return map1
}

// trimUnicodeSpacesExceptNewlines trims all Unicode space characters except newlines.
func trimUnicodeSpacesExceptNewlines(s string) string {
	var result strings.Builder
	for _, r := range s {
		if unicode.IsSpace(r) && r != '\n' && r != '\r' && r != ' ' {
			continue // Skip other Unicode spaces
		}
		result.WriteRune(r)
	}

	//Trim leading and trailing spaces after the loop to handle edge cases
	return strings.TrimFunc(result.String(), func(r rune) bool {
		return unicode.IsSpace(r) && r != '\n' && r != '\r'
	})
}
