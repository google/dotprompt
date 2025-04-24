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

// Package dotprompt provides functionality for working with executable prompt templates.
package dotprompt

import (
	"fmt"

	"github.com/invopop/jsonschema"
)

// DefineSchema registers a schema with the Dotprompt instance.
func (dp *Dotprompt) DefineSchema(name string, definition any) *jsonschema.Schema {
	if name == "" {
		panic("dotprompt.DefineSchema: schema name cannot be empty")
	}
	if definition == nil {
		panic("dotprompt.DefineSchema: schema definition cannot be nil")
	}

	var schema *jsonschema.Schema
	switch def := definition.(type) {
	case *jsonschema.Schema:
		schema = def
	default:
		reflector := jsonschema.Reflector{}
		schema = reflector.Reflect(definition)
	}

	if dp.Schemas == nil {
		dp.Schemas = make(map[string]*jsonschema.Schema)
	}

	dp.Schemas[name] = schema
	return schema
}

// LookupSchema retrieves a registered schema by name.
func (dp *Dotprompt) LookupSchema(name string) (*jsonschema.Schema, bool) {
	if dp.Schemas == nil {
		return nil, false
	}

	schema, exists := dp.Schemas[name]
	return schema, exists
}

// RegisterExternalSchemaLookup registers a function that can look up schemas
// from an external source.
func (dp *Dotprompt) RegisterExternalSchemaLookup(lookup func(string) any) {
	if dp.ExternalSchemaLookups == nil {
		dp.ExternalSchemaLookups = make([]func(string) any, 0)
	}

	dp.ExternalSchemaLookups = append(dp.ExternalSchemaLookups, lookup)
}

// LookupSchemaFromAnySource tries to find a schema by name from either the local
// registry or any registered external sources.
func (dp *Dotprompt) LookupSchemaFromAnySource(name string) any {
	if schema, exists := dp.LookupSchema(name); exists {
		return schema
	}

	for _, lookup := range dp.ExternalSchemaLookups {
		if schema := lookup(name); schema != nil {
			if dp.Schemas == nil {
				dp.Schemas = make(map[string]*jsonschema.Schema)
			}

			jsSchema, ok := schema.(*jsonschema.Schema)
			if !ok {
				reflector := jsonschema.Reflector{}
				jsSchema = reflector.Reflect(schema)
			}

			dp.Schemas[name] = jsSchema
			return jsSchema
		}
	}

	return nil
}

// ResolveSchemaReferences resolves any schema references in the metadata
// by looking them up in the schema registry.
func (dp *Dotprompt) ResolveSchemaReferences(metadata map[string]any) error {
	if inputSection, ok := metadata["input"].(map[string]any); ok {
		if schemaName, ok := inputSection["schema"].(string); ok && schemaName != "" {
			schema := dp.LookupSchemaFromAnySource(schemaName)
			if schema == nil {
				return fmt.Errorf("dotprompt: input schema '%s' not found", schemaName)
			}

			inputSection["schema"] = schema
		}
	}

	if outputSection, ok := metadata["output"].(map[string]any); ok {
		if schemaName, ok := outputSection["schema"].(string); ok && schemaName != "" {
			schema := dp.LookupSchemaFromAnySource(schemaName)
			if schema == nil {
				return fmt.Errorf("dotprompt: output schema '%s' not found", schemaName)
			}

			outputSection["schema"] = schema
		}
	}

	return nil
}

// DumpDotpromptSchemas prints all schemas stored in Dotprompt
func (dp *Dotprompt) DumpDotpromptSchemas() {
	fmt.Println("=== Dotprompt Schemas ===")

	if dp.Schemas != nil {
		fmt.Printf("Schemas count: %d\n", len(dp.Schemas))
		for name := range dp.Schemas {
			fmt.Printf("Schema: %s\n", name)
		}
	} else {
		fmt.Println("No schemas defined")
	}

	fmt.Printf("External schema lookups: %d\n", len(dp.ExternalSchemaLookups))
	fmt.Println("=========================")
}
