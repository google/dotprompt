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
	"slices"
	"sort"
	"strings"

	"github.com/invopop/jsonschema"
	orderedmap "github.com/wk8/go-ordered-map/v2"
)

// JSONSchemaScalarTypes defines the scalar types allowed in JSON schema.
var JSONSchemaScalarTypes = []string{
	"string",
	"boolean",
	"null",
	"number",
	"integer",
	"any",
}

// WildcardPropertyName is the name used for wildcard properties.
const WildcardPropertyName = "(*)"

// PicoschemaOptions defines options for the Picoschema parser.
type PicoschemaOptions struct {
	SchemaResolver SchemaResolver
}

// Picoschema parses a schema with the given options.
func Picoschema(schema any, options *PicoschemaOptions) (*jsonschema.Schema, error) {
	parser := NewPicoschemaParser(options)
	return parser.Parse(schema)
}

// PicoschemaParser is a parser for Picoschema.
type PicoschemaParser struct {
	SchemaResolver SchemaResolver
}

// NewPicoschemaParser creates a new PicoschemaParser with the given options.
func NewPicoschemaParser(options *PicoschemaOptions) *PicoschemaParser {
	return &PicoschemaParser{
		SchemaResolver: options.SchemaResolver,
	}
}

// mustResolveSchema resolves a schema name to a JSON schema using the SchemaResolver.
func (p *PicoschemaParser) mustResolveSchema(schemaName string) (*jsonschema.Schema, error) {
	if p.SchemaResolver == nil {
		return nil, fmt.Errorf("Picoschema: unsupported scalar type '%s'", schemaName)
	}

	val, err := p.SchemaResolver(schemaName)
	if err != nil {
		return nil, err
	}
	if val == nil {
		return nil, fmt.Errorf("Picoschema: could not find schema with name '%s'", schemaName)
	}
	return val, nil
}

// Parse parses the given schema and returns a JSON schema.
func (p *PicoschemaParser) Parse(schema any) (*jsonschema.Schema, error) {
	if schema == nil {
		return nil, nil
	}

	// Allow for top-level named schemas
	if schemaStr, ok := schema.(string); ok {
		typeDesc := extractDescription(schemaStr)
		if slices.Contains(JSONSchemaScalarTypes, typeDesc[0]) {
			out := &jsonschema.Schema{Type: typeDesc[0]}
			if typeDesc[1] != "" {
				out.Description = typeDesc[1]
			}
			return out, nil
		}
		resolvedSchema, err := p.mustResolveSchema(typeDesc[0])
		if err != nil {
			return nil, err
		}
		resolvedSchemaCopy := createCopy(resolvedSchema)
		if typeDesc[1] != "" {
			resolvedSchemaCopy.Description = typeDesc[1]
		}
		return resolvedSchemaCopy, nil
	}

	// if there's a JSON schema-ish type at the top level, treat as JSON schema
	if schemaMap, ok := schema.(map[string]any); ok {
		schemaBytes, err := json.Marshal(schemaMap)
		if err != nil {
			return nil, err
		}
		schemaJSON := &jsonschema.Schema{}
		if err := json.Unmarshal(schemaBytes, schemaJSON); err != nil {
			return nil, err
		}

		// Validate that all fields in schemaMap are present in schemaJSON
		if err := ValidateSchemaFields(schemaMap, schemaJSON); err == nil {
			if schemaJSON.Type != "" {
				if slices.Contains(append(JSONSchemaScalarTypes, "object", "array"), schemaJSON.Type) {
					return schemaJSON, nil
				}
			}

			if schemaJSON.Properties != nil {
				schemaJSON.Type = "object"
				return schemaJSON, nil
			}
		}
	}

	return p.parsePico(schema)
}

// validateSchemaFields checks if all fields in schemaMap are present in schemaJSON
func ValidateSchemaFields(schemaMap map[string]any, schemaJSON *jsonschema.Schema) error {
	// Convert schemaJSON to a map for comparison
	schemaJSONMap := make(map[string]any)
	schemaBytes, err := json.Marshal(schemaJSON)
	if err != nil {
		return err
	}
	if err := json.Unmarshal(schemaBytes, &schemaJSONMap); err != nil {
		return err
	}

	// Check for unknown fields
	for key := range schemaMap {
		if _, ok := schemaJSONMap[key]; !ok {
			return fmt.Errorf("unknown field %s in schema", key)
		}
	}
	return nil
}

