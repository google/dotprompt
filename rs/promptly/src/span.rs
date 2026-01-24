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

//! Source span tracking for error reporting.
//!
//! This module provides types for tracking source locations in `.prompt` files,
//! enabling Rust-style error messages with precise line and column information.

use serde::{Deserialize, Serialize};

/// A position in source code.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) struct Position {
    /// Byte offset from the start of the source.
    pub offset: usize,
    /// 1-indexed line number.
    pub line: u32,
    /// 1-indexed column number (UTF-8 aware).
    pub column: u32,
}

impl Position {
    /// Creates a new position.
    #[must_use]
    pub(crate) const fn new(offset: usize, line: u32, column: u32) -> Self {
        Self {
            offset,
            line,
            column,
        }
    }

    /// Creates a position at the start of the source.
    #[must_use]
    pub(crate) const fn start() -> Self {
        Self {
            offset: 0,
            line: 1,
            column: 1,
        }
    }
}

impl Default for Position {
    fn default() -> Self {
        Self::start()
    }
}

/// A span of source code.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub(crate) struct Span {
    /// Start position of the span.
    pub start: Position,
    /// End position of the span (exclusive).
    pub end: Position,
}

impl Span {
    /// Creates a span from line and column ranges.
    #[must_use]
    pub(crate) const fn from_line_col(
        start_line: u32,
        start_col: u32,
        end_line: u32,
        end_col: u32,
    ) -> Self {
        Self {
            start: Position::new(0, start_line, start_col),
            end: Position::new(0, end_line, end_col),
        }
    }
}

/// Calculates the position at a given byte offset in the source.
#[must_use]
pub(crate) fn position_at_offset(source: &str, offset: usize) -> Position {
    let mut line = 1u32;
    let mut column = 1u32;
    let mut current_offset = 0usize;

    for ch in source.chars() {
        if current_offset >= offset {
            break;
        }

        if ch == '\n' {
            line += 1;
            column = 1;
        } else {
            column += 1;
        }

        current_offset += ch.len_utf8();
    }

    Position::new(offset, line, column)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_position_at_offset_start() {
        let source = "hello\nworld";
        let pos = position_at_offset(source, 0);
        assert_eq!(pos.line, 1);
        assert_eq!(pos.column, 1);
    }

    #[test]
    fn test_position_at_offset_middle_of_line() {
        let source = "hello\nworld";
        let pos = position_at_offset(source, 3);
        assert_eq!(pos.line, 1);
        assert_eq!(pos.column, 4);
    }

    #[test]
    fn test_position_at_offset_second_line() {
        let source = "hello\nworld";
        let pos = position_at_offset(source, 6);
        assert_eq!(pos.line, 2);
        assert_eq!(pos.column, 1);
    }

    #[test]
    fn test_position_at_offset_end() {
        let source = "hello\nworld";
        let pos = position_at_offset(source, 11);
        assert_eq!(pos.line, 2);
        assert_eq!(pos.column, 6);
    }
}
