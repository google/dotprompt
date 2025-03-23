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

use handlebars::{
    Context, Handlebars, Helper, HelperDef, Output, RenderContext, RenderError, RenderErrorReason,
    Renderable,
};
use pyo3::exceptions::{PyFileNotFoundError, PyValueError};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use serde_json::Value;
use std::collections::HashMap;
use std::path::Path;

/// Python bindings for the handlebars-rust library.
///
/// This module provides Python access to the high-performance Handlebars-rust
/// implementation. Features includee:
///
/// - Context-based rendering.
/// - HTML escaping utilities.
/// - Strict mode and development mode.
/// - Template and helper function registration.
#[pymodule]
fn _native(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<HandlebarrzTemplate>()?;
    m.add_function(wrap_pyfunction!(html_escape, py)?)?;
    m.add_function(wrap_pyfunction!(no_escape, py)?)?;
    Ok(())
}

/// Escapes special HTML characters in a string to prevent XSS injection attacks
/// by converting the following characters to their corresponding HTML entities.
///
/// | Character | HTML Entity |
/// |-----------|-------------|
/// | `&`       | `&amp;`     |
/// | `<`       | `&lt;`      |
/// | `>`       | `&gt;`      |
/// | `"`       | `&quot;`    |
/// | `'`       | `&#x27;`    |
///
/// This function is used by default for all variable interpolations in
/// Handlebars templates (e.g., `{{var}}`), unless specifically bypassed with
/// triple braces (`{{{var}}}`) or the ampersand prefix (`{{&var}}`).
///
/// # Arguments
///
/// * `text` - String to be escaped.
///
/// # Returns
///
/// String with HTML special characters escaped.
#[pyfunction]
fn html_escape(text: &str) -> String {
    handlebars::html_escape(text)
}

/// Passes through a string without any escaping.
///
/// This function can be set as the escape function using `set_escape_fn()` when
/// HTML escaping is not desired for the entire template engine.  This is the
/// equivalent of the JS `SafeString` object.
///
/// # Arguments
///
/// * `text` - String to be returned without escaping.
///
/// # Returns
///
/// Unescaped string that was passed in.
#[pyfunction]
fn no_escape(text: &str) -> String {
    handlebars::no_escape(text)
}