// parsePico parses a Pico schema and returns a JSON schema.
// The function ensures that the input schema is correctly
// parsed and converted into a JSON schema, handling various
// types and optional properties appropriately.
func (p *PicoschemaParser) parsePico(obj any, path ...string) (*jsonschema.Schema, error) {
	// Handle the case where the object is a string
	if objStr, ok := obj.(string); ok {
		typeDesc := extractDescription(objStr)
		// If the type is not a scalar type, resolve it using the SchemaResolver
		if !slices.Contains(JSONSchemaScalarTypes, typeDesc[0]) {
			resolvedSchema, err := p.mustResolveSchema(typeDesc[0])
			if err != nil {
				return nil, err
			}
			// Create a deep copy to prevent shared references.
			resolvedSchemaCopy := createCopy(resolvedSchema)
			if typeDesc[1] != "" {
				resolvedSchemaCopy.Description = typeDesc[1]
			}
			return resolvedSchemaCopy, nil
		}

		// Handle the special case for "any" type
		if typeDesc[0] == "any" {
			if typeDesc[1] != "" {
				return &jsonschema.Schema{Description: typeDesc[1]}, nil
			}
			return &jsonschema.Schema{}, nil
		}

		// Return a JSON schema with type and optional description
		if typeDesc[1] != "" {
			return &jsonschema.Schema{Type: typeDesc[0], Description: typeDesc[1]}, nil
		}
		return &jsonschema.Schema{Type: typeDesc[0]}, nil
	} else if _, ok := obj.(map[string]any); !ok {
		return nil, fmt.Errorf("Picoschema: only consists of objects and strings. Got: %v", obj)
	}

	// Initialize the schema as an object with properties and required fields
	schema := &jsonschema.Schema{
		Type:       "object",
		Properties: orderedmap.New[string, *jsonschema.Schema](),
		Required:   []string{},
	}

	// Handle wildcard properties
	objMap := obj.(map[string]any)
	for key, value := range objMap {
		// wildcard property
		if key == WildcardPropertyName {
			parsedValue, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			parsedCopy := createCopy(parsedValue)
			schema.AdditionalProperties = parsedCopy
			continue
		}

		// Split the key into name and type description
		nameType := strings.SplitN(key, "(", 2)
		name := nameType[0]
		isOptional := strings.HasSuffix(name, "?")
		propertyName := strings.TrimSuffix(name, "?")

		// Add the property to the required list if it is not optional
		if !isOptional {
			schema.Required = append(schema.Required, propertyName)
		}

		// Handle properties without type description
		if len(nameType) == 1 {
			prop, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			propCopy := createCopy(prop)
			updatedProp := createCopy(prop)
			if isOptional && propCopy.Type != "" {
				updatedProp.AnyOf = []*jsonschema.Schema{propCopy, {Type: "null"}}
			}
			schema.Properties.Set(propertyName, updatedProp)
			continue
		}

		// Handle properties with type description
		typeDesc := extractDescription(strings.TrimSuffix(nameType[1], ")"))
		newProp := &jsonschema.Schema{}
		switch typeDesc[0] {
		case "array":
			items, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			newProp.Items = items
			if isOptional {
				newProp.AnyOf = []*jsonschema.Schema{{Type: "array"}, {Type: "null"}}
			} else {
				newProp.Type = "array"
			}
		case "object":
			prop, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			propCopy := createCopy(prop)
			updatedProp := createCopy(prop)
			if isOptional {
				updatedProp.AnyOf = []*jsonschema.Schema{propCopy, {Type: "null"}}
			}
			newProp = updatedProp
		case "enum":
			enumValues := value.([]any)
			if isOptional && !slices.ContainsFunc(enumValues, func(s any) bool { return s == nil }) {
				enumValues = append(enumValues, nil)
			}
			newProp.Enum = enumValues
		default:
			return nil, fmt.Errorf("Picoschema: parenthetical types must be 'object' or 'array', got: %s", typeDesc[0])
		}
		if typeDesc[1] != "" {
			newProp.Description = typeDesc[1]
		}
		schema.Properties.Set(propertyName, newProp)
	}

	// Sort the required properties and remove the required field if it is empty
	if len(schema.Required) != 0 {
		sort.Strings(schema.Required)
	}
	return schema, nil
}

// extractDescription extracts the type and description from a string.
func extractDescription(input string) [2]string {
	if !strings.Contains(input, ",") {
		return [2]string{input, ""}
	}

	parts := strings.SplitN(input, ",", 2)
	return [2]string{strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1])}
}
