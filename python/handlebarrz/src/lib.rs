// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

use handlebars::{
    Context, Handlebars, Helper, HelperDef, Output, RenderContext, RenderError, RenderErrorReason,
};
use pyo3::exceptions::{PyFileNotFoundError, PyValueError};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use serde_json::Value;
use std::collections::HashMap;
use std::path::Path;

/// Python bindings for the Handlebars templating engine implemented in Rust.
///
/// This module provides Python access to the high-performance Handlebars-rust
/// implementation. It exposes the core functionality needed for template
/// rendering, including:
///
/// - Template registration and management
/// - Context-based rendering
/// - Helper function registration
/// - Configuration options like strict mode and development mode
/// - HTML escaping utilities
///
/// The main class exposed is `HandlebarrzTemplate`, which wraps the Rust
/// `Handlebars` registry and provides methods for template operations.
#[pymodule]
fn _native(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<HandlebarrzTemplate>()?;
    m.add_function(wrap_pyfunction!(html_escape, py)?)?;
    m.add_function(wrap_pyfunction!(no_escape, py)?)?;
    Ok(())
}

/// Escapes special HTML characters in a string to prevent XSS attacks.
///
/// Converts the characters `&`, `<`, `>`, `"`, and `'` to their corresponding
/// HTML entities (`&amp;`, `&lt;`, `&gt;`, `&quot;`, and `&#x27;`).
///
/// This function is used by default for all variable interpolations in
/// Handlebars templates (e.g., `{{variable}}`), unless specifically bypassed
/// with triple braces (`{{{variable}}}`) or the ampersand prefix (`{{&variable}}`).
///
/// # Arguments
///
/// * `text` - The string to be HTML-escaped
///
/// # Returns
///
/// A new string with HTML special characters escaped
#[pyfunction]
fn html_escape(text: &str) -> String {
    handlebars::html_escape(text)
}

/// Passes through a string without any escaping or modification.
///
/// This function can be set as the escape function using `set_escape_fn()`
/// when HTML escaping is not desired for the entire template engine.
///
/// # Arguments
///
/// * `text` - The string to be returned without modification
///
/// # Returns
///
/// The same string that was passed in, without any changes
#[pyfunction]
fn no_escape(text: &str) -> String {
    handlebars::no_escape(text)
}

/// Python callable helper
struct PyHelperDef {
    func: PyObject,
}

impl HelperDef for PyHelperDef {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        _reg: &'reg Handlebars<'reg>,
        ctx: &'rc Context,
        _rc: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> Result<(), RenderError> {
        // Acquire GIL
        Python::with_gil(|py| {
            // Extract params
            let params: Vec<&Value> = h.params().iter().map(|p| p.value()).collect();
            let params_json = match serde_json::to_string(&params) {
                Ok(json) => json,
                Err(e) => {
                    let desc = format!("Failed to serialize params: {}", e);
                    return Err(RenderError::from(RenderErrorReason::Other(desc.into())));
                }
            };

            // Extract hash
            let hash = h.hash();
            let mut hash_map = HashMap::new();
            for (k, v) in hash.iter() {
                hash_map.insert(k.to_string(), v.value().clone());
            }
            let hash_json = match serde_json::to_string(&hash_map) {
                Ok(json) => json,
                Err(e) => {
                    let desc = format!("Failed to serialize hash: {}", e);
                    return Err(RenderError::from(RenderErrorReason::Other(desc.into())));
                }
            };

            // Convert context to JSON
            let ctx_json = match serde_json::to_string(ctx.data()) {
                Ok(json) => json,
                Err(e) => {
                    let desc = format!("Failed to serialize context: {}", e);
                    return Err(RenderError::from(RenderErrorReason::Other(desc.into())));
                }
            };

            // Call the Python function
            let result = self.func.call1(py, (params_json, hash_json, ctx_json));

            match result {
                Ok(result) => {
                    let result_str = match result.extract::<String>(py) {
                        Ok(s) => s,
                        Err(e) => {
                            let desc = format!("Failed to extract result: {}", e);
                            return Err(RenderError::from(RenderErrorReason::Other(desc.into())));
                        }
                    };
                    out.write(&result_str)?;
                    Ok(())
                }
                Err(e) => {
                    let desc = format!("Helper execution failed: {}", e);
                    Err(RenderError::from(RenderErrorReason::Other(desc.into())))
                }
            }
        })
    }
}

/// A Handlebars template engine instance.
///
/// This class provides methods for registering templates, partials, and helpers,
/// as well as rendering templates with data.
///
/// # Examples
///
/// ```python
/// import handlebarrz
///
/// # Create a new template engine instance
/// engine = handlebarrz.HandlebarrzTemplate()
///
/// # Register a template
/// engine.register_template('my_template', '<p>{{name}}</p>')
///
/// # Render the template with data
/// data = {'name': 'John'}
/// result = engine.render('my_template', data)
/// print(result)  # Output: <p>John</p>
/// ```
#[pyclass]
struct HandlebarrzTemplate {
    registry: Handlebars<'static>,
    py_helpers: HashMap<String, PyObject>,
}

#[pymethods]
impl HandlebarrzTemplate {
    /// Creates a new `HandlebarrzTemplate` instance.
    ///
    /// # Returns
    ///
    /// A new `HandlebarrzTemplate` instance
    #[new]
    fn new() -> Self {
        let registry = Handlebars::new();

        // Configure registry for block helpers
        // Block helpers are built into handlebars-rust, so we don't need to register them explicitly

        Self {
            registry,
            py_helpers: HashMap::new(),
        }
    }

