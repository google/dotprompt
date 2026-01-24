/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @file Tree-sitter grammar for Dotprompt files
 * @author Google
 * @license Apache-2.0
 *
 * Dotprompt files consist of:
 * 1. Optional YAML frontmatter (between --- delimiters)
 * 2. Template body with Handlebars expressions and Dotprompt markers
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

module.exports = grammar({
  name: 'dotprompt',

  extras: ($) => [/\s/],

  externals: ($) => [$._eof],

  rules: {
    // Document structure
    document: ($) =>
      seq(
        optional($.license_header),
        optional($.frontmatter),
        optional($.template_body)
      ),

    // License header (# comments before frontmatter)
    license_header: ($) => repeat1($.header_comment),

    header_comment: ($) => seq('#', /[^\n]*/, /\n/),

    // YAML Frontmatter (--- ... ---)
    frontmatter: ($) =>
      seq(
        $.frontmatter_delimiter,
        optional($.yaml_content),
        $.frontmatter_delimiter
      ),

    frontmatter_delimiter: ($) => '---',

    yaml_content: ($) => repeat1($.yaml_line),

    yaml_line: ($) => seq(/[^\n]*/, /\n/),

    // Template body
    template_body: ($) =>
      repeat1(
        choice(
          $.handlebars_expression,
          $.handlebars_block,
          $.dotprompt_marker,
          $.handlebars_comment,
          $.text
        )
      ),

    // Handlebars expressions: {{ ... }}
    handlebars_expression: ($) =>
      seq('{{', optional($.expression_content), '}}'),

    expression_content: ($) =>
      choice($.helper_call, $.variable_reference, $.partial_reference),

    // Helper call: {{helper arg1 arg2}}
    helper_call: ($) => seq($.helper_name, repeat($.argument)),

    helper_name: ($) => /[a-zA-Z_][a-zA-Z0-9_]*/,

    argument: ($) =>
      choice(
        $.string_literal,
        $.number_literal,
        $.boolean_literal,
        $.variable_reference,
        $.named_argument
      ),

    named_argument: ($) =>
      seq(
        $.identifier,
        '=',
        choice(
          $.string_literal,
          $.number_literal,
          $.boolean_literal,
          $.variable_reference
        )
      ),

    // Variable reference: {{variable}} or {{object.property}}
    variable_reference: ($) => /[a-zA-Z_@][a-zA-Z0-9_.]*/,

    // Partial reference: {{> partialName}}
    partial_reference: ($) =>
      seq('>', $.identifier, optional($.variable_reference)),

    // Handlebars blocks: {{#block}} ... {{/block}}
    handlebars_block: ($) =>
      choice($.block_expression, $.else_expression, $.close_block),

    block_expression: ($) => seq('{{#', $.block_name, repeat($.argument), '}}'),

    else_expression: ($) => '{{else}}',

    close_block: ($) => seq('{{/', $.block_name, '}}'),

    block_name: ($) => /[a-zA-Z_][a-zA-Z0-9_]*/,

    // Handlebars comments: {{! ... }} or {{!-- ... --}}
    handlebars_comment: ($) =>
      choice(seq('{{!', /[^}]*/, '}}'), seq('{{!--', /[^-]*/, '--}}')),

    // Dotprompt markers: <<<dotprompt:...>>>
    dotprompt_marker: ($) => seq('<<<dotprompt:', $.marker_content, '>>>'),

    marker_content: ($) => /[^>]+/,

    // Literals
    string_literal: ($) =>
      choice(seq('"', /[^"]*/, '"'), seq("'", /[^']*/, "'")),

    number_literal: ($) => /\d+(\.\d+)?/,

    boolean_literal: ($) => choice('true', 'false'),

    identifier: ($) => /[a-zA-Z_][a-zA-Z0-9_-]*/,

    // Plain text
    text: ($) => /[^{<]+/,
  },
});
