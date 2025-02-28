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

	. "github.com/google/dotprompt/go/dotprompt"
	"github.com/mitchellh/mapstructure"
	"gopkg.in/yaml.v3"
)

const SpecDir = "../../spec"

type Expect struct {
	Config   map[string]interface{}   `yaml:"config"`
	Ext      map[string]interface{}   `yaml:"ext"`
	Input    map[string]interface{}   `yaml:"input"`
	Output   map[string]interface{}   `yaml:"output"`
	Messages []map[string]interface{} `yaml:"messages"`
	Metadata map[string]interface{}   `yaml:"metadata"`
	Raw      map[string]interface{}   `yaml:"raw"`
}

type SpecTest struct {
	Desc    string                 `yaml:"desc"`
	Data    DataArgument           `yaml:"data"`
	Expect  Expect                 `yaml:"expect"`
	Options map[string]interface{} `yaml:"options"`
}

// compareMaps performs a deep comparison of two maps of type map[string]interface{}.
func compareMaps(map1, map2 map[string]interface{}) bool {
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
func deepEqual(v1, v2 interface{}) bool {
	if reflect.TypeOf(v1) != reflect.TypeOf(v2) {
		return false
	}
	switch v1 := v1.(type) {
	case map[string]interface{}:
		v2, ok := v2.(map[string]interface{})
		if !ok {
			return false
		}
		return compareMaps(v1, v2)
	case []interface{}:
		v2, ok := v2.([]interface{})
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

type SpecSuite struct {
	Name             string                    `yaml:"name"`
	Template         string                    `yaml:"template"`
	Data             DataArgument              `yaml:"data"`
	Schemas          map[string]JSONSchema     `yaml:"schemas"`
	Tools            map[string]ToolDefinition `yaml:"tools"`
	Partials         map[string]string         `yaml:"partials"`
	ResolverPartials map[string]string         `yaml:"resolverPartials"`
	Tests            []SpecTest                `yaml:"tests"`
}

func createTestCases(t *testing.T, s SpecSuite, tc SpecTest, dotpromptFactory func(suite SpecSuite) (*Dotprompt, *DotpromptOptions)) {
	t.Run(tc.Desc, func(t *testing.T) {
		env, dotpromptOptions := dotpromptFactory(s)

		// Define partials if they exist.
		// if s.Partials != nil {
		// 	for name, template := range s.Partials {
		// 		env.DefinePartial(name, template)
		// 	}
		// }

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
		prunedResult := pruneResult(result.PromptMetadata)
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

func createTestSuite(t *testing.T, suiteName string, suites []SpecSuite, dotpromptFactory func(suite SpecSuite) (*Dotprompt, *DotpromptOptions)) {
	t.Run(suiteName, func(t *testing.T) {
		for _, s := range suites {
			t.Run(s.Name, func(t *testing.T) {
				for _, tc := range s.Tests {
					// fmt.Println(tc)
					createTestCases(t, s, tc, dotpromptFactory)
				}
			})
		}
	})
}

func processSpecFile(t *testing.T, file string, dotpromptFactory func(suite SpecSuite) (*Dotprompt, *DotpromptOptions)) {
	suiteName := filepath.Base(file)
	content, err := os.ReadFile(file)
	if err != nil {
		t.Fatalf("Failed to read file: %v", err)
	}
	var suites []SpecSuite
	fmt.Println(suiteName)
	if err := yaml.Unmarshal(content, &suites); err != nil {
		t.Fatalf("Failed to unmarshal YAML: %v", err)
	}
	createTestSuite(t, suiteName, suites, dotpromptFactory)
}

func processSpecFiles(t *testing.T) {
	files, err := os.ReadDir(SpecDir)
	if err != nil {
		t.Fatalf("Failed to read spec directory: %v", err)
	}
	for _, file := range files {
		if !file.IsDir() && filepath.Ext(file.Name()) == ".yaml" {
			processSpecFile(t, filepath.Join(SpecDir, file.Name()), func(s SpecSuite) (*Dotprompt, *DotpromptOptions) {
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
	}
}

func TestSpecFiles(t *testing.T) {
	processSpecFiles(t)
}

func mergeData(data1, data2 DataArgument) DataArgument {
	merged := data1
	if data2.Input != nil {
		if merged.Input == nil {
			merged.Input = make(map[string]interface{})
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
			merged.Context = make(map[string]interface{})
		}
		for k, v := range data2.Context {
			merged.Context[k] = v
		}
	}
	return merged
}

func pruneResult(result PromptMetadata) map[string]interface{} {
	pruned := make(map[string]interface{})
	if len(result.Config) > 0 {
		pruned["config"] = result.Config
	}
	if len(result.Ext) > 0 {
		pruned["ext"] = result.Ext
	}
	if len(result.Input.Default) > 0 {
		pruned["input"] = result.Input
	}
	if result.Input.Default != nil || result.Input.Schema != nil {
		pruned["input"] = result.Input
	}
	if result.Output.Format != "" || result.Output.Schema != nil {
		pruned["output"] = result.Output
	}
	if len(result.HasMetadata.Metadata) > 0 {
		pruned["metadata"] = result.HasMetadata.Metadata
	}
	return pruned
}

func pruneExpected(expect Expect) map[string]interface{} {
	pruned := make(map[string]interface{})
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

func pruneMessages(messages []Message) []map[string]interface{} {
	pruned := make([]map[string]interface{}, 0)
	for _, message := range messages {
		prunedMessage := make(map[string]interface{})
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

func pruneContent(content []Part) []map[string]interface{} {
	pruned := make([]map[string]interface{}, 0)
	for _, part := range content {
		prunedPart := make(map[string]interface{})
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
				prunedPart["media"] = p.Media
			}
		case *ToolRequestPart:
			if len(p.ToolRequest) > 0 {
				prunedPart["toolRequest"] = p.ToolRequest
			}
		case *ToolResponsePart:
			if len(p.ToolResponse) > 0 {
				prunedPart["toolResponse"] = p.ToolResponse
			}
		case *PendingPart:
			if p.IsPending() {
				prunedPart["pending"] = true
			}
		}
		if len(part.GetMetadata()) > 0 {
			prunedPart["metadata"] = part.GetMetadata()
		}
		pruned = append(pruned, prunedPart)
	}
	return pruned
}

func compareResults(result, expected map[string]interface{}) bool {
	resultJSON, _ := json.Marshal(result)
	expectedJSON, _ := json.Marshal(expected)
	return string(resultJSON) == string(expectedJSON)
}
