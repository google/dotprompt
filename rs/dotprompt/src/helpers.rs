// Copyright 2026 Google LLC
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

//! Built-in Handlebars helpers for dotprompt.
//!
//! This module provides custom Handlebars helpers that enable dotprompt-specific
//! functionality like role markers, media references, and JSON serialization.

use handlebars::{Context, Handlebars, Helper, HelperResult, Output, RenderContext, Renderable};

/// Registers all built-in helpers with a Handlebars instance.
///
/// # Arguments
///
/// * `handlebars` - The Handlebars instance to register helpers with
pub fn register_builtin_helpers(handlebars: &mut Handlebars) {
    handlebars.register_helper("json", Box::new(json_helper));
    handlebars.register_helper("role", Box::new(role_helper));
    handlebars.register_helper("history", Box::new(history_helper));
    handlebars.register_helper("section", Box::new(section_helper));
    handlebars.register_helper("media", Box::new(media_helper));
    handlebars.register_helper("ifEquals", Box::new(if_equals_helper));
    handlebars.register_helper("unlessEquals", Box::new(unless_equals_helper));

    // Register @ prefix variable helpers
    // Note: Handlebars treats @var as private data, but we expose @state via local path
}

/// JSON serialization helper.
///
/// Converts a value to JSON string with optional indentation.
///
/// # Example
///
/// ```handlebars
/// {{json myObject}}
/// {{json myObject indent=2}}
/// ```
fn json_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let value = h.param(0).ok_or_else(|| {
        handlebars::RenderErrorReason::Other(
            "json helper requires at least one parameter".to_string(),
        )
    })?;

    let indent = h
        .hash_get("indent")
        .and_then(|v| v.value().as_u64())
        .unwrap_or(0);

    let json_str = if indent > 0 {
        serde_json::to_string_pretty(value.value()).map_err(|e| {
            handlebars::RenderErrorReason::Other(format!("JSON serialization failed: {e}"))
        })?
    } else {
        serde_json::to_string(value.value()).map_err(|e| {
            handlebars::RenderErrorReason::Other(format!("JSON serialization failed: {e}"))
        })?
    };

    out.write(&json_str)?;
    Ok(())
}

/// Role marker helper.
///
/// Creates a dotprompt role marker.
///
/// # Example
///
/// ```handlebars
/// {{role "system"}}
/// ```
fn role_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let role = h.param(0).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("role helper requires a role parameter".to_string())
    })?;

    let role_str = role
        .value()
        .as_str()
        .ok_or_else(|| handlebars::RenderErrorReason::Other("role must be a string".to_string()))?;

    out.write(&format!("<<<dotprompt:role:{role_str}>>>"))?;
    Ok(())
}

/// History marker helper.
///
/// Creates a dotprompt history placeholder.
///
/// # Example
///
/// ```handlebars
/// {{history}}
/// ```
fn history_helper(
    _: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    out.write("<<<dotprompt:history>>>")?;
    Ok(())
}

/// Section marker helper.
///
/// Creates a dotprompt section marker.
///
/// # Example
///
/// ```handlebars
/// {{section "examples"}}
/// ```
fn section_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let name = h.param(0).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("section helper requires a name parameter".to_string())
    })?;

    let name_str = name.value().as_str().ok_or_else(|| {
        handlebars::RenderErrorReason::Other("section name must be a string".to_string())
    })?;

    out.write(&format!("<<<dotprompt:section {name_str}>>>"))?;
    Ok(())
}

/// Media reference helper.
///
/// Creates a dotprompt media marker with URL and optional content type.
///
/// # Example
///
/// ```handlebars
/// {{media url="https://example.com/image.png"}}
/// {{media url="https://example.com/image.png" contentType="image/png"}}
/// ```
fn media_helper(
    h: &Helper,
    _: &Handlebars,
    _: &Context,
    _: &mut RenderContext,
    out: &mut dyn Output,
) -> HelperResult {
    let url = h.hash_get("url").ok_or_else(|| {
        handlebars::RenderErrorReason::Other("media helper requires url parameter".to_string())
    })?;

    let url_str = url
        .value()
        .as_str()
        .ok_or_else(|| handlebars::RenderErrorReason::Other("url must be a string".to_string()))?;

    let marker = if let Some(content_type) = h.hash_get("contentType") {
        let ct_str = content_type.value().as_str().ok_or_else(|| {
            handlebars::RenderErrorReason::Other("contentType must be a string".to_string())
        })?;
        format!("<<<dotprompt:media:url {url_str} {ct_str}>>>")
    } else {
        format!("<<<dotprompt:media:url {url_str}>>>")
    };

    out.write(&marker)?;
    Ok(())
}

/// Conditional equality block helper.
///
/// Renders content if two values are equal.
///
/// # Example
///
/// ```handlebars
/// {{#ifEquals value1 value2}}
///   They are equal!
/// {{else}}
///   Not equal.
/// {{/ifEquals}}
/// ```
fn if_equals_helper<'reg, 'rc>(
    h: &Helper<'rc>,
    hbs: &'reg Handlebars<'reg>,
    ctx: &'rc Context,
    rc: &mut RenderContext<'reg, 'rc>,
    out: &mut dyn Output,
) -> HelperResult {
    let param0 = h.param(0).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("ifEquals requires two parameters".to_string())
    })?;
    let param1 = h.param(1).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("ifEquals requires two parameters".to_string())
    })?;

    let are_equal = param0.value() == param1.value();

    let template_to_render = if are_equal { h.template() } else { h.inverse() };

    if let Some(template) = template_to_render {
        let rendered = template.renders(hbs, ctx, rc)?;
        out.write(&rendered)?;
    }

    Ok(())
}

/// Conditional inequality block helper.
///
/// Renders content if two values are not equal.
///
/// # Example
///
/// ```handlebars
/// {{#unlessEquals value1 value2}}
///   They are different!
/// {{else}}
///   They are equal.
/// {{/unlessEquals}}
/// ```
fn unless_equals_helper<'reg, 'rc>(
    h: &Helper<'rc>,
    hbs: &'reg Handlebars<'reg>,
    ctx: &'rc Context,
    rc: &mut RenderContext<'reg, 'rc>,
    out: &mut dyn Output,
) -> HelperResult {
    let param0 = h.param(0).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("unlessEquals requires two parameters".to_string())
    })?;
    let param1 = h.param(1).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("unlessEquals requires two parameters".to_string())
    })?;

    let are_equal = param0.value() == param1.value();

    let template_to_render = if are_equal { h.inverse() } else { h.template() };

    if let Some(template) = template_to_render {
        let rendered = template.renders(hbs, ctx, rc)?;
        out.write(&rendered)?;
    }

    Ok(())
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_json_helper() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json obj}}";
        let data = json!({"obj": {"foo": "bar"}});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert!(result.contains(r#""foo"#));
    }

    #[test]
    fn test_role_helper() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{role \"system\"}}";
        let result = hbs
            .render_template(template, &json!({}))
            .expect("render should succeed");
        assert_eq!(result, "<<<dotprompt:role:system>>>");
    }
}