/// Callable helper.
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
        Python::with_gil(|py| {
            // Extract params.
            let params: Vec<&Value> = h.params().iter().map(|p| p.value()).collect();
            let params_json = match serde_json::to_string(&params) {
                Ok(json) => json,
                Err(e) => {
                    let desc = format!("Failed to serialize params: {}", e);
                    return Err(RenderError::from(RenderErrorReason::Other(desc.into())));
                }
            };

            // Get hash.
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

            // Convert context to JSON.
            let ctx_json = match serde_json::to_string(ctx.data()) {
                Ok(json) => json,
                Err(e) => {
                    let desc = format!("Failed to serialize context: {}", e);
                    return Err(RenderError::from(RenderErrorReason::Other(desc.into())));
                }
            };

            // Call Python function.
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
/// This class provides methods for:
///
/// - registering templates
/// - registering partials
/// - registering helpers
/// - rendering with data
///
/// # Examples
///
/// ```python
/// import handlebarrz
///
/// # Create a new template native engine instance. In user-facing python
/// # code, please use the `Handlebars/Template` wrapper class.
/// engine = handlebarrz.HandlebarrzTemplate()
///
/// # Register template.
/// engine.register_template('my_template', '<p>{{name}}</p>')
///
/// # Render template with data.
/// data = {'name': 'John'}
/// result = engine.render('my_template', data)
/// print(result)              # Output: <p>John</p>
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
    /// A new `HandlebarrzTemplate` instance.
    #[new]
    fn new() -> Self {
        let registry = Handlebars::new();

        Self {
            registry,
            py_helpers: HashMap::new(),
        }
    }

    /// Sets the strict mode for the template engine.
    ///
    /// In strict mode, the engine raises an error if a template tries to access
    /// a non-existent variable or helper.
    ///
    /// # Arguments
    ///
    /// * `enabled` - Whether to enable strict mode.
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
    /// Whether strict mode is currently enabled.
    #[pyo3(text_signature = "($self)")]
    fn get_strict_mode(&self) -> bool {
        self.registry.strict_mode()
    }

    /// Sets the development mode for the template engine.
    ///
    /// In development mode, the engine will recompile templates on every
    /// render, which can be useful for development and debugging.
    ///
    /// # Arguments
    ///
    /// * `enabled` - Whether to enable development mode.
    ///
    /// # Returns
    ///
    /// `None`
    #[pyo3(text_signature = "($self, enabled)")]
    fn set_dev_mode(&mut self, enabled: bool) -> PyResult<()> {
        self.registry.set_dev_mode(enabled);
        Ok(())
    }

    /// Gets the development mode setting.
    ///
    /// # Returns
    ///
    /// Whether development mode is currently enabled.
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
    /// * `escape_fn` - The name of the escape function to use (either
    ///   "html_escape" or "no_escape").
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyValueError` if the specified escape function is not recognized.
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
    /// * `name` - Name of the template.
    /// * `template_string` - Template text.
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be registered.
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
    /// * `name` - The name of the partial.
    /// * `template_string` - The partial source code.
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyValueError` if the partial cannot be registered.
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
    /// * `name` - The name of the template.
    /// * `file_path` - The path to the template file.
    ///
    /// # Returns
    ///
    /// `None`
    ///
    /// # Raises
    ///
    /// `PyFileNotFoundError` if the template file does not exist.
    /// `PyValueError` if the template cannot be registered.
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
    /// * `name` - The name of the helper.
    /// * `helper_fn` - The Python function to use as the helper.
    ///
    /// # Returns
    ///
    /// `None`
    #[pyo3(text_signature = "($self, name, helper_fn)")]
    fn register_helper(&mut self, name: &str, helper_fn: PyObject) -> PyResult<()> {
        Python::with_gil(|py| {
            self.py_helpers
                .insert(name.to_string(), helper_fn.clone_ref(py));

            let helper = PyHelperDef { func: helper_fn };

            self.registry.register_helper(name, Box::new(helper));
        });

        Ok(())
    }

    /// Unregisters a template with the given name.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the template.
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
    /// * `name` - The name of the template.
    ///
    /// # Returns
    ///
    /// Whether the template exists.
    #[pyo3(text_signature = "($self, name)")]
    fn has_template(&self, name: &str) -> bool {
        self.registry.has_template(name)
    }

    /// Renders a template with the given data.
    ///
    /// # Arguments
    ///
    /// * `name` - The name of the template.
    /// * `data` - The data to use for rendering (as JSON).
    ///
    /// # Returns
    ///
    /// Rendered template as string.
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be rendered.
    #[pyo3(text_signature = "($self, name, data)")]
    fn render(&self, name: &str, data: &str) -> PyResult<String> {
        let data: Value = serde_json::from_str(data)
            .map_err(|e| PyValueError::new_err(format!("invalid JSON: {}", e)))?;

        self.registry
            .render(name, &data)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Renders a template string directly without registering.
    ///
    /// # Arguments
    ///
    /// * `template_string` - The template source code.
    /// * `data` - The data to use for rendering (as JSON).
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be rendered.
    ///
    /// # Returns
    ///
    /// Rendered template as a string.
    #[pyo3(text_signature = "($self, template_string, data)")]
    fn render_template(&self, template_string: &str, data: &str) -> PyResult<String> {
        let data: Value = serde_json::from_str(data)
            .map_err(|e| PyValueError::new_err(format!("invalid JSON: {}", e)))?;

        self.registry
            .render_template(template_string, &data)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Registers the extra helper functions.
    ///
    /// These helpers are not registered by default in the base template:
    ///
    /// - `ifEquals`
    /// - `unlessEquals`
    /// - `json`
    ///
    /// # Returns
    ///
    /// `None`
    #[pyo3(text_signature = "($self)")]
    fn register_extra_helpers(&mut self) -> PyResult<()> {
        self.registry
            .register_helper("ifEquals", Box::new(IF_EQUALS_HELPER));
        self.registry
            .register_helper("unlessEquals", Box::new(UNLESS_EQUALS_HELPER));
        self.registry.register_helper("json", Box::new(JSON_HELPER));
        Ok(())
    }
}

/// Helper for comparing equality between two values.
///
/// Renders the template block if `arg1` is equal to `arg2`.
/// Otherwise, it renders the inverse block (if provided).
///
/// ## Usage
///
/// ```handlebars
/// {{#ifEquals arg1 arg2}}
///   <p>arg1 is equal to arg2</p>
/// {{else}}
///   <p>arg1 is not equal to arg2</p>
/// {{/ifEquals}}
/// ```
///
/// ## Parameters
///
/// * `arg1`: The first argument to compare.
/// * `arg2`: The second argument to compare.
///
/// The helper renders the template block if `arg1` is equal to `arg2`.
/// Otherwise, it renders the inverse block (if provided).
#[derive(Clone, Copy, Debug)]
pub struct IfEqualsHelper {}

impl HelperDef for IfEqualsHelper {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        reg: &'reg Handlebars<'reg>,
        ctx: &'rc Context,
        rc: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> Result<(), RenderError> {
        let first = h.param(0).ok_or_else(|| {
            RenderError::from(RenderErrorReason::ParamNotFoundForIndex("ifEquals", 0))
        })?;
        let second = h.param(1).ok_or_else(|| {
            RenderError::from(RenderErrorReason::ParamNotFoundForIndex("ifEquals", 1))
        })?;

        if first.value() == second.value() {
            if let Some(template) = h.template() {
                template.render(reg, ctx, rc, out)?;
            }
        } else if let Some(template) = h.inverse() {
            template.render(reg, ctx, rc, out)?;
        }

        Ok(())
    }
}

/// Helper for comparing inequality between two values.
///
/// Renders the template block if `arg1` is not equal to `arg2`.
/// Otherwise, it renders the inverse block (if provided).
///
/// ## Usage
///
/// ```handlebars
/// {{#unlessEquals arg1 arg2}}
///   <p>arg1 is not equal to arg2</p>
/// {{else}}
///   <p>arg1 is equal to arg2</p>
/// {{/unlessEquals}}
/// ```
///
/// ## Parameters
///
/// * `arg1`: The first argument to compare.
/// * `arg2`: The second argument to compare.
///
/// The helper renders the template block if `arg1` is not equal to `arg2`.
/// Otherwise, it renders the inverse block (if provided).
#[derive(Clone, Copy, Debug)]
pub struct UnlessEqualsHelper {}

impl HelperDef for UnlessEqualsHelper {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        reg: &'reg Handlebars<'reg>,
        ctx: &'rc Context,
        rc: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> Result<(), RenderError> {
        let first = h.param(0).ok_or_else(|| {
            RenderError::from(RenderErrorReason::ParamNotFoundForIndex("unlessEquals", 0))
        })?;
        let second = h.param(1).ok_or_else(|| {
            RenderError::from(RenderErrorReason::ParamNotFoundForIndex("unlessEquals", 1))
        })?;

        if first.value() != second.value() {
            if let Some(template) = h.template() {
                template.render(reg, ctx, rc, out)?;
            }
        } else if let Some(template) = h.inverse() {
            template.render(reg, ctx, rc, out)?;
        }

        Ok(())
    }
}

/// Helper to serialize data to a JSON string.
///
/// ## Usage
///
/// ```handlebars
/// <script type="application/json">
///   {{json data indent=2}}
/// </script>
/// ```
///
/// ## Parameters
///
/// * `data`: The data to serialize to JSON.
///
/// ## Hash Arguments
///
/// * `indent`: Optional. If provided, the JSON output will be pretty-printed with the specified indent level (integer).
///             If not provided, the JSON output will be compact (no whitespace).
///
/// This helper is useful for embedding JSON data directly into templates,
/// for example, to pass configuration or data to client-side JavaScript code.
#[derive(Clone, Copy, Debug)]
pub struct JsonHelper {}

impl HelperDef for JsonHelper {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        _reg: &'reg Handlebars<'reg>,
        _ctx: &'rc Context,
        _rc: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> Result<(), RenderError> {
        let param = match h.param(0) {
            Some(p) => p.value(),
            None => {
                out.write("")?;
                return Ok(());
            }
        };

        let indent_param = h.hash_get("indent");
        let use_pretty = indent_param.is_some();
        let result = if use_pretty {
            serde_json::to_string_pretty(param)
        } else {
            serde_json::to_string(param)
        };
        let json_str = result.unwrap_or_else(|_| "{}".to_string());
        out.write(&json_str)?;
        Ok(())
    }
}

static IF_EQUALS_HELPER: IfEqualsHelper = IfEqualsHelper {};
static UNLESS_EQUALS_HELPER: UnlessEqualsHelper = UnlessEqualsHelper {};
static JSON_HELPER: JsonHelper = JsonHelper {};

#[cfg(test)]
mod tests {
    mod if_equals_tests {
        use super::super::*;
        use serde_json::json;

        #[test]
        fn with_true_condition_renders_main_block() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("ifEquals", Box::new(IF_EQUALS_HELPER));

            assert_eq!(
                handlebars
                    .render_template("{{#ifEquals 1 1}}yes{{else}}no{{/ifEquals}}", &json!({}))
                    .unwrap(),
                "yes"
            );
        }

        #[test]
        fn with_false_condition_renders_else_block() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("ifEquals", Box::new(IF_EQUALS_HELPER));

            assert_eq!(
                handlebars
                    .render_template("{{#ifEquals 1 2}}yes{{else}}no{{/ifEquals}}", &json!({}))
                    .unwrap(),
                "no"
            );
        }

        #[test]
        fn with_false_condition_and_no_else_renders_empty_string() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("ifEquals", Box::new(IF_EQUALS_HELPER));

            assert_eq!(
                handlebars
                    .render_template("{{#ifEquals 1 2}}yes{{/ifEquals}}", &json!({}))
                    .unwrap(),
                ""
            );
        }
    }

    mod unless_equals_tests {
        use super::super::*;
        use serde_json::json;

        #[test]
        fn with_false_condition_renders_main_block() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("unlessEquals", Box::new(UNLESS_EQUALS_HELPER));

            assert_eq!(
                handlebars
                    .render_template(
                        "{{#unlessEquals 1 2}}yes{{else}}no{{/unlessEquals}}",
                        &json!({})
                    )
                    .unwrap(),
                "yes"
            );
        }

        #[test]
        fn with_true_condition_renders_else_block() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("unlessEquals", Box::new(UNLESS_EQUALS_HELPER));

            assert_eq!(
                handlebars
                    .render_template(
                        "{{#unlessEquals 1 1}}yes{{else}}no{{/unlessEquals}}",
                        &json!({})
                    )
                    .unwrap(),
                "no"
            );
        }

        #[test]
        fn with_true_condition_and_no_else_renders_empty_string() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("unlessEquals", Box::new(UNLESS_EQUALS_HELPER));

            assert_eq!(
                handlebars
                    .render_template("{{#unlessEquals 1 1}}yes{{/unlessEquals}}", &json!({}))
                    .unwrap(),
                ""
            );
        }
    }

    mod json_tests {
        use super::super::*;
        use serde_json::json;

        #[test]
        fn renders_object_as_json() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("json", Box::new(JSON_HELPER));

            let data = json!({"a": 1, "b": 2});
            let rendered = handlebars.render_template("{{json this}}", &data).unwrap();
            assert_eq!(rendered, r#"{"a":1,"b":2}"#);
        }

        #[test]
        fn renders_object_with_indent() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("json", Box::new(JSON_HELPER));

            let data = json!({"a": 1, "b": 2});
            let rendered_indent = handlebars
                .render_template("{{json this indent=2}}", &data)
                .unwrap();
            assert!(rendered_indent.contains("\"a\": 1"));
            assert!(rendered_indent.contains("\"b\": 2"));
        }

        #[test]
        fn handles_empty_params() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("json", Box::new(JSON_HELPER));

            let rendered_empty_params = handlebars.render_template("{{json}}", &json!({})).unwrap();
            assert_eq!(rendered_empty_params, "");
        }

        #[test]
        fn renders_array_as_json() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("json", Box::new(JSON_HELPER));

            let array_data = json!([1, 2, 3]);
            let rendered_array = handlebars
                .render_template("{{json this}}", &array_data)
                .unwrap();
            assert_eq!(rendered_array, r#"[1,2,3]"#);
        }

        #[test]
        fn renders_array_with_indent() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("json", Box::new(JSON_HELPER));

            let array_data = json!([1, 2, 3]);
            let rendered_array_pretty = handlebars
                .render_template("{{json this indent=2}}", &array_data)
                .unwrap();
            assert!(rendered_array_pretty.contains("1,"));
            assert!(rendered_array_pretty.contains("2,"));
            assert!(rendered_array_pretty.contains("3"));
        }

        #[test]
        fn renders_empty_object() {
            let mut handlebars = Handlebars::new();
            handlebars.register_helper("json", Box::new(JSON_HELPER));

            let empty_map = json!({});
            let rendered_empty = handlebars
                .render_template("{{json this}}", &empty_map)
                .unwrap();
            assert_eq!(rendered_empty, "{}");
        }
    }
}
