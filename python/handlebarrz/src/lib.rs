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
    BlockContext, Context, Handlebars, Helper, HelperDef, Output, RenderContext, RenderError,
    RenderErrorReason, Renderable, ScopedJson, StringOutput, Template,
};
use pyo3::exceptions::{PyFileNotFoundError, PyValueError};
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

mod helpers;

const RUNTIME_PATH_HELPER: &str = "__handlebarrz_runtime_path";
const RUNTIME_SECTION_HELPER_PREFIX: &str = "__handlebarrz_runtime_section_";
const RUNTIME_INVERTED_SECTION_HELPER_PREFIX: &str = "__handlebarrz_runtime_inverted_section_";
const RUNTIME_ROOT_SENTINEL: &str = "__handlebarrz_runtime_root";

struct RuntimePathHelper;
struct DirectSectionHelper;

impl HelperDef for RuntimePathHelper {
    fn call_inner<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        _: &'reg Handlebars<'reg>,
        ctx: &'rc Context,
        rc: &mut RenderContext<'reg, 'rc>,
    ) -> Result<ScopedJson<'rc>, RenderError> {
        let raw = h
            .param(0)
            .and_then(|param| param.value().as_str())
            .ok_or_else(|| {
                RenderError::from(RenderErrorReason::Other(
                    "runtime path helper requires a path".to_owned(),
                ))
            })?;
        resolve_runtime_path(raw, ctx, rc)
    }
}

impl HelperDef for DirectSectionHelper {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        registry: &'reg Handlebars<'reg>,
        ctx: &'rc Context,
        rc: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> Result<(), RenderError> {
        let runtime_section = h
            .name()
            .strip_prefix(RUNTIME_SECTION_HELPER_PREFIX)
            .map(|encoded| (encoded, false))
            .or_else(|| {
                h.name()
                    .strip_prefix(RUNTIME_INVERTED_SECTION_HELPER_PREFIX)
                    .map(|encoded| (encoded, true))
            });
        let (value, inverted) = if let Some((encoded, inverted)) = runtime_section {
            let raw = decode_runtime_section_path(encoded)?;
            (resolve_runtime_path(&raw, ctx, rc)?, inverted)
        } else {
            (rc.evaluate(ctx, h.name())?, false)
        };

        render_direct_section(value.as_json(), inverted, h, registry, ctx, rc, out)
    }
}

fn encode_runtime_section_path(path: &str) -> String {
    path.as_bytes()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn decode_runtime_section_path(encoded: &str) -> Result<String, RenderError> {
    let bytes = encoded.as_bytes();
    if bytes.len() % 2 != 0 {
        return Err(RenderErrorReason::Other("invalid runtime section path".to_owned()).into());
    }
    let decoded = (0..bytes.len())
        .step_by(2)
        .map(|index| {
            std::str::from_utf8(&bytes[index..index + 2])
                .ok()
                .and_then(|pair| u8::from_str_radix(pair, 16).ok())
        })
        .collect::<Option<Vec<_>>>()
        .and_then(|value| String::from_utf8(value).ok())
        .ok_or_else(|| {
            RenderError::from(RenderErrorReason::Other(
                "invalid runtime section path".to_owned(),
            ))
        })?;
    Ok(decoded)
}

fn render_direct_section<'reg: 'rc, 'rc>(
    value: &Value,
    inverted: bool,
    h: &Helper<'rc>,
    registry: &'reg Handlebars<'reg>,
    ctx: &'rc Context,
    rc: &mut RenderContext<'reg, 'rc>,
    out: &mut dyn Output,
) -> Result<(), RenderError> {
    let truthy_template = if inverted { h.inverse() } else { h.template() };
    let falsey_template = if inverted { h.template() } else { h.inverse() };
    match value {
        Value::Null | Value::Bool(false) => {
            render_section_template(falsey_template, registry, ctx, rc, out)
        }
        Value::Bool(true) => render_section_template(truthy_template, registry, ctx, rc, out),
        Value::Array(values) if values.is_empty() => {
            render_section_template(falsey_template, registry, ctx, rc, out)
        }
        Value::Array(values) => {
            if inverted {
                return render_section_template(truthy_template, registry, ctx, rc, out);
            }
            for (index, item) in values.iter().enumerate() {
                let mut block = BlockContext::new();
                block.set_base_value(item.clone());
                block.set_local_var("index", Value::from(index));
                block.set_local_var("first", Value::Bool(index == 0));
                block.set_local_var("last", Value::Bool(index == values.len() - 1));
                rc.push_block(block);
                let result = render_section_template(truthy_template, registry, ctx, rc, out);
                rc.pop_block();
                result?;
            }
            Ok(())
        }
        _ => {
            let mut block = BlockContext::new();
            block.set_base_value(value.clone());
            rc.push_block(block);
            let result = render_section_template(truthy_template, registry, ctx, rc, out);
            rc.pop_block();
            result
        }
    }
}

