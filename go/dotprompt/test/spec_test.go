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
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"maps"

	"github.com/go-viper/mapstructure/v2"
	. "github.com/google/dotprompt/go/dotprompt"
	"github.com/invopop/jsonschema"
)

const SpecDir = "../../../spec"

func TestSpecFiles(t *testing.T) {
	processSpecFiles(t)
}

// compareMaps performs a deep comparison of two maps of type map[string]any.
func compareMaps(map1, map2 map[string]any) bool {
	if len(map1) != len(map2) {
		return false
	}
	for k, v1 := range map1 {
		v2, ok := map2[k]
		if !ok {
			return false
		}
		if !deepEqual(v1, v2) {
			return false
		}
	}
	return true
}

// deepEqual performs a deep comparison of two values.
func deepEqual(v1, v2 any) bool {
	if reflect.TypeOf(v1) != reflect.TypeOf(v2) {
		return false
	}
	switch v1 := v1.(type) {
	case map[string]any:
		v2, ok := v2.(map[string]any)
		if !ok {
			return false
		}
		return compareMaps(v1, v2)
	case []any:
		v2, ok := v2.([]any)
		if !ok {
			return false
		}
		if len(v1) != len(v2) {
			return false
		}
		for i := range v1 {
			if !deepEqual(v1[i], v2[i]) {
				return false
			}
		}
		return true
	default:
		return reflect.DeepEqual(v1, v2)
	}
}

// createTestCases creates and runs test cases for a given SpecSuite and SpecTest.
func createTestCases(t *testing.T, s SpecSuite, tc SpecTest, dotpromptFactory func(suite SpecSuite) (*Dotprompt, *DotpromptOptions)) {
	t.Run(tc.Desc, func(t *testing.T) {
		env, _ := dotpromptFactory(s)

		// Render the template.
		options := &PromptMetadata{}
		if err := mapstructure.Decode(tc.Options, options); err != nil {
			t.Fatalf("Failed to decode options: %v", err)
		}
		dataArg := mergeData(s.Data, tc.Data)
		result, err := env.Render(s.Template, &dataArg, options)
		if err != nil {
			t.Fatalf("Render failed: %v", err)
		}
		// Prune the result and compare to the expected output.
		prunedResult := pruneResult(t, result.PromptMetadata)
		if len(result.Messages) > 0 {
			prunedResult["messages"] = pruneMessages(result.Messages)
		}
		expected := pruneExpected(tc.Expect)

		// Compare the pruned result to the expected output.
		if !compareResults(prunedResult, expected) {
			t.Errorf("Render should produce the expected result. Got: %v, Expected: %v", prunedResult, expected)
		}

		// Only compare raw if the spec demands it.
		if tc.Expect.Raw != nil {
			if !compareMaps(result.Raw, tc.Expect.Raw) {
				t.Errorf("Raw output mismatch. Got: %v, Expected: %v", result.Raw, tc.Expect.Raw)
			}
		}
	})
}

// createTestSuite creates and runs a test suite for a given suite name and SpecSuite.
func createTestSuite(t *testing.T, suiteName string, suites []SpecSuite, dotpromptFactory func(suite SpecSuite) (*Dotprompt, *DotpromptOptions)) {
	t.Run(suiteName, func(t *testing.T) {
		for _, s := range suites {
			t.Run(s.Name, func(t *testing.T) {
				for _, tc := range s.Tests {
					createTestCases(t, s, tc, dotpromptFactory)
				}
			})
		}
	})
}

// processSpecFile processes a single spec file and creates a test suite for it.
func processSpecFile(t *testing.T, file string, dotpromptFactory func(suite SpecSuite) (*Dotprompt, *DotpromptOptions)) {
	suiteName := filepath.Base(file)
	content, err := os.ReadFile(file)
	if err != nil {
		t.Fatalf("Failed to read file: %v", err)
	}
	fmt.Println(suiteName)
	suites := convertToSpecSuite(t, content)
	createTestSuite(t, suiteName, suites, dotpromptFactory)
}

