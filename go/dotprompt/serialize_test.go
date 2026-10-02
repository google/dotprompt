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
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/invopop/jsonschema"
)

func TestParsedPromptMarshalText_NoFrontmatter(t *testing.T) {
	prompt := ParsedPrompt{
		PromptMetadata: PromptMetadata{
			Ext: make(map[string]map[string]any),
		},
		Template: "Hello {{name}}",
	}

	got, err := prompt.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText() returned error: %v", err)
	}

	if string(got) != "Hello {{name}}" {
		t.Fatalf("MarshalText() = %q, want %q", string(got), "Hello {{name}}")
	}
}

func TestParsedPromptUnmarshalTextMatchesParseDocument(t *testing.T) {
	source := `---
name: greet
description: Say hi
example.enabled: true
input:
  schema:
    name: string
output:
  format: json
---
Hello {{name}}`

	want, err := ParseDocument(source)
	if err != nil {
		t.Fatalf("ParseDocument() returned error: %v", err)
	}

	var got ParsedPrompt
	if err := got.UnmarshalText([]byte(source)); err != nil {
		t.Fatalf("UnmarshalText() returned error: %v", err)
	}

	if diff := cmp.Diff(want, got); diff != "" {
		t.Fatalf("UnmarshalText() mismatch (-want +got):\n%s", diff)
	}
}

func TestParsedPromptMarshalText_CanonicalOrdering(t *testing.T) {
	prompt := ParsedPrompt{
		PromptMetadata: PromptMetadata{
			Name:  "canonical",
			Model: "googleai/gemini-2.5-flash",
			Input: PromptMetadataInput{
				Schema: "string",
			},
			Output: PromptMetadataOutput{
				Format: "json",
			},
			Tools: []string{"lookup", "search"},
			Raw: map[string]any{
				"version":     "stale-version",
				"description": "stale-description",
				"beta":        "b",
				"alpha":       "a",
				"zeta.two":    "stale-ext",
			},
			Ext: map[string]map[string]any{
				"zeta": {"two": "value2"},
				"acme": {"one": "value1"},
			},
		},
		Template: "Body",
	}

	got, err := prompt.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText() returned error: %v", err)
	}

	want := strings.Join([]string{
		"---",
		"name: canonical",
		"model: googleai/gemini-2.5-flash",
		"input:",
		"  schema: string",
		"output:",
		"  format: json",
		"tools:",
		"- lookup",
		"- search",
		"alpha: a",
		"beta: b",
		"acme.one: value1",
		"zeta.two: value2",
		"---",
		"Body",
	}, "\n")

	if string(got) != want {
		t.Fatalf("MarshalText() = %q, want %q", string(got), want)
	}
}

func TestParsedPromptMarshalText_RoundTrip(t *testing.T) {
	source := `---
name: greet
description: Greeting prompt
custom: keep
myext.mode: friendly
input:
  default:
    locale: en
output:
  format: json
---
Hello {{name}}`

	parsed, err := ParseDocument(source)
	if err != nil {
		t.Fatalf("ParseDocument() returned error: %v", err)
	}

	serialized, err := parsed.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText() returned error: %v", err)
	}

	reparsed, err := ParseDocument(string(serialized))
	if err != nil {
		t.Fatalf("ParseDocument(serialized) returned error: %v", err)
	}

	if reparsed.Name != parsed.Name {
		t.Fatalf("Name = %q, want %q", reparsed.Name, parsed.Name)
	}
	if reparsed.Description != parsed.Description {
		t.Fatalf("Description = %q, want %q", reparsed.Description, parsed.Description)
	}
	if reparsed.Template != parsed.Template {
		t.Fatalf("Template = %q, want %q", reparsed.Template, parsed.Template)
	}
	if diff := cmp.Diff(parsed.Ext, reparsed.Ext); diff != "" {
		t.Fatalf("Ext mismatch (-want +got):\n%s", diff)
	}
	if diff := cmp.Diff(parsed.Input.Default, reparsed.Input.Default); diff != "" {
		t.Fatalf("Input.Default mismatch (-want +got):\n%s", diff)
	}
	if reparsed.Output.Format != parsed.Output.Format {
		t.Fatalf("Output.Format = %q, want %q", reparsed.Output.Format, parsed.Output.Format)
	}
	if reparsed.Raw["custom"] != "keep" {
		t.Fatalf("Raw[custom] = %v, want %q", reparsed.Raw["custom"], "keep")
	}
}

func TestParsedPromptMarshalText_SchemaRoundTrip(t *testing.T) {
	prompt := ParsedPrompt{
		PromptMetadata: PromptMetadata{
			Input: PromptMetadataInput{
				Schema: &jsonschema.Schema{
					Type:        "object",
					Description: "input schema",
				},
			},
			Output: PromptMetadataOutput{
				Schema: map[string]any{
					"type": "string",
				},
			},
		},
		Template: "Body",
	}

	serialized, err := prompt.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText() returned error: %v", err)
	}

	reparsed, err := ParseDocument(string(serialized))
	if err != nil {
		t.Fatalf("ParseDocument(serialized) returned error: %v", err)
	}

	inputSchema, ok := reparsed.Input.Schema.(map[string]any)
	if !ok {
		t.Fatalf("Input.Schema type = %T, want map[string]any", reparsed.Input.Schema)
	}
	wantInputSchema := map[string]any{
		"type":        "object",
		"description": "input schema",
	}
	if diff := cmp.Diff(wantInputSchema, inputSchema); diff != "" {
		t.Fatalf("Input.Schema mismatch (-want +got):\n%s", diff)
	}

	outputSchema, ok := reparsed.Output.Schema.(map[string]any)
	if !ok {
		t.Fatalf("Output.Schema type = %T, want map[string]any", reparsed.Output.Schema)
	}
	wantOutputSchema := map[string]any{
		"type": "string",
	}
	if diff := cmp.Diff(wantOutputSchema, outputSchema); diff != "" {
		t.Fatalf("Output.Schema mismatch (-want +got):\n%s", diff)
	}
}

