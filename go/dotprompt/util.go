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
	"encoding/json"
	"fmt"
	"strings"
	"unicode"

	"github.com/invopop/jsonschema"
	"maps"
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
	maps.Copy(newMapping, mapping)
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
	maps.Copy(map1, map2)

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

// createDeepCopy creates a copy of a *jsonschema.Schema object.
func createCopy(obj *jsonschema.Schema) *jsonschema.Schema {
	// Marshal the original object to JSON
	data, err := json.Marshal(obj)
	if err != nil {
		panic(fmt.Sprintf("failed to marshal schema: %v", err))
	}

	// Unmarshal the JSON data back to a new object
	copy := new(jsonschema.Schema)
	if err := json.Unmarshal(data, copy); err != nil {
		panic(fmt.Sprintf("failed to unmarshal schema: %v", err))
	}

	return copy
}
