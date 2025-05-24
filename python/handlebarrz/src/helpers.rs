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

#[cfg(test)]
mod if_equals_tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn with_true_condition_renders_main_block() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("ifEquals", Box::new(IfEqualsHelper {}));

        assert_eq!(
            handlebars
                .render_template("{{#ifEquals 1 1}}yes{{else}}no{{/ifEquals}}", &json!({}))
                .unwrap(),
            "yes"
        );
    }

    #[test]
    fn with_true_condition_renders_main_block_without_else_block() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("ifEquals", Box::new(IfEqualsHelper {}));

        assert_eq!(
            handlebars
                .render_template("{{#ifEquals 1 1}}yes{{/ifEquals}}", &json!({}))
                .unwrap(),
            "yes"
        );
    }

    #[test]
    fn with_false_condition_renders_else_block() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("ifEquals", Box::new(IfEqualsHelper {}));

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
        handlebars.register_helper("ifEquals", Box::new(IfEqualsHelper {}));

        assert_eq!(
            handlebars
                .render_template("{{#ifEquals 1 2}}yes{{/ifEquals}}", &json!({}))
                .unwrap(),
            ""
        );
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

#[cfg(test)]
mod unless_equals_tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn with_false_condition_renders_main_block() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("unlessEquals", Box::new(UnlessEqualsHelper {}));

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
    fn with_false_condition_renders_main_block_without_else_block() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("unlessEquals", Box::new(UnlessEqualsHelper {}));

        assert_eq!(
            handlebars
                .render_template("{{#unlessEquals 1 2}}yes{{/unlessEquals}}", &json!({}))
                .unwrap(),
            "yes"
        );
    }

    #[test]
    fn with_true_condition_renders_else_block() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("unlessEquals", Box::new(UnlessEqualsHelper {}));

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
        handlebars.register_helper("unlessEquals", Box::new(UnlessEqualsHelper {}));

        assert_eq!(
            handlebars
                .render_template("{{#unlessEquals 1 1}}yes{{/unlessEquals}}", &json!({}))
                .unwrap(),
            ""
        );
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
/// * `indent`: Optional. If provided, the JSON output will be pretty-printed
///   with the specified indent level (integer).  If not provided, the JSON
///   output will be compact (no whitespace).
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

#[cfg(test)]
mod json_tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn renders_object_as_json() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("json", Box::new(JsonHelper {}));

        let data = json!({"a": 1, "b": 2});
        let rendered = handlebars.render_template("{{json this}}", &data).unwrap();
        assert_eq!(rendered, r#"{"a":1,"b":2}"#);
    }

    #[test]
    fn renders_object_with_indent() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("json", Box::new(JsonHelper {}));

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
        handlebars.register_helper("json", Box::new(JsonHelper {}));

        let rendered_empty_params = handlebars.render_template("{{json}}", &json!({})).unwrap();
        assert_eq!(rendered_empty_params, "");
    }

    #[test]
    fn renders_array_as_json() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("json", Box::new(JsonHelper {}));

        let array_data = json!([1, 2, 3]);
        let rendered_array = handlebars
            .render_template("{{json this}}", &array_data)
            .unwrap();
        assert_eq!(rendered_array, r#"[1,2,3]"#);
    }

    #[test]
    fn renders_array_with_indent() {
        let mut handlebars = Handlebars::new();
        handlebars.register_helper("json", Box::new(JsonHelper {}));

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
        handlebars.register_helper("json", Box::new(JsonHelper {}));

        let empty_map = json!({});
        let rendered_empty = handlebars
            .render_template("{{json this}}", &empty_map)
            .unwrap();
        assert_eq!(rendered_empty, "{}");
    }
}