fn render_section_template<'reg: 'rc, 'rc>(
    template: Option<&'rc Template>,
    registry: &'reg Handlebars<'reg>,
    ctx: &'rc Context,
    rc: &mut RenderContext<'reg, 'rc>,
    out: &mut dyn Output,
) -> Result<(), RenderError> {
    if let Some(template) = template {
        template.render(registry, ctx, rc, out)
    } else {
        Ok(())
    }
}

fn resolve_runtime_path<'reg: 'rc, 'rc>(
    raw: &str,
    ctx: &'rc Context,
    rc: &mut RenderContext<'reg, 'rc>,
) -> Result<ScopedJson<'rc>, RenderError> {
    let Some((minimum_level, local_path)) = split_runtime_path(raw) else {
        return Ok(ScopedJson::Missing);
    };
    let name_end = local_path.find(['.', '/', '[']).unwrap_or(local_path.len());
    let name = &local_path[..name_end];
    let suffix = &local_path[name_end..];

    for level in minimum_level.. {
        let prefix = format!("@{}", "../".repeat(level));
        let sentinel_path = format!("{prefix}{RUNTIME_ROOT_SENTINEL}");
        let at_runtime_root = !rc.evaluate(ctx, &sentinel_path)?.is_missing();
        let candidate_path = format!("{prefix}{name}");
        let candidate = rc.evaluate(ctx, &candidate_path)?;
        if !candidate.is_missing() {
            if suffix.is_empty() {
                return Ok(candidate);
            }
            return resolve_runtime_suffix(candidate.as_json(), suffix);
        }
        if at_runtime_root {
            break;
        }
    }

    Ok(ScopedJson::Missing)
}

fn split_runtime_path(mut raw: &str) -> Option<(usize, &str)> {
    let mut levels = 0;
    while let Some(rest) = raw.strip_prefix("../") {
        levels += 1;
        raw = rest;
    }
    raw = raw.strip_prefix('@')?;
    while let Some(rest) = raw.strip_prefix("../") {
        levels += 1;
        raw = rest;
    }
    Some((levels, raw))
}

fn resolve_runtime_suffix(value: &Value, suffix: &str) -> Result<ScopedJson<'static>, RenderError> {
    let path = suffix.trim_start_matches(['.', '/']);
    if path.is_empty() {
        return Ok(ScopedJson::Derived(value.clone()));
    }

    let context = Context::wraps(value.clone())?;
    let render_context = RenderContext::new(None);
    let resolved = render_context.evaluate(&context, path)?;
    if resolved.is_missing() {
        Ok(ScopedJson::Missing)
    } else {
        Ok(ScopedJson::Derived(resolved.as_json().clone()))
    }
}

fn is_runtime_path(token: &str) -> bool {
    let Some((_, local_path)) = split_runtime_path(token) else {
        return false;
    };
    let name_end = local_path.find(['.', '/', '[']).unwrap_or(local_path.len());
    !matches!(&local_path[..name_end], "root" | "partial-block")
}

fn is_at_root_path(token: &str) -> bool {
    let Some((_, local_path)) = split_runtime_path(token) else {
        return false;
    };
    let name_end = local_path.find(['.', '/', '[']).unwrap_or(local_path.len());
    &local_path[..name_end] == "root"
}

