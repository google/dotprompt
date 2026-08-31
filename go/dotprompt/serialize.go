// Copyright 2026 Google LLC
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
	"errors"
	"maps"
	"reflect"
	"slices"
	"strings"

	"github.com/goccy/go-yaml"
	"github.com/invopop/jsonschema"
)

// MarshalText serializes the prompt into canonical .prompt text.
func (p ParsedPrompt) MarshalText() ([]byte, error) {
	frontmatter, err := p.frontmatter()
	if err != nil {
		return nil, err
	}
	if len(frontmatter) == 0 {
		return []byte(p.Template), nil
	}

	body, err := yaml.Marshal(frontmatter)
	if err != nil {
		return nil, err
	}
	return []byte("---\n" + string(body) + "---\n" + p.Template), nil
}

// UnmarshalText parses canonical or user-authored .prompt text into a ParsedPrompt.
func (p *ParsedPrompt) UnmarshalText(data []byte) error {
	if p == nil {
		return errors.New("dotprompt: cannot unmarshal into nil ParsedPrompt")
	}
	parsed, err := ParseDocument(string(data))
	if err != nil {
		return err
	}
	*p = parsed
	return nil
}

// String returns canonical .prompt text and should not be used when error handling matters.
//
// It is defined on *ParsedPrompt to avoid changing existing fmt.Stringer behavior
// for ParsedPrompt values.
func (p *ParsedPrompt) String() string {
	if p == nil {
		return ""
	}
	text, err := p.MarshalText()
	if err != nil {
		return ""
	}
	return string(text)
}

func (p ParsedPrompt) frontmatter() (yaml.MapSlice, error) {
	raw := maps.Clone(p.Raw)
	if raw == nil {
		raw = map[string]any{}
	}
	maps.DeleteFunc(raw, func(key string, _ any) bool {
		return slices.Contains(ReservedMetadataKeywords, key) || strings.Contains(key, ".")
	})

	ext := map[string]any{}
	for namespace, values := range p.Ext {
		for field, value := range values {
			ext[namespace+"."+field] = value
		}
	}

	items := yaml.MapSlice{}
	for _, field := range []sectionItem{
		itemValue("name", p.Name, p.Name != ""),
		itemValue("description", p.Description, p.Description != ""),
		itemValue("variant", p.Variant, p.Variant != ""),
		itemValue("version", p.Version, p.Version != ""),
		itemValue("model", p.Model, p.Model != ""),
		itemValue("maxTurns", p.MaxTurns, p.MaxTurns != 0),
		itemValue("config", p.Config, len(p.Config) > 0),
	} {
		if !field.ok {
			continue
		}
		var err error
		items, err = appendItem(items, field.key, field.value)
		if err != nil {
			return nil, err
		}
	}

	if input, err := metadataSection(
		itemValue("default", p.Input.Default, len(p.Input.Default) > 0),
		schemaItem("schema", p.Input.Schema),
	); err != nil {
		return nil, err
	} else if len(input) > 0 {
		items = append(items, yaml.MapItem{Key: "input", Value: input})
	}
	if output, err := metadataSection(
		itemValue("format", p.Output.Format, p.Output.Format != ""),
		schemaItem("schema", p.Output.Schema),
	); err != nil {
		return nil, err
	} else if len(output) > 0 {
		items = append(items, yaml.MapItem{Key: "output", Value: output})
	}
	if len(p.Tools) > 0 {
		var err error
		items, err = appendItem(items, "tools", p.Tools)
		if err != nil {
			return nil, err
		}
	}
	if len(p.ToolDefs) > 0 {
		toolDefs := make([]any, 0, len(p.ToolDefs))
		for _, toolDef := range p.ToolDefs {
			item, err := metadataSection(
				itemValue("name", toolDef.Name, true),
				itemValue("description", toolDef.Description, toolDef.Description != ""),
				schemaItem("inputSchema", toolDef.InputSchema),
				schemaItem("outputSchema", toolDef.OutputSchema),
			)
			if err != nil {
				return nil, err
			}
			toolDefs = append(toolDefs, item)
		}
		var err error
		items, err = appendItem(items, "toolDefs", toolDefs)
		if err != nil {
			return nil, err
		}
	}

	for _, key := range sortedKeys(raw) {
		var err error
		items, err = appendItem(items, key, raw[key])
		if err != nil {
			return nil, err
		}
	}
	for _, key := range sortedKeys(ext) {
		var err error
		items, err = appendItem(items, key, ext[key])
		if err != nil {
			return nil, err
		}
	}
	return items, nil
}

