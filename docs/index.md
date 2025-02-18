# Dotprompt

A **prompt** is an instruction provided to a model. Prompt engineering involves
tweaking these prompts to attempt to coax the model to do what you want. A
**prompt action** is used to render a prompt template producing a request that
can be passed to a **model**. Prompt actions are defined as either code or as
configuration files bearing the `.prompt` (read "dotprompt") extension.

Dotprompt is designed around the premise that **prompts are code**.  This
decouples prompt engineering from application development and allows prompt
engineers to rapidly iterate and test prompts independently of application
development.

**Dotprompt** is an executable prompt template file format for Generative AI. It
is designed to be agnostic to programming language and model provider to allow
for maximum flexibility in usage. Dotprompt extends the popular
[Handlebars](https://handlebarsjs.com) templating language with GenAI-specific
features.

## What's an executable prompt template?

An executable prompt template is a file that contains not only the text of a
prompt but also metadata and instructions for how to use that prompt with a
generative AI model. Here's what makes Dotprompt files executable:

- **Metadata Inclusion**: Dotprompt files include metadata about model
  configuration, input requirements, and expected output format. This
  information is typically stored in a YAML frontmatter section at the beginning
  of the file.

- **Self-Contained Entity**: Because a Dotprompt file contains all the necessary
  information to execute a prompt, it can be treated as a self-contained entity.
  This means you can "run" a Dotprompt file directly, without needing additional
  configuration or setup in your code.

- **Model Configuration**: The file specifies which model to use and how to
  configure it (e.g., temperature, max tokens).

- **Input Schema**: It defines the structure of the input data expected by the
  prompt, allowing for validation and type-checking.

- **Output Format**: The file can specify the expected format of the model's
  output, which can be used for parsing and validation.

- **Templating**: The prompt text itself uses Handlebars syntax, allowing for
  dynamic content insertion based on input variables.

This combination of features makes it possible to treat a Dotprompt file as an
executable unit, streamlining the process of working with AI models and ensuring
consistency across different uses of the same prompt.

## Example `.prompt` file

Here's an example of a Dotprompt file that extracts structured data from
provided text:

```handlebars
---
model: googleai/gemini-1.5-pro
input:
  schema:
    text: string
output:
  format: json
  schema:
    name?: string, the full name of the person
    age?: number, the age of the person
    occupation?: string, the person's occupation
---

Extract the requested information from the given text. If a piece of information
is not present, omit that field from the output.

Text: {{text}}
```

This Dotprompt file:

1. Specifies the use of the `googleai/gemini-1.5-pro` model.
2. Defines an input schema expecting a `text` string.
3. Specifies that the output should be in JSON format.
4. Provides a schema for the expected output, including fields for name, age,
   and occupation.
5. Uses Handlebars syntax (`{{text}}`) to insert the input text into the prompt.

When executed, this prompt would take a text input, analyze it using the
specified AI model, and return a structured JSON object with the extracted
information.

You can use `.prompt` files with [Firebase
Genkit](https://firebase.google.com/docs/genkit/dotprompt).
