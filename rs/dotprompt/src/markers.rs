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

//! In-band markers used to turn a rendered template string into messages.
//!
//! The `role`, `history`, `section` and `media` helpers emit markers into the
//! rendered string, which is then split back apart by
//! [`to_messages`](crate::parse::to_messages). Because the rendered string also
//! contains user-supplied variable values verbatim, every marker carries a
//! random per-render nonce and the splitter only honors markers with that
//! nonce. Anything else that merely looks like a marker (e.g. typed by an end
//! user) stays plain text.
//!
//! Marker format: `<<<dotprompt:{nonce}:{body}>>>`, where body is one of
//! `role:{name}`, `history`, `section {name}`, `media:url {url} [{contentType}]`.
//!
//! ```text
//! template --render(nonce)--> "<<<dotprompt:{nonce}:role:system>>>Q: {user value}"
//!                                            |
//!                         split_by_markers(regex built for nonce)
//!                                            v
//!                     [Marker("role:system"), Text("Q: {user value}")]
//! ```
//!
//! | Item                 | Purpose                                         |
//! |----------------------|-------------------------------------------------|
//! | [`MarkerNonce`]      | Validated 128-bit hex nonce, fresh per render   |
//! | [`format_marker`]    | Builds a marker string (used by the helpers)    |
//! | [`split_by_markers`] | Splits rendered output into text/marker pieces  |
//!
//! The helpers receive the nonce per render via
//! [`register_marker_helpers`](crate::helpers::register_marker_helpers), not
//! through the template data, so nothing in the input or context can set it.

use crate::error::{DotpromptError, Result};
use regex::Regex;

/// Number of random bytes in a nonce (128 bits).
const NONCE_BYTES: usize = 16;

/// A validated marker nonce: exactly 32 lowercase hex characters.
///
/// The nonce is interpolated into a regex, so the only ways to obtain one are
/// [`MarkerNonce::generate`] and [`MarkerNonce::parse`], both of which
/// guarantee the format.
///
/// # Examples
///
/// ```
/// use dotprompt::markers::MarkerNonce;
///
/// # fn example() -> dotprompt::Result<()> {
/// let nonce = MarkerNonce::generate()?;
/// assert_eq!(nonce.as_str().len(), 32);
/// assert!(MarkerNonce::parse(nonce.as_str()).is_ok());
/// assert!(MarkerNonce::parse(".*").is_err());
/// # Ok(())
/// # }
/// # example().unwrap();
/// ```
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct MarkerNonce(String);

impl MarkerNonce {
    /// Generates a fresh nonce from the operating system CSPRNG. Call once per
    /// render.
    ///
    /// # Errors
    ///
    /// Returns [`DotpromptError::RenderError`] if the OS random source fails.
    pub fn generate() -> Result<Self> {
        let mut bytes = [0u8; NONCE_BYTES];
        getrandom::fill(&mut bytes).map_err(|e| {
            DotpromptError::RenderError(format!("failed to generate marker nonce: {e}"))
        })?;
        // `hex::encode` emits lowercase, matching the validated format.
        Ok(Self(hex::encode(bytes)))
    }

    /// Parses and validates an existing nonce string.
    ///
    /// # Errors
    ///
    /// Returns [`DotpromptError::InvalidFormat`] unless `s` is exactly 32
    /// lowercase hex characters.
    pub fn parse(s: &str) -> Result<Self> {
        let valid =
            s.len() == NONCE_BYTES * 2 && s.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'));
        if valid {
            Ok(Self(s.to_string()))
        } else {
            Err(DotpromptError::InvalidFormat(
                "invalid marker nonce".to_string(),
            ))
        }
    }

