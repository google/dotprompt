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

//! Template parsing and frontmatter extraction.
//!
//! This module handles parsing dotprompt templates, extracting YAML frontmatter,
//! and converting rendered templates into Message arrays.

use crate::error::{DotpromptError, Result};
use crate::types::{
    DataArgument, MediaContent, MediaPart, Message, ParsedPrompt, Part, PendingPart,
    PromptMetadata, Role, TextPart,
};
use regex::Regex;
use std::collections::HashMap;
use std::sync::OnceLock;

/// Regex pattern for extracting YAML frontmatter.
static FRONTMATTER_RE: OnceLock<Regex> = OnceLock::new();

/// Regex for role and history markers.
static ROLE_AND_HISTORY_RE: OnceLock<Regex> = OnceLock::new();

/// Regex for media and section markers.
static MEDIA_AND_SECTION_RE: OnceLock<Regex> = OnceLock::new();

/// Role marker prefix in templates.
const ROLE_MARKER_PREFIX: &str = "<<<dotprompt:role:";
/// History marker prefix in templates.
const HISTORY_MARKER_PREFIX: &str = "<<<dotprompt:history";
/// Section marker prefix in templates.
const SECTION_MARKER_PREFIX: &str = "<<<dotprompt:section";
/// Media marker prefix in templates.
const MEDIA_MARKER_PREFIX: &str = "<<<dotprompt:media:url";

/// Gets or initializes the frontmatter regex pattern.
#[allow(clippy::expect_used)]
fn frontmatter_regex() -> &'static Regex {
    FRONTMATTER_RE.get_or_init(|| {
        Regex::new(
            r"(?s)^---\s*(?:\r\n|\r|\n)([\s\S]*?)(?:\r\n|\r|\n)---\s*(?:\r\n|\r|\n)([\s\S]*)$",
        )
        .expect("failed to compile frontmatter regex")
    })
}

/// Gets or initializes the role and history marker regex.
#[allow(clippy::expect_used)]
fn role_and_history_regex() -> &'static Regex {
    ROLE_AND_HISTORY_RE.get_or_init(|| {
        Regex::new(r"(<<<dotprompt:(?:role:[a-z]+|history))>>>")
            .expect("failed to compile role/history regex")
    })
}

/// Gets or initializes the media and section marker regex.
#[allow(clippy::expect_used)]
fn media_and_section_regex() -> &'static Regex {
    MEDIA_AND_SECTION_RE.get_or_init(|| {
        Regex::new(r"(<<<dotprompt:(?:media:url|section).*?)>>>")
            .expect("failed to compile media/section regex")
    })
}

/// Extracts YAML frontmatter and template body from source.
///
/// # Arguments
///
/// * `source` - The template source string including frontmatter
///
/// # Returns
///
/// Returns `(frontmatter_yaml, template_body)` tuple.
///
/// # Errors
///
/// Returns error if the format is invalid.
pub fn extract_frontmatter_and_body(source: &str) -> Result<(String, String)> {
    let re = frontmatter_regex();

    if let Some(captures) = re.captures(source) {
        let yaml = captures
            .get(1)
            .ok_or_else(|| DotpromptError::InvalidFormat("missing frontmatter".to_string()))?
            .as_str()
            .to_string();
        // Trim template body when there's frontmatter (matches JS behavior)
        let template = captures
            .get(2)
            .ok_or_else(|| DotpromptError::InvalidFormat("missing template body".to_string()))?
            .as_str()
            .trim()
            .to_string();
        Ok((yaml, template))
    } else {
        // No frontmatter, do NOT trim (matches JS behavior)
        Ok((String::new(), source.to_string()))
    }
}

/// Parses a dotprompt document into structured metadata and template.
///
/// # Arguments
///
/// * `source` - The complete dotprompt source including frontmatter
///
/// # Returns
///
/// Returns a `ParsedPrompt` with extracted metadata and template.
///
/// # Errors
///
/// Returns error if YAML parsing fails or format is invalid.
pub fn parse_document<M>(source: &str) -> Result<ParsedPrompt<M>>
where
    M: serde::de::DeserializeOwned + Default,
{
    let (yaml, template) = extract_frontmatter_and_body(source)?;

    let metadata: PromptMetadata<M> = if yaml.is_empty() {
        PromptMetadata::default()
    } else {
        serde_yaml::from_str(&yaml)?
    };

    Ok(ParsedPrompt { metadata, template })
}

