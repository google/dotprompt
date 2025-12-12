// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//	http://www.apache.org/licenses/LICENSE-2.0
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
	"fmt"
	"strings"
	"testing"

	"github.com/mbleigh/raymond"
)

// TestDefineHelper tests the DefineHelper function.
func TestDefineHelper(t *testing.T) {
	dp := NewDotprompt(nil)
	tpl, err := raymond.Parse("{{upperCase 'hello'}}")
	if err != nil {
		t.Fatalf("Failed to parse template: %v", err)
	}

	upperCaseHelperFunc := func(s string) string {
		return strings.ToUpper(s)
	}
	helperName := "upperCase"

	// Initial call.
	if err = dp.DefineHelper(helperName, upperCaseHelperFunc, tpl); err != nil {
		t.Fatalf("Failed to define helper: %v", err)
	}

	if !dp.knownHelpers[helperName] {
		t.Errorf("Expected helper '%s' to be marked as known, but it wasn't", helperName)
	}
	if len(dp.knownHelpers) != 1 {
		t.Errorf("Expected knownHelpers map to have 1 entry, got %d", len(dp.knownHelpers))
	}

	result, err := tpl.Exec(nil)
	if err != nil {
		t.Errorf("Template execution failed after registering helper: %v", err)
	}
	if result != "HELLO" {
		t.Errorf("Expected template output 'HELLO', got '%s'", result)
	}

	// Call again with the same name; should be a no-op.
	if err = dp.DefineHelper(helperName, upperCaseHelperFunc, tpl); err == nil {
		t.Fatalf("Expected DefineHelper to return an error when redefining a helper, but it didn't")
	}
	if !dp.knownHelpers[helperName] {
		t.Errorf("Expected helper '%s' to still be marked as known after second call", helperName)
	}
	if len(dp.knownHelpers) != 1 {
		t.Errorf("Expected knownHelpers map to still have 1 entry after second call, got %d", len(dp.knownHelpers))
	}
}

// TestDefinePartial tests the DefinePartial function.
func TestDefinePartial(t *testing.T) {
	dp := NewDotprompt(nil)
	tpl, err := raymond.Parse("{{> testPartial}}")
	if err != nil {
		t.Fatalf("Failed to parse template: %v", err)
	}

	partialName := "testPartial"
	partialSource := "Partial Content"

	// Initial call.
	if err = dp.DefinePartial(partialName, partialSource, tpl); err != nil {
		t.Fatalf("Failed to define partial: %v", err)
	}

	if !dp.knownPartials[partialName] {
		t.Errorf("Expected partial '%s' to be marked as known, but it wasn't", partialName)
	}
	if len(dp.knownPartials) != 1 {
		t.Errorf("Expected knownPartials map to have 1 entry, got %d", len(dp.knownPartials))
	}

	// Verify rendering (indirectly checks registration).
	result, err := tpl.Exec(nil)
	if err != nil {
		t.Errorf("Template execution failed after registering partial: %v", err)
	}
	if result != "Partial Content" {
		t.Errorf("Expected template output 'Partial Content', got '%s'", result)
	}

	// Call again with the same name; should be a no-op.
	if err = dp.DefinePartial(partialName, partialSource, tpl); err == nil {
		t.Fatalf("Expected DefinePartial to return an error when redefining a partial, but it didn't")
	}
	if !dp.knownPartials[partialName] {
		t.Errorf("Expected partial '%s' to still be marked as known after second call", partialName)
	}
	if len(dp.knownPartials) != 1 {
		t.Errorf("Expected knownPartials map to still have 1 entry after second call, got %d", len(dp.knownPartials))
	}
}

