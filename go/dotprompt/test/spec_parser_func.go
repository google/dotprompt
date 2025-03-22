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
	"fmt"
	"testing"

	dp "github.com/google/dotprompt/go/dotprompt"
	"github.com/invopop/jsonschema"
	"gopkg.in/yaml.v3"
)

// convertToSpecSuite converts the YAML content into a slice of SpecSuite objects.
func convertToSpecSuite(t *testing.T, content []byte) []SpecSuite {
	var suites []SpecSuite
	var raw []map[string]any

	// Unmarshal the YAML content into a raw slice of maps.
	if err := yaml.Unmarshal(content, &raw); err != nil {
		t.Fatalf("Failed to unmarshal YAML: %v", err)
	}

	// Iterate over each raw map and convert it to a SpecSuite object.
	for _, r := range raw {
		suite := SpecSuite{}
		if name, ok := r["name"].(string); ok {
			suite.Name = name
		}
		if template, ok := r["template"].(string); ok {
			suite.Template = template
		}
		suite.Data = convertDataArg(t, r["data"])
		suite.Schemas = convertSchema(t, r["schemas"])
		suite.Tools = convertTools(t, r["tools"])
		suite.Partials = convertMapString(r["partials"])
		suite.ResolverPartials = convertMapString(r["resolverPartials"])

		if r["tests"] != nil {
			suite.Tests = convertTestSpec(t, r["tests"])
		}
		suites = append(suites, suite)
	}

	return suites
}

// convertSchema converts the listed schema data into a map of *jsonschema.Schema objects.
func convertSchema(t *testing.T, schemaRaw any) map[string]*jsonschema.Schema {
	var schemas map[string]*jsonschema.Schema
	if schemaMap, ok := schemaRaw.(map[string]any); ok {
		schemaBytes, err := yaml.Marshal(schemaMap)
		if err != nil {
			t.Fatalf("Failed to marshal schemas: %v", err)
		}
		if err := yaml.Unmarshal(schemaBytes, &schemas); err != nil {
			t.Fatalf("Failed to unmarshal schema: %v", err)
		}
	}
	return schemas
}

// convertTools converts the raw tools data into a map of ToolDefinition objects.
func convertTools(t *testing.T, toolsRaw any) map[string]dp.ToolDefinition {
	var tools map[string]dp.ToolDefinition
	if toolsMap, ok := toolsRaw.(map[string]any); ok {
		toolsBytes, err := yaml.Marshal(toolsMap)
		if err != nil {
			t.Fatalf("Failed to marshal tool: %v", err)
		}
		if err := yaml.Unmarshal(toolsBytes, &tools); err != nil {
			t.Fatalf("Failed to unmarshal tool: %v", err)
		}
	}
	return tools
}

// convertMapString converts a raw map into a map of strings.
func convertMapString(rawMap any) map[string]string {
	strMap := make(map[string]string)
	if anyMap, ok := rawMap.(map[string]any); ok {
		for k, v := range anyMap {
			if value, ok := v.(string); ok {
				strMap[k] = value
			}
		}
	}
	return strMap
}

// convertTestSpec converts the raw test specifications into a slice of SpecTest objects.
func convertTestSpec(t *testing.T, testsRaw any) []SpecTest {
	var specTests []SpecTest
	if tests, ok := testsRaw.([]any); ok {
		for _, test := range tests {
			specTest := SpecTest{}
			if testMap, ok := test.(map[string]any); ok {
				if desc, ok := testMap["desc"].(string); ok {
					specTest.Desc = desc
				}
				specTest.Data = convertDataArg(t, testMap["data"])
				specTest.Expect = convertExpect(testMap["expect"])
				if options, ok := testMap["options"].(map[string]any); ok {
					specTest.Options = options
				}
				specTests = append(specTests, specTest)
			}
		}
	}
	return specTests
}

// convertExpect converts the raw expect data into an Expect object.
func convertExpect(expectRaw any) Expect {
	var expect Expect
	if expectMap, ok := expectRaw.(map[string]any); ok {
		if config, ok := expectMap["config"].(map[string]any); ok {
			expect.Config = config
		}
		if ext, ok := expectMap["ext"].(map[string]any); ok {
			expect.Ext = ext
		}
		if input, ok := expectMap["input"].(map[string]any); ok {
			expect.Input = input
		}
		if output, ok := expectMap["output"].(map[string]any); ok {
			expect.Output = output
		}
		if messages, ok := expectMap["messages"].([]any); ok {
			var msgArr []map[string]any
			for _, v := range messages {
				if vstruct, ok := v.(map[string]any); ok {
					msgArr = append(msgArr, vstruct)
				}
			}
			expect.Messages = msgArr
		}
		if metadata, ok := expectMap["metadata"].(map[string]any); ok {
			expect.Metadata = metadata
		}
		if raw, ok := expectMap["raw"].(map[string]any); ok {
			expect.Raw = raw
		}
	}
	return expect
}

