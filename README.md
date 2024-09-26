# Dotprompt: Executable GenAI Prompt Templates

**Dotprompt** is an executable prompt template file format for Generative AI. It is designed to be agnostic to programming language and model provider to allow for maximum flexibility in usage. Dotprompt extends the popular [Handlebars](https://handlebarsjs.com) templating language with GenAI-specific features.

## What's an executable prompt template?

An executable prompt template is a file that contains not only the text of a prompt but also metadata and instructions for how to use that prompt with a generative AI model. Here's what makes Dotprompt files executable:

- **Metadata Inclusion**: Dotprompt files include metadata about model configuration, input requirements, and expected output format. This information is typically stored in a YAML frontmatter section at the beginning of the file.

- **Self-Contained Entity**: Because a Dotprompt file contains all the necessary information to execute a prompt, it can be treated as a self-contained entity. This means you can "run" a Dotprompt file directly, without needing additional configuration or setup in your code.

- **Model Configuration**: The file specifies which model to use and how to configure it (e.g., temperature, max tokens).

- **Input Schema**: It defines the structure of the input data expected by the prompt, allowing for validation and type-checking.

- **Output Format**: The file can specify the expected format of the model's output, which can be used for parsing and validation.

- **Templating**: The prompt text itself uses Handlebars syntax, allowing for dynamic content insertion based on input variables.

This combination of features makes it possible to treat a Dotprompt file as an executable unit, streamlining the process of working with AI models and ensuring consistency across different uses of the same prompt.

## Example `.prompt` file

Here's an example of a Dotprompt file that extracts structured data from provided text:

```handlebars
---
model: googleai/gemini-1.5-pro
input:
  schema:
    text: string
output:
  format: json
  schema:
    title?: string, the title of the article if it has one
    summary: string, a 3-sentence summary of the text
    tags?(array, a list of string tag category for the text): String, 
---

Extract the requested information from the given text. If a piece of information is not present, omit that field from the output.

Text: {{text}}
```

This Dotprompt file:

1. Specifies the use of the `googleai/gemini-1.5-pro` model.
2. Defines an input schema expecting a `text` string.
3. Specifies that the output should be in JSON format.
4. Provides a schema for the expected output, including fields for name, age, and occupation.
5. Uses Handlebars syntax (`{{text}}`) to insert the input text into the prompt.

When executed, this prompt would take a text input, analyze it using the specified AI model, and return a structured JSON object with the extracted information.

## Installation

The remainder of this getting started guide will use the reference Dotprompt implementation included as part of the [Firebase Genkit](https://github.com/firebase/genkit) GenAI framework. To use other implementations of Dotprompt, see the [list of Implementations](/implementations).

First, install the necessary packages using NPM. Here we'll be using the [Gemini API](https://ai.google.dev/gemini-api) from Google as our model implementation:

```bash
npm i \
  @genkit-ai/core \
  @genkit-ai/ai \
  @genkit-ai/dotprompt \
  @genkit-ai/googleai
```

After installation, you'll need to set up your environment and initialize the Dotprompt system. Here's a basic setup:

```typescript
import { configureGenkit } from '@genkit-ai/core';
import { googleAI } from '@genkit-ai/googleai';
import { dotprompt, promptRef } from '@genkit-ai/dotprompt';

// Configure Genkit with the GoogleAI provider and Dotprompt plugin
configureGenkit({
  plugins: [googleAI(), dotprompt()],
});

// Now you're ready to use Dotprompt!
```

**Note:** You will need to set your Google AI API key to the `GOOGLE_API_KEY` environment variable or pass it as an option to the `googleAI()` plugin configuration.

With this setup, you can now create `.prompt` files in your project and use them in your code. For example, if you have a file named `extractInfo.prompt` with the content from the earlier example, you can use it like this:

```typescript
const extractInfoPrompt = promptRef('extractInfo');

const result = await extractInfoPrompt.generate({
  input: {
    text: "John Doe is a 35-year-old software engineer living in New York.",
  },
});

console.log(result.output());
// Output: { "name": "John Doe", "age": 35, "occupation": "software engineer" }
```

This setup allows you to leverage the power of Dotprompt, making your AI interactions more structured, reusable, and maintainable.

By following these steps, you'll have a basic Dotprompt setup ready to go. From here, you can create more complex prompts, integrate them into your application, and start harnessing the full power of generative AI in a structured, template-driven way.