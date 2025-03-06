// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"fmt"
	"slices"
	"sort"
	"strings"
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
func Picoschema(schema any, options *PicoschemaOptions) (JSONSchema, error) {
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
func (p *PicoschemaParser) mustResolveSchema(schemaName string) (JSONSchema, error) {
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
func (p *PicoschemaParser) Parse(schema any) (JSONSchema, error) {
	if schema == nil {
		return nil, nil
	}

	// Allow for top-level named schemas
	if schemaStr, ok := schema.(string); ok {
		typeDesc := extractDescription(schemaStr)
		if slices.Contains(JSONSchemaScalarTypes, typeDesc[0]) {
			out := JSONSchema{"type": typeDesc[0]}
			if typeDesc[1] != "" {
				out["description"] = typeDesc[1]
			}
			return out, nil
		}
		resolvedSchema, err := p.mustResolveSchema(typeDesc[0])
		if err != nil {
			return nil, err
		}
		if typeDesc[1] != "" {
			resolvedSchema["description"] = typeDesc[1]
		}
		return resolvedSchema, nil
	}

	// if there's a JSON schema-ish type at the top level, treat as JSON schema
	if schemaMap, ok := schema.(map[string]any); ok {
		if schemaType, ok := schemaMap["type"].(string); ok {
			if slices.Contains(append(JSONSchemaScalarTypes, "object", "array"), schemaType) {
				return schemaMap, nil
			}
		}

		if _, ok := schemaMap["properties"].(map[string]any); ok {
			schemaMap["type"] = "object"
			return schemaMap, nil
		}
	}

	return p.parsePico(schema)
}

// parsePico parses a Pico schema and returns a JSON schema.
// The function ensures that the input schema is correctly
// parsed and converted into a JSON schema, handling various
// types and optional properties appropriately.
func (p *PicoschemaParser) parsePico(obj any, path ...string) (JSONSchema, error) {
	// Handle the case where the object is a string
	if objStr, ok := obj.(string); ok {
		typeDesc := extractDescription(objStr)
		// If the type is not a scalar type, resolve it using the SchemaResolver
		if !slices.Contains(JSONSchemaScalarTypes, typeDesc[0]) {
			resolvedSchema, err := p.mustResolveSchema(typeDesc[0])
			if err != nil {
				return nil, err
			}
			if typeDesc[1] != "" {
				resolvedSchema["description"] = typeDesc[1]
			}
			return resolvedSchema, nil
		}

		// Handle the special case for "any" type
		if typeDesc[0] == "any" {
			if typeDesc[1] != "" {
				return JSONSchema{"description": typeDesc[1]}, nil
			}
			return JSONSchema{}, nil
		}

		// Return a JSON schema with type and optional description
		if typeDesc[1] != "" {
			return JSONSchema{"type": typeDesc[0], "description": typeDesc[1]}, nil
		}
		return JSONSchema{"type": typeDesc[0]}, nil
	} else if _, ok := obj.(map[string]any); !ok {
		return nil, fmt.Errorf("Picoschema: only consists of objects and strings. Got: %v", obj)
	}

	// Initialize the schema as an object with properties and required fields
	schema := JSONSchema{
		"type":                 "object",
		"properties":           map[string]any{},
		"required":             []string{},
		"additionalProperties": false,
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
			parsedCopy := createDeepCopy(parsedValue)
			schema["additionalProperties"] = parsedCopy
			continue
		}

		// Split the key into name and type description
		nameType := strings.SplitN(key, "(", 2)
		name := nameType[0]
		isOptional := strings.HasSuffix(name, "?")
		propertyName := strings.TrimSuffix(name, "?")

		// Add the property to the required list if it is not optional
		if !isOptional {
			schema["required"] = append(schema["required"].([]string), propertyName)
		}

		// Handle properties without type description
		if len(nameType) == 1 {
			prop, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			propCopy := createDeepCopy(prop)
			if isOptional {
				if propType, ok := prop["type"].(string); ok {
					propCopy["type"] = []any{propType, "null"}
				}
			}
			schema["properties"].(map[string]any)[propertyName] = propCopy
			continue
		}

		// Handle properties with type description
		typeDesc := extractDescription(strings.TrimSuffix(nameType[1], ")"))
		newProp := JSONSchema{}
		switch typeDesc[0] {
		case "array":
			items, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			newProp["items"] = items
			if isOptional {
				newProp["type"] = []any{"array", "null"}
			} else {
				newProp["type"] = "array"
			}
		case "object":
			prop, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			propCopy := createDeepCopy(prop)
			if isOptional {
				propCopy["type"] = []any{prop["type"], "null"}
			}
			newProp = propCopy
		case "enum":
			enumValues := value.([]any)
			if isOptional && !containsInterface(enumValues, nil) {
				enumValues = append(enumValues, nil)
			}
			newProp["enum"] = enumValues
		default:
			return nil, fmt.Errorf("Picoschema: parenthetical types must be 'object' or 'array', got: %s", typeDesc[0])
		}
		if typeDesc[1] != "" {
			newProp["description"] = typeDesc[1]
		}
		schema["properties"].(map[string]any)[propertyName] = newProp
	}

	// Sort the required properties and remove the required field if it is empty
	if len(schema["required"].([]string)) == 0 {
		delete(schema, "required")
	} else {
		sort.Strings(schema["required"].([]string))
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

// containsInterface checks if a slice contains a specific item.
func containsInterface(slice []any, item any) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