/// Splits a string by a regex, keeping the matched delimiters.
#[allow(clippy::unwrap_used)]
fn split_by_regex(source: &str, regex: &Regex) -> Vec<String> {
    let mut result = Vec::new();
    let mut last_end = 0;

    for cap in regex.captures_iter(source) {
        let full_match = cap.get(0).unwrap();
        let delimiter = cap.get(1).unwrap();

        // Add the text before the match if non-empty
        let before = &source[last_end..full_match.start()];
        if !before.trim().is_empty() {
            result.push(before.to_string());
        }

        // Add the captured delimiter (without the trailing >>>)
        result.push(delimiter.as_str().to_string());

        last_end = full_match.end();
    }

    // Add any remaining text after the last match
    let remaining = &source[last_end..];
    if !remaining.trim().is_empty() {
        result.push(remaining.to_string());
    }

    result
}

/// Splits by role and history markers.
fn split_by_role_and_history_markers(rendered_string: &str) -> Vec<String> {
    split_by_regex(rendered_string, role_and_history_regex())
}

/// Splits by media and section markers.
fn split_by_media_and_section_markers(source: &str) -> Vec<String> {
    split_by_regex(source, media_and_section_regex())
}

/// Parses a single piece into a Part.
fn parse_part(piece: &str) -> Part {
    if piece.starts_with(MEDIA_MARKER_PREFIX) {
        parse_media_part(piece)
    } else if piece.starts_with(SECTION_MARKER_PREFIX) {
        parse_section_part(piece)
    } else {
        Part::Text(TextPart {
            text: piece.to_string(),
            metadata: None,
        })
    }
}

/// Parses a media marker into a `MediaPart`.
fn parse_media_part(piece: &str) -> Part {
    // Format: "<<<dotprompt:media:url URL [CONTENT_TYPE]"
    let content = piece.strip_prefix(MEDIA_MARKER_PREFIX).unwrap_or(piece);
    let parts: Vec<&str> = content.split_whitespace().collect();

    let url = parts.first().unwrap_or(&"").to_string();
    let content_type = parts.get(1).map(std::string::ToString::to_string);

    Part::Media(MediaPart {
        media: MediaContent { url, content_type },
        metadata: None,
    })
}

/// Parses a section marker into a `PendingPart`.
fn parse_section_part(piece: &str) -> Part {
    // Format: "<<<dotprompt:section SECTION_TYPE"
    let content = piece.strip_prefix(SECTION_MARKER_PREFIX).unwrap_or(piece);
    let section_type = content.trim().to_string();

    let mut metadata = HashMap::new();
    metadata.insert(
        "purpose".to_string(),
        serde_json::Value::String(section_type),
    );
    metadata.insert("pending".to_string(), serde_json::Value::Bool(true));

    Part::Pending(PendingPart { metadata })
}

/// Converts source string into Parts (handling media and section markers).
fn to_parts(source: &str) -> Vec<Part> {
    split_by_media_and_section_markers(source)
        .iter()
        .map(|s| parse_part(s))
        .collect()
}

/// A message source during parsing.
struct MessageSource {
    role: Role,
    source: String,
    content: Option<Vec<Part>>,
    metadata: Option<HashMap<String, serde_json::Value>>,
}

impl MessageSource {
    const fn new(role: Role) -> Self {
        Self {
            role,
            source: String::new(),
            content: None,
            metadata: None,
        }
    }

    fn has_content(&self) -> bool {
        !self.source.trim().is_empty() || self.content.is_some()
    }
}

/// Transforms messages to history by adding purpose metadata.
fn transform_messages_to_history(messages: &[Message]) -> Vec<Message> {
    messages
        .iter()
        .map(|m| {
            let mut metadata = m.metadata.clone().unwrap_or_default();
            metadata.insert(
                "purpose".to_string(),
                serde_json::Value::String("history".to_string()),
            );
            Message {
                role: m.role,
                content: m.content.clone(),
                metadata: Some(metadata),
            }
        })
        .collect()
}

/// Checks if any message has history metadata.
fn messages_have_history(messages: &[Message]) -> bool {
    messages.iter().any(|m| {
        m.metadata
            .as_ref()
            .is_some_and(|meta| meta.get("purpose").is_some_and(|v| v == "history"))
    })
}

/// Inserts history messages at the appropriate position, adding purpose metadata.
fn insert_history(messages: Vec<Message>, history: Option<&Vec<Message>>) -> Vec<Message> {
    let history = match history {
        Some(h) if !h.is_empty() => h,
        _ => return messages,
    };

    // If messages already contain history, return as-is
    if messages_have_history(&messages) {
        return messages;
    }

    // If no messages, return history (without adding metadata for implicit insertion)
    if messages.is_empty() {
        return history.clone();
    }

    // If last message is user, insert history before it
    #[allow(clippy::collapsible_if)]
    if let Some(last) = messages.last() {
        if last.role == Role::User {
            let mut result: Vec<Message> = messages[..messages.len() - 1].to_vec();
            result.extend(history.iter().cloned());
            result.push(last.clone());
            return result;
        }
    }

    // Otherwise append history
    let mut result = messages;
    result.extend(history.iter().cloned());
    result
}

