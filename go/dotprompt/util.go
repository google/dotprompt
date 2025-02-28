// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import "strings"

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

// MergeMaps merges two map[string]interface{} objects and handles nil maps.
func MergeMaps(map1, map2 map[string]interface{}) map[string]interface{} {
	// If map1 is nil, initialize it as an empty map
	if map1 == nil {
		map1 = make(map[string]interface{})
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

// trimSpaces trims only the leading and trailing spaces but preserves newline characters.
func trimSpaces(s string) string {
	return strings.Trim(s, " \t")
}

// contains checks if a slice contains a string.
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
