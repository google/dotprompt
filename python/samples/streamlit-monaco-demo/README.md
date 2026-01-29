# Streamlit Monaco Dotprompt Demo

This sample demonstrates how to use the Monaco Editor with Dotprompt syntax highlighting in a Streamlit application.

## Setup

1.  Navigate to this directory:
    ```bash
    cd python/samples/streamlit-monaco-demo
    ```

2.  Create a virtual environment and install dependencies using `uv`:
    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    ```

## Running the Demo

Run the Streamlit app:

```bash
streamlit run app.py
```

## Note on Syntax Highlighting

This demo uses the `streamlit-monaco` component. If the component does not have the `dotprompt` language registered, syntax highlighting might fall back to plain text or standard Handlebars if configured. 
To fully enable `dotprompt` highlighting, the Monaco instance in the browser needs the grammar definition registered via `monaco.languages.register`.
