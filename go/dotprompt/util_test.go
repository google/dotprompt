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

func TestStringOrEmpty(t *testing.T) {
	if got := stringOrEmpty(nil); got != "" {
		t.Errorf("stringOrEmpty(nil) = %q, want \"\"", got)
	}
	if got := stringOrEmpty(""); got != "" {
		t.Errorf("stringOrEmpty(\"\") = %q, want \"\"", got)
	}
	if got := stringOrEmpty("test"); got != "test" {
		t.Errorf("stringOrEmpty(\"test\") = %q, want \"test\"", got)
	}
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
		want := map[string]any{"key": "value"}
		if diff := cmp.Diff(want, result); diff != "" {
			t.Errorf("getMapOrNil() mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("should return nil for nil map", func(t *testing.T) {
		result := getMapOrNil(nil, "key")
		if result != nil {
			t.Errorf("getMapOrNil(nil, \"key\") = %v, want nil", result)
		}
	})

	t.Run("should return nil for non-existent key", func(t *testing.T) {
		result := getMapOrNil(testMap, "nonExistentKey")
		if result != nil {
			t.Errorf("getMapOrNil(testMap, \"nonExistentKey\") = %v, want nil", result)
		}
	})

	t.Run("should return nil for value that's not a map", func(t *testing.T) {
		result := getMapOrNil(testMap, "notAMap")
		if result != nil {
			t.Errorf("getMapOrNil(testMap, \"notAMap\") = %v, want nil", result)
		}
	})

	t.Run("should return nil for nil value", func(t *testing.T) {
		result := getMapOrNil(testMap, "nilValue")
		if result != nil {
			t.Errorf("getMapOrNil(testMap, \"nilValue\") = %v, want nil", result)
		}
	})
}

func TestCopyMapping(t *testing.T) {
	original := map[string]any{
		"key1": "value1",
		"key2": "value2",
	}

	copy := copyMapping(original)

	if diff := cmp.Diff(original, copy); diff != "" {
		t.Errorf("copyMapping() mismatch (-want +got):\n%s", diff)
	}
}
func TestMergeMaps(t *testing.T) {
	t.Run("both maps are nil", func(t *testing.T) {
		result := MergeMaps(nil, nil)
		want := map[string]any{}
		if diff := cmp.Diff(want, result); diff != "" {
			t.Errorf("MergeMaps(nil, nil) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("first map is nil", func(t *testing.T) {
		map2 := map[string]any{"key1": "value1"}
		result := MergeMaps(nil, map2)
		if diff := cmp.Diff(map2, result); diff != "" {
			t.Errorf("MergeMaps(nil, map2) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("second map is nil", func(t *testing.T) {
		map1 := map[string]any{"key1": "value1"}
		result := MergeMaps(map1, nil)
		if diff := cmp.Diff(map1, result); diff != "" {
			t.Errorf("MergeMaps(map1, nil) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("both maps are non-nil", func(t *testing.T) {
		map1 := map[string]any{"key1": "value1"}
		map2 := map[string]any{"key2": "value2"}
		expected := map[string]any{"key1": "value1", "key2": "value2"}
		result := MergeMaps(map1, map2)
		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("MergeMaps(map1, map2) mismatch (-want +got):\n%s", diff)
		}
	})

	t.Run("overlapping keys", func(t *testing.T) {
		map1 := map[string]any{"key1": "value1"}
		map2 := map[string]any{"key1": "newValue1", "key2": "value2"}
		expected := map[string]any{"key1": "newValue1", "key2": "value2"}
		result := MergeMaps(map1, map2)
		if diff := cmp.Diff(expected, result); diff != "" {
			t.Errorf("MergeMaps(map1, map2) mismatch (-want +got):\n%s", diff)
		}
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
		if result != test.expected {
			t.Errorf("trimUnicodeSpacesExceptNewlines(%q) = %q, want %q", test.input, result, test.expected)
		}
	}
}
func TestCreateCopy(t *testing.T) {
	properties := orderedmap.New[string, *jsonschema.Schema]()
	properties.Set("property1", &jsonschema.Schema{Type: "string"})
	properties.Set("property2", &jsonschema.Schema{Type: "integer"})
	original := &jsonschema.Schema{
		Type:        "object",
		Title:       "Original Schema",
		Description: "This is the original schema",
		Properties:  properties,
	}

	copy := createCopy(original)

	if diff := cmp.Diff(original, copy, cmpopts.IgnoreUnexported(jsonschema.Schema{}, orderedmap.OrderedMap[string, *jsonschema.Schema]{})); diff != "" {
		t.Errorf("createCopy() mismatch (-want +got):\n%s", diff)
	}
	if original == copy {
		t.Errorf("createCopy() returned the same pointer")
	}

	// Modify the copy and ensure the original is not affected
	copy.Title = "Modified Schema"
	if original.Title == copy.Title {
		t.Errorf("original.Title was modified")
	}
	if original.Title != "Original Schema" {
		t.Errorf("original.Title = %q, want \"Original Schema\"", original.Title)
	}
}

func TestValidatePromptName(t *testing.T) {
	tests := []struct {
		name      string
		prompt    string
		shouldErr bool
	}{
		{"Empty string", "", true},
		{"Whitespace only", "   ", true},
		{"Null byte", "valid-name\x00.prompt", true},
		{"Escaped null byte", `valid-name\0.prompt`, true},

		// Basic Traversal
		{"Double dot", "..", true},
		{"Start double dot", "../etc/passwd", true},
		{"Embedded double dot", "subdir/../escape", true},

		// Windows/Mixed Sep
		{"Windows slash", `..\windows\system32`, true},
		{"Mixed slash", `..\../etc/passwd`, true},

		// Absolute Paths
		{"Absolute path", "/absolute/path.attack", true},
		{"Windows absolute C:", "C:/Windows/System32", true},
		{"Windows absolute backslash", `C:\Windows`, true},
		{"UNC path", `\\server\share`, true},

		// URL Encoded
		{"URL encoded ..", "%2e%2e/etc/passwd", true},
		{"URL encoded dot", "foo/%2e%2e/bar", true},
		{"Double URL encoded", "%252e%252e/etc/passwd", true},
		{"Double URL nested", "%25252e%25252e", true},

		// Homographs (if normalized correctly)
		// U+FF0E is Fullwidth Full Stop
		{"Fullwidth dot homograph", "\uff0e\uff0e/etc/passwd", false},

		// Current Directory
		{"Current dir ./", "./config", true},
		{"Current dir .\\", `.\config`, true},

		// Valid cases
		{"Simple name", "simple", false},
		{"Hyphenated", "my-prompt", false},
		{"Underscored", "my_prompt", false},
		{"Dots in middle", "a..b", false},
		{"Version dots", "version..2", false},
		{"Subdirectory", "subdir/nested", false},
		{"Deep nesting", "subdir/deeply/nested/prompt", false},
		{"Multiple dots", "a.b.c", false},
		{"Triple dot start", "...test", false},
		{"Triple dot end", "test...", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidatePromptName(tt.prompt)
			if tt.shouldErr {
				if err == nil {
					t.Errorf("ValidatePromptName(%q) expected error, got nil", tt.prompt)
				}
			} else {
				if err != nil {
					t.Errorf("ValidatePromptName(%q) expected no error, got %v", tt.prompt, err)
				}
			}
		})
	}
}
