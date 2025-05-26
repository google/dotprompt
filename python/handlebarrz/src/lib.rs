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

mod helpers;

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
    m.add_class::<HandlebarrzHelper>()?;
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

// Handlebars render context helper Python wrapper.
// WARNING: only intended to be used within the Python::with_gil(...) scope and not stored across threads.
#[pyclass(unsendable)]
pub struct HandlebarrzHelper {
    helper_ptr: *const Helper<'static>,
    reg_ptr: *const Handlebars<'static>,
    ctx_ptr: *const Context,
    rc_ptr: *mut RenderContext<'static, 'static>,
}

#[pymethods]
impl HandlebarrzHelper {
    #[new]
    fn new() -> Self {
        Self {
            helper_ptr: std::ptr::null(),
            reg_ptr: std::ptr::null(),
            ctx_ptr: std::ptr::null(),
            rc_ptr: std::ptr::null_mut(),
        }
    }

    // Returns JSON representation of a context.
    #[pyo3(text_signature = "($self)")]
    pub fn context_json(&self) -> PyResult<String> {
        let ctx = unsafe { &*self.ctx_ptr };
        return serde_json::to_string(ctx.data())
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()));
    }

    // Returns hash JSON value for a given key (resolved within the context).
    #[pyo3(text_signature = "($self, key)")]
    pub fn hash_value_json(&self, key: &str) -> PyResult<String> {
        let helper = unsafe { &*self.helper_ptr };
        if let Some(path_and_json) = helper.hash_get(key) {
            let value = path_and_json.value();
            return serde_json::to_string(value)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()));
        } else {
            return Ok(String::new());
        }
    }

    // Renders into a string and returns the default inner template (if the helper is a block helper).
    #[pyo3(text_signature = "($self)")]
    pub fn template(&self) -> PyResult<String> {
        let helper = unsafe { &*self.helper_ptr };
        let reg = unsafe { &*self.reg_ptr };
        let ctx = unsafe { &*self.ctx_ptr };
        let rc = unsafe { &mut *self.rc_ptr };

        if let Some(template) = helper.template() {
            template
                .renders(reg, ctx, rc)
                .map_err(|e| PyValueError::new_err(e.to_string()))
        } else {
            Ok(String::new())
        }
    }

    // Renders into a string and returns the template of else branch (if any).
    #[pyo3(text_signature = "($self)")]
    pub fn inverse(&self) -> PyResult<String> {
        let helper = unsafe { &*self.helper_ptr };
        let reg = unsafe { &*self.reg_ptr };
        let ctx = unsafe { &*self.ctx_ptr };
        let rc = unsafe { &mut *self.rc_ptr };

        if let Some(template) = helper.inverse() {
            template
                .renders(reg, ctx, rc)
                .map_err(|e| PyValueError::new_err(e.to_string()))
        } else {
            Ok(String::new())
        }
    }
}

/// Callable helper.
struct PyHelperDef {
    func: PyObject,
}

impl HelperDef for PyHelperDef {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        reg: &'reg Handlebars<'reg>,
        ctx: &'rc Context,
        rc: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> Result<(), RenderError> {
        Python::with_gil(|py| {
            // Extract params.
            let params: Vec<&Value> = h.params().iter().map(|p| p.value()).collect();
            let params_json = match serde_json::to_string(&params) {
                Ok(json) => json,
                Err(e) => {
                    let desc = format!("Failed to serialize params: {}", e);
                    return Err(RenderError::from(RenderErrorReason::Other(desc)));
                }
            };

            // Call Python function.
            let py_helper = HandlebarrzHelper {
                helper_ptr: h as *const _ as *const Helper<'static>,
                reg_ptr: reg as *const _ as *const Handlebars<'static>,
                ctx_ptr: ctx as *const _,
                rc_ptr: rc as *mut _ as *mut RenderContext<'static, 'static>,
            };
            let py_helper_obj = Py::new(py, py_helper).map_err(|e| {
                RenderError::from(RenderErrorReason::Other(format!(
                    "Failed to create HandlebarrzHelper: {}",
                    e
                )))
            })?;

            let result = self.func.call1(py, (params_json, py_helper_obj));

            match result {
                Ok(result) => {
                    let result_str = match result.extract::<String>(py) {
                        Ok(s) => s,
                        Err(e) => {
                            let desc = format!("Failed to extract result: {}", e);
                            return Err(RenderError::from(RenderErrorReason::Other(desc)));
                        }
                    };
                    out.write(&result_str)?;
                    Ok(())
                }
                Err(e) => {
                    let desc = format!("Helper execution failed: {}", e);
                    Err(RenderError::from(RenderErrorReason::Other(desc)))
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
                )));
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
    /// * `data_json` - The data to use for rendering (as JSON).
    /// * `options_json` - Optional. If provided, the data will be merged with this JSON object.
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be rendered.
    ///
    /// # Returns
    ///
    /// Rendered template as a string.
    #[pyo3(text_signature = "($self, template_string, data_json, options_json = None)")]
    fn render_template(
        &self,
        template_string: &str,
        data_json: &str,
        _options_json: Option<&str>,
    ) -> PyResult<String> {
        let data: Value = serde_json::from_str(data_json)
            .map_err(|e| PyValueError::new_err(format!("invalid JSON: {}", e)))?;

        // TODO: Implement setting the data attribute of runtime options.
        // if let Some(options_str) = options_json {
        //     let options_data: Value = serde_json::from_str(options_str)
        //         .map_err(|e| PyValueError::new_err(format!("invalid options JSON: {}", e)))?;

        //     if let (Some(data_map), Some(_options_map)) =
        //         (data.as_object_mut(), options_data.as_object())
        //     {
        //         data_map.insert("@data".to_string(), options_data.clone());
        //     }
        // }

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
            .register_helper("ifEquals", Box::new(helpers::IfEqualsHelper {}));
        self.registry
            .register_helper("unlessEquals", Box::new(helpers::UnlessEqualsHelper {}));
        self.registry
            .register_helper("json", Box::new(helpers::JsonHelper {}));
        Ok(())
    }
}
