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
	"errors"
	"fmt"
	"reflect"
	"regexp"
	"strings"

	"maps"

	"github.com/invopop/jsonschema"
	"github.com/mbleigh/raymond"
)

// PartialResolver is a function to resolve partial names to their content.
type PartialResolver func(partialName string) (string, error)

// DotpromptOptions defines the options for the Dotprompt instance.
type DotpromptOptions struct {
	DefaultModel    string
	ModelConfigs    map[string]any
	Helpers         map[string]any
	Partials        map[string]string
	Tools           map[string]ToolDefinition
	ToolResolver    ToolResolver
	Schemas         map[string]*jsonschema.Schema
	SchemaResolver  SchemaResolver
	PartialResolver PartialResolver
}

// Dotprompt is the main struct for the Dotprompt instance.
type Dotprompt struct {
	knownHelpers          map[string]bool
	defaultModel          string
	modelConfigs          map[string]any
	tools                 map[string]ToolDefinition
	toolResolver          ToolResolver
	schemaResolver        SchemaResolver
	partialResolver       PartialResolver
	knownPartials         map[string]bool
	Template              *raymond.Template
	Helpers               map[string]any
	Partials              map[string]string
	Schemas               map[string]*jsonschema.Schema
	ExternalSchemaLookups []func(string) any
}

// NewDotprompt creates a new Dotprompt instance with the given options.
func NewDotprompt(options *DotpromptOptions) *Dotprompt {
	// Always initialize maps
	dp := &Dotprompt{
		knownHelpers:          make(map[string]bool),
		knownPartials:         make(map[string]bool),
		ExternalSchemaLookups: make([]func(string) any, 0),
	}

	if options != nil {
		dp.modelConfigs = options.ModelConfigs
		dp.defaultModel = options.DefaultModel
		dp.tools = options.Tools
		dp.toolResolver = options.ToolResolver
		dp.Schemas = options.Schemas
		dp.schemaResolver = options.SchemaResolver
		dp.partialResolver = options.PartialResolver
		dp.Helpers = options.Helpers
		dp.Partials = options.Partials

		if dp.tools == nil {
			dp.tools = make(map[string]ToolDefinition)
		}
		if dp.Schemas == nil {
			dp.Schemas = make(map[string]*jsonschema.Schema)
		}
		if dp.Helpers == nil {
			dp.Helpers = make(map[string]any)
		}
		if dp.Partials == nil {
			dp.Partials = make(map[string]string)
		}
		if dp.modelConfigs == nil {
			dp.modelConfigs = make(map[string]any)
		}
	} else {
		// Ensure maps are initialized even if options are nil.
		dp.tools = make(map[string]ToolDefinition)
		dp.Schemas = make(map[string]*jsonschema.Schema)
		dp.Helpers = make(map[string]any)
		dp.Partials = make(map[string]string)
		dp.modelConfigs = make(map[string]any)
	}

	return dp
}

// DefineHelper registers a helper function.
func (dp *Dotprompt) DefineHelper(name string, helper any, tpl *raymond.Template) error {
	if dp.knownHelpers[name] {
		return fmt.Errorf("the helper is already registered: %s", name)
	}
	tpl.RegisterHelper(name, helper)
	dp.knownHelpers[name] = true
	return nil
}

// DefinePartial registers a partial template.
func (dp *Dotprompt) DefinePartial(name string, source string, tpl *raymond.Template) error {
	if dp.knownPartials[name] {
		return fmt.Errorf("the partial is already registered: %s", name)
	}
	tpl.RegisterPartial(name, source)
	dp.knownPartials[name] = true
	return nil
}

// TODO: Add register helpers
func (dp *Dotprompt) RegisterHelpers(tpl *raymond.Template) error {
	if dp.Helpers != nil {
		for key, helper := range dp.Helpers {
			if err := dp.DefineHelper(key, helper, tpl); err != nil {
				return err
			}
		}
	}
	for name, helper := range templateHelpers {
		if !dp.knownHelpers[name] {
			if err := dp.DefineHelper(name, helper, tpl); err != nil {
				return err
			}
		}
	}
	return nil
}

func (dp *Dotprompt) RegisterPartials(tpl *raymond.Template, template string) error {
	if dp.Partials != nil {
		for key, partial := range dp.Partials {
			if err := dp.DefinePartial(key, partial, tpl); err != nil {
				return err
			}
		}
	}
	if err := dp.resolvePartials(template, tpl); err != nil {
		return err
	}
	return nil
}

func (dp *Dotprompt) initializeTemplate(tpl *raymond.Template) {
	dp.Template = tpl
	dp.knownHelpers = make(map[string]bool)
	dp.knownPartials = make(map[string]bool)
}

