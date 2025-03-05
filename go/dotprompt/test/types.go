// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	dp "github.com/google/dotprompt/go/dotprompt"
)

type Expect struct {
	Config   map[string]any   `yaml:"config"`
	Ext      map[string]any   `yaml:"ext"`
	Input    map[string]any   `yaml:"input"`
	Output   map[string]any   `yaml:"output"`
	Messages []map[string]any `yaml:"messages"`
	Metadata map[string]any   `yaml:"metadata"`
	Raw      map[string]any   `yaml:"raw"`
}

type SpecTest struct {
	Desc    string          `yaml:"desc"`
	Data    dp.DataArgument `yaml:"data"`
	Expect  Expect          `yaml:"expect"`
	Options map[string]any  `yaml:"options"`
}

type SpecSuite struct {
	Name             string                       `yaml:"name"`
	Template         string                       `yaml:"template"`
	Data             dp.DataArgument              `yaml:"data"`
	Schemas          map[string]dp.JSONSchema     `yaml:"schemas"`
	Tools            map[string]dp.ToolDefinition `yaml:"tools"`
	Partials         map[string]string            `yaml:"partials"`
	ResolverPartials map[string]string            `yaml:"resolverPartials"`
	Tests            []SpecTest                   `yaml:"tests"`
}
