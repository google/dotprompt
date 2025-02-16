# The `.prompt` file format

**Dotprompt files** contain configuration in the form of YAML front matter
delineated by `---` sequences followed by variable-interpolated UTF-8 encoded
text templates, which can optionally use [Handlebars](https://handlebarsjs.com)
for templating:

## Example 1

Here's an example of a `.prompt` file that extracts structured data from
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

The portion in the triple-dashes is YAML front matter. The rest of the file is
the prompt, which can optionally use Handlebars templates.

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

## Example 2

Here is another example `.prompt` file:

```handlebars
---
model: googleai/gemini-1.5-flash
config:
  temperature: 0.9
input:
  schema:
    location: string
    style?: string
    name?: string
  default:
    location: a restaurant
---

You are the world's most welcoming AI assistant and are currently working at {{location}}.

Greet a guest{{#if name}} named {{name}}{{/if}}{{#if style}} in the style of {{style}}{{/if}}.
```

This Dotprompt file:

1. Specifies the use of the `googleai/gemini-1.5-flash` model.
2. Defines a config block with a `temperature` of 0.9.
3. Specifies an input schema with a `location` string and optional `style` and
   `name` strings.
4. Provides a default value for the `location` field.
5. Uses Handlebars syntax (`{{location}}`) to insert the value of the `location`
   field into the prompt.

When executed, this prompt would take a text input, analyze it using the
specified AI model, and return a structured JSON object with the extracted
information.

## Specification

The Dotprompt project uses a YAML-based specification system for testing
template rendering, variable substitution, metadata handling, and other core
functionality. This document explains how the specification system works and how
to add new test cases.

### Organization

The specification files are located in the `/spec` directory and include:

- `metadata.yaml`: Tests for metadata state handling and configuration
- `variables.yaml`: Tests for variable substitution and default values
- `partials.yaml`: Tests for partial template functionality
- `picoschema.yaml`: Tests for schema validation

### YAML File Format

Each YAML file contains a list of test suites. A test suite has the following
structure:

```yaml
- name: suite_name
  template: |
    Template content with {{variables}}
  tests:
    - desc: Description of the test case
      data:
        input:
          variable_name: value
      expect:
        messages:
          - role: user
            content: [{ text: "Expected output" }]
```

#### Key Components

- `name`: Identifier for the test suite
- `template`: The template string to be rendered
- `tests`: List of test cases
  - `desc`: Description of what the test verifies
  - `data`: Input data for the test
  - `expect`: Expected output after rendering

### Features Tested

#### 1. Variable Substitution

```yaml
# Example from variables.yaml
- name: basic
  template: |
    Hello, {{name}}!
  tests:
    - desc: uses a provided variable
      data:
        input: { name: "Michael" }
      expect:
        messages:
          - role: user
            content: [{ text: "Hello, Michael!\n" }]
```

#### 2. Metadata and State

```yaml
# Example from metadata.yaml
- name: metadata_state
  template: |
    Current count is {{@state.count}}
    Status is {{@state.status}}
```

#### 3. Configuration and Extensions

```yaml
# Example with frontmatter
- name: ext
  template: |
    ---
    model: cool-model
    config:
      temperature: 3
    ext1.foo: bar
    ---
```

### Test Implementation

The test runner is implemented in `js/test/spec.test.ts` and:

1. Automatically discovers all `.yaml` files in the spec directory.
2. Creates test suites for each YAML file.
3. Executes individual test cases using Vitest.
4. Verifies:
   - Template rendering output
   - Configuration values
   - Extension fields
   - Raw frontmatter
   - Metadata rendering
   - Error cases

### Adding New Tests

To add new tests:

1. Choose the appropriate YAML file based on the feature being tested.
2. Add a new test suite or extend an existing one.
3. Follow the YAML structure shown above.
4. Include clear descriptions for each test case.
5. Specify both input data and expected output.

### Test Execution Process

For each test case, the system:

1. Creates a new `Dotprompt` environment.
2. Configures it with any specified schemas, tools, and partials.
3. Renders the template with the test data.
4. Compares the result with the expected output.
5. Validates additional aspects like raw output and metadata when specified.

This specification system provides a declarative way to verify the template
engine's behavior, making it easy to maintain existing tests and add new ones as
features are developed.