// DefineTool registers a tool definition.
func (dp *Dotprompt) DefineTool(def ToolDefinition) *Dotprompt {
	dp.tools[def.Name] = def
	return dp
}

// Parse parses the source string into a ParsedPrompt.
func (dp *Dotprompt) Parse(source string) (ParsedPrompt, error) {
	return ParseDocument(source)
}

// Render renders the source string with the given data and options.
func (dp *Dotprompt) Render(source string, data *DataArgument, options *PromptMetadata) (RenderedPrompt, error) {
	renderer, err := dp.Compile(source, options)
	if err != nil {
		return RenderedPrompt{}, err
	}
	return renderer(data, options)
}

// Compile compiles the source string into a PromptFunction.
func (dp *Dotprompt) Compile(source string, additionalMetadata *PromptMetadata) (PromptFunction, error) {
	parsedPrompt, err := dp.Parse(source)
	if err != nil {
		return nil, err
	}
	if additionalMetadata != nil {
		parsedPrompt = mergeMetadata(parsedPrompt, additionalMetadata)
	}

	renderTpl, err := raymond.Parse(parsedPrompt.Template)
	if err != nil {
		return nil, err
	}
	dp.initializeTemplate(renderTpl)

	// RegisterHelpers()
	if err = dp.RegisterHelpers(dp.Template); err != nil {
		return nil, err
	}
	if err = dp.RegisterPartials(dp.Template, parsedPrompt.Template); err != nil {
		return nil, err
	}

	renderFunc := func(data *DataArgument, options *PromptMetadata) (RenderedPrompt, error) {
		mergedMetadata, err := dp.RenderMetadata(parsedPrompt, options)
		if err != nil {
			return RenderedPrompt{}, err
		}

		var inputContext map[string]any
		defaultInput := make(map[string]any)
		if mergedMetadata.Input.Default != nil {
			maps.Copy(defaultInput, mergedMetadata.Input.Default)
		}
		inputContext = MergeMaps(defaultInput, data.Input)
		privDF := raymond.NewDataFrame()
		for k, v := range data.Context {
			privDF.Set(k, v)
		}

		renderedString, err := dp.Template.ExecWith(inputContext, privDF, &raymond.ExecOptions{
			NoEscape: true,
		})

		if err != nil {
			return RenderedPrompt{}, err
		}

		messages, err := ToMessages(renderedString, data)
		if err != nil {
			return RenderedPrompt{}, err
		}
		return RenderedPrompt{
			PromptMetadata: mergedMetadata,
			Messages:       messages,
		}, nil
	}

	return renderFunc, nil
}

// IdentifyPartials identifies partials in the template.
func (d *Dotprompt) identifyPartials(template string) []string {
	// Simplified partial identification logic
	var partials []string
	lines := strings.Split(template, "\n")
	for _, line := range lines {
		re := regexp.MustCompile(`{{>\s*([^}]+)\s*}}`)
		// Find all matches in the template
		matches := re.FindAllStringSubmatch(line, -1)

		for _, match := range matches {
			if len(match) > 1 {
				partialName := strings.TrimSpace(match[1])
				partials = append(partials, partialName)
			}
		}
	}
	return partials
}

// resolvePartials resolves and registers partials in the template.
func (dp *Dotprompt) resolvePartials(template string, tpl *raymond.Template) error {
	if dp.partialResolver == nil {
		return nil
	}

	partials := dp.identifyPartials(template)
	for _, partial := range partials {
		if _, exists := dp.knownPartials[partial]; !exists {
			content, err := dp.partialResolver(partial)
			if err != nil {
				return err
			}
			if content != "" {
				if err = dp.DefinePartial(partial, content, tpl); err != nil {
					return err
				}
				err = dp.resolvePartials(content, tpl)
				if err != nil {
					return err
				}
			}
		}
	}
	return nil
}

// mergeMetadata merges additional metadata into the parsed prompt.
func mergeMetadata(parsedPrompt ParsedPrompt, additionalMetadata *PromptMetadata) ParsedPrompt {
	if additionalMetadata != nil {
		if additionalMetadata.Model != "" {
			parsedPrompt.Model = additionalMetadata.Model
		}
		if additionalMetadata.Config != nil {
			parsedPrompt.Config = additionalMetadata.Config
		}
	}
	return parsedPrompt
}