func TestParsedPromptMarshalText_ConfigAndMaxTurnsRoundTrip(t *testing.T) {
	prompt := ParsedPrompt{
		PromptMetadata: PromptMetadata{
			MaxTurns: 3,
			Config: ModelConfig{
				"temperature": 0.2,
				"topK":        5,
			},
		},
		Template: "Body",
	}

	serialized, err := prompt.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText() returned error: %v", err)
	}

	want := strings.Join([]string{
		"---",
		"maxTurns: 3",
		"config:",
		"  temperature: 0.2",
		"  topK: 5",
		"---",
		"Body",
	}, "\n")
	if string(serialized) != want {
		t.Fatalf("MarshalText() = %q, want %q", string(serialized), want)
	}

	reparsed, err := ParseDocument(string(serialized))
	if err != nil {
		t.Fatalf("ParseDocument(serialized) returned error: %v", err)
	}

	if reparsed.MaxTurns != prompt.MaxTurns {
		t.Fatalf("MaxTurns = %d, want %d", reparsed.MaxTurns, prompt.MaxTurns)
	}
	if got := reparsed.Config["temperature"]; got != 0.2 {
		t.Fatalf("Config[temperature] = %#v, want %#v", got, 0.2)
	}
	if got := reparsed.Config["topK"]; got != uint64(5) {
		t.Fatalf("Config[topK] = %#v, want %#v", got, uint64(5))
	}
}

func TestParsedPromptMarshalText_ToolDefsRoundTrip(t *testing.T) {
	prompt := ParsedPrompt{
		PromptMetadata: PromptMetadata{
			ToolDefs: []ToolDefinition{
				{
					Name:        "lookup",
					Description: "Find a record",
					InputSchema: "string",
					OutputSchema: &jsonschema.Schema{
						Type: "number",
					},
				},
			},
		},
		Template: "Body",
	}

	serialized, err := prompt.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText() returned error: %v", err)
	}

	reparsed, err := ParseDocument(string(serialized))
	if err != nil {
		t.Fatalf("ParseDocument(serialized) returned error: %v", err)
	}

	if len(reparsed.ToolDefs) != 1 {
		t.Fatalf("len(ToolDefs) = %d, want 1", len(reparsed.ToolDefs))
	}

	toolDef := reparsed.ToolDefs[0]
	if toolDef.Name != "lookup" {
		t.Fatalf("ToolDefs[0].Name = %q, want %q", toolDef.Name, "lookup")
	}
	if toolDef.Description != "Find a record" {
		t.Fatalf("ToolDefs[0].Description = %q, want %q", toolDef.Description, "Find a record")
	}
	if toolDef.InputSchema != "string" {
		t.Fatalf("ToolDefs[0].InputSchema = %#v, want %q", toolDef.InputSchema, "string")
	}

	outputSchema, ok := toolDef.OutputSchema.(map[string]any)
	if !ok {
		t.Fatalf("ToolDefs[0].OutputSchema type = %T, want map[string]any", toolDef.OutputSchema)
	}
	wantOutputSchema := map[string]any{
		"type": "number",
	}
	if diff := cmp.Diff(wantOutputSchema, outputSchema); diff != "" {
		t.Fatalf("ToolDefs[0].OutputSchema mismatch (-want +got):\n%s", diff)
	}
}

func TestParsedPromptStringMatchesMarshalText(t *testing.T) {
	prompt := ParsedPrompt{
		PromptMetadata: PromptMetadata{
			Name: "greet",
		},
		Template: "Hi",
	}

	want, err := prompt.MarshalText()
	if err != nil {
		t.Fatalf("MarshalText() returned error: %v", err)
	}

	if got := prompt.String(); got != string(want) {
		t.Fatalf("String() = %q, want %q", got, string(want))
	}
}

func TestParsedPromptStringReturnsEmptyOnFailure(t *testing.T) {
	prompt := ParsedPrompt{
		PromptMetadata: PromptMetadata{
			Raw: map[string]any{
				"custom": func() {},
			},
		},
		Template: "Body",
	}

	if _, err := prompt.MarshalText(); err == nil {
		t.Fatal("MarshalText() expected error, got nil")
	}

	if got := prompt.String(); got != "" {
		t.Fatalf("String() = %q, want empty string", got)
	}
}

func TestParsedPromptString_NilReceiver(t *testing.T) {
	var prompt *ParsedPrompt

	if got := prompt.String(); got != "" {
		t.Fatalf("String() = %q, want empty string", got)
	}
}

func TestParsedPromptUnmarshalText_NilReceiver(t *testing.T) {
	var prompt *ParsedPrompt

	err := prompt.UnmarshalText([]byte("Hello"))
	if err == nil {
		t.Fatal("UnmarshalText() expected error, got nil")
	}
	if got := err.Error(); got != "dotprompt: cannot unmarshal into nil ParsedPrompt" {
		t.Fatalf("UnmarshalText() error = %q, want %q", got, "dotprompt: cannot unmarshal into nil ParsedPrompt")
	}
}
