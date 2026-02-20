# Go Dotprompt Library Usage Example

This directory contains sample code demonstrating how to use the `dotprompt` library in Go.

## File Structure

- `example.prompt`: The prompt definition file. It defines metadata with YAML front matter and the template in the body.
- `main.go`: An executable program that reads, parses, and renders `example.prompt` and outputs the result.

## How to Run

1.  Change the current directory to `go/example`.
    ```bash
    cd go/example
    ```

2.  Tidy the dependencies.
    ```bash
    go mod tidy
    ```

3.  Run the program.
    ```bash
    go run main.go
    ```

## Output

When you run the program, the metadata from the `.prompt` file and the messages after applying the data will be displayed on standard output.

```text
--- Metadata ---
Model: gemini-2.5-flash
Description: Summarize the input text.

--- Messages ---
Role: user
Content: Please summarize the following text.

dotprompt is a library and toolset for managing and executing prompts. It defines metadata with YAML front matter and describes the prompt body with Handlebars templates. This makes it easy to reuse, maintain, and version control prompts.
----------
Role: model
Content: Yes, I understand. I will summarize it.
----------
