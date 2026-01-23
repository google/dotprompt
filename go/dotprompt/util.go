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
	"maps"
	"net/url"
	"strings"
	"unicode"

	"github.com/invopop/jsonschema"
	"golang.org/x/text/unicode/norm"
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

// intOrZero returns the int value of an any or a 0 if it's not an int
func intOrZero(value any) int {
	if value == nil {
		return 0
	}

	if intValue, ok := value.(uint64); ok {
		return int(intValue)
	}

	return 0
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

	// Trim leading and trailing spaces after the loop to handle edge cases
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

// ValidatePromptName validates that a prompt name doesn't contain path traversal sequences.
//
// This function implements multiple layers of validation to prevent path
// traversal attacks (CWE-22):
// 1. URL decoding - catches %2e%2e encoded dots
// 2. Unicode normalization - catches homograph bypass attempts
// 3. Segment-based validation - checks each path component for leading dots
//
// It returns an error if the name implies path traversal or other unsafe patterns.
func ValidatePromptName(name string) error {
	if name == "" {
		return fmt.Errorf("prompt name cannot be empty")
	}

	// Check for whitespace-only names
	if strings.TrimSpace(name) == "" {
		return fmt.Errorf("invalid prompt name: '%s'", name)
	}

	// Check for null bytes
	if strings.ContainsRune(name, '\x00') {
		return fmt.Errorf("invalid prompt name: '%s'", name)
	}

	// Check for null byte escape sequence pattern (backslash followed by zero)
	// This catches suspicious escape sequences even if not actual null bytes
	if strings.Contains(name, `\0`) {
		return fmt.Errorf("invalid prompt name: null byte escape sequence not allowed: '%s'", name)
	}

	// SECURITY FIX 1: Decode URL-encoded input BEFORE validation
	// This catches bypasses like %2e%2e which decodes to ..
	// SECURITY: Decode iteratively to catch double-encoding bypasses (%252e%252e)
	decoded := name
	for range 3 {
		newDecoded, err := url.QueryUnescape(decoded)
		if err != nil {
			// If decoding fails, we proceed with the current value
			// In strict mode we might want to fail, but for now we follow best effort
			break
		}
		if newDecoded == decoded {
			break
		}
		decoded = newDecoded
	}

	// Check for remaining encoded characters (potential double-encoding bypass)
	if strings.Contains(decoded, "%") {
		return fmt.Errorf("invalid prompt name: encoded characters not allowed: '%s'", name)
	}
	name = decoded

	// SECURITY FIX 2: Normalize Unicode BEFORE validation
	// This catches homograph attacks where visually similar characters
	// are used to bypass validation
	// Note: NFC doesn't convert all Unicode dots, so we check for suspicious patterns
	normalized := norm.NFC.String(name)

	// Check for current directory reference patterns
	if strings.Contains(normalized, "./") || strings.Contains(normalized, ".\\") {
		return fmt.Errorf("invalid path: current directory reference not allowed: '%s'", name)
	}

	// SECURITY FIX 3: Check for path traversal using segment-based validation
	// This catches:
	// - Segments that are only dots: "..", "...", "....", etc.
	// - Segments STARTING with "..": "..config", "..hidden" (leading parent reference)
	// - Segments ENDING with ".." when followed by non-alphanumeric: "safe..", "0.."
	// Allows: "a..b", "file..txt", "...test", "test..." (legitimate filename patterns)

	// Normalize checks by replacing backslashes with slashes
	normalizedForCheck := strings.ReplaceAll(normalized, "\\", "/")
	segments := strings.SplitSeq(normalizedForCheck, "/")

	for seg := range segments {
		// Check if segment is ONLY dots (2 or more)
		isOnlyDots := len(seg) >= 2
		if isOnlyDots {
			for _, r := range seg {
				if r != '.' {
					isOnlyDots = false
					break
				}
			}
		}
		if isOnlyDots {
			return fmt.Errorf("path traversal not allowed: '%s'", name)
		}

		// Check if segment STARTS with ".." (potential bypass: "..config", "..hidden")
		// Allow segments starting with 3+ dots like "...test" which are legitimate filenames
		// Block only if it starts with exactly ".." (2 dots) not "...", "...." etc
		if len(seg) > 2 && seg[0] == '.' && seg[1] == '.' && seg[2] != '.' {
			// Starts with exactly ".." followed by non-dot - check if valid pattern
			// Go implementation of python's match(r'^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$', seg) is strictly not applicable here as we are in the start check
			// Wait, the python logic was:
			// if len(seg) > 2 and seg[0] == '.' and seg[1] == '.' and seg[2] != '.':
			// 	if not re.match(r'^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$', seg):
			//      raise ...
			// But wait, if it starts with '..', it can't match '^[a-zA-Z0-9]+...' which expects alphanumeric start.
			// So effectively, if it starts with '..', it is rejected UNLESS it is '...' (which is handled by len(seg)>2 check above? No, '...' starts with '..').

			// Let's re-read python logic:
			// if len(seg) > 2 and seg[0] == '.' and seg[1] == '.' and seg[2] != '.':
			//    match alphanumeric..alphanumeric

			// If it starts with '..x', the match 'alphanum..alphanum' will FAIL because it starts with dot.
			// So this effectively bans anything starting with '..' that isn't '...' (3 dots or more).
			// Yes.
			return fmt.Errorf("path traversal not allowed: '%s'", name)
		}

		// Check if segment ENDS with ".." (potential bypass: "safe..", "0..", "test..")
		if strings.HasSuffix(seg, "..") && len(seg) > 2 {
			// Allow if: alphanumeric..alphanumeric (has chars after ..) -> Wait, if it ends with .., it has NO chars after ..
			// The python code:
			// if seg.endswith('..') and len(seg) > 2:
			//   has_chars_after = bool(re.match(r'^[a-zA-Z0-9]+\.\.[a-zA-Z0-9]+$', seg))
			//   has_trailing_triple = bool(re.match(r'.*\.\.\.+$', seg))

			// If it ends with '..', has_chars_after must be False.
			// So effectively we only allow it if it has trailing triple dots (e.g. `test...`)

			// Let's implement trailing triple check.
			// Check if it ends with '...'
			if !strings.HasSuffix(seg, "...") {
				return fmt.Errorf("path traversal not allowed: '%s'", name)
			}
		}
	}

	// Check for absolute paths (Unix-style)
	if strings.HasPrefix(normalized, "/") {
		return fmt.Errorf("invalid path: absolute paths not allowed: '%s'", name)
	}

	// Check for trailing slash
	if strings.HasSuffix(normalizedForCheck, "/") {
		return fmt.Errorf("invalid path: trailing slash not allowed: '%s'", name)
	}

	// Check for Windows absolute paths (e.g., C:/, C:\)
	// Only block when first char is a letter AND second is :
	if len(normalized) > 1 && normalized[1] == ':' && unicode.IsLetter(rune(normalized[0])) {
		return fmt.Errorf("invalid prompt name: '%s'", name)
	}

	// Check for UNC network paths (\\server\share)
	if strings.HasPrefix(normalized, "\\\\") {
		return fmt.Errorf("invalid prompt name: '%s'", name)
	}

	return nil
}