fn transform_expression(expression: &str) -> String {
    let mut output = String::with_capacity(expression.len());
    let chars: Vec<char> = expression.chars().collect();
    let mut index = 0;

    while index < chars.len() {
        let ch = chars[index];
        if ch == '"' || ch == '\'' {
            let quote = ch;
            output.push(ch);
            index += 1;
            while index < chars.len() {
                let current = chars[index];
                output.push(current);
                index += 1;
                if current == '\\' && index < chars.len() {
                    output.push(chars[index]);
                    index += 1;
                } else if current == quote {
                    break;
                }
            }
            continue;
        }

        if ch.is_whitespace() || matches!(ch, '(' | ')' | '=') {
            output.push(ch);
            index += 1;
            continue;
        }

        let start = index;
        let mut bracket_depth = 0;
        while index < chars.len() {
            let current = chars[index];
            if current == '[' {
                bracket_depth += 1;
            } else if current == ']' && bracket_depth > 0 {
                bracket_depth -= 1;
            }
            if bracket_depth == 0 && (current.is_whitespace() || matches!(current, '(' | ')' | '='))
            {
                break;
            }
            index += 1;
        }

        let token: String = chars[start..index].iter().collect();
        let leading_control_len = usize::from(token.starts_with('~'));
        let trailing_control_len = usize::from(token.ends_with('~'));
        if leading_control_len + trailing_control_len >= token.len() {
            output.push_str(&token);
            continue;
        }
        let controlled_path = &token[leading_control_len..token.len() - trailing_control_len];
        let sigil_len = controlled_path
            .chars()
            .take_while(|value| matches!(value, '#' | '^' | '&'))
            .map(char::len_utf8)
            .sum();
        let (sigil, path) = controlled_path.split_at(sigil_len);
        if is_runtime_path(path) {
            output.push_str(&token[..leading_control_len]);
            output.push_str(sigil);
            output.push('(');
            output.push_str(RUNTIME_PATH_HELPER);
            output.push(' ');
            output.push_str(
                &serde_json::to_string(path)
                    .expect("serializing a Rust string to JSON cannot fail"),
            );
            output.push(')');
            output.push_str(&token[token.len() - trailing_control_len..]);
        } else {
            output.push_str(&token);
        }
    }

    output
}

fn direct_runtime_section(expression: &str) -> Option<(char, &str, usize, usize)> {
    let bytes = expression.as_bytes();
    let mut marker = expression.len() - expression.trim_start().len();
    if bytes.get(marker) == Some(&b'~') {
        marker += 1;
    }
    let section_kind = *bytes.get(marker)? as char;
    if !matches!(section_kind, '#' | '^' | '/') {
        return None;
    }

    let path_start = marker + 1;
    let path_end = expression[path_start..]
        .find(|ch: char| ch.is_whitespace() || ch == '~')
        .map_or(expression.len(), |offset| path_start + offset);
    let path = &expression[path_start..path_end];
    if !is_runtime_path(path)
        || !expression[path_end..]
            .trim_matches(['~', ' ', '\t', '\r', '\n'])
            .is_empty()
    {
        return None;
    }
    Some((section_kind, path, marker, path_end))
}

fn lower_runtime_section(
    expression: &str,
    runtime_sections: &mut Vec<(String, String)>,
) -> Option<String> {
    let (section_kind, path, marker, path_end) = direct_runtime_section(expression)?;
    match section_kind {
        '#' | '^' => {
            let helper_prefix = if section_kind == '^' {
                RUNTIME_INVERTED_SECTION_HELPER_PREFIX
            } else {
                RUNTIME_SECTION_HELPER_PREFIX
            };
            let helper_name = format!("{helper_prefix}{}", encode_runtime_section_path(path));
            runtime_sections.push((path.to_owned(), helper_name.clone()));
            Some(format!(
                "{}#{}{}",
                &expression[..marker],
                helper_name,
                &expression[path_end..],
            ))
        }
        '/' if runtime_sections
            .last()
            .is_some_and(|(open, _)| open == path) =>
        {
            let (_, helper_name) = runtime_sections.pop()?;
            Some(format!(
                "{}/{}{}",
                &expression[..marker],
                helper_name,
                &expression[path_end..],
            ))
        }
        _ => None,
    }
}

