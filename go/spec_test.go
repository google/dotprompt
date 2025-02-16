// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

package dotprompt

import (
	"os"
	"path/filepath"
	"testing"

	"gopkg.in/yaml.v3"
)

// SpecSuite represents a test suite from the YAML specification
type SpecSuite struct {
	Name             string                    `yaml:"name"`
	Template         string                    `yaml:"template"`
	Data             map[string]interface{}    `yaml:"data,omitempty"`
	Schemas          map[string]JSONSchema     `yaml:"schemas,omitempty"`
	Tools            map[string]ToolDefinition `yaml:"tools,omitempty"`
	Partials         map[string]string         `yaml:"partials,omitempty"`
	ResolverPartials map[string]string         `yaml:"resolverPartials,omitempty"`
	Tests            []TestCase                `yaml:"tests"`
}

// TestCase represents an individual test within a suite
type TestCase struct {
	Description string                 `yaml:"desc,omitempty"`
	Data        map[string]interface{} `yaml:"data"`
	Expected    ExpectedResult         `yaml:"expect"`
	Options     map[string]interface{} `yaml:"options"`
}

// ExpectedResult represents the expected output of a test
type ExpectedResult struct {
	Raw      string                 `yaml:"raw,omitempty"`
	Ext      map[string]interface{} `yaml:"ext,omitempty"`
	Config   map[string]interface{} `yaml:"config,omitempty"`
	Metadata map[string]interface{} `yaml:"metadata,omitempty"`
	Messages []interface{}          `yaml:"messages,omitempty"`
}

// loadTestSuites reads and parses YAML test files from the spec directory
func loadTestSuites(t *testing.T, specDir string) []SpecSuite {
	files, err := os.ReadDir(specDir)
	if err != nil {
		t.Fatalf("failed to read spec directory: %v", err)
	}

	var allSuites []SpecSuite
	for _, file := range files {
		if file.IsDir() || filepath.Ext(file.Name()) != ".yaml" {
			continue
		}

		path := filepath.Join(specDir, file.Name())
		content, err := os.ReadFile(path)
		if err != nil {
			t.Fatalf("failed to read file %s: %v", path, err)
		}

		var suites []SpecSuite
		if err := yaml.Unmarshal(content, &suites); err != nil {
			t.Fatalf("failed to parse YAML from %s: %v", path, err)
		}

		allSuites = append(allSuites, suites...)
	}

	return allSuites
}

func TestDotprompt(t *testing.T) {
	suites := loadTestSuites(t, "../spec")

	for _, suite := range suites {
		// Create a suite-level scope for the suite name
		suite := suite
		t.Run(suite.Name, func(t *testing.T) {
			// Run tests in parallel at the suite level
			t.Parallel()

			for _, tc := range suite.Tests {
				// Create a test-level scope for the test case
				tc := tc
				testName := tc.Description
				if testName == "" {
					testName = "should match expected output"
				}

				t.Run(testName, func(t *testing.T) {
					// Run individual tests in parallel
					t.Parallel()

					env := NewDotprompt(&DotpromptOptions{
						Schemas: suite.Schemas,
						Tools:   suite.Tools,
						PartialResolver: func(name string) string {
							if suite.ResolverPartials != nil {
								if partial, ok := suite.ResolverPartials[name]; ok {
									return partial
								}
							}
							return ""
						},
					})

					// Register any partials defined in the suite
					if suite.Partials != nil {
						for name, template := range suite.Partials {
							env.DefinePartial(name, template)
						}
					}

					// Merge suite-level data with test-case data
					data := make(map[string]interface{})
					for k, v := range suite.Data {
						data[k] = v
					}
					for k, v := range tc.Data {
						data[k] = v
					}

					// Test the render function
					result, err := env.Render(suite.Template, data, tc.Options)
					if err != nil {
						t.Fatalf("render failed: %v", err)
					}

					// Compare results excluding raw field
					compareResults(t, result, tc.Expected)

					// Only compare raw if it's specified in the expected results
					if tc.Expected.Raw != "" {
						if result.Raw != tc.Expected.Raw {
							t.Errorf("raw output mismatch\ngot: %v\nwant: %v",
								result.Raw, tc.Expected.Raw)
						}
					}

					// Test the renderMetadata function
					metadataResult, err := env.RenderMetadata(suite.Template, tc.Options)
					if err != nil {
						t.Fatalf("renderMetadata failed: %v", err)
					}

					// Compare metadata results
					compareMetadataResults(t, metadataResult, tc.Expected)
				})
			}
		})
	}
}

func compareResults(t *testing.T, got, want ExpectedResult) {
	// Initialize empty maps if they're nil
	if got.Ext == nil {
		got.Ext = make(map[string]interface{})
	}
	if got.Config == nil {
		got.Config = make(map[string]interface{})
	}
	if got.Metadata == nil {
		got.Metadata = make(map[string]interface{})
	}

	// Compare each field
	compareMap(t, "ext", got.Ext, want.Ext)
	compareMap(t, "config", got.Config, want.Config)
	compareMap(t, "metadata", got.Metadata, want.Metadata)
}

func compareMetadataResults(t *testing.T, got, want ExpectedResult) {
	// Skip messages comparison for metadata results
	compareResults(t, got, want)
}

func compareMap(t *testing.T, field string, got, want map[string]interface{}) {
	if len(got) != len(want) {
		t.Errorf("%s field length mismatch: got %d, want %d", field, len(got), len(want))
		return
	}

	for k, wantV := range want {
		gotV, exists := got[k]
		if !exists {
			t.Errorf("%s field missing key %q", field, k)
			continue
		}
		if !deepEqual(gotV, wantV) {
			t.Errorf("%s field value mismatch for key %q:\ngot: %v\nwant: %v",
				field, k, gotV, wantV)
		}
	}
}

// deepEqual performs a deep comparison of two values
func deepEqual(a, b interface{}) bool {
	// This is a simplified version. In practice, you might want to use
	// reflection or a more sophisticated comparison function
	return a == b
}