// RenderMetadata renders the metadata for the prompt.
func (dp *Dotprompt) RenderMetadata(source any, additionalMetadata *PromptMetadata) (PromptMetadata, error) {
	var parsedSource ParsedPrompt
	var err error
	switch v := source.(type) {
	case string:
		parsedSource, err = dp.Parse(v)
		if err != nil {
			return PromptMetadata{}, err
		}
	case ParsedPrompt:
		parsedSource = v
	default:
		return PromptMetadata{}, errors.New("invalid source type")
	}

	if additionalMetadata == nil {
		additionalMetadata = &PromptMetadata{}
	}
	selectedModel := additionalMetadata.Model
	if selectedModel == "" {
		selectedModel = parsedSource.Model
	}
	if selectedModel == "" {
		selectedModel = dp.defaultModel
	}

	modelConfig, ok := dp.modelConfigs[selectedModel].(map[string]any)
	if !ok {
		modelConfig = make(map[string]any)
	}
	metadata := []*PromptMetadata{}
	metadata = append(metadata, &parsedSource.PromptMetadata)
	metadata = append(metadata, additionalMetadata)

	return dp.ResolveMetadata(PromptMetadata{Config: modelConfig}, metadata)
}

// mergeStructs merges two structures of type PromptMetadata
func mergeStructs(out, merge PromptMetadata) PromptMetadata {
	outVal := reflect.ValueOf(&out).Elem()
	mergeVal := reflect.ValueOf(merge)

	for i := range mergeVal.NumField() {
		field := mergeVal.Type().Field(i)
		value := mergeVal.Field(i)

		if !value.IsZero() {
			outVal.FieldByName(field.Name).Set(value)
		}
	}

	return out
}

// ResolveMetadata resolves and merges metadata.
func (dp *Dotprompt) ResolveMetadata(base PromptMetadata, merges []*PromptMetadata) (PromptMetadata, error) {
	out := base
	for _, merge := range merges {
		if merge == nil {
			continue
		}
		out = mergeStructs(out, *merge)

		maps.Copy(out.Config, merge.Config)
	}
	out, err := dp.ResolveTools(out)
	if err != nil {
		return PromptMetadata{}, err
	}
	return dp.RenderPicoschema(out)
}

// ResolveTools resolves tools in the metadata.
func (dp *Dotprompt) ResolveTools(base PromptMetadata) (PromptMetadata, error) {
	out := base
	if out.Tools != nil {
		var outTools []string
		if out.ToolDefs == nil {
			out.ToolDefs = make([]ToolDefinition, 0)
		}

		for _, toolName := range out.Tools {
			if tool, exists := dp.tools[toolName]; exists {
				out.ToolDefs = append(out.ToolDefs, tool)
			} else if dp.toolResolver != nil {
				resolvedTool, err := dp.toolResolver(toolName)
				if err != nil {
					return PromptMetadata{}, err
				}
				if reflect.DeepEqual(resolvedTool, ToolDefinition{}) {
					return PromptMetadata{}, fmt.Errorf("Dotprompt: Unable to resolve tool '%s' to a recognized tool definition", toolName)
				}
				out.ToolDefs = append(out.ToolDefs, resolvedTool)
			} else {
				outTools = append(outTools, toolName)
			}
		}

		out.Tools = outTools
	}
	return out, nil
}

// RenderPicoschema renders the picoschema for the metadata.
func (dp *Dotprompt) RenderPicoschema(meta PromptMetadata) (PromptMetadata, error) {
	if meta.Output.Schema == nil && meta.Input.Schema == nil {
		return meta, nil
	}

	newMeta := meta
	if meta.Input.Schema != nil {
		schema, err := Picoschema(meta.Input.Schema, &PicoschemaOptions{
			SchemaResolver: func(name string) (*jsonschema.Schema, error) {
				return dp.WrappedSchemaResolver(name)
			},
		})
		if err != nil {
			return PromptMetadata{}, err
		}
		newMeta.Input.Schema = Schema(schema)
	}
	if meta.Output.Schema != nil {
		schema, err := Picoschema(meta.Output.Schema, &PicoschemaOptions{
			SchemaResolver: func(name string) (*jsonschema.Schema, error) {
				return dp.WrappedSchemaResolver(name)
			},
		})
		if err != nil {
			return PromptMetadata{}, err
		}
		newMeta.Output.Schema = Schema(schema)
	}
	return newMeta, nil
}

// WrappedSchemaResolver resolves Schema.
func (dp *Dotprompt) WrappedSchemaResolver(name string) (*jsonschema.Schema, error) {
	if schema, exists := dp.Schemas[name]; exists {
		return schema, nil
	}
	if dp.schemaResolver != nil {
		return dp.schemaResolver(name)
	}
	return nil, nil
}