    /// Sets the strict mode for the template engine.
    ///
    /// In strict mode, the engine will raise an error if a template tries to
    /// access a non-existent variable or helper.
    ///
    /// # Arguments
    ///
    /// * `enabled` - Whether to enable strict mode
    ///
    /// # Returns
    ///
    /// `None`
    #[pyo3(text_signature = "($self, enabled)")]
    fn set_strict_mode(&mut self, enabled: bool) -> PyResult<()> {
        self.registry.set_strict_mode(enabled);
        Ok(())
    }

    /// Gets the current strict mode setting.
    ///
    /// # Returns
    ///
    /// Whether strict mode is currently enabled
    #[pyo3(text_signature = "($self)")]
    fn get_strict_mode(&self) -> bool {
        self.registry.strict_mode()
    }

    /// Sets the development mode for the template engine.
    ///
    /// In development mode, the engine will recompile templates on every render,
    /// which can be useful for development and debugging.
    ///
    /// # Arguments
    ///
    /// * `enabled` - Whether to enable development mode
    ///
    /// # Returns
    ///
    /// `None`
    #[pyo3(text_signature = "($self, enabled)")]
    fn set_dev_mode(&mut self, enabled: bool) -> PyResult<()> {
        self.registry.set_dev_mode(enabled);
        Ok(())
    }

    /// Gets the current development mode setting.
    ///
    /// # Returns
    ///
    /// Whether development mode is currently enabled
    #[pyo3(text_signature = "($self)")]
    fn get_dev_mode(&self) -> bool {
        self.registry.dev_mode()
    }

    /// Sets the escape function for the template engine.
    ///
    /// The escape function is used to escape special characters in template
    /// variables. By default, the `html_escape` function is used.
    ///
    /// # Arguments
    ///
    /// * `escape_fn` - The name of the escape function to use (either "html_escape" or "no_escape")
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyValueError` if the specified escape function is not recognized
    #[pyo3(text_signature = "($self, escape_fn)")]
    fn set_escape_fn(&mut self, escape_fn: &str) -> PyResult<()> {
        match escape_fn {
            "html_escape" => self.registry.register_escape_fn(handlebars::html_escape),
            "no_escape" => self.registry.register_escape_fn(handlebars::no_escape),
            _ => {
                return Err(PyValueError::new_err(format!(
                    "Unknown escape function: {}",
                    escape_fn
                )))
            }
        }
        Ok(())
    }

    /// Registers a template with the given name.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the template
    /// * `template_string` - The template source code
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be registered
    #[pyo3(text_signature = "($self, name, template_string)")]
    fn register_template(&mut self, name: &str, template_string: &str) -> PyResult<()> {
        self.registry
            .register_template_string(name, template_string)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Registers a partial with the given name.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the partial
    /// * `template_string` - The partial source code
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyValueError` if the partial cannot be registered
    #[pyo3(text_signature = "($self, name, template_string)")]
    fn register_partial(&mut self, name: &str, template_string: &str) -> PyResult<()> {
        self.registry
            .register_partial(name, template_string)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Registers a template file with the given name.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the template
    /// * `file_path` - The path to the template file
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyFileNotFoundError` if the template file does not exist
    /// `PyValueError` if the template cannot be registered
    #[pyo3(text_signature = "($self, name, file_path)")]
    fn register_template_file(&mut self, name: &str, file_path: &str) -> PyResult<()> {
        let path = Path::new(file_path);
        if !path.exists() {
            return Err(PyFileNotFoundError::new_err(format!(
                "Template file not found: {}",
                file_path
            )));
        }

        self.registry
            .register_template_file(name, file_path)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Registers a helper function with the given name.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the helper
    /// * `helper_fn` - The Python function to use as the helper
    ///
    /// # Returns
    ///
    /// `None`
    #[pyo3(text_signature = "($self, name, helper_fn)")]
    fn register_helper(&mut self, name: &str, helper_fn: PyObject) -> PyResult<()> {
        // Store Python function reference using GIL
        Python::with_gil(|py| {
            self.py_helpers
                .insert(name.to_string(), helper_fn.clone_ref(py));

            // Create helper wrapper
            let helper = PyHelperDef { func: helper_fn };

            // Register helper
            self.registry.register_helper(name, Box::new(helper));
        });

        Ok(())
    }

    /// Unregisters a template with the given name.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the template
    ///
    /// # Returns
    ///
    /// `None`
    #[pyo3(text_signature = "($self, name)")]
    fn unregister_template(&mut self, name: &str) -> PyResult<()> {
        self.registry.unregister_template(name);
        Ok(())
    }

    /// Checks if a template with the given name exists.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the template
    ///
    /// # Returns
    ///
    /// Whether the template exists
    #[pyo3(text_signature = "($self, name)")]
    fn has_template(&self, name: &str) -> bool {
        self.registry.has_template(name)
    }

    /// Renders a template with the given data.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the template
    /// * `data` - The data to use for rendering (as a JSON string)
    ///
    /// # Returns
    ///
    /// The rendered template as a string
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be rendered
    #[pyo3(text_signature = "($self, name, data)")]
    fn render(&self, name: &str, data: &str) -> PyResult<String> {
        let data: Value = serde_json::from_str(data)
            .map_err(|e| PyValueError::new_err(format!("Invalid JSON data: {}", e)))?;

        self.registry
            .render(name, &data)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Renders a template string directly without registering.
    ///
    /// # Arguments
    ///
    /// * `template_string` - The template source code
    /// * `data` - The data to use for rendering (as a JSON string)
    ///
    /// # Returns
    ///
    /// The rendered template as a string
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be rendered
    #[pyo3(text_signature = "($self, template_string, data)")]
    fn render_template(&self, template_string: &str, data: &str) -> PyResult<String> {
        let data: Value = serde_json::from_str(data)
            .map_err(|e| PyValueError::new_err(format!("Invalid JSON data: {}", e)))?;

        self.registry
            .render_template(template_string, &data)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }
}