fn find_tag_end(source: &str, mut index: usize, close: &str) -> Option<usize> {
    let bytes = source.as_bytes();
    let mut quote = None;
    while index < source.len() {
        let ch = bytes[index] as char;
        if let Some(current_quote) = quote {
            if ch == '\\' {
                index += 2;
                continue;
            }
            if ch == current_quote {
                quote = None;
            }
            index += 1;
            continue;
        }
        if ch == '"' || ch == '\'' {
            quote = Some(ch);
            index += 1;
            continue;
        }
        if source[index..].starts_with(close) {
            return Some(index);
        }
        index += 1;
    }
    None
}

fn transform_runtime_paths(source: &str) -> String {
    let mut output = String::with_capacity(source.len());
    let mut cursor = 0;
    let mut runtime_sections = Vec::new();

    while let Some(relative_start) = source[cursor..].find("{{") {
        let start = cursor + relative_start;
        output.push_str(&source[cursor..start]);

        if source[start..].starts_with("{{{{") {
            let Some(open_end) = source[start + 4..].find("}}}}") else {
                output.push_str(&source[start..]);
                return output;
            };
            let open_end = start + 4 + open_end;
            let raw_name = source[start + 4..open_end].trim().trim_start_matches('#');
            let close_tag = format!("{{{{/{raw_name}}}}}");
            let raw_content_start = open_end + 4;
            if let Some(close_offset) = source[raw_content_start..].find(&close_tag) {
                let raw_end = raw_content_start + close_offset + close_tag.len();
                output.push_str(&source[start..raw_end]);
                cursor = raw_end;
                continue;
            }
            output.push_str(&source[start..]);
            return output;
        }

        if source[start..].starts_with("{{!--") {
            let Some(close_offset) = source[start + 6..].find("--}}") else {
                output.push_str(&source[start..]);
                return output;
            };
            let end = start + 6 + close_offset + 4;
            output.push_str(&source[start..end]);
            cursor = end;
            continue;
        }

        let triple = source[start..].starts_with("{{{");
        let open_len = if triple { 3 } else { 2 };
        let close = if triple { "}}}" } else { "}}" };
        let content_start = start + open_len;
        let Some(content_end) = find_tag_end(source, content_start, close) else {
            output.push_str(&source[start..]);
            return output;
        };
        let expression = &source[content_start..content_end];
        if let Some(lowered) = lower_runtime_section(expression, &mut runtime_sections) {
            output.push_str(&source[start..content_start]);
            output.push_str(&lowered);
            output.push_str(close);
        } else if expression.trim_start().starts_with('!')
            || expression.trim_start().starts_with('/')
        {
            output.push_str(&source[start..content_end + close.len()]);
        } else {
            output.push_str(&source[start..content_start]);
            output.push_str(&transform_expression(expression));
            output.push_str(close);
        }
        cursor = content_end + close.len();
    }

    output.push_str(&source[cursor..]);
    output
}

