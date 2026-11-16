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
//!
//! The marker helpers (`role`, `history`, `section`, `media`) emit nonce-bearing
//! markers (see the crate-private `markers` module). The nonce changes on every
//! render, so they are bound per render as local helpers on the
//! [`RenderContext`] by the crate-private `register_marker_helpers`, which
//! [`Dotprompt`](crate::Dotprompt) calls.
//! Local helpers take precedence over registry helpers and are visible inside
//! blocks (`#each`, `#with`, ...) and partials, which share the render context.
//!
//! ```text
//! Registry (shared)                    RenderContext (one per render)
//! +-------------------------------+    +----------------------------------+
//! | json, ifEquals, unlessEquals  |    | role, history, section, media    |
//! | role, history, section, media |    |   bound to this render's nonce   |
//! |   (unbound: always error)     |    |   (shadow the registry entries)  |
//! +-------------------------------+    +----------------------------------+
//! ```

use crate::markers::{MarkerNonce, format_marker};
use handlebars::{
    Context, Handlebars, Helper, HelperDef, HelperResult, Output, RenderContext, RenderErrorReason,
    Renderable,
};

/// Registers all built-in helpers with a Handlebars instance.
///
/// The marker helpers registered here are unbound: they fail when called, so a
/// template must be rendered through [`Dotprompt`](crate::Dotprompt), which
/// binds them to a per-render nonce, to emit markers the parser will trust.
///
/// # Arguments
///
/// * `handlebars` - The Handlebars instance to register helpers with
pub fn register_builtin_helpers(handlebars: &mut Handlebars) {
    handlebars.register_helper("json", Box::new(json_helper));
    for kind in MarkerKind::ALL {
        handlebars.register_helper(kind.name(), Box::new(MarkerHelper { kind, nonce: None }));
    }
    handlebars.register_helper("ifEquals", Box::new(if_equals_helper));
    handlebars.register_helper("unlessEquals", Box::new(unless_equals_helper));

    // Register @ prefix variable helpers
    // Note: Handlebars treats @var as private data, but we expose @state via local path
}

/// Binds the marker helpers (`role`, `history`, `section`, `media`) to `nonce`
/// for a single render.
///
/// They are registered as local helpers on `rc`, shadowing the unbound ones
/// from [`register_builtin_helpers`]. Pair this with
/// [`to_messages`](crate::parse::to_messages) using the same nonce.
///
/// Crate-private because callers would otherwise have to manage nonces and
/// the marker format themselves; see the unit tests for usage.
pub(crate) fn register_marker_helpers(rc: &mut RenderContext<'_, '_>, nonce: &MarkerNonce) {
    for kind in MarkerKind::ALL {
        let helper = MarkerHelper {
            kind,
            nonce: Some(nonce.clone()),
        };
        rc.register_local_helper(kind.name(), Box::new(helper));
    }
}

/// The helpers that emit in-band markers.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum MarkerKind {
    Role,
    History,
    Section,
    Media,
}

impl MarkerKind {
    const ALL: [Self; 4] = [Self::Role, Self::History, Self::Section, Self::Media];

    /// Template-facing helper name.
    const fn name(self) -> &'static str {
        match self {
            Self::Role => "role",
            Self::History => "history",
            Self::Section => "section",
            Self::Media => "media",
        }
    }
}

/// Error raised when a marker helper runs without a per-render nonce.
const UNBOUND_MARKER_HELPER_ERROR: &str =
    "dotprompt: marker helpers (role, history, section, media) must be rendered via Dotprompt";

/// A marker helper, optionally bound to a per-render nonce.
#[derive(Debug)]
struct MarkerHelper {
    kind: MarkerKind,
    /// `None` for the registry-level fallback, which always errors.
    nonce: Option<MarkerNonce>,
}

impl HelperDef for MarkerHelper {
    fn call<'reg: 'rc, 'rc>(
        &self,
        h: &Helper<'rc>,
        _: &'reg Handlebars<'reg>,
        _: &'rc Context,
        _: &mut RenderContext<'reg, 'rc>,
        out: &mut dyn Output,
    ) -> HelperResult {
        let nonce = self
            .nonce
            .as_ref()
            .ok_or_else(|| RenderErrorReason::Other(UNBOUND_MARKER_HELPER_ERROR.to_string()))?;
        let body = match self.kind {
            MarkerKind::Role => role_body(h)?,
            MarkerKind::History => "history".to_string(),
            MarkerKind::Section => section_body(h)?,
            MarkerKind::Media => media_body(h)?,
        };
        out.write(&format_marker(nonce, &body))?;
        Ok(())
    }
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
    use serde::Serialize;

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
        // Create custom formatter with specified indent (N spaces)
        // Note: indent values are always small (typically 2-4), so truncation is safe
        #[allow(clippy::cast_possible_truncation)]
        let indent_str = " ".repeat(indent as usize);
        let mut buf = Vec::new();
        let formatter = serde_json::ser::PrettyFormatter::with_indent(indent_str.as_bytes());
        let mut ser = serde_json::Serializer::with_formatter(&mut buf, formatter);
        value.value().serialize(&mut ser).map_err(|e| {
            handlebars::RenderErrorReason::Other(format!("JSON serialization failed: {e}"))
        })?;
        String::from_utf8(buf).map_err(|e| {
            handlebars::RenderErrorReason::Other(format!("UTF-8 conversion failed: {e}"))
        })?
    } else {
        serde_json::to_string(value.value()).map_err(|e| {
            handlebars::RenderErrorReason::Other(format!("JSON serialization failed: {e}"))
        })?
    };

    out.write(&json_str)?;
    Ok(())
}

