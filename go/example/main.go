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
