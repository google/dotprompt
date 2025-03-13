// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	dp "github.com/google/dotprompt/go/dotprompt"
	"github.com/invopop/jsonschema"
)

// Expect represents the expected output of a test case.
type Expect struct {
	Config   map[string]any   `yaml:"config"`   // Configuration settings
	Ext      map[string]any   `yaml:"ext"`      // External data
	Input    map[string]any   `yaml:"input"`    // Input data
	Output   map[string]any   `yaml:"output"`   // Output data
	Messages []map[string]any `yaml:"messages"` // Messages
	Metadata map[string]any   `yaml:"metadata"` // Metadata
	Raw      map[string]any   `yaml:"raw"`      // Raw output
}

// SpecTest represents a single test case within a test suite.
type SpecTest struct {
	Desc    string          `yaml:"desc"`    // Description of the test case
	Data    dp.DataArgument `yaml:"data"`    // Data argument for the test case
	Expect  Expect          `yaml:"expect"`  // Expected output of the test case
	Options map[string]any  `yaml:"options"` // Additional options for the test case
}

// SpecSuite represents a suite of test cases.
type SpecSuite struct {
	Name             string                        `yaml:"name"`             // Name of the test suite
	Template         string                        `yaml:"template"`         // Template used in the test suite
	Data             dp.DataArgument               `yaml:"data"`             // Data argument for the test suite
	Schemas          map[string]*jsonschema.Schema `yaml:"schemas"`          // JSON schemas used in the test suite
	Tools            map[string]dp.ToolDefinition  `yaml:"tools"`            // Tool definitions used in the test suite
	Partials         map[string]string             `yaml:"partials"`         // Partials used in the test suite
	ResolverPartials map[string]string             `yaml:"resolverPartials"` // Resolver partials used in the test suite
	Tests            []SpecTest                    `yaml:"tests"`            // List of test cases in the test suite
}
