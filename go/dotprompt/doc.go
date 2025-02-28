// Copyright 2025 Google LLC
// SPDX-License-Identifier: Apache-2.0

// Package dotprompt provides functionality for parsing and working with
// dotprompt templates.
//
// Dotprompt is a format for defining prompts for large language models (LLMs)
// with support for templating, history management, and multi-modal content.
// This Go implementation provides types and functions for parsing dotprompt
// templates and converting them into structured messages that can be sent to
// LLM APIs.
//
// The package includes:
//   - Type definitions for messages, parts, documents, and other dotprompt
//     concepts
//   - Functions for parsing dotprompt templates into structured data
//   - Utilities for handling message history and multi-modal content
//   - Support for extracting and processing frontmatter metadata
package dotprompt