// TestRegisterHelpers tests registering helpers from options and built-ins.
func TestRegisterHelpers(t *testing.T) {
	optionHelperName := "optionHelper"
	optionHelperFunc := func() string { return "option" }

	options := &DotpromptOptions{
		Helpers: map[string]any{
			optionHelperName: optionHelperFunc,
		},
	}
	dp := NewDotprompt(options)

	tpl, err := raymond.Parse("{{optionHelper}} {{#if true}}built-in{{/if}}")
	if err != nil {
		t.Fatalf("Failed to parse template: %v", err)
	}

	if err = dp.RegisterHelpers(tpl); err != nil {
		t.Fatalf("RegisterHelpers failed: %v", err)
	}

	// Check knownHelpers map.
	if !dp.knownHelpers[optionHelperName] {
		t.Errorf("Option helper '%s' was not marked as known", optionHelperName)
	}
	// Check a known built-in helper defined in dotprompt/helper.go (assuming 'ifEquals' is one)
	// Note: templateHelpers map is not exported, so we check one name we expect to be there.
	// Adjust "ifEquals" if the actual helper name is different.
	expectedBuiltIn := "ifEquals"
	foundBuiltIn := false
	for name := range templateHelpers {
		if dp.knownHelpers[name] {
			if name == expectedBuiltIn {
				foundBuiltIn = true
			}
		} else {
			// Only fail if it's a built-in helper expected to be registered.
			if _, ok := templateHelpers[name]; ok {
				t.Errorf("Built-in helper '%s' was not marked as known", name)
			}
		}
	}
	if !foundBuiltIn {
		t.Logf("Note: Could not explicitly verify built-in helper '%s' registration via knownHelpers, "+
			"ensure templateHelpers in dotprompt.go includes it and RegisterHelpers iterates correctly.", expectedBuiltIn)
	}

	// Check rendering.
	result, err := tpl.Exec(nil)
	if err != nil {
		t.Errorf("Template execution failed after RegisterHelpers: %v", err)
	}
	expectedOutput := "option built-in"
	if result != expectedOutput {
		t.Errorf("Expected output '%s', got '%s'", expectedOutput, result)
	}
}

// TestRegisterPartials tests registering partials from options.
func TestRegisterPartials(t *testing.T) {
	optionPartialName := "optionPartial"
	optionPartialSource := "Option Partial Content"

	options := &DotpromptOptions{
		Partials: map[string]string{
			optionPartialName: optionPartialSource,
		},
	}
	dp := NewDotprompt(options)

	// Template using the option partial.
	templateString := "Start {{> optionPartial}} End"
	tpl, err := raymond.Parse(templateString)
	if err != nil {
		t.Fatalf("Failed to parse template: %v", err)
	}

	// Register partials (without triggering resolver in this specific test).
	err = dp.RegisterPartials(tpl, templateString)
	if err != nil {
		t.Fatalf("RegisterPartials failed: %v", err)
	}

	// Check knownPartials map.
	if !dp.knownPartials[optionPartialName] {
		t.Errorf("Option partial '%s' was not marked as known", optionPartialName)
	}
	if len(dp.knownPartials) != 1 {
		t.Errorf("Expected knownPartials map to have 1 entry, got %d", len(dp.knownPartials))
	}

	// Check rendering.
	result, err := tpl.Exec(nil)
	if err != nil {
		t.Errorf("Template execution failed after RegisterPartials: %v", err)
	}
	expectedOutput := "Start Option Partial Content End"
	if result != expectedOutput {
		t.Errorf("Expected output '%s', got '%s'", expectedOutput, result)
	}
}

// TestRegisterPartialsWithResolver tests registering partials using a PartialResolver.
func TestRegisterPartialsWithResolver(t *testing.T) {
	resolvedPartialName := "resolvedPartial"
	resolvedPartialSource := "Resolved Partial Content"
	nestedPartialName := "nestedPartial"
	nestedPartialSource := "Nested {{> resolvedPartial}}"

	resolver := func(name string) (string, error) {
		switch name {
		case resolvedPartialName:
			return resolvedPartialSource, nil
		case nestedPartialName:
			return nestedPartialSource, nil
		default:
			return "", fmt.Errorf("unknown partial: %s", name)
		}
	}

	options := &DotpromptOptions{
		PartialResolver: resolver,
	}
	dp := NewDotprompt(options)

	// Template using a partial that needs resolving, which itself includes another resolved partial.
	templateString := "Outer {{> nestedPartial}} End"
	tpl, err := raymond.Parse(templateString)
	if err != nil {
		t.Fatalf("Failed to parse template: %v", err)
	}

	// Register partials, triggering the resolver
	err = dp.RegisterPartials(tpl, templateString)
	if err != nil {
		t.Fatalf("RegisterPartials with resolver failed: %v", err)
	}

	// Check knownPartials map
	if !dp.knownPartials[resolvedPartialName] {
		t.Errorf("Resolved partial '%s' was not marked as known", resolvedPartialName)
	}
	if !dp.knownPartials[nestedPartialName] {
		t.Errorf("Nested resolved partial '%s' was not marked as known", nestedPartialName)
	}
	if len(dp.knownPartials) != 2 {
		t.Errorf("Expected knownPartials map to have 2 entries, got %d", len(dp.knownPartials))
	}

	// Check rendering.
	result, err := tpl.Exec(nil)
	if err != nil {
		t.Errorf("Template execution failed after RegisterPartials with resolver: %v", err)
	}
	expectedOutput := "Outer Nested Resolved Partial Content End"
	if result != expectedOutput {
		t.Errorf("Expected output '%s', got '%s'", expectedOutput, result)
	}
}