fn expression_reads_at_root(expression: &str) -> bool {
    let chars: Vec<char> = expression.chars().collect();
    let mut index = 0;
    while index < chars.len() {
        let ch = chars[index];
        if ch == '"' || ch == '\'' {
            let quote = ch;
            index += 1;
            while index < chars.len() {
                let current = chars[index];
                index += 1;
                if current == '\\' && index < chars.len() {
                    index += 1;
                } else if current == quote {
                    break;
                }
            }
            continue;
        }
        if ch.is_whitespace() || matches!(ch, '(' | ')' | '=') {
            index += 1;
            continue;
        }
        let start = index;
        let mut bracket_depth = 0;
        while index < chars.len() {
            let current = chars[index];
            if current == '[' {
                bracket_depth += 1;
            } else if current == ']' && bracket_depth > 0 {
                bracket_depth -= 1;
            }
            if bracket_depth == 0 && (current.is_whitespace() || matches!(current, '(' | ')' | '='))
            {
                break;
            }
            index += 1;
        }
        let token: String = chars[start..index].iter().collect();
        let leading_control_len = usize::from(token.starts_with('~'));
        let trailing_control_len = usize::from(token.ends_with('~'));
        if leading_control_len + trailing_control_len >= token.len() {
            continue;
        }
        let controlled_path = &token[leading_control_len..token.len() - trailing_control_len];
        let sigil_len = controlled_path
            .chars()
            .take_while(|value| matches!(value, '#' | '^' | '&'))
            .map(char::len_utf8)
            .sum();
        let path = &controlled_path[sigil_len..];
        if is_at_root_path(path) {
            return true;
        }
    }
    false
}

fn partial_name_from_expression(expression: &str) -> Option<String> {
    let mut rest = expression.trim().trim_start_matches('~').trim_start();
    if let Some(stripped) = rest.strip_prefix('#') {
        rest = stripped.trim_start();
    }
    rest = rest.strip_prefix('>')?.trim_start_matches('~').trim_start();
    let name: String = rest
        .chars()
        .take_while(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '_' | '.' | '-'))
        .collect();
    if name.is_empty() { None } else { Some(name) }
}

fn visit_live_expressions(source: &str, mut visit: impl FnMut(&str)) {
    let mut cursor = 0;
    while let Some(relative_start) = source[cursor..].find("{{") {
        let start = cursor + relative_start;
        if source[start..].starts_with("{{{{") {
            let Some(open_end) = source[start + 4..].find("}}}}") else {
                return;
            };
            let open_end = start + 4 + open_end;
            let raw_name = source[start + 4..open_end].trim().trim_start_matches('#');
            let close_tag = format!("{{{{/{raw_name}}}}}");
            let raw_content_start = open_end + 4;
            if let Some(close_offset) = source[raw_content_start..].find(&close_tag) {
                cursor = raw_content_start + close_offset + close_tag.len();
                continue;
            }
            return;
        }
        if source[start..].starts_with("{{!--") {
            let Some(close_offset) = source[start + 6..].find("--}}") else {
                return;
            };
            cursor = start + 6 + close_offset + 4;
            continue;
        }
        let triple = source[start..].starts_with("{{{");
        let open_len = if triple { 3 } else { 2 };
        let close = if triple { "}}}" } else { "}}" };
        let content_start = start + open_len;
        let Some(content_end) = find_tag_end(source, content_start, close) else {
            return;
        };
        let expression = &source[content_start..content_end];
        if !(expression.trim_start().starts_with('!') || expression.trim_start().starts_with('/')) {
            visit(expression);
        }
        cursor = content_end + close.len();
    }
}

fn source_reads_at_root(source: &str) -> bool {
    let mut reads = false;
    visit_live_expressions(source, |expression| {
        if expression_reads_at_root(expression) {
            reads = true;
        }
    });
    reads
}

fn source_partial_names(source: &str) -> Vec<String> {
    let mut names = Vec::new();
    visit_live_expressions(source, |expression| {
        if let Some(name) = partial_name_from_expression(expression) {
            names.push(name);
        }
    });
    names
}

fn reachable_reads_at_root(entry_source: &str, sources: &HashMap<String, String>) -> bool {
    if source_reads_at_root(entry_source) {
        return true;
    }
    let mut pending = source_partial_names(entry_source);
    let mut seen = std::collections::HashSet::new();
    while let Some(name) = pending.pop() {
        if !seen.insert(name.clone()) {
            continue;
        }
        let Some(source) = sources.get(&name) else {
            continue;
        };
        if source_reads_at_root(source) {
            return true;
        }
        pending.extend(source_partial_names(source));
    }
    false
}