/// Role marker body (`role:{name}`).
///
/// # Example
///
/// ```handlebars
/// {{role "system"}}
/// ```
fn role_body(h: &Helper) -> Result<String, RenderErrorReason> {
    let role = h.param(0).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("role helper requires a role parameter".to_string())
    })?;

    let role_str = role
        .value()
        .as_str()
        .ok_or_else(|| handlebars::RenderErrorReason::Other("role must be a string".to_string()))?;

    Ok(format!("role:{role_str}"))
}

/// Section marker body (`section {name}`).
///
/// # Example
///
/// ```handlebars
/// {{section "examples"}}
/// ```
fn section_body(h: &Helper) -> Result<String, RenderErrorReason> {
    let name = h.param(0).ok_or_else(|| {
        handlebars::RenderErrorReason::Other("section helper requires a name parameter".to_string())
    })?;

    let name_str = name.value().as_str().ok_or_else(|| {
        handlebars::RenderErrorReason::Other("section name must be a string".to_string())
    })?;

    Ok(format!("section {name_str}"))
}

/// Media marker body (`media:url {url} [{contentType}]`).
///
/// # Example
///
/// ```handlebars
/// {{media url="https://example.com/image.png"}}
/// {{media url="https://example.com/image.png" contentType="image/png"}}
/// ```
fn media_body(h: &Helper) -> Result<String, RenderErrorReason> {
    let url = h.hash_get("url").ok_or_else(|| {
        handlebars::RenderErrorReason::Other("media helper requires url parameter".to_string())
    })?;

    let url_str = url
        .value()
        .as_str()
        .ok_or_else(|| handlebars::RenderErrorReason::Other("url must be a string".to_string()))?;

    let body = if let Some(content_type) = h.hash_get("contentType") {
        let ct_str = content_type.value().as_str().ok_or_else(|| {
            handlebars::RenderErrorReason::Other("contentType must be a string".to_string())
        })?;
        format!("media:url {url_str} {ct_str}")
    } else {
        format!("media:url {url_str}")
    };

    Ok(body)
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

    // JSON helper tests

    #[test]
    fn test_json_helper_basic_object() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json obj}}";
        let data = json!({"obj": {"foo": "bar"}});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, r#"{"foo":"bar"}"#);
    }

    #[test]
    fn test_json_helper_with_2_space_indent() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json obj indent=2}}";
        let data = json!({"obj": {"test": true}});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        // Should have 2-space indentation and newlines
        assert!(result.contains('\n'));
        assert!(result.contains("  "));
        assert!(result.contains("\"test\""));
    }

    #[test]
    fn test_json_helper_with_4_space_indent() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json obj indent=4}}";
        let data = json!({"obj": {"test": true}});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        // Should have 4-space indentation
        assert!(result.contains("    "));
        assert!(result.contains('\n'));
    }

    #[test]
    fn test_json_helper_nested_objects() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json obj}}";
        let data = json!({"obj": {"outer": {"inner": {"value": 42}}}});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, r#"{"outer":{"inner":{"value":42}}}"#);
    }

    #[test]
    fn test_json_helper_array() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json arr}}";
        let data = json!({"arr": [1, 2, 3]});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "[1,2,3]");
    }

    #[test]
    fn test_json_helper_empty_object() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json obj}}";
        let data = json!({"obj": {}});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "{}");
    }

    #[test]
    fn test_json_helper_empty_array() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{json arr}}";
        let data = json!({"arr": []});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "[]");
    }

    // Marker helper tests

    const NONCE: &str = "0123456789abcdef0123456789abcdef";

    /// Renders `template` with the marker helpers bound to [`NONCE`].
    fn render_marker(hbs: &Handlebars, template: &str, data: &serde_json::Value) -> String {
        let nonce = MarkerNonce::parse(NONCE).expect("valid nonce");
        let template = handlebars::Template::compile(template).expect("template should compile");
        let ctx = Context::wraps(data).expect("context should wrap");
        let mut rc = RenderContext::new(None);
        register_marker_helpers(&mut rc, &nonce);
        template
            .renders(hbs, &ctx, &mut rc)
            .expect("render should succeed")
    }

    fn render_marker_simple(template: &str) -> String {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);
        render_marker(&hbs, template, &json!({}))
    }

    #[test]
    fn test_role_helper_system() {
        assert_eq!(
            render_marker_simple("{{role \"system\"}}"),
            format!("<<<dotprompt:{NONCE}:role:system>>>")
        );
    }

    #[test]
    fn test_role_helper_user() {
        assert_eq!(
            render_marker_simple("{{role \"user\"}}"),
            format!("<<<dotprompt:{NONCE}:role:user>>>")
        );
    }

    #[test]
    fn test_role_helper_model() {
        assert_eq!(
            render_marker_simple("{{role \"model\"}}"),
            format!("<<<dotprompt:{NONCE}:role:model>>>")
        );
    }

    #[test]
    fn test_history_helper() {
        assert_eq!(
            render_marker_simple("{{history}}"),
            format!("<<<dotprompt:{NONCE}:history>>>")
        );
    }

    #[test]
    fn test_section_helper() {
        assert_eq!(
            render_marker_simple("{{section \"examples\"}}"),
            format!("<<<dotprompt:{NONCE}:section examples>>>")
        );
    }

    #[test]
    fn test_media_helper_url_only() {
        assert_eq!(
            render_marker_simple(r#"{{media url="https://example.com/image.png"}}"#),
            format!("<<<dotprompt:{NONCE}:media:url https://example.com/image.png>>>")
        );
    }

    #[test]
    fn test_media_helper_url_and_content_type() {
        assert_eq!(
            render_marker_simple(
                r#"{{media url="https://example.com/image.png" contentType="image/png"}}"#,
            ),
            format!("<<<dotprompt:{NONCE}:media:url https://example.com/image.png image/png>>>")
        );
    }

    #[test]
    fn test_marker_helpers_are_bound_inside_blocks_and_partials() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);
        hbs.register_template_string("turn", "{{role this}}")
            .expect("partial should compile");
        let result = render_marker(
            &hbs,
            "{{#each roles}}{{> turn}}{{/each}}{{#with obj}}{{history}}{{/with}}",
            &json!({ "roles": ["user"], "obj": {"k": 1} }),
        );
        assert_eq!(
            result,
            format!("<<<dotprompt:{NONCE}:role:user>>><<<dotprompt:{NONCE}:history>>>")
        );
    }

    #[test]
    fn test_marker_helpers_fail_when_unbound() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);
        for template in [
            "{{role \"system\"}}",
            "{{history}}",
            "{{section \"output\"}}",
            r#"{{media url="https://example.com/a.png"}}"#,
        ] {
            assert!(
                hbs.render_template(template, &json!({})).is_err(),
                "{template} should fail without a bound nonce"
            );
        }
    }

    // ifEquals helper tests

    #[test]
    fn test_if_equals_equal_int_values() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{#ifEquals a b}}yes{{else}}no{{/ifEquals}}";
        let data = json!({"a": 1, "b": 1});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "yes");
    }

    #[test]
    fn test_if_equals_unequal_int_values() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{#ifEquals a b}}yes{{else}}no{{/ifEquals}}";
        let data = json!({"a": 1, "b": 2});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "no");
    }

    #[test]
    fn test_if_equals_equal_string_values() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{#ifEquals a b}}yes{{else}}no{{/ifEquals}}";
        let data = json!({"a": "test", "b": "test"});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "yes");
    }

    #[test]
    fn test_if_equals_type_safety_int_vs_string() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        // Test that 5 (int) != "5" (string) - strict type equality
        let template = "{{#ifEquals a b}}equal{{else}}not equal{{/ifEquals}}";
        let data = json!({"a": 5, "b": "5"});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "not equal");
    }

    #[test]
    fn test_if_equals_boolean_comparison() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{#ifEquals a b}}equal{{else}}not equal{{/ifEquals}}";

        // true == true
        let data = json!({"a": true, "b": true});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "equal");

        // true != false
        let data = json!({"a": true, "b": false});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "not equal");
    }

    #[test]
    fn test_if_equals_null_comparison() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{#ifEquals a b}}equal{{else}}not equal{{/ifEquals}}";

        // null == null
        let data = json!({"a": null, "b": null});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "equal");

        // null != 0
        let data = json!({"a": null, "b": 0});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "not equal");
    }

    // unlessEquals helper tests

    #[test]
    fn test_unless_equals_unequal_values() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{#unlessEquals a b}}yes{{else}}no{{/unlessEquals}}";
        let data = json!({"a": 1, "b": 2});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "yes");
    }

    #[test]
    fn test_unless_equals_equal_values() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        let template = "{{#unlessEquals a b}}yes{{else}}no{{/unlessEquals}}";
        let data = json!({"a": 1, "b": 1});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "no");
    }

    #[test]
    fn test_unless_equals_type_safety_int_vs_string() {
        let mut hbs = Handlebars::new();
        register_builtin_helpers(&mut hbs);

        // Test that 5 (int) != "5" (string) - strict type inequality
        let template = "{{#unlessEquals a b}}not equal{{else}}equal{{/unlessEquals}}";
        let data = json!({"a": 5, "b": "5"});
        let result = hbs
            .render_template(template, &data)
            .expect("render should succeed");
        assert_eq!(result, "not equal");
    }
}
