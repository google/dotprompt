;; Copyright 2026 Google LLC
;;
;; Licensed under the Apache License, Version 2.0 (the "License");
;; you may not use this file except in compliance with the License.
;; You may obtain a copy of the License at
;;
;;     http://www.apache.org/licenses/LICENSE-2.0
;;
;; Unless required by applicable law or agreed to in writing, software
;; distributed under the License is distributed on an "AS IS" BASIS,
;; WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
;; See the License for the specific language governing permissions and
;; limitations under the License.
;;
;; SPDX-License-Identifier: Apache-2.0

; Highlight queries for Dotprompt Tree-sitter grammar
; For use with nvim-treesitter

; License header comments
(header_comment) @comment

; Frontmatter
(frontmatter_delimiter) @punctuation.delimiter
(yaml_content) @embedded
(yaml_line) @string

; Handlebars expressions
(handlebars_expression
  "{{" @punctuation.bracket
  "}}" @punctuation.bracket)

; Helper names
(helper_name) @function.call

; Block expressions
(block_expression
  "{{#" @punctuation.bracket
  (block_name) @keyword.control
  "}}" @punctuation.bracket)

(close_block
  "{{/" @punctuation.bracket
  (block_name) @keyword.control
  "}}" @punctuation.bracket)

(else_expression) @keyword.control

; Dotprompt-specific helpers
((helper_name) @keyword.control.dotprompt
  (#any-of? @keyword.control.dotprompt
    "role" "json" "media" "history" "section" "ifEquals" "unlessEquals"))

; Block keywords
((block_name) @keyword.control.flow
  (#any-of? @keyword.control.flow
    "if" "unless" "each" "with" "role" "section"))

; Partials
(partial_reference
  ">" @punctuation.special
  (identifier) @function)

; Variables
(variable_reference) @variable

; Special variables
((variable_reference) @variable.builtin
  (#any-of? @variable.builtin "@index" "@first" "@last" "@key" "this"))

; Arguments
(named_argument
  (identifier) @property
  "=" @operator)

; Literals
(string_literal) @string
(number_literal) @number
(boolean_literal) @boolean

; Comments
(handlebars_comment) @comment

; Dotprompt markers
(dotprompt_marker
  "<<<dotprompt:" @keyword.directive
  (marker_content) @string.special
  ">>>" @keyword.directive)

; Plain text
(text) @none