fn compile_template(
    name: Option<&str>,
    source: &str,
) -> Result<Template, handlebars::TemplateError> {
    let transformed = transform_runtime_paths(source);
    let mut template = Template::compile(&transformed)?;
    template.name = name.map(str::to_owned);
    Ok(template)
}

fn render_with_runtime(
    registry: &Handlebars<'static>,
    template: &Template,
    input: Value,
    runtime_data: Value,
    reads_at_root: bool,
) -> Result<String, RenderError> {
    let context = Context::wraps(input)?;
    let mut render_context = RenderContext::new(template.name.as_ref());
    if let Some(root) = render_context.block_mut() {
        root.set_local_var(RUNTIME_ROOT_SENTINEL, Value::Bool(true));
        if let Value::Object(values) = runtime_data {
            if reads_at_root && values.contains_key("root") {
                return Err(RenderError::from(RenderErrorReason::Other(
                    "runtime data key 'root' is reserved".to_owned(),
                )));
            }
            // @root is the input document. A leftover context "root" must not
            // become that token, and must not fail a prompt that never asked
            // for @root.
            for (name, value) in values {
                if name != "root" {
                    root.set_local_var(&name, value);
                }
            }
        }
    }
    render_context.register_local_helper(RUNTIME_PATH_HELPER, Box::new(RuntimePathHelper));
    let mut output = StringOutput::new();
    template.render(registry, &context, &mut render_context, &mut output)?;
    output.into_string().map_err(RenderError::from)
}

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
    m.add_class::<HandlebarrzHelperOptions>()?;
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

/// Handlebars helper options Python wrapper.
///
/// WARNING: only intended to be used within the Python::with_gil(...) scope and not stored across threads.
#[pyclass(unsendable)]
pub struct HandlebarrzHelperOptions {
    helper_ptr: *const Helper<'static>,
    reg_ptr: *const Handlebars<'static>,
    ctx_ptr: *const Context,
    rc_ptr: *mut RenderContext<'static, 'static>,
}

#[pymethods]
impl HandlebarrzHelperOptions {
    #[new]
    fn new() -> Self {
        Self {
            helper_ptr: std::ptr::null(),
            reg_ptr: std::ptr::null(),
            ctx_ptr: std::ptr::null(),
            rc_ptr: std::ptr::null_mut(),
        }
    }

    /// Returns JSON representation of a context.
    #[pyo3(text_signature = "($self)")]
    pub fn context_json(&self) -> PyResult<String> {
        let ctx = unsafe { &*self.ctx_ptr };
        serde_json::to_string(ctx.data())
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// Returns hash JSON value for a given key (resolved within the context).
    #[pyo3(text_signature = "($self, key)")]
    pub fn hash_value_json(&self, key: &str) -> PyResult<String> {
        let helper = unsafe { &*self.helper_ptr };
        if let Some(path_and_json) = helper.hash_get(key) {
            let value = path_and_json.value();
            serde_json::to_string(value)
                .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
        } else {
            Ok(String::new())
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
                    let desc = format!("Failed to serialize params: {e}");
                    return Err(RenderError::from(RenderErrorReason::Other(desc)));
                }
            };

            // Create template helper context.
            let py_options = HandlebarrzHelperOptions {
                helper_ptr: h as *const _ as *const _,
                reg_ptr: reg as *const _ as *const _,
                ctx_ptr: ctx as *const _,
                rc_ptr: rc as *mut _ as *mut _,
            };
            let py_options_obj = Py::new(py, py_options).map_err(|e| {
                RenderError::from(RenderErrorReason::Other(format!(
                    "Failed to create HandlebarrzHelperOptions: {e}"
                )))
            })?;

            // Call Python function.
            let result = self.func.call1(py, (params_json, py_options_obj));

            match result {
                Ok(result) => {
                    let result_str = match result.extract::<String>(py) {
                        Ok(s) => s,
                        Err(e) => {
                            let desc = format!("Failed to extract result: {e}");
                            return Err(RenderError::from(RenderErrorReason::Other(desc)));
                        }
                    };
                    out.write(&result_str)?;
                    Ok(())
                }
                Err(e) => {
                    let desc = format!("Helper execution failed: {e}");
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
    template_files: HashMap<String, PathBuf>,
    template_sources: HashMap<String, String>,
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
        let mut registry = Handlebars::new();
        registry.register_helper("blockHelperMissing", Box::new(DirectSectionHelper));

        Self {
            registry,
            py_helpers: HashMap::new(),
            template_files: HashMap::new(),
            template_sources: HashMap::new(),
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
                    "Unknown escape function: {escape_fn}"
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
        let template = compile_template(Some(name), template_string)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        self.registry.register_template(name, template);
        self.template_files.remove(name);
        self.template_sources
            .insert(name.to_owned(), template_string.to_owned());
        Ok(())
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
        let template = compile_template(Some(name), template_string)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        self.registry.register_template(name, template);
        self.template_sources
            .insert(name.to_owned(), template_string.to_owned());
        Ok(())
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
                "Template file not found: {file_path}"
            )));
        }

