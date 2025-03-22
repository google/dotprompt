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