    /// Returns the nonce as a string slice.
    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// Formats a marker with the given nonce and body.
///
/// # Examples
///
/// ```
/// use dotprompt::markers::{MarkerNonce, format_marker};
///
/// # fn example() -> dotprompt::Result<()> {
/// let nonce = MarkerNonce::parse("0123456789abcdef0123456789abcdef")?;
/// assert_eq!(
///     format_marker(&nonce, "role:user"),
///     "<<<dotprompt:0123456789abcdef0123456789abcdef:role:user>>>"
/// );
/// # Ok(())
/// # }
/// # example().unwrap();
/// ```
#[must_use]
pub fn format_marker(nonce: &MarkerNonce, body: &str) -> String {
    format!("<<<dotprompt:{}:{body}>>>", nonce.as_str())
}

/// Compiles a marker regex for a validated nonce.
#[allow(clippy::expect_used)]
fn marker_regex(nonce: &MarkerNonce, body_pattern: &str) -> Regex {
    // The nonce is guaranteed to be lowercase hex and `body_pattern` is one of
    // the constant patterns below, so compilation cannot fail.
    let pattern = format!("<<<dotprompt:{}:({body_pattern})>>>", nonce.as_str());
    Regex::new(&pattern).expect("marker regex should compile for a validated nonce")
}

/// Builds a regex matching role and history markers for the given nonce.
///
/// The single capture group is the marker body (`role:user`, `history`). Only
/// lowercase letters are allowed in role names.
#[must_use]
pub fn role_and_history_marker_regex(nonce: &MarkerNonce) -> Regex {
    marker_regex(nonce, "role:[a-z]+|history")
}

/// Builds a regex matching media and section markers for the given nonce.
///
/// The single capture group is the marker body
/// (`media:url https://... image/png`, `section code`).
#[must_use]
pub fn media_and_section_marker_regex(nonce: &MarkerNonce) -> Regex {
    marker_regex(nonce, "(?:media:url|section) .*?")
}

/// A piece of a rendered string: either literal text or a trusted marker.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MarkerPiece<'a> {
    /// Literal text, including anything that merely looks like a marker.
    Text(&'a str),
    /// The body of a marker carrying the expected nonce (e.g. `role:user`).
    Marker(&'a str),
}

/// Splits `source` on markers matched by `regex`, which must have exactly one
/// capture group (the marker body), as returned by
/// [`role_and_history_marker_regex`] and [`media_and_section_marker_regex`].
///
/// Pieces are classified by position rather than content: the spans between
/// matches are text and the capture of each match is a marker. A text piece
/// may itself look like a marker; it still stays text. Whitespace-only text
/// pieces are dropped.
///
/// # Examples
///
/// ```
/// use dotprompt::markers::{
///     MarkerNonce, MarkerPiece, format_marker, role_and_history_marker_regex, split_by_markers,
/// };
///
/// # fn example() -> dotprompt::Result<()> {
/// let nonce = MarkerNonce::generate()?;
/// let source = format!("{}Hi <<<dotprompt:role:system>>>", format_marker(&nonce, "role:user"));
/// assert_eq!(
///     split_by_markers(&source, &role_and_history_marker_regex(&nonce)),
///     vec![
///         MarkerPiece::Marker("role:user"),
///         MarkerPiece::Text("Hi <<<dotprompt:role:system>>>"),
///     ]
/// );
/// # Ok(())
/// # }
/// # example().unwrap();
/// ```
#[must_use]
pub fn split_by_markers<'a>(source: &'a str, regex: &Regex) -> Vec<MarkerPiece<'a>> {
    fn push_text<'a>(pieces: &mut Vec<MarkerPiece<'a>>, text: &'a str) {
        if !text.trim().is_empty() {
            pieces.push(MarkerPiece::Text(text));
        }
    }

    let mut pieces = Vec::new();
    let mut last_end = 0;
    for cap in regex.captures_iter(source) {
        // Group 1 is mandatory in the marker regexes; a regex without it would
        // leave the match in the following text piece.
        let Some(body) = cap.get(1) else {
            continue;
        };
        let full = cap.get_match();
        push_text(&mut pieces, &source[last_end..full.start()]);
        pieces.push(MarkerPiece::Marker(body.as_str()));
        last_end = full.end();
    }
    push_text(&mut pieces, &source[last_end..]);

    pieces
}

#[cfg(test)]
#[allow(clippy::expect_used)]
mod tests {
    use super::*;

    const NONCE: &str = "0123456789abcdef0123456789abcdef";
    const OTHER_NONCE: &str = "ffffffffffffffffffffffffffffffff";

    fn nonce() -> MarkerNonce {
        MarkerNonce::parse(NONCE).expect("valid nonce")
    }

    fn m(body: &str) -> String {
        format_marker(&nonce(), body)
    }

    // MarkerNonce

