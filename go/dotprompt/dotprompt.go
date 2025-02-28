// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"errors"
	"fmt"
	"reflect"

	"github.com/aymerick/raymond"
)

// PartialResolver is a function to resolve partial names to their content.
type PartialResolver func(partialName string) (string, error)

// DotpromptOptions defines the options for the Dotprompt instance.
type DotpromptOptions struct {
	DefaultModel    string
	ModelConfigs    map[string]interface{}
	Helpers         map[string]interface{}
	Partials        map[string]string
	Tools           map[string]ToolDefinition
	ToolResolver    ToolResolver
	Schemas         map[string]JSONSchema
	SchemaResolver  SchemaResolver
	PartialResolver PartialResolver
}

// Dotprompt is the main struct for the Dotprompt instance.
type Dotprompt struct {
	knownHelpers    map[string]bool
	defaultModel    string
	modelConfigs    map[string]interface{}
	tools           map[string]ToolDefinition
	toolResolver    ToolResolver
	schemas         map[string]JSONSchema
	schemaResolver  SchemaResolver
	partialResolver PartialResolver
}

// NewDotprompt creates a new Dotprompt instance with the given options.
func NewDotprompt(options *DotpromptOptions) *Dotprompt {
	dp := &Dotprompt{
		knownHelpers: make(map[string]bool),
	}
	if options != nil {
		dp = &Dotprompt{
			knownHelpers:    make(map[string]bool),
			modelConfigs:    options.ModelConfigs,
			defaultModel:    options.DefaultModel,
			tools:           options.Tools,
			toolResolver:    options.ToolResolver,
			schemas:         options.Schemas,
			schemaResolver:  options.SchemaResolver,
			partialResolver: options.PartialResolver,
		}
	}

	return dp
}

// DefineHelper registers a helper function.
func (dp *Dotprompt) defineHelper(name string, helper interface{}, tpl *raymond.Template) {
	if dp.knownHelpers[name] {
		return
	}
	tpl.RegisterHelper(name, helper)
	dp.knownHelpers[name] = true
}

// DefinePartial registers a partial template.
// func (dp *Dotprompt) definePartial(name string, source string, tpl *raymond.Template) {
// 	tpl.RegisterPartial(name, source)
// }

// TODO: Add register helpers
func (dp *Dotprompt) RegisterHelpers(options *DotpromptOptions, tpl *raymond.Template) {
	if options != nil && options.Helpers != nil {
		for key, helper := range options.Helpers {
			dp.defineHelper(key, helper, tpl)
		}
	}
	for name, helper := range templateHelpers {
		dp.defineHelper(name, helper, tpl)
	}
}

// func (dp *Dotprompt) RegisterPartials(options *DotpromptOptions, tpl *raymond.Template, template string) error {
// 	if options.Partials != nil {
// 		for key, partial := range options.Partials {
// 			dp.definePartial(key, partial, tpl)
// 		}
// 	}
// 	err := dp.resolvePartials(template, tpl)
// 	if err != nil {
// 		return err
// 	}
// 	return nil
// }

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
func (dp *Dotprompt) Render(source string, data *DataArgument, options *PromptMetadata, dotpromptOptions *DotpromptOptions) (RenderedPrompt, error) {
	renderer, err := dp.Compile(source, options, dotpromptOptions)
	if err != nil {
		return RenderedPrompt{}, err
	}
	return renderer(data, options)
}