// convertDataArg converts the raw data argument into a DataArgument object.
func convertDataArg(t *testing.T, dataMap any) dp.DataArgument {
	dataArg := dp.DataArgument{}
	if data, ok := dataMap.(map[string]any); ok {
		if data["messages"] != nil {
			rawMessages := data["messages"].([]any)
			messages := convertMessages(t, rawMessages)
			dataArg.Messages = messages
		}
		if data["docs"] != nil {
			rawDocs := data["docs"].([]any)
			docs := convertDocs(t, rawDocs)
			dataArg.Docs = docs
		}
		if data["input"] != nil {
			dataArg.Input = data["input"].(map[string]any)
		}
		if data["context"] != nil {
			dataArg.Context = data["context"].(map[string]any)
		}
	}
	return dataArg
}

// convertMessages converts the raw messages data into a slice of Message objects.
func convertMessages(t *testing.T, rawMessages []any) []dp.Message {
	messages := []dp.Message{}
	for _, rawMessage := range rawMessages {
		if message, ok := rawMessage.(map[string]any); ok {
			var msgType dp.Message
			if rawContents, ok := message["content"].([]any); ok {
				contents := convertContents(t, rawContents)
				if contents != nil {
					msgType.Content = contents
				}
			}
			if message["role"] != nil {
				msgType.Role = dp.Role(message["role"].(string))
			}
			if message["metadata"] != nil {
				msgType.Metadata = message["metadata"].(map[string]any)
			}
			messages = append(messages, msgType)
		}
	}
	return messages
}

// convertDocs converts the raw documents data into a slice of Document objects.
func convertDocs(t *testing.T, rawDocs []any) []dp.Document {
	docs := []dp.Document{}
	for _, rawDoc := range rawDocs {
		if doc, ok := rawDoc.(map[string]any); ok {
			document := dp.Document{}
			if doc["content"] != nil {
				rawContents := doc["content"].([]any)
				contents := convertContents(t, rawContents)
				document.Content = contents
			}
			if doc["metadata"] != nil {
				document.Metadata = doc["metadata"].(map[string]any)
			}
			docs = append(docs, document)
		}
	}
	return docs
}

// convertContents converts the raw contents data into a slice of Part objects.
func convertContents(t *testing.T, rawContents []any) []dp.Part {
	contents := []dp.Part{}
	for _, rawContent := range rawContents {
		if content, ok := rawContent.(map[string]any); ok {
			part := convertContent(t, content)
			if part != nil {
				contents = append(contents, part)
			}
		}
	}
	return contents
}

// convertContent converts a raw content map into a Part object.
func convertContent(t *testing.T, content map[string]any) dp.Part {
	partData, err := yaml.Marshal(content)
	if err != nil {
		t.Fatalf("Failed to marshal content: %v", err)
	}

	var part dp.Part
	if textPart := unmarshalTextPart(partData); textPart != nil {
		part = textPart
	} else if dataPart := unmarshalDataPart(partData); dataPart != nil {
		part = dataPart
	} else if mediaPart := unmarshalMediaPart(partData); mediaPart != nil {
		part = mediaPart
	} else if toolRequestPart := unmarshalToolRequestPart(partData); toolRequestPart != nil {
		part = toolRequestPart
	} else if toolResponsePart := unmarshalToolResponsePart(partData); toolResponsePart != nil {
		part = toolResponsePart
	} else if pendingPart := unmarshalPendingPart(partData); pendingPart != nil {
		part = pendingPart
	} else {
		fmt.Println("Unknown part type")
		return nil
	}
	return part
}

// unmarshalTextPart unmarshals data into a TextPart object if possible.
func unmarshalTextPart(data []byte) *dp.TextPart {
	var textPart dp.TextPart
	if err := yaml.Unmarshal(data, &textPart); err == nil && textPart.Text != "" {
		return &textPart
	}
	return nil
}

// unmarshalDataPart unmarshals data into a DataPart object if possible.
func unmarshalDataPart(data []byte) *dp.DataPart {
	var dataPart dp.DataPart
	if err := yaml.Unmarshal(data, &dataPart); err == nil && dataPart.Data != nil {
		return &dataPart
	}
	return nil
}

// unmarshalMediaPart unmarshals data into a MediaPart object if possible.
func unmarshalMediaPart(data []byte) *dp.MediaPart {
	var mediaPart dp.MediaPart
	if err := yaml.Unmarshal(data, &mediaPart); err == nil && mediaPart.Media.URL != "" {
		return &mediaPart
	}
	return nil
}

// unmarshalToolRequestPart unmarshals data into a ToolRequestPart object if possible.
func unmarshalToolRequestPart(data []byte) *dp.ToolRequestPart {
	var toolRequestPart dp.ToolRequestPart
	if err := yaml.Unmarshal(data, &toolRequestPart); err == nil && toolRequestPart.ToolRequest != nil {
		return &toolRequestPart
	}
	return nil
}

// unmarshalToolResponsePart unmarshals data into a ToolResponsePart object if possible.
func unmarshalToolResponsePart(data []byte) *dp.ToolResponsePart {
	var toolResponsePart dp.ToolResponsePart
	if err := yaml.Unmarshal(data, &toolResponsePart); err == nil && toolResponsePart.ToolResponse != nil {
		return &toolResponsePart
	}
	return nil
}

// unmarshalPendingPart unmarshals data into a PendingPart object if possible.
func unmarshalPendingPart(data []byte) *dp.PendingPart {
	var pendingPart dp.PendingPart
	if err := yaml.Unmarshal(data, &pendingPart); err == nil {
		return &pendingPart
	}
	return nil
}
