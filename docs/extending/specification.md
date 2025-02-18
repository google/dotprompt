# Specification

The Dotprompt project uses a YAML-based specification system for testing
template rendering, variable substitution, metadata handling, and other core
functionality. This document explains how the specification system works and how
to add new test cases.

## File Organization

The specification files are located in the `/spec` directory and include:

- `metadata.yaml`: Tests for metadata state handling and configuration
- `variables.yaml`: Tests for variable substitution and default values
- `partials.yaml`: Tests for partial template functionality
- `picoschema.yaml`: Tests for schema validation

## YAML File Format

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

### Key Components

- `name`: Identifier for the test suite
- `template`: The template string to be rendered
- `tests`: List of test cases
  - `desc`: Description of what the test verifies
  - `data`: Input data for the test
  - `expect`: Expected output after rendering

## Features Tested

### 1. Variable Substitution

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

### 2. Metadata and State

```yaml
# Example from metadata.yaml
- name: metadata_state
  template: |
    Current count is {{@state.count}}
    Status is {{@state.status}}
```

### 3. Configuration and Extensions

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

## Test Implementation

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

## Adding New Tests

To add new tests:

1. Choose the appropriate YAML file based on the feature being tested.
2. Add a new test suite or extend an existing one.
3. Follow the YAML structure shown above.
4. Include clear descriptions for each test case.
5. Specify both input data and expected output.

## Test Execution Process

For each test case, the system:

1. Creates a new `Dotprompt` environment.
2. Configures it with any specified schemas, tools, and partials.
3. Renders the template with the test data.
4. Compares the result with the expected output.
5. Validates additional aspects like raw output and metadata when specified.

This specification system provides a declarative way to verify the template
engine's behavior, making it easy to maintain existing tests and add new ones as
features are developed.
