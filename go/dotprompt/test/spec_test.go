// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	"github.com/go-viper/mapstructure/v2"
	. "github.com/google/dotprompt/go/dotprompt"
	"gopkg.in/yaml.v3"
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
		env, dotpromptOptions := dotpromptFactory(s)

		// Render the template.
		options := &PromptMetadata{}
		if err := mapstructure.Decode(tc.Options, options); err != nil {
			t.Fatalf("Failed to decode options: %v", err)
		}
		dataArg := mergeData(s.Data, tc.Data)
		result, err := env.Render(s.Template, &dataArg, options, dotpromptOptions)
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
		for k, v := range data2.Input {
			merged.Input[k] = v
		}
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
		for k, v := range data2.Context {
			merged.Context[k] = v
		}
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
			inputMap["schema"] = pruneSchema(t, result.Input.Schema)
		}
		if result.Input.Default != nil {
			inputMap["default"] = result.Input.Default
		}
		pruned["input"] = inputMap
	}
	if result.Output.Format != "" || result.Output.Schema != nil {
		outputMap := make(map[string]any)
		if result.Output.Schema != nil {
			outputMap["schema"] = pruneSchema(t, result.Output.Schema)
		}
		if result.Output.Format != "" {
			outputMap["format"] = result.Output.Format
		}
		pruned["output"] = outputMap
	}
	if len(result.HasMetadata.Metadata) > 0 {
		pruned["metadata"] = result.HasMetadata.Metadata
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
		if len(message.HasMetadata.Metadata) > 0 {
			prunedMessage["metadata"] = message.HasMetadata.Metadata
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
				prunedPart["media"] = map[string]any{
					"url":         p.Media.URL,
					"contentType": p.Media.ContentType,
				}
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

// pruneSchema prunes a schema for comparison.
func pruneSchema(t *testing.T, schema Schema) map[string]any {
	schemaMap := make(map[string]any)
	schemaBytes, _ := yaml.Marshal(schema)
	if err := yaml.Unmarshal(schemaBytes, &schemaMap); err != nil {
		t.Fatalf("Failed to unmarshal output: %v", err)
	}
	return schemaMap
}

// compareResults compares the result and expected output.
func compareResults(result, expected map[string]any) bool {
	resultJSON, _ := json.Marshal(result)
	expectedJSON, _ := json.Marshal(expected)
	return string(resultJSON) == string(expectedJSON)
}