type sectionItem struct {
	key   string
	value any
	ok    bool
}

func itemValue(key string, value any, ok bool) sectionItem {
	return sectionItem{key: key, value: value, ok: ok}
}

func schemaItem(key string, value any) sectionItem {
	return itemValue(key, value, value != nil)
}

func metadataSection(parts ...sectionItem) (yaml.MapSlice, error) {
	items := yaml.MapSlice{}
	for _, part := range parts {
		if !part.ok {
			continue
		}
		var err error
		items, err = appendItem(items, part.key, part.value)
		if err != nil {
			return nil, err
		}
	}
	return items, nil
}

func appendItem(items yaml.MapSlice, key string, value any) (yaml.MapSlice, error) {
	ordered, err := orderedYAML(value)
	if err != nil {
		return nil, err
	}
	return append(items, yaml.MapItem{Key: key, Value: ordered}), nil
}

func orderedYAML(value any) (any, error) {
	switch value := value.(type) {
	case nil, string:
		return value, nil
	case *jsonschema.Schema:
		return jsonSchemaMap(value)
	case jsonschema.Schema:
		return jsonSchemaMap(&value)
	case yaml.MapSlice:
		out := make(yaml.MapSlice, 0, len(value))
		for _, item := range value {
			normalized, err := orderedYAML(item.Value)
			if err != nil {
				return nil, err
			}
			out = append(out, yaml.MapItem{Key: item.Key, Value: normalized})
		}
		return out, nil
	case map[string]any:
		out := make(yaml.MapSlice, 0, len(value))
		for _, key := range sortedKeys(value) {
			normalized, err := orderedYAML(value[key])
			if err != nil {
				return nil, err
			}
			out = append(out, yaml.MapItem{Key: key, Value: normalized})
		}
		return out, nil
	case []any:
		out := make([]any, 0, len(value))
		for _, item := range value {
			normalized, err := orderedYAML(item)
			if err != nil {
				return nil, err
			}
			out = append(out, normalized)
		}
		return out, nil
	}

	rv := reflect.ValueOf(value)
	switch rv.Kind() {
	case reflect.Map:
		if rv.Type().Key().Kind() != reflect.String {
			return value, nil
		}
		keys := make([]string, 0, rv.Len())
		for _, key := range rv.MapKeys() {
			keys = append(keys, key.String())
		}
		slices.Sort(keys)

		out := make(yaml.MapSlice, 0, len(keys))
		for _, key := range keys {
			normalized, err := orderedYAML(rv.MapIndex(reflect.ValueOf(key)).Interface())
			if err != nil {
				return nil, err
			}
			out = append(out, yaml.MapItem{Key: key, Value: normalized})
		}
		return out, nil
	case reflect.Slice, reflect.Array:
		out := make([]any, 0, rv.Len())
		for i := range rv.Len() {
			normalized, err := orderedYAML(rv.Index(i).Interface())
			if err != nil {
				return nil, err
			}
			out = append(out, normalized)
		}
		return out, nil
	default:
		return value, nil
	}
}

func sortedKeys[M ~map[string]V, V any](m M) []string {
	return slices.Sorted(maps.Keys(m))
}

func jsonSchemaMap(schema *jsonschema.Schema) (map[string]any, error) {
	data, err := json.Marshal(schema)
	if err != nil {
		return nil, err
	}
	out := map[string]any{}
	return out, json.Unmarshal(data, &out)
}
