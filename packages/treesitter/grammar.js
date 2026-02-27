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
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

module.exports = grammar({
  name: 'dotprompt',

  rules: {
    document: ($) =>
      seq(
        optional($.license_header),
        optional($.frontmatter),
        optional($.template_body)
      ),

    license_header: ($) => repeat1($.header_comment),

    header_comment: ($) => token(seq('#', /.*/)),

    frontmatter: ($) =>
      prec(
        1,
        seq(
          $.frontmatter_delimiter,
          /\r?\n/,
          alias(repeat($._yaml_content), $.yaml_content),
          $.frontmatter_delimiter,
          /\r?\n/
        )
      ),

    frontmatter_delimiter: ($) => token(prec(10, '---')),

    _yaml_content: ($) => choice($.yaml_line, $.header_comment, /\s+/),

    yaml_line: ($) =>
      seq(
        field('key', alias(/[a-zA-Z_][a-zA-Z0-9_-]*/, $.yaml_key)),
        ':',
        optional(field('value', alias(/.+/, $.yaml_value))),
        /\r?\n/
      ),

    template_body: ($) => repeat1($._content),

    _content: ($) =>
      choice(
        $.handlebars_block,
        $.handlebars_expression,
        $.handlebars_comment,
        $.text
      ),

    handlebars_block: ($) =>
      seq(
        $.block_expression, // block_start renamed
        repeat($._content),
        $.close_block // block_end renamed
      ),

    block_expression: ($) =>
      seq(
        '{{#',
        field('name', alias($.path, $.block_name)), // helper_name -> block_name
        repeat($.argument), // _param -> argument
        '}}'
      ),

    close_block: ($) =>
      seq('{{/', field('name', alias($.path, $.block_name)), '}}'),

    handlebars_expression: ($) => seq('{{', $.expression_content, '}}'),

    expression_content: ($) =>
      choice(
        seq('>', alias($.path, $.partial_reference)),
        'else',
        seq(alias($.path, $.helper_name), repeat1($.argument)),
        alias($.variable_reference, $.variable_reference)
      ),

    handlebars_comment: ($) =>
      choice(
        seq('{{!', /([^}]|}[^}])*?/, '}}'),
        seq('{{!--', /([^-]|-+|-[^}])*?/, '--}}')
      ),

    argument: ($) =>
      choice(
        $.string_literal,
        $.number,
        $.boolean,
        $.variable_reference,
        $.hash_param
      ),

    hash_param: ($) =>
      seq(
        field('key', alias($.path, $.key)),
        '=',
        field(
          'value',
          choice($.string_literal, $.number, $.boolean, $.variable_reference)
        )
      ),

    variable_reference: ($) =>
      choice(
        /@[a-zA-Z_][a-zA-Z0-9_]*/, // @index, @first
        $.path
      ),

    path: ($) => /[a-zA-Z_][a-zA-Z0-9_.]*/,

    string_literal: ($) =>
      choice(seq('"', /([^"\\]|\\.)*/, '"'), seq("'", /([^'\\]|\\.)*/, "'")),

    number: ($) => /-?\d+(\.\d+)?/,

    boolean: ($) => choice('true', 'false'),

    text: ($) => /[^{#]+|\{|#/,
  },
});