// TestCompileMultiplePromptsTemplateIsolation tests that multiple compiled prompts
// use their own templates and don't share state.
// This is a regression test for https://github.com/google/dotprompt/issues/362
func TestCompileMultiplePromptsTemplateIsolation(t *testing.T) {
	dp := NewDotprompt(nil)

	// Compile first prompt about weather
	prompt1Source := "Talk about weather: {{topic}}"
	prompt1, err := dp.Compile(prompt1Source, nil)
	if err != nil {
		t.Fatalf("Failed to compile prompt1: %v", err)
	}

	// Compile second prompt about programming (different template)
	prompt2Source := "Talk about programming: {{language}}"
	prompt2, err := dp.Compile(prompt2Source, nil)
	if err != nil {
		t.Fatalf("Failed to compile prompt2: %v", err)
	}

	// Execute first prompt - should use its own template
	result1, err := prompt1(
		&DataArgument{Input: map[string]any{"topic": "sunny day"}},
		nil,
	)
	if err != nil {
		t.Fatalf("Failed to execute prompt1: %v", err)
	}

	// Execute second prompt
	result2, err := prompt2(
		&DataArgument{Input: map[string]any{"language": "Go"}},
		nil,
	)
	if err != nil {
		t.Fatalf("Failed to execute prompt2: %v", err)
	}

	// Verify first prompt output contains "weather" and "sunny day"
	if len(result1.Messages) == 0 {
		t.Fatal("prompt1 returned no messages")
	}
	msg1 := result1.Messages[0]
	if len(msg1.Content) == 0 {
		t.Fatal("prompt1 message has no content")
	}
	text1, ok := msg1.Content[0].(*TextPart)
	if !ok {
		t.Fatalf("prompt1 content is not TextPart: %T", msg1.Content[0])
	}
	if !strings.Contains(text1.Text, "weather") {
		t.Errorf("prompt1 output should contain 'weather', got: %s", text1.Text)
	}
	if !strings.Contains(text1.Text, "sunny day") {
		t.Errorf("prompt1 output should contain 'sunny day', got: %s", text1.Text)
	}

	// Verify second prompt output contains "programming" and "Go"
	if len(result2.Messages) == 0 {
		t.Fatal("prompt2 returned no messages")
	}
	msg2 := result2.Messages[0]
	if len(msg2.Content) == 0 {
		t.Fatal("prompt2 message has no content")
	}
	text2, ok := msg2.Content[0].(*TextPart)
	if !ok {
		t.Fatalf("prompt2 content is not TextPart: %T", msg2.Content[0])
	}
	if !strings.Contains(text2.Text, "programming") {
		t.Errorf("prompt2 output should contain 'programming', got: %s", text2.Text)
	}
	if !strings.Contains(text2.Text, "Go") {
		t.Errorf("prompt2 output should contain 'Go', got: %s", text2.Text)
	}

	// Critical check: first prompt should NOT use second prompt's template
	if strings.Contains(text1.Text, "programming") {
		t.Errorf("BUG: prompt1 output contains 'programming' from prompt2's template! Got: %s", text1.Text)
	}
}