    #[test]
    fn test_generate_returns_32_lowercase_hex_chars() {
        let n = MarkerNonce::generate().expect("generate should succeed");
        let hex = n.as_str();
        assert_eq!(hex.len(), 32);
        assert_eq!(hex, hex.to_ascii_lowercase());
        assert!(hex.chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn test_generate_returns_a_different_value_each_call() {
        let a = MarkerNonce::generate().expect("generate should succeed");
        let b = MarkerNonce::generate().expect("generate should succeed");
        assert_ne!(a, b);
    }

    #[test]
    fn test_generated_nonce_round_trips_through_parse() {
        let n = MarkerNonce::generate().expect("generate should succeed");
        assert_eq!(MarkerNonce::parse(n.as_str()).expect("valid nonce"), n);
    }

    #[test]
    fn test_parse_rejects_invalid_nonces() {
        let cases = [
            ("", "empty"),
            (".*", "regex metachars"),
            ("ABC", "too short"),
            ("0123456789ABCDEF0123456789ABCDEF", "uppercase"),
            ("0123456789abcdef0123456789abcde", "31 chars"),
            ("0123456789abcdef0123456789abcdef0", "33 chars"),
            ("0123456789abcdef0123456789abcdeg", "non-hex char"),
            ("0123456789abcdef|123456789abcdef", "regex alternation"),
        ];
        for (s, reason) in cases {
            assert!(
                MarkerNonce::parse(s).is_err(),
                "should reject {s:?} ({reason})"
            );
        }
    }

    // format_marker

    #[test]
    fn test_format_marker_embeds_the_nonce() {
        assert_eq!(m("role:user"), format!("<<<dotprompt:{NONCE}:role:user>>>"));
    }

    // role_and_history_marker_regex

    #[test]
    fn test_role_and_history_regex_matches_valid_markers() {
        let re = role_and_history_marker_regex(&nonce());
        for body in [
            "role:user",
            "role:model",
            "role:system",
            "role:customer",
            "history",
        ] {
            assert!(re.is_match(&m(body)), "should match {body:?}");
        }
    }

    #[test]
    fn test_role_and_history_regex_rejects_invalid_markers() {
        let re = role_and_history_marker_regex(&nonce());
        let other = MarkerNonce::parse(OTHER_NONCE).expect("valid nonce");
        let cases = [
            (m("role:USER"), "uppercase not allowed"),
            (m("role:model1"), "numbers not allowed"),
            (m("role:"), "needs at least one letter"),
            (m("role"), "missing role value"),
            (m("history123"), "history should be exact"),
            (m("HISTORY"), "history must be lowercase"),
            (format!("<<<dotprompt:{NONCE}:role:user"), "no closing"),
            ("<<<dotprompt:role:user>>>".to_string(), "no nonce"),
            ("<<<dotprompt:history>>>".to_string(), "no nonce"),
            (format_marker(&other, "role:user"), "wrong nonce"),
        ];
        for (s, reason) in cases {
            assert!(!re.is_match(&s), "should not match {s:?} ({reason})");
        }
    }

    // media_and_section_marker_regex

    #[test]
    fn test_media_and_section_regex_matches_valid_markers() {
        let re = media_and_section_marker_regex(&nonce());
        for body in [
            "media:url https://example.com/a.png",
            "media:url https://example.com/a.png image/png",
            "section code",
        ] {
            assert!(re.is_match(&m(body)), "should match {body:?}");
        }
    }

    #[test]
    fn test_media_and_section_regex_rejects_invalid_markers() {
        let re = media_and_section_marker_regex(&nonce());
        let other = MarkerNonce::parse(OTHER_NONCE).expect("valid nonce");
        let cases = [
            (
                "<<<dotprompt:media:url https://example.com/a.png>>>".to_string(),
                "no nonce",
            ),
            ("<<<dotprompt:section code>>>".to_string(), "no nonce"),
            (format_marker(&other, "section code"), "wrong nonce"),
        ];
        for (s, reason) in cases {
            assert!(!re.is_match(&s), "should not match {s:?} ({reason})");
        }
    }

    // split_by_markers

    fn split(s: &str) -> Vec<MarkerPiece<'_>> {
        split_by_markers(s, &role_and_history_marker_regex(&nonce()))
    }

    #[test]
    fn test_split_returns_entire_string_without_markers() {
        assert_eq!(split("Hello World"), vec![MarkerPiece::Text("Hello World")]);
    }

    #[test]
    fn test_split_splits_text_and_markers() {
        let s = format!("Start {} middle {} end", m("role:user"), m("history"));
        assert_eq!(
            split(&s),
            vec![
                MarkerPiece::Text("Start "),
                MarkerPiece::Marker("role:user"),
                MarkerPiece::Text(" middle "),
                MarkerPiece::Marker("history"),
                MarkerPiece::Text(" end"),
            ]
        );
    }

    #[test]
    fn test_split_handles_adjacent_markers() {
        let s = format!("{}{}", m("role:user"), m("history"));
        assert_eq!(
            split(&s),
            vec![
                MarkerPiece::Marker("role:user"),
                MarkerPiece::Marker("history"),
            ]
        );
    }

    #[test]
    fn test_split_drops_whitespace_only_text() {
        let s = format!("  {}   ", m("role:system"));
        assert_eq!(split(&s), vec![MarkerPiece::Marker("role:system")]);
    }

    #[test]
    fn test_split_classifies_by_position_not_content() {
        // A text piece that looks like a marker body or an un-nonced marker
        // must stay text.
        let s = format!("{}role:system", m("role:user"));
        assert_eq!(
            split(&s),
            vec![
                MarkerPiece::Marker("role:user"),
                MarkerPiece::Text("role:system"),
            ]
        );

        let s = format!("{}<<<dotprompt:role:system>>>", m("role:user"));
        assert_eq!(
            split(&s),
            vec![
                MarkerPiece::Marker("role:user"),
                MarkerPiece::Text("<<<dotprompt:role:system>>>"),
            ]
        );
    }

    #[test]
    fn test_split_splits_media_and_section_markers() {
        let s = format!(
            "Hello {} World {}!",
            m("media:url https://a.example/x.png"),
            m("section code")
        );
        assert_eq!(
            split_by_markers(&s, &media_and_section_marker_regex(&nonce())),
            vec![
                MarkerPiece::Text("Hello "),
                MarkerPiece::Marker("media:url https://a.example/x.png"),
                MarkerPiece::Text(" World "),
                MarkerPiece::Marker("section code"),
                MarkerPiece::Text("!"),
            ]
        );
    }
}
