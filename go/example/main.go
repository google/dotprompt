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

package main

import (
	"fmt"
	"os"

	"github.com/google/dotprompt/go/dotprompt"
)

func main() {
	// Read the .prompt file
	source, err := os.ReadFile("example.prompt")
	if err != nil {
		panic(err)
	}

	// Create a Dotprompt instance
	dp := dotprompt.NewDotprompt(nil)

	// Compile the prompt
	// Compile calls Parse internally
	promptFunc, err := dp.Compile(string(source), nil)
	if err != nil {
		panic(err)
	}

	// Data to pass during rendering
	data := &dotprompt.DataArgument{
		Input: map[string]any{
			"text": "dotprompt is a library and toolset for managing and executing prompts. It defines metadata with YAML front matter and describes the prompt body with Handlebars templates. This makes it easy to reuse, maintain, and version control prompts.",
		},
	}

	// Render the prompt
	renderedPrompt, err := promptFunc(data, nil)
	if err != nil {
		panic(err)
	}

	// Display the results
	fmt.Println("--- Metadata ---")
	fmt.Printf("Model: %s\n", renderedPrompt.Model)
	fmt.Printf("Description: %s\n", renderedPrompt.Description)

	fmt.Println("\n--- Messages ---")
	for _, msg := range renderedPrompt.Messages {
		fmt.Printf("Role: %s\n", msg.Role)
		for _, part := range msg.Content {
			if textPart, ok := part.(*dotprompt.TextPart); ok {
				fmt.Printf("Content: %s\n", textPart.Text)
			}
		}
		fmt.Println("----------")
	}
}
