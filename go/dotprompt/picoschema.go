// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"fmt"
	"slices"
	"strings"
)

var JSONSchemaScalarTypes = []string{
	"string",
	"boolean",
	"null",
	"number",
	"integer",
	"any",
}

const WildcardPropertyName = "(*)"

type PicoschemaOptions struct {
	SchemaResolver SchemaResolver
}

func Picoschema(schema any, options *PicoschemaOptions) (JSONSchema, error) {
	parser := NewPicoschemaParser(options)
	return parser.Parse(schema)
}

type PicoschemaParser struct {
	SchemaResolver SchemaResolver
}

func NewPicoschemaParser(options *PicoschemaOptions) *PicoschemaParser {
	return &PicoschemaParser{
		SchemaResolver: options.SchemaResolver,
	}
}

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
		if slices.Contains(append(JSONSchemaScalarTypes, "object", "array"), schemaMap["type"].(string)) {
			return schemaMap, nil
		}
		if _, ok := schemaMap["properties"].(map[string]any); ok {
			schemaMap["type"] = "object"
			return schemaMap, nil
		}
	}

	return p.parsePico(schema)
}

func (p *PicoschemaParser) parsePico(obj any, path ...string) (JSONSchema, error) {
	if objStr, ok := obj.(string); ok {
		typeDesc := extractDescription(objStr)
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

		if typeDesc[0] == "any" {
			if typeDesc[1] != "" {
				return JSONSchema{"description": typeDesc[1]}, nil
			}
			return JSONSchema{}, nil
		}

		if typeDesc[1] != "" {
			return JSONSchema{"type": typeDesc[0], "description": typeDesc[1]}, nil
		}
		return JSONSchema{"type": typeDesc[0]}, nil
	} else if _, ok := obj.(map[string]any); !ok {
		return nil, fmt.Errorf("Picoschema: only consists of objects and strings. Got: %v", obj)
	}

	schema := JSONSchema{
		"type":                 "object",
		"properties":           map[string]any{},
		"required":             []string{},
		"additionalProperties": false,
	}

	objMap := obj.(map[string]any)
	for key, value := range objMap {
		// wildcard property
		if key == WildcardPropertyName {
			parsedValue, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			schema["additionalProperties"] = parsedValue
			continue
		}

		nameType := strings.SplitN(key, "(", 2)
		name := nameType[0]
		isOptional := strings.HasSuffix(name, "?")
		propertyName := strings.TrimSuffix(name, "?")

		if !isOptional {
			schema["required"] = append(schema["required"].([]string), propertyName)
		}

		if len(nameType) == 1 {
			prop, err := p.parsePico(value, append(path, key)...)
			if err != nil {
				return nil, err
			}
			if isOptional {
				prop["type"] = []any{prop["type"], "null"}
			}
			schema["properties"].(map[string]any)[propertyName] = prop
			continue
		}

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
			if isOptional {
				prop["type"] = []any{prop["type"], "null"}
			}
			newProp = prop
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

	if len(schema["required"].([]string)) == 0 {
		delete(schema, "required")
	}
	return schema, nil
}

func extractDescription(input string) [2]string {
	if !strings.Contains(input, ",") {
		return [2]string{input, ""}
	}

	parts := strings.SplitN(input, ",", 2)
	return [2]string{strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1])}
}

func containsInterface(slice []any, item any) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