        let source = fs::read_to_string(path).map_err(|e| PyValueError::new_err(e.to_string()))?;
        let template = compile_template(Some(name), &source)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        self.registry.register_template(name, template);
        self.template_files.insert(name.to_owned(), path.to_owned());
        self.template_sources.insert(name.to_owned(), source);
        Ok(())
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
        self.template_files.remove(name);
        self.template_sources.remove(name);
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
    #[pyo3(text_signature = "($self, name, data, runtime_data)")]
    fn render(&self, name: &str, data: &str, runtime_data: &str) -> PyResult<String> {
        let data: Value = serde_json::from_str(data)
            .map_err(|e| PyValueError::new_err(format!("invalid JSON: {e}")))?;
        let runtime_data: Value = serde_json::from_str(runtime_data)
            .map_err(|e| PyValueError::new_err(format!("invalid runtime data JSON: {e}")))?;
        let reloaded;
        let mut reloaded_source = None;
        let template = if self.registry.dev_mode() {
            if let Some(path) = self.template_files.get(name) {
                let source =
                    fs::read_to_string(path).map_err(|e| PyValueError::new_err(e.to_string()))?;
                reloaded = compile_template(Some(name), &source)
                    .map_err(|e| PyValueError::new_err(e.to_string()))?;
                reloaded_source = Some(source);
                &reloaded
            } else {
                self.registry
                    .get_template(name)
                    .ok_or_else(|| PyValueError::new_err(format!("Template not found: {name}")))?
            }
        } else {
            self.registry
                .get_template(name)
                .ok_or_else(|| PyValueError::new_err(format!("Template not found: {name}")))?
        };
        let entry_source = reloaded_source
            .as_deref()
            .or_else(|| self.template_sources.get(name).map(String::as_str))
            .unwrap_or("");
        let reads_at_root = reachable_reads_at_root(entry_source, &self.template_sources);
        render_with_runtime(&self.registry, template, data, runtime_data, reads_at_root)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Renders a template string directly without registering.
    ///
    /// # Arguments
    ///
    /// * `template_string` - The template source code.
    /// * `data_json` - The data to use for rendering (as JSON).
    ///
    /// # Raises
    ///
    /// `PyValueError` if the template cannot be rendered.
    ///
    /// # Returns
    ///
    /// Rendered template as a string.
    #[pyo3(text_signature = "($self, template_string, data_json, runtime_data_json)")]
    fn render_template(
        &self,
        template_string: &str,
        data_json: &str,
        runtime_data_json: &str,
    ) -> PyResult<String> {
        let data: Value = serde_json::from_str(data_json)
            .map_err(|e| PyValueError::new_err(format!("invalid JSON: {e}")))?;
        let runtime_data: Value = serde_json::from_str(runtime_data_json)
            .map_err(|e| PyValueError::new_err(format!("invalid runtime data JSON: {e}")))?;
        let template = compile_template(None, template_string)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse template: {e}")))?;
        let reads_at_root = reachable_reads_at_root(template_string, &self.template_sources);
        render_with_runtime(&self.registry, &template, data, runtime_data, reads_at_root)
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