/// Converts message sources to Messages.
fn message_sources_to_messages(sources: Vec<MessageSource>) -> Vec<Message> {
    sources
        .into_iter()
        .filter(MessageSource::has_content)
        .map(|ms| {
            let content = ms.content.unwrap_or_else(|| to_parts(&ms.source));
            Message {
                role: ms.role,
                content,
                metadata: ms.metadata,
            }
        })
        .collect()
}

/// Converts a rendered template string into an array of Messages.
///
/// This function processes role markers and splits content accordingly.
///
/// # Arguments
///
/// * `rendered_string` - The rendered template output
/// * `data` - Optional data argument containing history messages
///
/// # Returns
///
/// Returns a vector of `Message` objects.
#[must_use]
pub fn to_messages<V>(rendered_string: &str, data: Option<&DataArgument<V>>) -> Vec<Message>
where
    V: serde::Serialize + Default,
{
    let mut current_message = MessageSource::new(Role::User);
    let mut message_sources: Vec<MessageSource> = Vec::new();

    for piece in split_by_role_and_history_markers(rendered_string) {
        if piece.starts_with(ROLE_MARKER_PREFIX) {
            // Parse role from marker
            let role_str = piece.strip_prefix(ROLE_MARKER_PREFIX).unwrap_or("user");
            let role = match role_str {
                "model" => Role::Model,
                "tool" => Role::Tool,
                "system" => Role::System,
                // "user" and anything else -> Role::User
                _ => Role::User,
            };

            if current_message.source.trim().is_empty() {
                // Update role of current message
                current_message.role = role;
            } else {
                // Save current and start new
                message_sources.push(current_message);
                current_message = MessageSource::new(role);
            }
        } else if piece.starts_with(HISTORY_MARKER_PREFIX) {
            // Save current message if it has content
            if !current_message.source.trim().is_empty() {
                message_sources.push(current_message);
            }

            // Add history messages
            #[allow(clippy::collapsible_if)]
            if let Some(data_arg) = data {
                if let Some(history) = &data_arg.messages {
                    for msg in transform_messages_to_history(history) {
                        message_sources.push(MessageSource {
                            role: msg.role,
                            source: String::new(),
                            content: Some(msg.content),
                            metadata: msg.metadata,
                        });
                    }
                }
            }

            // Start new message for content after history
            current_message = MessageSource::new(Role::Model);
        } else {
            // Regular content
            current_message.source.push_str(&piece);
        }
    }

    // Push final message
    message_sources.push(current_message);

    let messages = message_sources_to_messages(message_sources);

    // Insert history if not already present
    let history = data.and_then(|d| d.messages.as_ref());
    insert_history(messages, history)
}

#[cfg(test)]
#[allow(clippy::expect_used)] // Tests can use expect() for clarity
mod tests {
    use super::*;

    #[test]
    fn test_extract_frontmatter_and_body() {
        let source = "---\nmodel: gemini-pro\n---\nHello {{name}}!";
        let (yaml, template) = extract_frontmatter_and_body(source).expect("parse should succeed");
        assert!(yaml.contains("model: gemini-pro"));
        assert_eq!(template, "Hello {{name}}!");
    }

    #[test]
    fn test_extract_no_frontmatter() {
        let source = "Hello {{name}}!";
        let (yaml, template) = extract_frontmatter_and_body(source).expect("parse should succeed");
        assert_eq!(yaml, "");
        assert_eq!(template, "Hello {{name}}!");
    }

    #[test]
    fn test_parse_document() {
        let source = "---\nmodel: gemini-pro\n---\nHello!";
        let parsed: ParsedPrompt = parse_document(source).expect("parse should succeed");
        assert_eq!(parsed.metadata.model, Some("gemini-pro".to_string()));
        assert_eq!(parsed.template, "Hello!");
    }

    #[test]
    fn test_to_messages_simple() {
        let rendered = "Hello world!";
        let messages = to_messages::<serde_json::Value>(rendered, None);
        assert_eq!(messages.len(), 1);
        assert_eq!(messages[0].role, Role::User);
    }

    #[test]
    fn test_to_messages_with_roles() {
        let rendered = "<<<dotprompt:role:user>>>Hello\n<<<dotprompt:role:model>>>Hi there!";
        let messages = to_messages::<serde_json::Value>(rendered, None);
        assert_eq!(messages.len(), 2);
        assert_eq!(messages[0].role, Role::User);
        assert_eq!(messages[1].role, Role::Model);
    }

    #[test]
    fn test_to_messages_with_media() {
        let rendered = "<<<dotprompt:media:url http://example.com/img.jpg image/jpeg>>>";
        let messages = to_messages::<serde_json::Value>(rendered, None);
        assert_eq!(messages.len(), 1);
        assert!(matches!(messages[0].content[0], Part::Media(_)));
    }
}
