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
	"github.com/stretchr/testify/assert"
)

func TestDefineSchema(t *testing.T) {
	dp := NewDotprompt(nil)

	testSchema := &jsonschema.Schema{Type: "string"}
	result := dp.DefineSchema("Person", testSchema)
	assert.Equal(t, testSchema, result)

	schema, exists := dp.LookupSchema("Person")
	assert.True(t, exists)
	assert.Equal(t, testSchema, schema)

	newSchema := &jsonschema.Schema{Type: "object"}
	result = dp.DefineSchema("Person", newSchema)
	assert.Equal(t, newSchema, result)

	schema, exists = dp.LookupSchema("Person")
	assert.True(t, exists)
	assert.Equal(t, newSchema, schema)

	assert.Panics(t, func() { dp.DefineSchema("", testSchema) })
	assert.Panics(t, func() { dp.DefineSchema("Test", nil) })
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
	assert.Equal(t, testSchema, schema)

	schema = dp.LookupSchemaFromAnySource("NonExistentSchema")
	assert.Nil(t, schema)
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
	assert.NoError(t, err)
	inputSection := metadata["input"].(map[string]any)
	assert.Equal(t, testSchema, inputSection["schema"])

	metadata = map[string]any{
		"output": map[string]any{
			"schema": "TestSchema",
		},
	}
	err = dp.ResolveSchemaReferences(metadata)
	assert.NoError(t, err)
	outputSection := metadata["output"].(map[string]any)
	assert.Equal(t, testSchema, outputSection["schema"])

	metadata = map[string]any{
		"input": map[string]any{
			"schema": "NonExistentSchema",
		},
	}
	err = dp.ResolveSchemaReferences(metadata)
	assert.Error(t, err)
}