// processSpecFiles processes all spec files in the SpecDir directory.
func processSpecFiles(t *testing.T) {
	err := filepath.Walk(SpecDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && filepath.Ext(info.Name()) == ".yaml" {
			processSpecFile(t, path, func(s SpecSuite) (*Dotprompt, *DotpromptOptions) {
				options := &DotpromptOptions{
					Schemas:  s.Schemas,
					Tools:    s.Tools,
					Partials: s.Partials,
					PartialResolver: func(name string) (string, error) {
						if partial, ok := s.ResolverPartials[name]; ok {
							return partial, nil
						}
						return "", nil
					},
				}
				return NewDotprompt(options), options
			})
		}
		return nil
	})
	if err != nil {
		t.Fatalf("Failed to read spec directory: %v", err)
	}
}

// mergeData merges two DataArgument objects.
func mergeData(data1, data2 DataArgument) DataArgument {
	merged := data1
	if data2.Input != nil {
		if merged.Input == nil {
			merged.Input = make(map[string]any)
		}
		maps.Copy(merged.Input, data2.Input)
	}
	if data2.Docs != nil {
		merged.Docs = append(merged.Docs, data2.Docs...)
	}
	if data2.Messages != nil {
		merged.Messages = append(merged.Messages, data2.Messages...)
	}
	if data2.Context != nil {
		if merged.Context == nil {
			merged.Context = make(map[string]any)
		}
		maps.Copy(merged.Context, data2.Context)
	}
	return merged
}

// pruneResult prunes the result of a PromptMetadata object for comparison.
func pruneResult(t *testing.T, result PromptMetadata) map[string]any {
	pruned := make(map[string]any)
	if len(result.Config) > 0 {
		pruned["config"] = result.Config
	}
	if len(result.Ext) > 0 {
		pruned["ext"] = result.Ext
	}
	if result.Input.Default != nil || result.Input.Schema != nil {
		inputMap := make(map[string]any)
		if result.Input.Schema != nil {
			if inputSchema, ok := result.Output.Schema.(*jsonschema.Schema); ok {
				rawInput, _ := result.Raw["output"].(map[string]any)
				rawSchema, _ := rawInput["schema"].(map[string]any)
				inputMap["schema"] = pruneSchema(inputSchema, rawSchema)
			}
		}
		if result.Input.Default != nil {
			inputMap["default"] = result.Input.Default
		}
		pruned["input"] = inputMap
	}
	if result.Output.Format != "" || result.Output.Schema != nil {
		outputMap := make(map[string]any)
		if result.Output.Schema != nil {
			if outputSchema, ok := result.Output.Schema.(*jsonschema.Schema); ok {
				rawOutput, _ := result.Raw["output"].(map[string]any)
				rawSchema, _ := rawOutput["schema"].(map[string]any)
				outputMap["schema"] = pruneSchema(outputSchema, rawSchema)
			}
		}
		if result.Output.Format != "" {
			outputMap["format"] = result.Output.Format
		}
		pruned["output"] = outputMap
	}
	if len(result.Metadata) > 0 {
		pruned["metadata"] = result.Metadata
	}
	return pruned
}

// pruneExpected prunes the expected output for comparison.
func pruneExpected(expect Expect) map[string]any {
	pruned := make(map[string]any)
	if len(expect.Config) > 0 {
		pruned["config"] = expect.Config
	}
	if len(expect.Ext) > 0 {
		pruned["ext"] = expect.Ext
	}
	if len(expect.Input) > 0 {
		pruned["input"] = expect.Input
	}
	if len(expect.Output) > 0 {
		pruned["output"] = expect.Output
	}
	if len(expect.Messages) > 0 {
		pruned["messages"] = expect.Messages
	}
	if len(expect.Metadata) > 0 {
		pruned["metadata"] = expect.Metadata
	}
	return pruned
}

