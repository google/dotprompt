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

	"github.com/invopop/jsonschema"
)

func TestDefineSchema(t *testing.T) {
	dp := NewDotprompt(nil)

	testSchema := &jsonschema.Schema{Type: "string"}
	result := dp.DefineSchema("Person", testSchema)
	if result != testSchema {
		t.Errorf("Expected dp.DefineSchema to return the same schema, got %v, want %v", result, testSchema)
	}

	schema, exists := dp.LookupSchema("Person")
	if !exists {
		t.Error("Expected schema to exist after defining it")
	}
	if schema != testSchema {
		t.Errorf("Expected lookup to return the same schema, got %v, want %v", schema, testSchema)
	}

	newSchema := &jsonschema.Schema{Type: "object"}
	result = dp.DefineSchema("Person", newSchema)
	if result != newSchema {
		t.Errorf("Expected dp.DefineSchema to return the same schema, got %v, want %v", result, newSchema)
	}

	schema, exists = dp.LookupSchema("Person")
	if !exists {
		t.Error("Expected schema to exist after redefining it")
	}
	if schema != newSchema {
		t.Errorf("Expected lookup to return the redefined schema, got %v, want %v", schema, newSchema)
	}

	// Testing panic scenarios
	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Error("Expected panic with empty name, but it didn't happen")
			}
		}()
		dp.DefineSchema("", testSchema)
	}()

	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Error("Expected panic with nil schema, but it didn't happen")
			}
		}()
		dp.DefineSchema("Test", nil)
	}()
}

func TestExternalSchemaLookup(t *testing.T) {
	dp := NewDotprompt(nil)

	testSchema := &jsonschema.Schema{Type: "number"}
	dp.RegisterExternalSchemaLookup(func(name string) any {
		if name == "ExternalSchema" {
			return testSchema
		}
		return nil
	})

	schema := dp.LookupSchemaFromAnySource("ExternalSchema")
	if schema != testSchema {
		t.Errorf("Expected external lookup to return the test schema, got %v, want %v", schema, testSchema)
	}

	schema = dp.LookupSchemaFromAnySource("NonExistentSchema")
	if schema != nil {
		t.Errorf("Expected nil for non-existent schema, got %v", schema)
	}
}

func TestResolveSchemaReferences(t *testing.T) {
	dp := NewDotprompt(nil)

	testSchema := &jsonschema.Schema{Type: "string"}
	dp.DefineSchema("TestSchema", testSchema)

	metadata := map[string]any{
		"input": map[string]any{
			"schema": "TestSchema",
		},
	}
	err := dp.ResolveSchemaReferences(metadata)
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	inputSection := metadata["input"].(map[string]any)
	if inputSection["schema"] != testSchema {
		t.Errorf("Expected schema reference to be resolved, got %v, want %v", inputSection["schema"], testSchema)
	}

	metadata = map[string]any{
		"output": map[string]any{
			"schema": "TestSchema",
		},
	}
	err = dp.ResolveSchemaReferences(metadata)
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	outputSection := metadata["output"].(map[string]any)
	if outputSection["schema"] != testSchema {
		t.Errorf("Expected schema reference to be resolved, got %v, want %v", outputSection["schema"], testSchema)
	}

	metadata = map[string]any{
		"input": map[string]any{
			"schema": "NonExistentSchema",
		},
	}
	err = dp.ResolveSchemaReferences(metadata)
	if err == nil {
		t.Error("Expected error for non-existent schema, got nil")
	}
}