// Compile compiles the source string into a PromptFunction.
func (dp *Dotprompt) Compile(source string, additionalMetadata *PromptMetadata, dotpromptOptions *DotpromptOptions) (PromptFunction, error) {
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

	// RegisterHelpers()
	dp.RegisterHelpers(dotpromptOptions, renderTpl)
	// err = dp.RegisterPartials(dotpromptOptions, renderTpl, parsedPrompt.Template)
	if err != nil {
		return nil, err
	}

	renderFunc := func(data *DataArgument, options *PromptMetadata) (RenderedPrompt, error) {
		mergedMetadata, err := dp.RenderMetadata(parsedPrompt, options)
		if err != nil {
			return RenderedPrompt{}, err
		}

		inputContext := MergeMaps(data.Input, data.Context)
		renderedString, err := renderTpl.Exec(inputContext)

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
// func (d *Dotprompt) identifyPartials(template string) []string {
// 	// Simplified partial identification logic
// 	var partials []string
// 	lines := strings.Split(template, "\n")
// 	for _, line := range lines {
// 		// if strings.Contains(line, "{{>") {
// 		// 	str1 := strings.TrimSuffix(line, "}}")
// 		// 	str2 := strings.TrimPrefix(str1, "{{>")
// 		// 	partialName := strings.TrimSpace(str2)
// 		// 	partials = append(partials, partialName)
// 		// }
// 		re := regexp.MustCompile(`{{>\s*([^}]+)\s*}}`)
// 		// Find all matches in the template
// 		matches := re.FindAllStringSubmatch(line, -1)

// 		for _, match := range matches {
// 			if len(match) > 1 {
// 				partialName := strings.TrimSpace(match[1])
// 				partials = append(partials, partialName)
// 			}
// 		}
// 	}
// 	return partials
// }

// TODO: Add functionality to resolve partials
// resolvePartials resolves and registers partials in the template.
// func (dp *Dotprompt) resolvePartials(template string, tpl *raymond.Template) error {
// 	if dp.partialResolver == nil {
// 		return nil
// 	}

// 	// partials := dp.identifyPartials(template)
// 	// for _, partial := range partials {

// 	// 	_, err := dp.partialResolver(partial)
// 	// 	if err != nil {
// 	// 		return err
// 	// 	}
// 	// 	tpl.RegisterPartialTemplate()
// 	// 	// if _, exists := raymond.Partials[partial]; !exists {
// 	// 	// 	content, err := dp.partialResolver(partial)
// 	// 	// 	if err != nil {
// 	// 	// 		return err
// 	// 	// 	}
// 	// 	// 	if content != "" {
// 	// 	// 		dp.definePartial(partial, content)
// 	// 	// 		err = dp.resolvePartials(content)
// 	// 	// 		if err != nil {
// 	// 	// 			return err
// 	// 	// 		}
// 	// 	// 	}
// 	// 	// }
// 	// }
// 	return nil
// }

// mergeMetadata merges additional metadata into the parsed prompt.
func mergeMetadata(parsedPrompt ParsedPrompt, additionalMetadata *PromptMetadata) ParsedPrompt {
	if additionalMetadata != nil {
		if additionalMetadata.Model != "" {
			parsedPrompt.PromptMetadata.Model = additionalMetadata.Model
		}
		if additionalMetadata.Config != nil {
			parsedPrompt.PromptMetadata.Config = additionalMetadata.Config
		}
	}
	return parsedPrompt
}

// RenderMetadata renders the metadata for the prompt.
func (dp *Dotprompt) RenderMetadata(source interface{}, additionalMetadata *PromptMetadata) (PromptMetadata, error) {
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
		selectedModel = parsedSource.PromptMetadata.Model
	}
	if selectedModel == "" {
		selectedModel = dp.defaultModel
	}

	modelConfig, ok := dp.modelConfigs[selectedModel].(map[string]interface{})
	if !ok {
		modelConfig = make(map[string]interface{})
	}
	metadata := []*PromptMetadata{}
	metadata = append(metadata, &parsedSource.PromptMetadata)
	metadata = append(metadata, additionalMetadata)

	return dp.ResolveMetadata(PromptMetadata{Config: modelConfig}, metadata)
}

// Assuming out and merges[i] are of type PromptMetadata
func mergeStructs(out, merge PromptMetadata) PromptMetadata {
	outVal := reflect.ValueOf(&out).Elem()
	mergeVal := reflect.ValueOf(merge)

	for i := 0; i < mergeVal.NumField(); i++ {
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
		// config := out.Config
		// if config == nil {
		// 	config = make(map[string]any)
		// }
		out = mergeStructs(out, *merge)

		for key, value := range merge.Config {
			out.Config[key] = value
		}
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
			SchemaResolver: func(name string) (JSONSchema, error) {
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
			SchemaResolver: func(name string) (JSONSchema, error) {
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

// WrappedSchemaResolver resolves schemas.
func (dp *Dotprompt) WrappedSchemaResolver(name string) (JSONSchema, error) {
	if schema, exists := dp.schemas[name]; exists {
		return schema, nil
	}
	if dp.schemaResolver != nil {
		return dp.schemaResolver(name)
	}
	return nil, nil
}