// pruneMessages prunes the messages for comparison.
func pruneMessages(messages []Message) []map[string]any {
	pruned := make([]map[string]any, 0)
	for _, message := range messages {
		prunedMessage := make(map[string]any)
		if len(message.Content) > 0 {
			prunedMessage["content"] = pruneContent(message.Content)
		}
		if len(message.Metadata) > 0 {
			prunedMessage["metadata"] = message.Metadata
		}
		if len(message.Role) > 0 {
			prunedMessage["role"] = message.Role
		}
		pruned = append(pruned, prunedMessage)
	}
	return pruned
}

// pruneContent prunes the content of a message for comparison.
func pruneContent(content []Part) []map[string]any {
	pruned := make([]map[string]any, 0)
	for _, part := range content {
		prunedPart := make(map[string]any)
		switch p := part.(type) {
		case *TextPart:
			if p.Text != "" {
				prunedPart["text"] = p.Text
			}
		case *DataPart:
			if len(p.Data) > 0 {
				prunedPart["data"] = p.Data
			}
		case *MediaPart:
			if p.Media.URL != "" || p.Media.ContentType != "" {
				mediaMap := map[string]any{
					"url": p.Media.URL,
				}
				// Only include contentType if it's not empty (matches JSON omitempty behavior)
				if p.Media.ContentType != "" {
					mediaMap["contentType"] = p.Media.ContentType
				}
				prunedPart["media"] = mediaMap
			}
		case *ToolRequestPart:
			if len(p.ToolRequest) > 0 {
				prunedPart["toolRequest"] = p.ToolRequest
			}
		case *ToolResponsePart:
			if len(p.ToolResponse) > 0 {
				prunedPart["toolResponse"] = p.ToolResponse
			}
		}
		if len(part.GetMetadata()) > 0 {
			prunedPart["metadata"] = part.GetMetadata()
		}
		pruned = append(pruned, prunedPart)
	}
	return pruned
}

func pruneSchema(schema *jsonschema.Schema, rawSchema map[string]any) map[string]any {
	schemaMap := make(map[string]any)
	if len(schema.AnyOf) != 0 {
		schemaMap["type"] = []string{}
		typeList := []string{}
		for _, anySchema := range schema.AnyOf {
			if anySchema.Type == "null" {
				typeList = append(typeList, "null")
			} else {
				typeList = append(typeList, anySchema.Type)
			}
		}
		schemaMap["type"] = typeList
	} else if schema.Type != "" {
		schemaMap["type"] = schema.Type
	}
	if schema.Description != "" {
		schemaMap["description"] = schema.Description
	}
	if schema.Items != nil {
		schemaMap["items"] = pruneSchema(schema.Items, rawSchema)
	}

	if schema.Type == "object" {
		if schema.AdditionalProperties == nil {
			if rawSchema != nil {
				schemaBytes, _ := json.Marshal(rawSchema)
				schemaJSON := &jsonschema.Schema{}
				_ = json.Unmarshal(schemaBytes, schemaJSON)
				// Validate that all fields in schemaMap are present in schemaJSON
				if err := ValidateSchemaFields(rawSchema, schemaJSON); err != nil {
					schemaMap["additionalProperties"] = false
				}
			}
		} else {
			schemaMap["additionalProperties"] = pruneSchema(schema.AdditionalProperties, rawSchema)
		}
		if len(schema.Required) != 0 {
			schemaMap["required"] = schema.Required
		}
		propMap := make(map[string]any)
		for property := schema.Properties.Oldest(); property != nil; property = property.Next() {
			propName := property.Key
			prop := property.Value
			propMap[propName] = pruneSchema(prop, rawSchema)
		}
		schemaMap["properties"] = propMap
	}

	if len(schema.Enum) != 0 {
		schemaMap["enum"] = schema.Enum
	}

	return schemaMap

}

// compareResults compares the result and expected output.
func compareResults(result, expected map[string]any) bool {
	resultJSON, _ := json.Marshal(result)
	expectedJSON, _ := json.Marshal(expected)
	return string(resultJSON) == string(expectedJSON)
}
