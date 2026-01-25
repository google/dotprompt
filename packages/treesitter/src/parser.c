/*
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

#include "tree_sitter/parser.h"

#if defined(__GNUC__) || defined(__clang__)
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"
#endif

#define LANGUAGE_VERSION 14
#define STATE_COUNT 87
#define LARGE_STATE_COUNT 2
#define SYMBOL_COUNT 56
#define ALIAS_COUNT 5
#define TOKEN_COUNT 33
#define EXTERNAL_TOKEN_COUNT 0
#define FIELD_COUNT 3
#define MAX_ALIAS_SEQUENCE_LENGTH 5
#define PRODUCTION_ID_COUNT 9

enum ts_symbol_identifiers {
  sym_header_comment = 1,
  aux_sym_frontmatter_token1 = 2,
  sym_frontmatter_delimiter = 3,
  aux_sym__yaml_content_token1 = 4,
  aux_sym_yaml_line_token1 = 5,
  anon_sym_COLON = 6,
  aux_sym_yaml_line_token2 = 7,
  anon_sym_LBRACE_LBRACE_POUND = 8,
  anon_sym_RBRACE_RBRACE = 9,
  anon_sym_LBRACE_LBRACE_SLASH = 10,
  anon_sym_LBRACE_LBRACE = 11,
  anon_sym_GT = 12,
  anon_sym_else = 13,
  anon_sym_LBRACE_LBRACE_BANG = 14,
  aux_sym_handlebars_comment_token1 = 15,
  anon_sym_LBRACE_LBRACE_BANG_DASH_DASH = 16,
  aux_sym_handlebars_comment_token2 = 17,
  anon_sym_DASH_DASH_RBRACE_RBRACE = 18,
  anon_sym_EQ = 19,
  aux_sym_variable_reference_token1 = 20,
  sym_path = 21,
  anon_sym_DQUOTE = 22,
  aux_sym_string_literal_token1 = 23,
  anon_sym_SQUOTE = 24,
  aux_sym_string_literal_token2 = 25,
  sym_number = 26,
  anon_sym_true = 27,
  anon_sym_false = 28,
  anon_sym_LT_LT_LTdotprompt_COLON = 29,
  aux_sym_dotprompt_marker_token1 = 30,
  anon_sym_GT_GT_GT = 31,
  sym_text = 32,
  sym_document = 33,
  sym_license_header = 34,
  sym_frontmatter = 35,
  sym__yaml_content = 36,
  sym_yaml_line = 37,
  sym_template_body = 38,
  sym__content = 39,
  sym_handlebars_block = 40,
  sym_block_expression = 41,
  sym_close_block = 42,
  sym_handlebars_expression = 43,
  sym_expression_content = 44,
  sym_handlebars_comment = 45,
  sym_argument = 46,
  sym_hash_param = 47,
  sym_variable_reference = 48,
  sym_string_literal = 49,
  sym_boolean = 50,
  sym_dotprompt_marker = 51,
  aux_sym_license_header_repeat1 = 52,
  aux_sym_frontmatter_repeat1 = 53,
  aux_sym_template_body_repeat1 = 54,
  aux_sym_block_expression_repeat1 = 55,
  alias_sym_block_name = 56,
  alias_sym_helper_name = 57,
  alias_sym_key = 58,
  alias_sym_partial_reference = 59,
  alias_sym_yaml_content = 60,
};

static const char * const ts_symbol_names[] = {
  [ts_builtin_sym_end] = "end",
  [sym_header_comment] = "header_comment",
  [aux_sym_frontmatter_token1] = "frontmatter_token1",
  [sym_frontmatter_delimiter] = "frontmatter_delimiter",
  [aux_sym__yaml_content_token1] = "_yaml_content_token1",
  [aux_sym_yaml_line_token1] = "yaml_key",
  [anon_sym_COLON] = ":",
  [aux_sym_yaml_line_token2] = "yaml_value",
  [anon_sym_LBRACE_LBRACE_POUND] = "{{#",
  [anon_sym_RBRACE_RBRACE] = "}}",
  [anon_sym_LBRACE_LBRACE_SLASH] = "{{/",
  [anon_sym_LBRACE_LBRACE] = "{{",
  [anon_sym_GT] = ">",
  [anon_sym_else] = "else",
  [anon_sym_LBRACE_LBRACE_BANG] = "{{!",
  [aux_sym_handlebars_comment_token1] = "handlebars_comment_token1",
  [anon_sym_LBRACE_LBRACE_BANG_DASH_DASH] = "{{!--",
  [aux_sym_handlebars_comment_token2] = "handlebars_comment_token2",
  [anon_sym_DASH_DASH_RBRACE_RBRACE] = "--}}",
  [anon_sym_EQ] = "=",
  [aux_sym_variable_reference_token1] = "variable_reference_token1",
  [sym_path] = "path",
  [anon_sym_DQUOTE] = "\"",
  [aux_sym_string_literal_token1] = "string_literal_token1",
  [anon_sym_SQUOTE] = "'",
  [aux_sym_string_literal_token2] = "string_literal_token2",
  [sym_number] = "number",
  [anon_sym_true] = "true",
  [anon_sym_false] = "false",
  [anon_sym_LT_LT_LTdotprompt_COLON] = "<<<dotprompt:",
  [aux_sym_dotprompt_marker_token1] = "marker_content",
  [anon_sym_GT_GT_GT] = ">>>",
  [sym_text] = "text",
  [sym_document] = "document",
  [sym_license_header] = "license_header",
  [sym_frontmatter] = "frontmatter",
  [sym__yaml_content] = "_yaml_content",
  [sym_yaml_line] = "yaml_line",
  [sym_template_body] = "template_body",
  [sym__content] = "_content",
  [sym_handlebars_block] = "handlebars_block",
  [sym_block_expression] = "block_expression",
  [sym_close_block] = "close_block",
  [sym_handlebars_expression] = "handlebars_expression",
  [sym_expression_content] = "expression_content",
  [sym_handlebars_comment] = "handlebars_comment",
  [sym_argument] = "argument",
  [sym_hash_param] = "hash_param",
  [sym_variable_reference] = "variable_reference",
  [sym_string_literal] = "string_literal",
  [sym_boolean] = "boolean",
  [sym_dotprompt_marker] = "dotprompt_marker",
  [aux_sym_license_header_repeat1] = "license_header_repeat1",
  [aux_sym_frontmatter_repeat1] = "frontmatter_repeat1",
  [aux_sym_template_body_repeat1] = "template_body_repeat1",
  [aux_sym_block_expression_repeat1] = "block_expression_repeat1",
  [alias_sym_block_name] = "block_name",
  [alias_sym_helper_name] = "helper_name",
  [alias_sym_key] = "key",
  [alias_sym_partial_reference] = "partial_reference",
  [alias_sym_yaml_content] = "yaml_content",
};

static const TSSymbol ts_symbol_map[] = {
  [ts_builtin_sym_end] = ts_builtin_sym_end,
  [sym_header_comment] = sym_header_comment,
  [aux_sym_frontmatter_token1] = aux_sym_frontmatter_token1,
  [sym_frontmatter_delimiter] = sym_frontmatter_delimiter,
  [aux_sym__yaml_content_token1] = aux_sym__yaml_content_token1,
  [aux_sym_yaml_line_token1] = aux_sym_yaml_line_token1,
  [anon_sym_COLON] = anon_sym_COLON,
  [aux_sym_yaml_line_token2] = aux_sym_yaml_line_token2,
  [anon_sym_LBRACE_LBRACE_POUND] = anon_sym_LBRACE_LBRACE_POUND,
  [anon_sym_RBRACE_RBRACE] = anon_sym_RBRACE_RBRACE,
  [anon_sym_LBRACE_LBRACE_SLASH] = anon_sym_LBRACE_LBRACE_SLASH,
  [anon_sym_LBRACE_LBRACE] = anon_sym_LBRACE_LBRACE,
  [anon_sym_GT] = anon_sym_GT,
  [anon_sym_else] = anon_sym_else,
  [anon_sym_LBRACE_LBRACE_BANG] = anon_sym_LBRACE_LBRACE_BANG,
  [aux_sym_handlebars_comment_token1] = aux_sym_handlebars_comment_token1,
  [anon_sym_LBRACE_LBRACE_BANG_DASH_DASH] = anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
  [aux_sym_handlebars_comment_token2] = aux_sym_handlebars_comment_token2,
  [anon_sym_DASH_DASH_RBRACE_RBRACE] = anon_sym_DASH_DASH_RBRACE_RBRACE,
  [anon_sym_EQ] = anon_sym_EQ,
  [aux_sym_variable_reference_token1] = aux_sym_variable_reference_token1,
  [sym_path] = sym_path,
  [anon_sym_DQUOTE] = anon_sym_DQUOTE,
  [aux_sym_string_literal_token1] = aux_sym_string_literal_token1,
  [anon_sym_SQUOTE] = anon_sym_SQUOTE,
  [aux_sym_string_literal_token2] = aux_sym_string_literal_token2,
  [sym_number] = sym_number,
  [anon_sym_true] = anon_sym_true,
  [anon_sym_false] = anon_sym_false,
  [anon_sym_LT_LT_LTdotprompt_COLON] = anon_sym_LT_LT_LTdotprompt_COLON,
  [aux_sym_dotprompt_marker_token1] = aux_sym_dotprompt_marker_token1,
  [anon_sym_GT_GT_GT] = anon_sym_GT_GT_GT,
  [sym_text] = sym_text,
  [sym_document] = sym_document,
  [sym_license_header] = sym_license_header,
  [sym_frontmatter] = sym_frontmatter,
  [sym__yaml_content] = sym__yaml_content,
  [sym_yaml_line] = sym_yaml_line,
  [sym_template_body] = sym_template_body,
  [sym__content] = sym__content,
  [sym_handlebars_block] = sym_handlebars_block,
  [sym_block_expression] = sym_block_expression,
  [sym_close_block] = sym_close_block,
  [sym_handlebars_expression] = sym_handlebars_expression,
  [sym_expression_content] = sym_expression_content,
  [sym_handlebars_comment] = sym_handlebars_comment,
  [sym_argument] = sym_argument,
  [sym_hash_param] = sym_hash_param,
  [sym_variable_reference] = sym_variable_reference,
  [sym_string_literal] = sym_string_literal,
  [sym_boolean] = sym_boolean,
  [sym_dotprompt_marker] = sym_dotprompt_marker,
  [aux_sym_license_header_repeat1] = aux_sym_license_header_repeat1,
  [aux_sym_frontmatter_repeat1] = aux_sym_frontmatter_repeat1,
  [aux_sym_template_body_repeat1] = aux_sym_template_body_repeat1,
  [aux_sym_block_expression_repeat1] = aux_sym_block_expression_repeat1,
  [alias_sym_block_name] = alias_sym_block_name,
  [alias_sym_helper_name] = alias_sym_helper_name,
  [alias_sym_key] = alias_sym_key,
  [alias_sym_partial_reference] = alias_sym_partial_reference,
  [alias_sym_yaml_content] = alias_sym_yaml_content,
};

static const TSSymbolMetadata ts_symbol_metadata[] = {
  [ts_builtin_sym_end] = {
    .visible = false,
    .named = true,
  },
  [sym_header_comment] = {
    .visible = true,
    .named = true,
  },
  [aux_sym_frontmatter_token1] = {
    .visible = false,
    .named = false,
  },
  [sym_frontmatter_delimiter] = {
    .visible = true,
    .named = true,
  },
  [aux_sym__yaml_content_token1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_yaml_line_token1] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_COLON] = {
    .visible = true,
    .named = false,
  },
  [aux_sym_yaml_line_token2] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_LBRACE_LBRACE_POUND] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_RBRACE_RBRACE] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LBRACE_LBRACE_SLASH] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LBRACE_LBRACE] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_GT] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_else] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LBRACE_LBRACE_BANG] = {
    .visible = true,
    .named = false,
  },
  [aux_sym_handlebars_comment_token1] = {
    .visible = false,
    .named = false,
  },
  [anon_sym_LBRACE_LBRACE_BANG_DASH_DASH] = {
    .visible = true,
    .named = false,
  },
  [aux_sym_handlebars_comment_token2] = {
    .visible = false,
    .named = false,
  },
  [anon_sym_DASH_DASH_RBRACE_RBRACE] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_EQ] = {
    .visible = true,
    .named = false,
  },
  [aux_sym_variable_reference_token1] = {
    .visible = false,
    .named = false,
  },
  [sym_path] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_DQUOTE] = {
    .visible = true,
    .named = false,
  },
  [aux_sym_string_literal_token1] = {
    .visible = false,
    .named = false,
  },
  [anon_sym_SQUOTE] = {
    .visible = true,
    .named = false,
  },
  [aux_sym_string_literal_token2] = {
    .visible = false,
    .named = false,
  },
  [sym_number] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_true] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_false] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LT_LT_LTdotprompt_COLON] = {
    .visible = true,
    .named = false,
  },
  [aux_sym_dotprompt_marker_token1] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_GT_GT_GT] = {
    .visible = true,
    .named = false,
  },
  [sym_text] = {
    .visible = true,
    .named = true,
  },
  [sym_document] = {
    .visible = true,
    .named = true,
  },
  [sym_license_header] = {
    .visible = true,
    .named = true,
  },
  [sym_frontmatter] = {
    .visible = true,
    .named = true,
  },
  [sym__yaml_content] = {
    .visible = false,
    .named = true,
  },
  [sym_yaml_line] = {
    .visible = true,
    .named = true,
  },
  [sym_template_body] = {
    .visible = true,
    .named = true,
  },
  [sym__content] = {
    .visible = false,
    .named = true,
  },
  [sym_handlebars_block] = {
    .visible = true,
    .named = true,
  },
  [sym_block_expression] = {
    .visible = true,
    .named = true,
  },
  [sym_close_block] = {
    .visible = true,
    .named = true,
  },
  [sym_handlebars_expression] = {
    .visible = true,
    .named = true,
  },
  [sym_expression_content] = {
    .visible = true,
    .named = true,
  },
  [sym_handlebars_comment] = {
    .visible = true,
    .named = true,
  },
  [sym_argument] = {
    .visible = true,
    .named = true,
  },
  [sym_hash_param] = {
    .visible = true,
    .named = true,
  },
  [sym_variable_reference] = {
    .visible = true,
    .named = true,
  },
  [sym_string_literal] = {
    .visible = true,
    .named = true,
  },
  [sym_boolean] = {
    .visible = true,
    .named = true,
  },
  [sym_dotprompt_marker] = {
    .visible = true,
    .named = true,
  },
  [aux_sym_license_header_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_frontmatter_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_template_body_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_block_expression_repeat1] = {
    .visible = false,
    .named = false,
  },
  [alias_sym_block_name] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_helper_name] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_key] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_partial_reference] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_yaml_content] = {
    .visible = true,
    .named = true,
  },
};

enum ts_field_identifiers {
  field_key = 1,
  field_name = 2,
  field_value = 3,
};

static const char * const ts_field_names[] = {
  [0] = NULL,
  [field_key] = "key",
  [field_name] = "name",
  [field_value] = "value",
};

static const TSFieldMapSlice ts_field_map_slices[PRODUCTION_ID_COUNT] = {
  [2] = {.index = 0, .length = 1},
  [5] = {.index = 1, .length = 1},
  [7] = {.index = 2, .length = 2},
  [8] = {.index = 2, .length = 2},
};

static const TSFieldMapEntry ts_field_map_entries[] = {
  [0] =
    {field_name, 1},
  [1] =
    {field_key, 0},
  [2] =
    {field_key, 0},
    {field_value, 2},
};

static const TSSymbol ts_alias_sequences[PRODUCTION_ID_COUNT][MAX_ALIAS_SEQUENCE_LENGTH] = {
  [0] = {0},
  [1] = {
    [0] = sym_variable_reference,
  },
  [2] = {
    [1] = alias_sym_block_name,
  },
  [3] = {
    [1] = alias_sym_partial_reference,
  },
  [4] = {
    [0] = alias_sym_helper_name,
  },
  [6] = {
    [2] = alias_sym_yaml_content,
  },
  [7] = {
    [0] = alias_sym_key,
  },
};

static const uint16_t ts_non_terminal_alias_map[] = {
  sym_variable_reference, 2,
    sym_variable_reference,
    sym_variable_reference,
  aux_sym_frontmatter_repeat1, 2,
    aux_sym_frontmatter_repeat1,
    alias_sym_yaml_content,
  0,
};

static const TSStateId ts_primary_state_ids[STATE_COUNT] = {
  [0] = 0,
  [1] = 1,
  [2] = 2,
  [3] = 3,
  [4] = 4,
  [5] = 5,
  [6] = 4,
  [7] = 7,
  [8] = 5,
  [9] = 9,
  [10] = 10,
  [11] = 9,
  [12] = 12,
  [13] = 13,
  [14] = 14,
  [15] = 15,
  [16] = 16,
  [17] = 17,
  [18] = 18,
  [19] = 19,
  [20] = 20,
  [21] = 21,
  [22] = 22,
  [23] = 23,
  [24] = 24,
  [25] = 25,
  [26] = 26,
  [27] = 27,
  [28] = 28,
  [29] = 29,
  [30] = 29,
  [31] = 31,
  [32] = 32,
  [33] = 33,
  [34] = 34,
  [35] = 35,
  [36] = 36,
  [37] = 37,
  [38] = 38,
  [39] = 39,
  [40] = 37,
  [41] = 39,
  [42] = 27,
  [43] = 31,
  [44] = 26,
  [45] = 45,
  [46] = 45,
  [47] = 47,
  [48] = 48,
  [49] = 49,
  [50] = 50,
  [51] = 51,
  [52] = 52,
  [53] = 53,
  [54] = 54,
  [55] = 55,
  [56] = 56,
  [57] = 57,
  [58] = 58,
  [59] = 59,
  [60] = 60,
  [61] = 61,
  [62] = 62,
  [63] = 63,
  [64] = 64,
  [65] = 65,
  [66] = 66,
  [67] = 67,
  [68] = 68,
  [69] = 64,
  [70] = 70,
  [71] = 71,
  [72] = 72,
  [73] = 73,
  [74] = 74,
  [75] = 75,
  [76] = 76,
  [77] = 51,
  [78] = 65,
  [79] = 76,
  [80] = 80,
  [81] = 52,
  [82] = 82,
  [83] = 80,
  [84] = 75,
  [85] = 74,
  [86] = 61,
};

static bool ts_lex(TSLexer *lexer, TSStateId state) {
  START_LEXER();
  eof = lexer->eof(lexer);
  switch (state) {
    case 0:
      if (eof) ADVANCE(40);
      ADVANCE_MAP(
        '"', 78,
        '#', 41,
        '\'', 81,
        '-', 6,
        ':', 47,
        '<', 13,
        '=', 65,
        '>', 56,
        '@', 33,
        'e', 71,
        'f', 67,
        't', 73,
        '{', 26,
        '}', 27,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(0);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(84);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 1:
      if (lookahead == '\n') ADVANCE(42);
      if (lookahead == '\r') ADVANCE(48);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') ADVANCE(48);
      if (lookahead != 0) ADVANCE(49);
      END_STATE();
    case 2:
      if (lookahead == '\n') ADVANCE(43);
      if (lookahead == '\r') ADVANCE(2);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') SKIP(2);
      END_STATE();
    case 3:
      ADVANCE_MAP(
        '"', 78,
        '\'', 81,
        '-', 31,
        '=', 65,
        '>', 14,
        '@', 33,
        'f', 67,
        't', 73,
        '}', 27,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(3);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(84);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 4:
      if (lookahead == '#') ADVANCE(41);
      if (lookahead == '-') ADVANCE(10);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(45);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(46);
      END_STATE();
    case 5:
      if (lookahead == '#') ADVANCE(92);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(100);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(96);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 6:
      if (lookahead == '-') ADVANCE(8);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(84);
      END_STATE();
    case 7:
      if (lookahead == '-') ADVANCE(44);
      END_STATE();
    case 8:
      if (lookahead == '-') ADVANCE(44);
      if (lookahead == '}') ADVANCE(28);
      END_STATE();
    case 9:
      if (lookahead == '-') ADVANCE(61);
      END_STATE();
    case 10:
      if (lookahead == '-') ADVANCE(7);
      END_STATE();
    case 11:
      if (lookahead == ':') ADVANCE(88);
      END_STATE();
    case 12:
      if (lookahead == '<') ADVANCE(17);
      END_STATE();
    case 13:
      if (lookahead == '<') ADVANCE(12);
      END_STATE();
    case 14:
      if (lookahead == '>') ADVANCE(15);
      END_STATE();
    case 15:
      if (lookahead == '>') ADVANCE(91);
      END_STATE();
    case 16:
      if (lookahead == '>') ADVANCE(55);
      if (lookahead == '@') ADVANCE(33);
      if (lookahead == 'e') ADVANCE(71);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(16);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 17:
      if (lookahead == 'd') ADVANCE(19);
      END_STATE();
    case 18:
      if (lookahead == 'm') ADVANCE(22);
      END_STATE();
    case 19:
      if (lookahead == 'o') ADVANCE(24);
      END_STATE();
    case 20:
      if (lookahead == 'o') ADVANCE(18);
      END_STATE();
    case 21:
      if (lookahead == 'p') ADVANCE(23);
      END_STATE();
    case 22:
      if (lookahead == 'p') ADVANCE(25);
      END_STATE();
    case 23:
      if (lookahead == 'r') ADVANCE(20);
      END_STATE();
    case 24:
      if (lookahead == 't') ADVANCE(21);
      END_STATE();
    case 25:
      if (lookahead == 't') ADVANCE(11);
      END_STATE();
    case 26:
      if (lookahead == '{') ADVANCE(54);
      END_STATE();
    case 27:
      if (lookahead == '}') ADVANCE(51);
      END_STATE();
    case 28:
      if (lookahead == '}') ADVANCE(64);
      END_STATE();
    case 29:
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(29);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 30:
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(89);
      if (lookahead != 0 &&
          lookahead != '>') ADVANCE(90);
      END_STATE();
    case 31:
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(84);
      END_STATE();
    case 32:
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(85);
      END_STATE();
    case 33:
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(66);
      END_STATE();
    case 34:
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(83);
      END_STATE();
    case 35:
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(80);
      END_STATE();
    case 36:
      if (lookahead != 0 &&
          lookahead != '}') ADVANCE(60);
      END_STATE();
    case 37:
      if (eof) ADVANCE(40);
      if (lookahead == '#') ADVANCE(41);
      if (lookahead == '-') ADVANCE(98);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(101);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(93);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 38:
      if (eof) ADVANCE(40);
      if (lookahead == '#') ADVANCE(92);
      if (lookahead == '-') ADVANCE(98);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(101);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(94);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 39:
      if (eof) ADVANCE(40);
      if (lookahead == '#') ADVANCE(92);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(101);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(95);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 40:
      ACCEPT_TOKEN(ts_builtin_sym_end);
      END_STATE();
    case 41:
      ACCEPT_TOKEN(sym_header_comment);
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(41);
      END_STATE();
    case 42:
      ACCEPT_TOKEN(aux_sym_frontmatter_token1);
      if (lookahead == '\n') ADVANCE(42);
      if (lookahead == '\r') ADVANCE(48);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') ADVANCE(48);
      END_STATE();
    case 43:
      ACCEPT_TOKEN(aux_sym_frontmatter_token1);
      if (lookahead == '\n') ADVANCE(43);
      if (lookahead == '\r') ADVANCE(2);
      END_STATE();
    case 44:
      ACCEPT_TOKEN(sym_frontmatter_delimiter);
      END_STATE();
    case 45:
      ACCEPT_TOKEN(aux_sym__yaml_content_token1);
      if (lookahead == '-') ADVANCE(10);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(45);
      END_STATE();
    case 46:
      ACCEPT_TOKEN(aux_sym_yaml_line_token1);
      if (lookahead == '-' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(46);
      END_STATE();
    case 47:
      ACCEPT_TOKEN(anon_sym_COLON);
      END_STATE();
    case 48:
      ACCEPT_TOKEN(aux_sym_yaml_line_token2);
      if (lookahead == '\n') ADVANCE(42);
      if (lookahead == '\r') ADVANCE(48);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') ADVANCE(48);
      if (lookahead != 0) ADVANCE(49);
      END_STATE();
    case 49:
      ACCEPT_TOKEN(aux_sym_yaml_line_token2);
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(49);
      END_STATE();
    case 50:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_POUND);
      END_STATE();
    case 51:
      ACCEPT_TOKEN(anon_sym_RBRACE_RBRACE);
      END_STATE();
    case 52:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_SLASH);
      END_STATE();
    case 53:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE);
      if (lookahead == '!') ADVANCE(58);
      if (lookahead == '#') ADVANCE(50);
      END_STATE();
    case 54:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE);
      if (lookahead == '!') ADVANCE(58);
      if (lookahead == '#') ADVANCE(50);
      if (lookahead == '/') ADVANCE(52);
      END_STATE();
    case 55:
      ACCEPT_TOKEN(anon_sym_GT);
      END_STATE();
    case 56:
      ACCEPT_TOKEN(anon_sym_GT);
      if (lookahead == '>') ADVANCE(15);
      END_STATE();
    case 57:
      ACCEPT_TOKEN(anon_sym_else);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 58:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_BANG);
      if (lookahead == '-') ADVANCE(9);
      END_STATE();
    case 59:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token1);
      if (lookahead == '}') ADVANCE(36);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(59);
      if (lookahead != 0) ADVANCE(60);
      END_STATE();
    case 60:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token1);
      if (lookahead == '}') ADVANCE(36);
      if (lookahead != 0) ADVANCE(60);
      END_STATE();
    case 61:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_BANG_DASH_DASH);
      END_STATE();
    case 62:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token2);
      if (lookahead == '-') ADVANCE(63);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(62);
      if (lookahead != 0) ADVANCE(63);
      END_STATE();
    case 63:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token2);
      if (lookahead == '-') ADVANCE(63);
      if (lookahead != 0) ADVANCE(63);
      END_STATE();
    case 64:
      ACCEPT_TOKEN(anon_sym_DASH_DASH_RBRACE_RBRACE);
      END_STATE();
    case 65:
      ACCEPT_TOKEN(anon_sym_EQ);
      END_STATE();
    case 66:
      ACCEPT_TOKEN(aux_sym_variable_reference_token1);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(66);
      END_STATE();
    case 67:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'a') ADVANCE(72);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 68:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'e') ADVANCE(57);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 69:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'e') ADVANCE(86);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 70:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'e') ADVANCE(87);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 71:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'l') ADVANCE(74);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 72:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'l') ADVANCE(75);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 73:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'r') ADVANCE(76);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 74:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 's') ADVANCE(68);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 75:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 's') ADVANCE(70);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 76:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'u') ADVANCE(69);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 77:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 78:
      ACCEPT_TOKEN(anon_sym_DQUOTE);
      END_STATE();
    case 79:
      ACCEPT_TOKEN(aux_sym_string_literal_token1);
      if (lookahead == '\\') ADVANCE(35);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(79);
      if (lookahead != 0 &&
          lookahead != '"') ADVANCE(80);
      END_STATE();
    case 80:
      ACCEPT_TOKEN(aux_sym_string_literal_token1);
      if (lookahead == '\\') ADVANCE(35);
      if (lookahead != 0 &&
          lookahead != '"') ADVANCE(80);
      END_STATE();
    case 81:
      ACCEPT_TOKEN(anon_sym_SQUOTE);
      END_STATE();
    case 82:
      ACCEPT_TOKEN(aux_sym_string_literal_token2);
      if (lookahead == '\\') ADVANCE(34);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(82);
      if (lookahead != 0 &&
          lookahead != '\'') ADVANCE(83);
      END_STATE();
    case 83:
      ACCEPT_TOKEN(aux_sym_string_literal_token2);
      if (lookahead == '\\') ADVANCE(34);
      if (lookahead != 0 &&
          lookahead != '\'') ADVANCE(83);
      END_STATE();
    case 84:
      ACCEPT_TOKEN(sym_number);
      if (lookahead == '.') ADVANCE(32);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(84);
      END_STATE();
    case 85:
      ACCEPT_TOKEN(sym_number);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(85);
      END_STATE();
    case 86:
      ACCEPT_TOKEN(anon_sym_true);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 87:
      ACCEPT_TOKEN(anon_sym_false);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(77);
      END_STATE();
    case 88:
      ACCEPT_TOKEN(anon_sym_LT_LT_LTdotprompt_COLON);
      END_STATE();
    case 89:
      ACCEPT_TOKEN(aux_sym_dotprompt_marker_token1);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(89);
      if (lookahead != 0 &&
          lookahead != '>') ADVANCE(90);
      END_STATE();
    case 90:
      ACCEPT_TOKEN(aux_sym_dotprompt_marker_token1);
      if (lookahead != 0 &&
          lookahead != '>') ADVANCE(90);
      END_STATE();
    case 91:
      ACCEPT_TOKEN(anon_sym_GT_GT_GT);
      END_STATE();
    case 92:
      ACCEPT_TOKEN(sym_text);
      END_STATE();
    case 93:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(41);
      if (lookahead == '-') ADVANCE(98);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(101);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(93);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 94:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(92);
      if (lookahead == '-') ADVANCE(98);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(101);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(94);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 95:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(92);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(101);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(95);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 96:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(92);
      if (lookahead == '<') ADVANCE(99);
      if (lookahead == '{') ADVANCE(100);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(96);
      if (lookahead != 0) ADVANCE(102);
      END_STATE();
    case 97:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '-') ADVANCE(44);
      if (lookahead != 0 &&
          lookahead != '#' &&
          lookahead != '<' &&
          lookahead != '{') ADVANCE(102);
      END_STATE();
    case 98:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '-') ADVANCE(97);
      if (lookahead != 0 &&
          lookahead != '#' &&
          lookahead != '<' &&
          lookahead != '{') ADVANCE(102);
      END_STATE();
    case 99:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '<') ADVANCE(12);
      END_STATE();
    case 100:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '{') ADVANCE(54);
      END_STATE();
    case 101:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '{') ADVANCE(53);
      END_STATE();
    case 102:
      ACCEPT_TOKEN(sym_text);
      if (lookahead != 0 &&
          lookahead != '#' &&
          lookahead != '<' &&
          lookahead != '{') ADVANCE(102);
      END_STATE();
    default:
      return false;
  }
}

static const TSLexMode ts_lex_modes[STATE_COUNT] = {
  [0] = {.lex_state = 0},
  [1] = {.lex_state = 37},
  [2] = {.lex_state = 38},
  [3] = {.lex_state = 39},
  [4] = {.lex_state = 5},
  [5] = {.lex_state = 5},
  [6] = {.lex_state = 5},
  [7] = {.lex_state = 39},
  [8] = {.lex_state = 5},
  [9] = {.lex_state = 5},
  [10] = {.lex_state = 39},
  [11] = {.lex_state = 39},
  [12] = {.lex_state = 3},
  [13] = {.lex_state = 3},
  [14] = {.lex_state = 3},
  [15] = {.lex_state = 3},
  [16] = {.lex_state = 3},
  [17] = {.lex_state = 3},
  [18] = {.lex_state = 37},
  [19] = {.lex_state = 37},
  [20] = {.lex_state = 3},
  [21] = {.lex_state = 3},
  [22] = {.lex_state = 3},
  [23] = {.lex_state = 3},
  [24] = {.lex_state = 3},
  [25] = {.lex_state = 3},
  [26] = {.lex_state = 5},
  [27] = {.lex_state = 39},
  [28] = {.lex_state = 39},
  [29] = {.lex_state = 39},
  [30] = {.lex_state = 5},
  [31] = {.lex_state = 5},
  [32] = {.lex_state = 5},
  [33] = {.lex_state = 4},
  [34] = {.lex_state = 4},
  [35] = {.lex_state = 4},
  [36] = {.lex_state = 5},
  [37] = {.lex_state = 39},
  [38] = {.lex_state = 39},
  [39] = {.lex_state = 39},
  [40] = {.lex_state = 5},
  [41] = {.lex_state = 5},
  [42] = {.lex_state = 5},
  [43] = {.lex_state = 39},
  [44] = {.lex_state = 39},
  [45] = {.lex_state = 16},
  [46] = {.lex_state = 16},
  [47] = {.lex_state = 4},
  [48] = {.lex_state = 4},
  [49] = {.lex_state = 4},
  [50] = {.lex_state = 1},
  [51] = {.lex_state = 0},
  [52] = {.lex_state = 0},
  [53] = {.lex_state = 2},
  [54] = {.lex_state = 82},
  [55] = {.lex_state = 2},
  [56] = {.lex_state = 79},
  [57] = {.lex_state = 0},
  [58] = {.lex_state = 0},
  [59] = {.lex_state = 0},
  [60] = {.lex_state = 2},
  [61] = {.lex_state = 29},
  [62] = {.lex_state = 0},
  [63] = {.lex_state = 2},
  [64] = {.lex_state = 3},
  [65] = {.lex_state = 0},
  [66] = {.lex_state = 0},
  [67] = {.lex_state = 0},
  [68] = {.lex_state = 0},
  [69] = {.lex_state = 3},
  [70] = {.lex_state = 0},
  [71] = {.lex_state = 29},
  [72] = {.lex_state = 0},
  [73] = {.lex_state = 0},
  [74] = {.lex_state = 30},
  [75] = {.lex_state = 62},
  [76] = {.lex_state = 0},
  [77] = {.lex_state = 0},
  [78] = {.lex_state = 0},
  [79] = {.lex_state = 0},
  [80] = {.lex_state = 59},
  [81] = {.lex_state = 0},
  [82] = {.lex_state = 29},
  [83] = {.lex_state = 59},
  [84] = {.lex_state = 62},
  [85] = {.lex_state = 30},
  [86] = {.lex_state = 29},
};

static const uint16_t ts_parse_table[LARGE_STATE_COUNT][SYMBOL_COUNT] = {
  [0] = {
    [ts_builtin_sym_end] = ACTIONS(1),
    [sym_header_comment] = ACTIONS(1),
    [sym_frontmatter_delimiter] = ACTIONS(1),
    [anon_sym_COLON] = ACTIONS(1),
    [anon_sym_LBRACE_LBRACE_POUND] = ACTIONS(1),
    [anon_sym_RBRACE_RBRACE] = ACTIONS(1),
    [anon_sym_LBRACE_LBRACE_SLASH] = ACTIONS(1),
    [anon_sym_LBRACE_LBRACE] = ACTIONS(1),
    [anon_sym_GT] = ACTIONS(1),
    [anon_sym_else] = ACTIONS(1),
    [anon_sym_LBRACE_LBRACE_BANG] = ACTIONS(1),
    [anon_sym_LBRACE_LBRACE_BANG_DASH_DASH] = ACTIONS(1),
    [anon_sym_DASH_DASH_RBRACE_RBRACE] = ACTIONS(1),
    [anon_sym_EQ] = ACTIONS(1),
    [aux_sym_variable_reference_token1] = ACTIONS(1),
    [sym_path] = ACTIONS(1),
    [anon_sym_DQUOTE] = ACTIONS(1),
    [anon_sym_SQUOTE] = ACTIONS(1),
    [sym_number] = ACTIONS(1),
    [anon_sym_true] = ACTIONS(1),
    [anon_sym_false] = ACTIONS(1),
    [anon_sym_LT_LT_LTdotprompt_COLON] = ACTIONS(1),
    [anon_sym_GT_GT_GT] = ACTIONS(1),
  },
  [1] = {
    [sym_document] = STATE(73),
    [sym_license_header] = STATE(2),
    [sym_frontmatter] = STATE(7),
    [sym_template_body] = STATE(72),
    [sym__content] = STATE(10),
    [sym_handlebars_block] = STATE(10),
    [sym_block_expression] = STATE(8),
    [sym_handlebars_expression] = STATE(10),
    [sym_handlebars_comment] = STATE(10),
    [sym_dotprompt_marker] = STATE(10),
    [aux_sym_license_header_repeat1] = STATE(18),
    [aux_sym_template_body_repeat1] = STATE(10),
    [ts_builtin_sym_end] = ACTIONS(3),
    [sym_header_comment] = ACTIONS(5),
    [sym_frontmatter_delimiter] = ACTIONS(7),
    [anon_sym_LBRACE_LBRACE_POUND] = ACTIONS(9),
    [anon_sym_LBRACE_LBRACE] = ACTIONS(11),
    [anon_sym_LBRACE_LBRACE_BANG] = ACTIONS(13),
    [anon_sym_LBRACE_LBRACE_BANG_DASH_DASH] = ACTIONS(15),
    [anon_sym_LT_LT_LTdotprompt_COLON] = ACTIONS(17),
    [sym_text] = ACTIONS(19),
  },
};

static const uint16_t ts_small_parse_table[] = {
  [0] = 12,
    ACTIONS(7), 1,
      sym_frontmatter_delimiter,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(11), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(13), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(15), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(17), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(19), 1,
      sym_text,
    ACTIONS(21), 1,
      ts_builtin_sym_end,
    STATE(3), 1,
      sym_frontmatter,
    STATE(8), 1,
      sym_block_expression,
    STATE(62), 1,
      sym_template_body,
    STATE(10), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [42] = 10,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(11), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(13), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(15), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(17), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(19), 1,
      sym_text,
    ACTIONS(23), 1,
      ts_builtin_sym_end,
    STATE(8), 1,
      sym_block_expression,
    STATE(68), 1,
      sym_template_body,
    STATE(10), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [78] = 10,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(25), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(27), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(29), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(31), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(33), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(35), 1,
      sym_text,
    STATE(5), 1,
      sym_block_expression,
    STATE(41), 1,
      sym_close_block,
    STATE(9), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [114] = 10,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(25), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(27), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(29), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(31), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(33), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(37), 1,
      sym_text,
    STATE(5), 1,
      sym_block_expression,
    STATE(30), 1,
      sym_close_block,
    STATE(4), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [150] = 10,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(27), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(29), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(31), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(33), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(35), 1,
      sym_text,
    ACTIONS(39), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    STATE(5), 1,
      sym_block_expression,
    STATE(39), 1,
      sym_close_block,
    STATE(9), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [186] = 10,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(11), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(13), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(15), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(17), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(19), 1,
      sym_text,
    ACTIONS(21), 1,
      ts_builtin_sym_end,
    STATE(8), 1,
      sym_block_expression,
    STATE(62), 1,
      sym_template_body,
    STATE(10), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [222] = 10,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(27), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(29), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(31), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(33), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(39), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(41), 1,
      sym_text,
    STATE(5), 1,
      sym_block_expression,
    STATE(29), 1,
      sym_close_block,
    STATE(6), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [258] = 9,
    ACTIONS(43), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(46), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(48), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(51), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(54), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(57), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(60), 1,
      sym_text,
    STATE(5), 1,
      sym_block_expression,
    STATE(9), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [291] = 9,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(11), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(13), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(15), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(17), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(63), 1,
      ts_builtin_sym_end,
    ACTIONS(65), 1,
      sym_text,
    STATE(8), 1,
      sym_block_expression,
    STATE(11), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [324] = 9,
    ACTIONS(43), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(67), 1,
      ts_builtin_sym_end,
    ACTIONS(69), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(72), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(75), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(78), 1,
      anon_sym_LT_LT_LTdotprompt_COLON,
    ACTIONS(81), 1,
      sym_text,
    STATE(8), 1,
      sym_block_expression,
    STATE(11), 6,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      sym_dotprompt_marker,
      aux_sym_template_body_repeat1,
  [357] = 9,
    ACTIONS(84), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(86), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(88), 1,
      sym_path,
    ACTIONS(90), 1,
      anon_sym_DQUOTE,
    ACTIONS(92), 1,
      anon_sym_SQUOTE,
    ACTIONS(94), 1,
      sym_number,
    ACTIONS(96), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(16), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(21), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [390] = 9,
    ACTIONS(98), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(100), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(103), 1,
      sym_path,
    ACTIONS(106), 1,
      anon_sym_DQUOTE,
    ACTIONS(109), 1,
      anon_sym_SQUOTE,
    ACTIONS(112), 1,
      sym_number,
    ACTIONS(115), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(13), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(21), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [423] = 9,
    ACTIONS(86), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(88), 1,
      sym_path,
    ACTIONS(90), 1,
      anon_sym_DQUOTE,
    ACTIONS(92), 1,
      anon_sym_SQUOTE,
    ACTIONS(94), 1,
      sym_number,
    ACTIONS(118), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(96), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(15), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(21), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [456] = 9,
    ACTIONS(86), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(88), 1,
      sym_path,
    ACTIONS(90), 1,
      anon_sym_DQUOTE,
    ACTIONS(92), 1,
      anon_sym_SQUOTE,
    ACTIONS(94), 1,
      sym_number,
    ACTIONS(120), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(96), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(13), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(21), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [489] = 9,
    ACTIONS(86), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(88), 1,
      sym_path,
    ACTIONS(90), 1,
      anon_sym_DQUOTE,
    ACTIONS(92), 1,
      anon_sym_SQUOTE,
    ACTIONS(94), 1,
      sym_number,
    ACTIONS(122), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(96), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(13), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(21), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [522] = 7,
    ACTIONS(86), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(90), 1,
      anon_sym_DQUOTE,
    ACTIONS(92), 1,
      anon_sym_SQUOTE,
    ACTIONS(124), 1,
      sym_path,
    ACTIONS(126), 1,
      sym_number,
    ACTIONS(96), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(24), 3,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [547] = 4,
    ACTIONS(128), 1,
      ts_builtin_sym_end,
    ACTIONS(130), 1,
      sym_header_comment,
    STATE(19), 1,
      aux_sym_license_header_repeat1,
    ACTIONS(132), 7,
      sym_frontmatter_delimiter,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [566] = 4,
    ACTIONS(134), 1,
      ts_builtin_sym_end,
    ACTIONS(136), 1,
      sym_header_comment,
    STATE(19), 1,
      aux_sym_license_header_repeat1,
    ACTIONS(139), 7,
      sym_frontmatter_delimiter,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [585] = 3,
    ACTIONS(141), 1,
      anon_sym_EQ,
    ACTIONS(143), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(118), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [601] = 2,
    ACTIONS(147), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(145), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [614] = 2,
    ACTIONS(143), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(118), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [627] = 2,
    ACTIONS(151), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(149), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [640] = 2,
    ACTIONS(155), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(153), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [653] = 2,
    ACTIONS(159), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(157), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [666] = 1,
    ACTIONS(161), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [676] = 2,
    ACTIONS(163), 1,
      ts_builtin_sym_end,
    ACTIONS(165), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [688] = 2,
    ACTIONS(167), 1,
      ts_builtin_sym_end,
    ACTIONS(169), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [700] = 2,
    ACTIONS(171), 1,
      ts_builtin_sym_end,
    ACTIONS(173), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [712] = 1,
    ACTIONS(173), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [722] = 1,
    ACTIONS(175), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [732] = 1,
    ACTIONS(177), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [742] = 5,
    ACTIONS(181), 1,
      sym_frontmatter_delimiter,
    ACTIONS(183), 1,
      aux_sym_yaml_line_token1,
    STATE(35), 1,
      aux_sym_frontmatter_repeat1,
    ACTIONS(179), 2,
      sym_header_comment,
      aux_sym__yaml_content_token1,
    STATE(49), 2,
      sym__yaml_content,
      sym_yaml_line,
  [760] = 5,
    ACTIONS(188), 1,
      sym_frontmatter_delimiter,
    ACTIONS(190), 1,
      aux_sym_yaml_line_token1,
    STATE(34), 1,
      aux_sym_frontmatter_repeat1,
    ACTIONS(185), 2,
      sym_header_comment,
      aux_sym__yaml_content_token1,
    STATE(49), 2,
      sym__yaml_content,
      sym_yaml_line,
  [778] = 5,
    ACTIONS(183), 1,
      aux_sym_yaml_line_token1,
    ACTIONS(193), 1,
      sym_frontmatter_delimiter,
    STATE(34), 1,
      aux_sym_frontmatter_repeat1,
    ACTIONS(179), 2,
      sym_header_comment,
      aux_sym__yaml_content_token1,
    STATE(49), 2,
      sym__yaml_content,
      sym_yaml_line,
  [796] = 1,
    ACTIONS(195), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [806] = 2,
    ACTIONS(197), 1,
      ts_builtin_sym_end,
    ACTIONS(199), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [818] = 2,
    ACTIONS(201), 1,
      ts_builtin_sym_end,
    ACTIONS(203), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [830] = 2,
    ACTIONS(205), 1,
      ts_builtin_sym_end,
    ACTIONS(207), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [842] = 1,
    ACTIONS(199), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [852] = 1,
    ACTIONS(207), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [862] = 1,
    ACTIONS(165), 7,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [872] = 2,
    ACTIONS(209), 1,
      ts_builtin_sym_end,
    ACTIONS(175), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [884] = 2,
    ACTIONS(211), 1,
      ts_builtin_sym_end,
    ACTIONS(161), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      anon_sym_LT_LT_LTdotprompt_COLON,
      sym_text,
  [896] = 6,
    ACTIONS(86), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(213), 1,
      anon_sym_GT,
    ACTIONS(215), 1,
      anon_sym_else,
    ACTIONS(217), 1,
      sym_path,
    STATE(67), 1,
      sym_variable_reference,
    STATE(76), 1,
      sym_expression_content,
  [915] = 6,
    ACTIONS(86), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(213), 1,
      anon_sym_GT,
    ACTIONS(215), 1,
      anon_sym_else,
    ACTIONS(217), 1,
      sym_path,
    STATE(67), 1,
      sym_variable_reference,
    STATE(79), 1,
      sym_expression_content,
  [934] = 1,
    ACTIONS(219), 4,
      sym_header_comment,
      sym_frontmatter_delimiter,
      aux_sym__yaml_content_token1,
      aux_sym_yaml_line_token1,
  [941] = 1,
    ACTIONS(221), 4,
      sym_header_comment,
      sym_frontmatter_delimiter,
      aux_sym__yaml_content_token1,
      aux_sym_yaml_line_token1,
  [948] = 1,
    ACTIONS(223), 4,
      sym_header_comment,
      sym_frontmatter_delimiter,
      aux_sym__yaml_content_token1,
      aux_sym_yaml_line_token1,
  [955] = 2,
    ACTIONS(225), 1,
      aux_sym_frontmatter_token1,
    ACTIONS(227), 1,
      aux_sym_yaml_line_token2,
  [962] = 1,
    ACTIONS(229), 1,
      anon_sym_RBRACE_RBRACE,
  [966] = 1,
    ACTIONS(231), 1,
      anon_sym_RBRACE_RBRACE,
  [970] = 1,
    ACTIONS(233), 1,
      aux_sym_frontmatter_token1,
  [974] = 1,
    ACTIONS(235), 1,
      aux_sym_string_literal_token2,
  [978] = 1,
    ACTIONS(237), 1,
      aux_sym_frontmatter_token1,
  [982] = 1,
    ACTIONS(239), 1,
      aux_sym_string_literal_token1,
  [986] = 1,
    ACTIONS(241), 1,
      anon_sym_DQUOTE,
  [990] = 1,
    ACTIONS(241), 1,
      anon_sym_SQUOTE,
  [994] = 1,
    ACTIONS(243), 1,
      anon_sym_COLON,
  [998] = 1,
    ACTIONS(245), 1,
      aux_sym_frontmatter_token1,
  [1002] = 1,
    ACTIONS(247), 1,
      sym_path,
  [1006] = 1,
    ACTIONS(23), 1,
      ts_builtin_sym_end,
  [1010] = 1,
    ACTIONS(249), 1,
      aux_sym_frontmatter_token1,
  [1014] = 1,
    ACTIONS(251), 1,
      anon_sym_GT_GT_GT,
  [1018] = 1,
    ACTIONS(229), 1,
      anon_sym_DASH_DASH_RBRACE_RBRACE,
  [1022] = 1,
    ACTIONS(253), 1,
      anon_sym_RBRACE_RBRACE,
  [1026] = 1,
    ACTIONS(255), 1,
      anon_sym_RBRACE_RBRACE,
  [1030] = 1,
    ACTIONS(257), 1,
      ts_builtin_sym_end,
  [1034] = 1,
    ACTIONS(259), 1,
      anon_sym_GT_GT_GT,
  [1038] = 1,
    ACTIONS(261), 1,
      anon_sym_RBRACE_RBRACE,
  [1042] = 1,
    ACTIONS(263), 1,
      sym_path,
  [1046] = 1,
    ACTIONS(21), 1,
      ts_builtin_sym_end,
  [1050] = 1,
    ACTIONS(265), 1,
      ts_builtin_sym_end,
  [1054] = 1,
    ACTIONS(267), 1,
      aux_sym_dotprompt_marker_token1,
  [1058] = 1,
    ACTIONS(269), 1,
      aux_sym_handlebars_comment_token2,
  [1062] = 1,
    ACTIONS(271), 1,
      anon_sym_RBRACE_RBRACE,
  [1066] = 1,
    ACTIONS(273), 1,
      anon_sym_RBRACE_RBRACE,
  [1070] = 1,
    ACTIONS(273), 1,
      anon_sym_DASH_DASH_RBRACE_RBRACE,
  [1074] = 1,
    ACTIONS(275), 1,
      anon_sym_RBRACE_RBRACE,
  [1078] = 1,
    ACTIONS(277), 1,
      aux_sym_handlebars_comment_token1,
  [1082] = 1,
    ACTIONS(279), 1,
      anon_sym_RBRACE_RBRACE,
  [1086] = 1,
    ACTIONS(281), 1,
      sym_path,
  [1090] = 1,
    ACTIONS(283), 1,
      aux_sym_handlebars_comment_token1,
  [1094] = 1,
    ACTIONS(285), 1,
      aux_sym_handlebars_comment_token2,
  [1098] = 1,
    ACTIONS(287), 1,
      aux_sym_dotprompt_marker_token1,
  [1102] = 1,
    ACTIONS(289), 1,
      sym_path,
};

static const uint32_t ts_small_parse_table_map[] = {
  [SMALL_STATE(2)] = 0,
  [SMALL_STATE(3)] = 42,
  [SMALL_STATE(4)] = 78,
  [SMALL_STATE(5)] = 114,
  [SMALL_STATE(6)] = 150,
  [SMALL_STATE(7)] = 186,
  [SMALL_STATE(8)] = 222,
  [SMALL_STATE(9)] = 258,
  [SMALL_STATE(10)] = 291,
  [SMALL_STATE(11)] = 324,
  [SMALL_STATE(12)] = 357,
  [SMALL_STATE(13)] = 390,
  [SMALL_STATE(14)] = 423,
  [SMALL_STATE(15)] = 456,
  [SMALL_STATE(16)] = 489,
  [SMALL_STATE(17)] = 522,
  [SMALL_STATE(18)] = 547,
  [SMALL_STATE(19)] = 566,
  [SMALL_STATE(20)] = 585,
  [SMALL_STATE(21)] = 601,
  [SMALL_STATE(22)] = 614,
  [SMALL_STATE(23)] = 627,
  [SMALL_STATE(24)] = 640,
  [SMALL_STATE(25)] = 653,
  [SMALL_STATE(26)] = 666,
  [SMALL_STATE(27)] = 676,
  [SMALL_STATE(28)] = 688,
  [SMALL_STATE(29)] = 700,
  [SMALL_STATE(30)] = 712,
  [SMALL_STATE(31)] = 722,
  [SMALL_STATE(32)] = 732,
  [SMALL_STATE(33)] = 742,
  [SMALL_STATE(34)] = 760,
  [SMALL_STATE(35)] = 778,
  [SMALL_STATE(36)] = 796,
  [SMALL_STATE(37)] = 806,
  [SMALL_STATE(38)] = 818,
  [SMALL_STATE(39)] = 830,
  [SMALL_STATE(40)] = 842,
  [SMALL_STATE(41)] = 852,
  [SMALL_STATE(42)] = 862,
  [SMALL_STATE(43)] = 872,
  [SMALL_STATE(44)] = 884,
  [SMALL_STATE(45)] = 896,
  [SMALL_STATE(46)] = 915,
  [SMALL_STATE(47)] = 934,
  [SMALL_STATE(48)] = 941,
  [SMALL_STATE(49)] = 948,
  [SMALL_STATE(50)] = 955,
  [SMALL_STATE(51)] = 962,
  [SMALL_STATE(52)] = 966,
  [SMALL_STATE(53)] = 970,
  [SMALL_STATE(54)] = 974,
  [SMALL_STATE(55)] = 978,
  [SMALL_STATE(56)] = 982,
  [SMALL_STATE(57)] = 986,
  [SMALL_STATE(58)] = 990,
  [SMALL_STATE(59)] = 994,
  [SMALL_STATE(60)] = 998,
  [SMALL_STATE(61)] = 1002,
  [SMALL_STATE(62)] = 1006,
  [SMALL_STATE(63)] = 1010,
  [SMALL_STATE(64)] = 1014,
  [SMALL_STATE(65)] = 1018,
  [SMALL_STATE(66)] = 1022,
  [SMALL_STATE(67)] = 1026,
  [SMALL_STATE(68)] = 1030,
  [SMALL_STATE(69)] = 1034,
  [SMALL_STATE(70)] = 1038,
  [SMALL_STATE(71)] = 1042,
  [SMALL_STATE(72)] = 1046,
  [SMALL_STATE(73)] = 1050,
  [SMALL_STATE(74)] = 1054,
  [SMALL_STATE(75)] = 1058,
  [SMALL_STATE(76)] = 1062,
  [SMALL_STATE(77)] = 1066,
  [SMALL_STATE(78)] = 1070,
  [SMALL_STATE(79)] = 1074,
  [SMALL_STATE(80)] = 1078,
  [SMALL_STATE(81)] = 1082,
  [SMALL_STATE(82)] = 1086,
  [SMALL_STATE(83)] = 1090,
  [SMALL_STATE(84)] = 1094,
  [SMALL_STATE(85)] = 1098,
  [SMALL_STATE(86)] = 1102,
};

static const TSParseActionEntry ts_parse_actions[] = {
  [0] = {.entry = {.count = 0, .reusable = false}},
  [1] = {.entry = {.count = 1, .reusable = false}}, RECOVER(),
  [3] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 0, 0, 0),
  [5] = {.entry = {.count = 1, .reusable = false}}, SHIFT(18),
  [7] = {.entry = {.count = 1, .reusable = false}}, SHIFT(53),
  [9] = {.entry = {.count = 1, .reusable = false}}, SHIFT(82),
  [11] = {.entry = {.count = 1, .reusable = false}}, SHIFT(46),
  [13] = {.entry = {.count = 1, .reusable = false}}, SHIFT(80),
  [15] = {.entry = {.count = 1, .reusable = false}}, SHIFT(75),
  [17] = {.entry = {.count = 1, .reusable = false}}, SHIFT(74),
  [19] = {.entry = {.count = 1, .reusable = false}}, SHIFT(10),
  [21] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 1, 0, 0),
  [23] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 2, 0, 0),
  [25] = {.entry = {.count = 1, .reusable = false}}, SHIFT(86),
  [27] = {.entry = {.count = 1, .reusable = false}}, SHIFT(45),
  [29] = {.entry = {.count = 1, .reusable = false}}, SHIFT(83),
  [31] = {.entry = {.count = 1, .reusable = false}}, SHIFT(84),
  [33] = {.entry = {.count = 1, .reusable = false}}, SHIFT(85),
  [35] = {.entry = {.count = 1, .reusable = false}}, SHIFT(9),
  [37] = {.entry = {.count = 1, .reusable = false}}, SHIFT(4),
  [39] = {.entry = {.count = 1, .reusable = false}}, SHIFT(61),
  [41] = {.entry = {.count = 1, .reusable = false}}, SHIFT(6),
  [43] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(82),
  [46] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0),
  [48] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(45),
  [51] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(83),
  [54] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(84),
  [57] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(85),
  [60] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(9),
  [63] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_template_body, 1, 0, 0),
  [65] = {.entry = {.count = 1, .reusable = false}}, SHIFT(11),
  [67] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0),
  [69] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(46),
  [72] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(80),
  [75] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(75),
  [78] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(74),
  [81] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(11),
  [84] = {.entry = {.count = 1, .reusable = true}}, SHIFT(36),
  [86] = {.entry = {.count = 1, .reusable = true}}, SHIFT(22),
  [88] = {.entry = {.count = 1, .reusable = false}}, SHIFT(20),
  [90] = {.entry = {.count = 1, .reusable = true}}, SHIFT(56),
  [92] = {.entry = {.count = 1, .reusable = true}}, SHIFT(54),
  [94] = {.entry = {.count = 1, .reusable = true}}, SHIFT(21),
  [96] = {.entry = {.count = 1, .reusable = false}}, SHIFT(25),
  [98] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0),
  [100] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(22),
  [103] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(20),
  [106] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(56),
  [109] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(54),
  [112] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(21),
  [115] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(25),
  [118] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_variable_reference, 1, 0, 0),
  [120] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 2, 0, 4),
  [122] = {.entry = {.count = 1, .reusable = true}}, SHIFT(32),
  [124] = {.entry = {.count = 1, .reusable = false}}, SHIFT(22),
  [126] = {.entry = {.count = 1, .reusable = true}}, SHIFT(24),
  [128] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_license_header, 1, 0, 0),
  [130] = {.entry = {.count = 1, .reusable = false}}, SHIFT(19),
  [132] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_license_header, 1, 0, 0),
  [134] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_license_header_repeat1, 2, 0, 0),
  [136] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_license_header_repeat1, 2, 0, 0), SHIFT_REPEAT(19),
  [139] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_license_header_repeat1, 2, 0, 0),
  [141] = {.entry = {.count = 1, .reusable = true}}, SHIFT(17),
  [143] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_variable_reference, 1, 0, 0),
  [145] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_argument, 1, 0, 0),
  [147] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_argument, 1, 0, 0),
  [149] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_string_literal, 3, 0, 0),
  [151] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_string_literal, 3, 0, 0),
  [153] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_hash_param, 3, 0, 7),
  [155] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_hash_param, 3, 0, 7),
  [157] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_boolean, 1, 0, 0),
  [159] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_boolean, 1, 0, 0),
  [161] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_comment, 3, 0, 0),
  [163] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_close_block, 3, 0, 2),
  [165] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_close_block, 3, 0, 2),
  [167] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_frontmatter, 5, 0, 6),
  [169] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_frontmatter, 5, 0, 6),
  [171] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_block, 2, 0, 0),
  [173] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_block, 2, 0, 0),
  [175] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_expression, 3, 0, 0),
  [177] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_block_expression, 4, 0, 2),
  [179] = {.entry = {.count = 1, .reusable = false}}, SHIFT(49),
  [181] = {.entry = {.count = 1, .reusable = false}}, SHIFT(60),
  [183] = {.entry = {.count = 1, .reusable = false}}, SHIFT(59),
  [185] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 2, 0, 0), SHIFT_REPEAT(49),
  [188] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 2, 0, 0),
  [190] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 2, 0, 0), SHIFT_REPEAT(59),
  [193] = {.entry = {.count = 1, .reusable = false}}, SHIFT(55),
  [195] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_block_expression, 3, 0, 2),
  [197] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_dotprompt_marker, 3, 0, 0),
  [199] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_dotprompt_marker, 3, 0, 0),
  [201] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_frontmatter, 4, 0, 0),
  [203] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_frontmatter, 4, 0, 0),
  [205] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_block, 3, 0, 0),
  [207] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_block, 3, 0, 0),
  [209] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_expression, 3, 0, 0),
  [211] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_comment, 3, 0, 0),
  [213] = {.entry = {.count = 1, .reusable = true}}, SHIFT(71),
  [215] = {.entry = {.count = 1, .reusable = false}}, SHIFT(70),
  [217] = {.entry = {.count = 1, .reusable = false}}, SHIFT(14),
  [219] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_yaml_line, 3, 0, 5),
  [221] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_yaml_line, 4, 0, 8),
  [223] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 1, 0, 0),
  [225] = {.entry = {.count = 1, .reusable = false}}, SHIFT(47),
  [227] = {.entry = {.count = 1, .reusable = false}}, SHIFT(63),
  [229] = {.entry = {.count = 1, .reusable = true}}, SHIFT(44),
  [231] = {.entry = {.count = 1, .reusable = true}}, SHIFT(27),
  [233] = {.entry = {.count = 1, .reusable = true}}, SHIFT(33),
  [235] = {.entry = {.count = 1, .reusable = true}}, SHIFT(58),
  [237] = {.entry = {.count = 1, .reusable = true}}, SHIFT(28),
  [239] = {.entry = {.count = 1, .reusable = true}}, SHIFT(57),
  [241] = {.entry = {.count = 1, .reusable = true}}, SHIFT(23),
  [243] = {.entry = {.count = 1, .reusable = true}}, SHIFT(50),
  [245] = {.entry = {.count = 1, .reusable = true}}, SHIFT(38),
  [247] = {.entry = {.count = 1, .reusable = true}}, SHIFT(52),
  [249] = {.entry = {.count = 1, .reusable = true}}, SHIFT(48),
  [251] = {.entry = {.count = 1, .reusable = true}}, SHIFT(37),
  [253] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 2, 0, 3),
  [255] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 1, 0, 1),
  [257] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 3, 0, 0),
  [259] = {.entry = {.count = 1, .reusable = true}}, SHIFT(40),
  [261] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 1, 0, 0),
  [263] = {.entry = {.count = 1, .reusable = true}}, SHIFT(66),
  [265] = {.entry = {.count = 1, .reusable = true}},  ACCEPT_INPUT(),
  [267] = {.entry = {.count = 1, .reusable = true}}, SHIFT(64),
  [269] = {.entry = {.count = 1, .reusable = true}}, SHIFT(65),
  [271] = {.entry = {.count = 1, .reusable = true}}, SHIFT(31),
  [273] = {.entry = {.count = 1, .reusable = true}}, SHIFT(26),
  [275] = {.entry = {.count = 1, .reusable = true}}, SHIFT(43),
  [277] = {.entry = {.count = 1, .reusable = true}}, SHIFT(51),
  [279] = {.entry = {.count = 1, .reusable = true}}, SHIFT(42),
  [281] = {.entry = {.count = 1, .reusable = true}}, SHIFT(12),
  [283] = {.entry = {.count = 1, .reusable = true}}, SHIFT(77),
  [285] = {.entry = {.count = 1, .reusable = true}}, SHIFT(78),
  [287] = {.entry = {.count = 1, .reusable = true}}, SHIFT(69),
  [289] = {.entry = {.count = 1, .reusable = true}}, SHIFT(81),
};

#ifdef __cplusplus
extern "C" {
#endif
#ifdef TREE_SITTER_HIDE_SYMBOLS
#define TS_PUBLIC
#elif defined(_WIN32)
#define TS_PUBLIC __declspec(dllexport)
#else
#define TS_PUBLIC __attribute__((visibility("default")))
#endif

TS_PUBLIC const TSLanguage *tree_sitter_dotprompt(void) {
  static const TSLanguage language = {
    .version = LANGUAGE_VERSION,
    .symbol_count = SYMBOL_COUNT,
    .alias_count = ALIAS_COUNT,
    .token_count = TOKEN_COUNT,
    .external_token_count = EXTERNAL_TOKEN_COUNT,
    .state_count = STATE_COUNT,
    .large_state_count = LARGE_STATE_COUNT,
    .production_id_count = PRODUCTION_ID_COUNT,
    .field_count = FIELD_COUNT,
    .max_alias_sequence_length = MAX_ALIAS_SEQUENCE_LENGTH,
    .parse_table = &ts_parse_table[0][0],
    .small_parse_table = ts_small_parse_table,
    .small_parse_table_map = ts_small_parse_table_map,
    .parse_actions = ts_parse_actions,
    .symbol_names = ts_symbol_names,
    .field_names = ts_field_names,
    .field_map_slices = ts_field_map_slices,
    .field_map_entries = ts_field_map_entries,
    .symbol_metadata = ts_symbol_metadata,
    .public_symbol_map = ts_symbol_map,
    .alias_map = ts_non_terminal_alias_map,
    .alias_sequences = &ts_alias_sequences[0][0],
    .lex_modes = ts_lex_modes,
    .lex_fn = ts_lex,
    .primary_state_ids = ts_primary_state_ids,
  };
  return &language;
}
#ifdef __cplusplus
}
#endif
