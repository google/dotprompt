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

//! Picoschema to JSON Schema conversion.
//!
//! This module provides functionality to convert compact "picoschema" syntax
//! into full JSON Schema definitions.

use crate::error::{DotpromptError, Result};
use crate::types::JsonSchema;
use serde_json::json;

/// Converts a picoschema definition to JSON Schema.
///
/// Picoschema supports compact syntax like:
/// - `string`, `number`, `boolean`, `object`, `array`
/// - `string[]` for arrays of strings
/// - `{field: type, ...}` for objects
/// - `type | null` for nullable types
///
/// # Arguments
///
/// * `schema` - The picoschema as a JSON Value (can be string or object)
///
/// # Returns  
///
/// Returns a JSON Schema as a `JsonSchema`.
///
/// # Errors
///
/// Returns error if the picoschema syntax is invalid.
pub fn picoschema_to_json_schema(schema: &serde_json::Value) -> Result<JsonSchema> {
    // Handle object types
    if let Some(obj) = schema.as_object() {
        // If it's already JSON Schema with "type" or "properties", return as-is
        if obj.contains_key("type") || obj.contains_key("properties") {
            return Ok(schema.clone());
        }

        // Otherwise, convert field by field
        let mut properties = serde_json::Map::new();
        for (key, value) in obj {
            properties.insert(key.clone(), picoschema_to_json_schema(value)?);
        }
        return Ok(json!({
            "type": "object",
            "properties": properties
        }));
    }

    // If it's a string, parse the picoschema syntax
    if let Some(schema_str) = schema.as_str() {
        return parse_picoschema_string(schema_str);
    }

    Ok(schema.clone())
}

/// Parses a picoschema string into JSON Schema.
fn parse_picoschema_string(schema_str: &str) -> Result<JsonSchema> {
    let trimmed = schema_str.trim();

    // Handle array syntax: "type[]"
    if let Some(inner_type) = trimmed.strip_suffix("[]") {
        let items_schema = parse_picoschema_string(inner_type)?;
        return Ok(json!({
            "type": "array",
            "items": items_schema
        }));
    }

    // Handle union syntax: "type1 | type2"
    if trimmed.contains('|') {
        let types: Vec<_> = trimmed
            .split('|')
            .map(|s| parse_picoschema_string(s.trim()))
            .collect::<Result<Vec<_>>>()?;
        return Ok(json!({
            "anyOf": types
        }));
    }

    // Handle primitive types
    // Handle primitive types
    match trimmed {
        "string" | "number" | "integer" | "boolean" | "object" | "array" | "null" => {
            Ok(json!({"type": trimmed}))
        }
        _ => {
            // Unknown type, return as-is or error
            Err(DotpromptError::PicoschemaError(format!(
                "unknown picoschema type: {trimmed}"
            )))
        }
    }
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod tests {
    use super::*;

    #[test]
    fn test_primitive_types() {
        let schema =
            picoschema_to_json_schema(&json!("string")).expect("conversion should succeed");
        assert_eq!(schema["type"], "string");
    }

    #[test]
    fn test_array_syntax() {
        let schema =
            picoschema_to_json_schema(&json!("string[]")).expect("conversion should succeed");
        assert_eq!(schema["type"], "array");
        assert_eq!(schema["items"]["type"], "string");
    }

    #[test]
    fn test_union_syntax() {
        let schema =
            picoschema_to_json_schema(&json!("string | null")).expect("conversion should succeed");
        assert!(schema["anyOf"].is_array());
    }

    #[test]
    fn test_object_schema() {
        let input = json!({
            "name": "string",
            "age": "number"
        });
        let schema = picoschema_to_json_schema(&input).expect("conversion should succeed");
        assert_eq!(schema["type"], "object");
        assert!(schema["properties"].is_object());
    }
}
