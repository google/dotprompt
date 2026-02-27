#include "tree_sitter/parser.h"

#if defined(__GNUC__) || defined(__clang__)
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"
#endif

#define LANGUAGE_VERSION 14
#define STATE_COUNT 81
#define LARGE_STATE_COUNT 2
#define SYMBOL_COUNT 52
#define ALIAS_COUNT 5
#define TOKEN_COUNT 30
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
  sym_text = 29,
  sym_document = 30,
  sym_license_header = 31,
  sym_frontmatter = 32,
  sym__yaml_content = 33,
  sym_yaml_line = 34,
  sym_template_body = 35,
  sym__content = 36,
  sym_handlebars_block = 37,
  sym_block_expression = 38,
  sym_close_block = 39,
  sym_handlebars_expression = 40,
  sym_expression_content = 41,
  sym_handlebars_comment = 42,
  sym_argument = 43,
  sym_hash_param = 44,
  sym_variable_reference = 45,
  sym_string_literal = 46,
  sym_boolean = 47,
  aux_sym_license_header_repeat1 = 48,
  aux_sym_frontmatter_repeat1 = 49,
  aux_sym_template_body_repeat1 = 50,
  aux_sym_block_expression_repeat1 = 51,
  alias_sym_block_name = 52,
  alias_sym_helper_name = 53,
  alias_sym_key = 54,
  alias_sym_partial_reference = 55,
  alias_sym_yaml_content = 56,
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
  [6] = 6,
  [7] = 7,
  [8] = 8,
  [9] = 9,
  [10] = 10,
  [11] = 8,
  [12] = 9,
  [13] = 13,
  [14] = 14,
  [15] = 14,
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
  [30] = 30,
  [31] = 31,
  [32] = 32,
  [33] = 31,
  [34] = 34,
  [35] = 35,
  [36] = 34,
  [37] = 37,
  [38] = 38,
  [39] = 39,
  [40] = 40,
  [41] = 37,
  [42] = 29,
  [43] = 39,
  [44] = 30,
  [45] = 45,
  [46] = 46,
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
  [69] = 69,
  [70] = 70,
  [71] = 71,
  [72] = 50,
  [73] = 64,
  [74] = 49,
  [75] = 75,
  [76] = 56,
  [77] = 77,
  [78] = 75,
  [79] = 71,
  [80] = 59,
};

static bool ts_lex(TSLexer *lexer, TSStateId state) {
  START_LEXER();
  eof = lexer->eof(lexer);
  switch (state) {
    case 0:
      if (eof) ADVANCE(25);
      ADVANCE_MAP(
        '"', 62,
        '#', 26,
        '\'', 65,
        '-', 6,
        ':', 32,
        '=', 49,
        '>', 40,
        '@', 18,
        'e', 55,
        'f', 51,
        't', 57,
        '{', 12,
        '}', 13,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(0);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(68);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 1:
      if (lookahead == '\n') ADVANCE(27);
      if (lookahead == '\r') ADVANCE(33);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') ADVANCE(33);
      if (lookahead != 0) ADVANCE(34);
      END_STATE();
    case 2:
      if (lookahead == '\n') ADVANCE(28);
      if (lookahead == '\r') ADVANCE(2);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') SKIP(2);
      END_STATE();
    case 3:
      ADVANCE_MAP(
        '"', 62,
        '\'', 65,
        '-', 16,
        '=', 49,
        '@', 18,
        'f', 51,
        't', 57,
        '}', 13,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(3);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(68);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 4:
      if (lookahead == '#') ADVANCE(26);
      if (lookahead == '-') ADVANCE(10);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(30);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(31);
      END_STATE();
    case 5:
      if (lookahead == '#') ADVANCE(72);
      if (lookahead == '{') ADVANCE(79);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(76);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 6:
      if (lookahead == '-') ADVANCE(8);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(68);
      END_STATE();
    case 7:
      if (lookahead == '-') ADVANCE(29);
      END_STATE();
    case 8:
      if (lookahead == '-') ADVANCE(29);
      if (lookahead == '}') ADVANCE(14);
      END_STATE();
    case 9:
      if (lookahead == '-') ADVANCE(45);
      END_STATE();
    case 10:
      if (lookahead == '-') ADVANCE(7);
      END_STATE();
    case 11:
      if (lookahead == '>') ADVANCE(40);
      if (lookahead == '@') ADVANCE(18);
      if (lookahead == 'e') ADVANCE(55);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(11);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 12:
      if (lookahead == '{') ADVANCE(39);
      END_STATE();
    case 13:
      if (lookahead == '}') ADVANCE(36);
      END_STATE();
    case 14:
      if (lookahead == '}') ADVANCE(48);
      END_STATE();
    case 15:
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(15);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 16:
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(68);
      END_STATE();
    case 17:
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(69);
      END_STATE();
    case 18:
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(50);
      END_STATE();
    case 19:
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(67);
      END_STATE();
    case 20:
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(64);
      END_STATE();
    case 21:
      if (lookahead != 0 &&
          lookahead != '}') ADVANCE(44);
      END_STATE();
    case 22:
      if (eof) ADVANCE(25);
      if (lookahead == '#') ADVANCE(26);
      if (lookahead == '-') ADVANCE(78);
      if (lookahead == '{') ADVANCE(80);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(73);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 23:
      if (eof) ADVANCE(25);
      if (lookahead == '#') ADVANCE(72);
      if (lookahead == '-') ADVANCE(78);
      if (lookahead == '{') ADVANCE(80);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(74);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 24:
      if (eof) ADVANCE(25);
      if (lookahead == '#') ADVANCE(72);
      if (lookahead == '{') ADVANCE(80);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(75);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 25:
      ACCEPT_TOKEN(ts_builtin_sym_end);
      END_STATE();
    case 26:
      ACCEPT_TOKEN(sym_header_comment);
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(26);
      END_STATE();
    case 27:
      ACCEPT_TOKEN(aux_sym_frontmatter_token1);
      if (lookahead == '\n') ADVANCE(27);
      if (lookahead == '\r') ADVANCE(33);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') ADVANCE(33);
      END_STATE();
    case 28:
      ACCEPT_TOKEN(aux_sym_frontmatter_token1);
      if (lookahead == '\n') ADVANCE(28);
      if (lookahead == '\r') ADVANCE(2);
      END_STATE();
    case 29:
      ACCEPT_TOKEN(sym_frontmatter_delimiter);
      END_STATE();
    case 30:
      ACCEPT_TOKEN(aux_sym__yaml_content_token1);
      if (lookahead == '-') ADVANCE(10);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(30);
      END_STATE();
    case 31:
      ACCEPT_TOKEN(aux_sym_yaml_line_token1);
      if (lookahead == '-' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(31);
      END_STATE();
    case 32:
      ACCEPT_TOKEN(anon_sym_COLON);
      END_STATE();
    case 33:
      ACCEPT_TOKEN(aux_sym_yaml_line_token2);
      if (lookahead == '\n') ADVANCE(27);
      if (lookahead == '\r') ADVANCE(33);
      if (('\t' <= lookahead && lookahead <= '\f') ||
          lookahead == ' ') ADVANCE(33);
      if (lookahead != 0) ADVANCE(34);
      END_STATE();
    case 34:
      ACCEPT_TOKEN(aux_sym_yaml_line_token2);
      if (lookahead != 0 &&
          lookahead != '\n') ADVANCE(34);
      END_STATE();
    case 35:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_POUND);
      END_STATE();
    case 36:
      ACCEPT_TOKEN(anon_sym_RBRACE_RBRACE);
      END_STATE();
    case 37:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_SLASH);
      END_STATE();
    case 38:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE);
      if (lookahead == '!') ADVANCE(42);
      if (lookahead == '#') ADVANCE(35);
      END_STATE();
    case 39:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE);
      if (lookahead == '!') ADVANCE(42);
      if (lookahead == '#') ADVANCE(35);
      if (lookahead == '/') ADVANCE(37);
      END_STATE();
    case 40:
      ACCEPT_TOKEN(anon_sym_GT);
      END_STATE();
    case 41:
      ACCEPT_TOKEN(anon_sym_else);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 42:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_BANG);
      if (lookahead == '-') ADVANCE(9);
      END_STATE();
    case 43:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token1);
      if (lookahead == '}') ADVANCE(21);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(43);
      if (lookahead != 0) ADVANCE(44);
      END_STATE();
    case 44:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token1);
      if (lookahead == '}') ADVANCE(21);
      if (lookahead != 0) ADVANCE(44);
      END_STATE();
    case 45:
      ACCEPT_TOKEN(anon_sym_LBRACE_LBRACE_BANG_DASH_DASH);
      END_STATE();
    case 46:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token2);
      if (lookahead == '-') ADVANCE(47);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(46);
      if (lookahead != 0) ADVANCE(47);
      END_STATE();
    case 47:
      ACCEPT_TOKEN(aux_sym_handlebars_comment_token2);
      if (lookahead == '-') ADVANCE(47);
      if (lookahead != 0) ADVANCE(47);
      END_STATE();
    case 48:
      ACCEPT_TOKEN(anon_sym_DASH_DASH_RBRACE_RBRACE);
      END_STATE();
    case 49:
      ACCEPT_TOKEN(anon_sym_EQ);
      END_STATE();
    case 50:
      ACCEPT_TOKEN(aux_sym_variable_reference_token1);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(50);
      END_STATE();
    case 51:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'a') ADVANCE(56);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 52:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'e') ADVANCE(41);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 53:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'e') ADVANCE(70);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 54:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'e') ADVANCE(71);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 55:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'l') ADVANCE(58);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 56:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'l') ADVANCE(59);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 57:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'r') ADVANCE(60);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 58:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 's') ADVANCE(52);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 59:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 's') ADVANCE(54);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 60:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == 'u') ADVANCE(53);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 61:
      ACCEPT_TOKEN(sym_path);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 62:
      ACCEPT_TOKEN(anon_sym_DQUOTE);
      END_STATE();
    case 63:
      ACCEPT_TOKEN(aux_sym_string_literal_token1);
      if (lookahead == '\\') ADVANCE(20);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(63);
      if (lookahead != 0 &&
          lookahead != '"') ADVANCE(64);
      END_STATE();
    case 64:
      ACCEPT_TOKEN(aux_sym_string_literal_token1);
      if (lookahead == '\\') ADVANCE(20);
      if (lookahead != 0 &&
          lookahead != '"') ADVANCE(64);
      END_STATE();
    case 65:
      ACCEPT_TOKEN(anon_sym_SQUOTE);
      END_STATE();
    case 66:
      ACCEPT_TOKEN(aux_sym_string_literal_token2);
      if (lookahead == '\\') ADVANCE(19);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(66);
      if (lookahead != 0 &&
          lookahead != '\'') ADVANCE(67);
      END_STATE();
    case 67:
      ACCEPT_TOKEN(aux_sym_string_literal_token2);
      if (lookahead == '\\') ADVANCE(19);
      if (lookahead != 0 &&
          lookahead != '\'') ADVANCE(67);
      END_STATE();
    case 68:
      ACCEPT_TOKEN(sym_number);
      if (lookahead == '.') ADVANCE(17);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(68);
      END_STATE();
    case 69:
      ACCEPT_TOKEN(sym_number);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(69);
      END_STATE();
    case 70:
      ACCEPT_TOKEN(anon_sym_true);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 71:
      ACCEPT_TOKEN(anon_sym_false);
      if (lookahead == '.' ||
          ('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(61);
      END_STATE();
    case 72:
      ACCEPT_TOKEN(sym_text);
      END_STATE();
    case 73:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(26);
      if (lookahead == '-') ADVANCE(78);
      if (lookahead == '{') ADVANCE(80);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(73);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 74:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(72);
      if (lookahead == '-') ADVANCE(78);
      if (lookahead == '{') ADVANCE(80);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(74);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 75:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(72);
      if (lookahead == '{') ADVANCE(80);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(75);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 76:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '#') ADVANCE(72);
      if (lookahead == '{') ADVANCE(79);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(76);
      if (lookahead != 0) ADVANCE(81);
      END_STATE();
    case 77:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '-') ADVANCE(29);
      if (lookahead != 0 &&
          lookahead != '#' &&
          lookahead != '{') ADVANCE(81);
      END_STATE();
    case 78:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '-') ADVANCE(77);
      if (lookahead != 0 &&
          lookahead != '#' &&
          lookahead != '{') ADVANCE(81);
      END_STATE();
    case 79:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '{') ADVANCE(39);
      END_STATE();
    case 80:
      ACCEPT_TOKEN(sym_text);
      if (lookahead == '{') ADVANCE(38);
      END_STATE();
    case 81:
      ACCEPT_TOKEN(sym_text);
      if (lookahead != 0 &&
          lookahead != '#' &&
          lookahead != '{') ADVANCE(81);
      END_STATE();
    default:
      return false;
  }
}

static const TSLexMode ts_lex_modes[STATE_COUNT] = {
  [0] = {.lex_state = 0},
  [1] = {.lex_state = 22},
  [2] = {.lex_state = 23},
  [3] = {.lex_state = 3},
  [4] = {.lex_state = 3},
  [5] = {.lex_state = 3},
  [6] = {.lex_state = 3},
  [7] = {.lex_state = 3},
  [8] = {.lex_state = 5},
  [9] = {.lex_state = 5},
  [10] = {.lex_state = 24},
  [11] = {.lex_state = 5},
  [12] = {.lex_state = 5},
  [13] = {.lex_state = 24},
  [14] = {.lex_state = 5},
  [15] = {.lex_state = 24},
  [16] = {.lex_state = 24},
  [17] = {.lex_state = 3},
  [18] = {.lex_state = 22},
  [19] = {.lex_state = 3},
  [20] = {.lex_state = 22},
  [21] = {.lex_state = 3},
  [22] = {.lex_state = 3},
  [23] = {.lex_state = 3},
  [24] = {.lex_state = 3},
  [25] = {.lex_state = 3},
  [26] = {.lex_state = 4},
  [27] = {.lex_state = 4},
  [28] = {.lex_state = 4},
  [29] = {.lex_state = 11},
  [30] = {.lex_state = 5},
  [31] = {.lex_state = 5},
  [32] = {.lex_state = 5},
  [33] = {.lex_state = 24},
  [34] = {.lex_state = 5},
  [35] = {.lex_state = 5},
  [36] = {.lex_state = 24},
  [37] = {.lex_state = 24},
  [38] = {.lex_state = 24},
  [39] = {.lex_state = 5},
  [40] = {.lex_state = 24},
  [41] = {.lex_state = 5},
  [42] = {.lex_state = 11},
  [43] = {.lex_state = 24},
  [44] = {.lex_state = 24},
  [45] = {.lex_state = 4},
  [46] = {.lex_state = 4},
  [47] = {.lex_state = 4},
  [48] = {.lex_state = 1},
  [49] = {.lex_state = 0},
  [50] = {.lex_state = 0},
  [51] = {.lex_state = 2},
  [52] = {.lex_state = 66},
  [53] = {.lex_state = 63},
  [54] = {.lex_state = 0},
  [55] = {.lex_state = 0},
  [56] = {.lex_state = 0},
  [57] = {.lex_state = 0},
  [58] = {.lex_state = 2},
  [59] = {.lex_state = 15},
  [60] = {.lex_state = 2},
  [61] = {.lex_state = 0},
  [62] = {.lex_state = 0},
  [63] = {.lex_state = 2},
  [64] = {.lex_state = 0},
  [65] = {.lex_state = 0},
  [66] = {.lex_state = 0},
  [67] = {.lex_state = 0},
  [68] = {.lex_state = 15},
  [69] = {.lex_state = 0},
  [70] = {.lex_state = 0},
  [71] = {.lex_state = 46},
  [72] = {.lex_state = 0},
  [73] = {.lex_state = 0},
  [74] = {.lex_state = 0},
  [75] = {.lex_state = 43},
  [76] = {.lex_state = 0},
  [77] = {.lex_state = 15},
  [78] = {.lex_state = 43},
  [79] = {.lex_state = 46},
  [80] = {.lex_state = 15},
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
  },
  [1] = {
    [sym_document] = STATE(70),
    [sym_license_header] = STATE(2),
    [sym_frontmatter] = STATE(10),
    [sym_template_body] = STATE(69),
    [sym__content] = STATE(16),
    [sym_handlebars_block] = STATE(16),
    [sym_block_expression] = STATE(12),
    [sym_handlebars_expression] = STATE(16),
    [sym_handlebars_comment] = STATE(16),
    [aux_sym_license_header_repeat1] = STATE(20),
    [aux_sym_template_body_repeat1] = STATE(16),
    [ts_builtin_sym_end] = ACTIONS(3),
    [sym_header_comment] = ACTIONS(5),
    [sym_frontmatter_delimiter] = ACTIONS(7),
    [anon_sym_LBRACE_LBRACE_POUND] = ACTIONS(9),
    [anon_sym_LBRACE_LBRACE] = ACTIONS(11),
    [anon_sym_LBRACE_LBRACE_BANG] = ACTIONS(13),
    [anon_sym_LBRACE_LBRACE_BANG_DASH_DASH] = ACTIONS(15),
    [sym_text] = ACTIONS(17),
  },
};

static const uint16_t ts_small_parse_table[] = {
  [0] = 11,
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
      sym_text,
    ACTIONS(19), 1,
      ts_builtin_sym_end,
    STATE(12), 1,
      sym_block_expression,
    STATE(13), 1,
      sym_frontmatter,
    STATE(61), 1,
      sym_template_body,
    STATE(16), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [38] = 9,
    ACTIONS(21), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(23), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(25), 1,
      sym_path,
    ACTIONS(27), 1,
      anon_sym_DQUOTE,
    ACTIONS(29), 1,
      anon_sym_SQUOTE,
    ACTIONS(31), 1,
      sym_number,
    ACTIONS(33), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(5), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(25), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [71] = 9,
    ACTIONS(23), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(25), 1,
      sym_path,
    ACTIONS(27), 1,
      anon_sym_DQUOTE,
    ACTIONS(29), 1,
      anon_sym_SQUOTE,
    ACTIONS(31), 1,
      sym_number,
    ACTIONS(35), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(33), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(5), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(25), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [104] = 9,
    ACTIONS(37), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(39), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(42), 1,
      sym_path,
    ACTIONS(45), 1,
      anon_sym_DQUOTE,
    ACTIONS(48), 1,
      anon_sym_SQUOTE,
    ACTIONS(51), 1,
      sym_number,
    ACTIONS(54), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(5), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(25), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [137] = 9,
    ACTIONS(23), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(25), 1,
      sym_path,
    ACTIONS(27), 1,
      anon_sym_DQUOTE,
    ACTIONS(29), 1,
      anon_sym_SQUOTE,
    ACTIONS(31), 1,
      sym_number,
    ACTIONS(57), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(33), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(4), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(25), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [170] = 9,
    ACTIONS(23), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(25), 1,
      sym_path,
    ACTIONS(27), 1,
      anon_sym_DQUOTE,
    ACTIONS(29), 1,
      anon_sym_SQUOTE,
    ACTIONS(31), 1,
      sym_number,
    ACTIONS(59), 1,
      anon_sym_RBRACE_RBRACE,
    ACTIONS(33), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(3), 2,
      sym_argument,
      aux_sym_block_expression_repeat1,
    STATE(25), 4,
      sym_hash_param,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [203] = 9,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(61), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(63), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(65), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(67), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(69), 1,
      sym_text,
    STATE(9), 1,
      sym_block_expression,
    STATE(31), 1,
      sym_close_block,
    STATE(14), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [235] = 9,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(61), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(63), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(65), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(67), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(71), 1,
      sym_text,
    STATE(9), 1,
      sym_block_expression,
    STATE(34), 1,
      sym_close_block,
    STATE(8), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [267] = 9,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(11), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(13), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(15), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(17), 1,
      sym_text,
    ACTIONS(19), 1,
      ts_builtin_sym_end,
    STATE(12), 1,
      sym_block_expression,
    STATE(61), 1,
      sym_template_body,
    STATE(16), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [299] = 9,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(63), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(65), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(67), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(69), 1,
      sym_text,
    ACTIONS(73), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    STATE(9), 1,
      sym_block_expression,
    STATE(33), 1,
      sym_close_block,
    STATE(14), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [331] = 9,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(63), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(65), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(67), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(73), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(75), 1,
      sym_text,
    STATE(9), 1,
      sym_block_expression,
    STATE(36), 1,
      sym_close_block,
    STATE(11), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [363] = 9,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(11), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(13), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(15), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(17), 1,
      sym_text,
    ACTIONS(77), 1,
      ts_builtin_sym_end,
    STATE(12), 1,
      sym_block_expression,
    STATE(62), 1,
      sym_template_body,
    STATE(16), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [395] = 8,
    ACTIONS(79), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(82), 1,
      anon_sym_LBRACE_LBRACE_SLASH,
    ACTIONS(84), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(87), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(90), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(93), 1,
      sym_text,
    STATE(9), 1,
      sym_block_expression,
    STATE(14), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [424] = 8,
    ACTIONS(79), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(96), 1,
      ts_builtin_sym_end,
    ACTIONS(98), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(101), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(104), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(107), 1,
      sym_text,
    STATE(12), 1,
      sym_block_expression,
    STATE(15), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [453] = 8,
    ACTIONS(9), 1,
      anon_sym_LBRACE_LBRACE_POUND,
    ACTIONS(11), 1,
      anon_sym_LBRACE_LBRACE,
    ACTIONS(13), 1,
      anon_sym_LBRACE_LBRACE_BANG,
    ACTIONS(15), 1,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
    ACTIONS(110), 1,
      ts_builtin_sym_end,
    ACTIONS(112), 1,
      sym_text,
    STATE(12), 1,
      sym_block_expression,
    STATE(15), 5,
      sym__content,
      sym_handlebars_block,
      sym_handlebars_expression,
      sym_handlebars_comment,
      aux_sym_template_body_repeat1,
  [482] = 7,
    ACTIONS(23), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(27), 1,
      anon_sym_DQUOTE,
    ACTIONS(29), 1,
      anon_sym_SQUOTE,
    ACTIONS(114), 1,
      sym_path,
    ACTIONS(116), 1,
      sym_number,
    ACTIONS(33), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(24), 3,
      sym_variable_reference,
      sym_string_literal,
      sym_boolean,
  [507] = 4,
    ACTIONS(118), 1,
      ts_builtin_sym_end,
    ACTIONS(120), 1,
      sym_header_comment,
    STATE(18), 1,
      aux_sym_license_header_repeat1,
    ACTIONS(123), 6,
      sym_frontmatter_delimiter,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [525] = 3,
    ACTIONS(125), 1,
      anon_sym_EQ,
    ACTIONS(127), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(59), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [541] = 4,
    ACTIONS(129), 1,
      ts_builtin_sym_end,
    ACTIONS(131), 1,
      sym_header_comment,
    STATE(18), 1,
      aux_sym_license_header_repeat1,
    ACTIONS(133), 6,
      sym_frontmatter_delimiter,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [559] = 2,
    ACTIONS(127), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(59), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [572] = 2,
    ACTIONS(137), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(135), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [585] = 2,
    ACTIONS(141), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(139), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [598] = 2,
    ACTIONS(145), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(143), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [611] = 2,
    ACTIONS(149), 3,
      sym_path,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(147), 5,
      anon_sym_RBRACE_RBRACE,
      aux_sym_variable_reference_token1,
      anon_sym_DQUOTE,
      anon_sym_SQUOTE,
      sym_number,
  [624] = 5,
    ACTIONS(154), 1,
      sym_frontmatter_delimiter,
    ACTIONS(156), 1,
      aux_sym_yaml_line_token1,
    STATE(26), 1,
      aux_sym_frontmatter_repeat1,
    ACTIONS(151), 2,
      sym_header_comment,
      aux_sym__yaml_content_token1,
    STATE(47), 2,
      sym__yaml_content,
      sym_yaml_line,
  [642] = 5,
    ACTIONS(161), 1,
      sym_frontmatter_delimiter,
    ACTIONS(163), 1,
      aux_sym_yaml_line_token1,
    STATE(28), 1,
      aux_sym_frontmatter_repeat1,
    ACTIONS(159), 2,
      sym_header_comment,
      aux_sym__yaml_content_token1,
    STATE(47), 2,
      sym__yaml_content,
      sym_yaml_line,
  [660] = 5,
    ACTIONS(163), 1,
      aux_sym_yaml_line_token1,
    ACTIONS(165), 1,
      sym_frontmatter_delimiter,
    STATE(26), 1,
      aux_sym_frontmatter_repeat1,
    ACTIONS(159), 2,
      sym_header_comment,
      aux_sym__yaml_content_token1,
    STATE(47), 2,
      sym__yaml_content,
      sym_yaml_line,
  [678] = 6,
    ACTIONS(23), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(167), 1,
      anon_sym_GT,
    ACTIONS(169), 1,
      anon_sym_else,
    ACTIONS(171), 1,
      sym_path,
    STATE(57), 1,
      sym_variable_reference,
    STATE(72), 1,
      sym_expression_content,
  [697] = 1,
    ACTIONS(173), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [706] = 1,
    ACTIONS(175), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [715] = 1,
    ACTIONS(177), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [724] = 2,
    ACTIONS(179), 1,
      ts_builtin_sym_end,
    ACTIONS(175), 5,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [735] = 1,
    ACTIONS(181), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [744] = 1,
    ACTIONS(183), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [753] = 2,
    ACTIONS(185), 1,
      ts_builtin_sym_end,
    ACTIONS(181), 5,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [764] = 2,
    ACTIONS(187), 1,
      ts_builtin_sym_end,
    ACTIONS(189), 5,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [775] = 2,
    ACTIONS(191), 1,
      ts_builtin_sym_end,
    ACTIONS(193), 5,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [786] = 1,
    ACTIONS(195), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [795] = 2,
    ACTIONS(197), 1,
      ts_builtin_sym_end,
    ACTIONS(199), 5,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [806] = 1,
    ACTIONS(189), 6,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE_SLASH,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [815] = 6,
    ACTIONS(23), 1,
      aux_sym_variable_reference_token1,
    ACTIONS(167), 1,
      anon_sym_GT,
    ACTIONS(169), 1,
      anon_sym_else,
    ACTIONS(171), 1,
      sym_path,
    STATE(50), 1,
      sym_expression_content,
    STATE(57), 1,
      sym_variable_reference,
  [834] = 2,
    ACTIONS(201), 1,
      ts_builtin_sym_end,
    ACTIONS(195), 5,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [845] = 2,
    ACTIONS(203), 1,
      ts_builtin_sym_end,
    ACTIONS(173), 5,
      anon_sym_LBRACE_LBRACE_POUND,
      anon_sym_LBRACE_LBRACE,
      anon_sym_LBRACE_LBRACE_BANG,
      anon_sym_LBRACE_LBRACE_BANG_DASH_DASH,
      sym_text,
  [856] = 1,
    ACTIONS(205), 4,
      sym_header_comment,
      sym_frontmatter_delimiter,
      aux_sym__yaml_content_token1,
      aux_sym_yaml_line_token1,
  [863] = 1,
    ACTIONS(207), 4,
      sym_header_comment,
      sym_frontmatter_delimiter,
      aux_sym__yaml_content_token1,
      aux_sym_yaml_line_token1,
  [870] = 1,
    ACTIONS(209), 4,
      sym_header_comment,
      sym_frontmatter_delimiter,
      aux_sym__yaml_content_token1,
      aux_sym_yaml_line_token1,
  [877] = 2,
    ACTIONS(211), 1,
      aux_sym_frontmatter_token1,
    ACTIONS(213), 1,
      aux_sym_yaml_line_token2,
  [884] = 1,
    ACTIONS(215), 1,
      anon_sym_DASH_DASH_RBRACE_RBRACE,
  [888] = 1,
    ACTIONS(217), 1,
      anon_sym_RBRACE_RBRACE,
  [892] = 1,
    ACTIONS(219), 1,
      aux_sym_frontmatter_token1,
  [896] = 1,
    ACTIONS(221), 1,
      aux_sym_string_literal_token2,
  [900] = 1,
    ACTIONS(223), 1,
      aux_sym_string_literal_token1,
  [904] = 1,
    ACTIONS(225), 1,
      anon_sym_DQUOTE,
  [908] = 1,
    ACTIONS(225), 1,
      anon_sym_SQUOTE,
  [912] = 1,
    ACTIONS(227), 1,
      anon_sym_RBRACE_RBRACE,
  [916] = 1,
    ACTIONS(229), 1,
      anon_sym_RBRACE_RBRACE,
  [920] = 1,
    ACTIONS(231), 1,
      aux_sym_frontmatter_token1,
  [924] = 1,
    ACTIONS(233), 1,
      sym_path,
  [928] = 1,
    ACTIONS(235), 1,
      aux_sym_frontmatter_token1,
  [932] = 1,
    ACTIONS(77), 1,
      ts_builtin_sym_end,
  [936] = 1,
    ACTIONS(237), 1,
      ts_builtin_sym_end,
  [940] = 1,
    ACTIONS(239), 1,
      aux_sym_frontmatter_token1,
  [944] = 1,
    ACTIONS(215), 1,
      anon_sym_RBRACE_RBRACE,
  [948] = 1,
    ACTIONS(241), 1,
      anon_sym_COLON,
  [952] = 1,
    ACTIONS(243), 1,
      anon_sym_RBRACE_RBRACE,
  [956] = 1,
    ACTIONS(245), 1,
      anon_sym_RBRACE_RBRACE,
  [960] = 1,
    ACTIONS(247), 1,
      sym_path,
  [964] = 1,
    ACTIONS(19), 1,
      ts_builtin_sym_end,
  [968] = 1,
    ACTIONS(249), 1,
      ts_builtin_sym_end,
  [972] = 1,
    ACTIONS(251), 1,
      aux_sym_handlebars_comment_token2,
  [976] = 1,
    ACTIONS(253), 1,
      anon_sym_RBRACE_RBRACE,
  [980] = 1,
    ACTIONS(255), 1,
      anon_sym_RBRACE_RBRACE,
  [984] = 1,
    ACTIONS(255), 1,
      anon_sym_DASH_DASH_RBRACE_RBRACE,
  [988] = 1,
    ACTIONS(257), 1,
      aux_sym_handlebars_comment_token1,
  [992] = 1,
    ACTIONS(259), 1,
      anon_sym_RBRACE_RBRACE,
  [996] = 1,
    ACTIONS(261), 1,
      sym_path,
  [1000] = 1,
    ACTIONS(263), 1,
      aux_sym_handlebars_comment_token1,
  [1004] = 1,
    ACTIONS(265), 1,
      aux_sym_handlebars_comment_token2,
  [1008] = 1,
    ACTIONS(267), 1,
      sym_path,
};

static const uint32_t ts_small_parse_table_map[] = {
  [SMALL_STATE(2)] = 0,
  [SMALL_STATE(3)] = 38,
  [SMALL_STATE(4)] = 71,
  [SMALL_STATE(5)] = 104,
  [SMALL_STATE(6)] = 137,
  [SMALL_STATE(7)] = 170,
  [SMALL_STATE(8)] = 203,
  [SMALL_STATE(9)] = 235,
  [SMALL_STATE(10)] = 267,
  [SMALL_STATE(11)] = 299,
  [SMALL_STATE(12)] = 331,
  [SMALL_STATE(13)] = 363,
  [SMALL_STATE(14)] = 395,
  [SMALL_STATE(15)] = 424,
  [SMALL_STATE(16)] = 453,
  [SMALL_STATE(17)] = 482,
  [SMALL_STATE(18)] = 507,
  [SMALL_STATE(19)] = 525,
  [SMALL_STATE(20)] = 541,
  [SMALL_STATE(21)] = 559,
  [SMALL_STATE(22)] = 572,
  [SMALL_STATE(23)] = 585,
  [SMALL_STATE(24)] = 598,
  [SMALL_STATE(25)] = 611,
  [SMALL_STATE(26)] = 624,
  [SMALL_STATE(27)] = 642,
  [SMALL_STATE(28)] = 660,
  [SMALL_STATE(29)] = 678,
  [SMALL_STATE(30)] = 697,
  [SMALL_STATE(31)] = 706,
  [SMALL_STATE(32)] = 715,
  [SMALL_STATE(33)] = 724,
  [SMALL_STATE(34)] = 735,
  [SMALL_STATE(35)] = 744,
  [SMALL_STATE(36)] = 753,
  [SMALL_STATE(37)] = 764,
  [SMALL_STATE(38)] = 775,
  [SMALL_STATE(39)] = 786,
  [SMALL_STATE(40)] = 795,
  [SMALL_STATE(41)] = 806,
  [SMALL_STATE(42)] = 815,
  [SMALL_STATE(43)] = 834,
  [SMALL_STATE(44)] = 845,
  [SMALL_STATE(45)] = 856,
  [SMALL_STATE(46)] = 863,
  [SMALL_STATE(47)] = 870,
  [SMALL_STATE(48)] = 877,
  [SMALL_STATE(49)] = 884,
  [SMALL_STATE(50)] = 888,
  [SMALL_STATE(51)] = 892,
  [SMALL_STATE(52)] = 896,
  [SMALL_STATE(53)] = 900,
  [SMALL_STATE(54)] = 904,
  [SMALL_STATE(55)] = 908,
  [SMALL_STATE(56)] = 912,
  [SMALL_STATE(57)] = 916,
  [SMALL_STATE(58)] = 920,
  [SMALL_STATE(59)] = 924,
  [SMALL_STATE(60)] = 928,
  [SMALL_STATE(61)] = 932,
  [SMALL_STATE(62)] = 936,
  [SMALL_STATE(63)] = 940,
  [SMALL_STATE(64)] = 944,
  [SMALL_STATE(65)] = 948,
  [SMALL_STATE(66)] = 952,
  [SMALL_STATE(67)] = 956,
  [SMALL_STATE(68)] = 960,
  [SMALL_STATE(69)] = 964,
  [SMALL_STATE(70)] = 968,
  [SMALL_STATE(71)] = 972,
  [SMALL_STATE(72)] = 976,
  [SMALL_STATE(73)] = 980,
  [SMALL_STATE(74)] = 984,
  [SMALL_STATE(75)] = 988,
  [SMALL_STATE(76)] = 992,
  [SMALL_STATE(77)] = 996,
  [SMALL_STATE(78)] = 1000,
  [SMALL_STATE(79)] = 1004,
  [SMALL_STATE(80)] = 1008,
};

static const TSParseActionEntry ts_parse_actions[] = {
  [0] = {.entry = {.count = 0, .reusable = false}},
  [1] = {.entry = {.count = 1, .reusable = false}}, RECOVER(),
  [3] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 0, 0, 0),
  [5] = {.entry = {.count = 1, .reusable = false}}, SHIFT(20),
  [7] = {.entry = {.count = 1, .reusable = false}}, SHIFT(63),
  [9] = {.entry = {.count = 1, .reusable = false}}, SHIFT(77),
  [11] = {.entry = {.count = 1, .reusable = false}}, SHIFT(42),
  [13] = {.entry = {.count = 1, .reusable = false}}, SHIFT(75),
  [15] = {.entry = {.count = 1, .reusable = false}}, SHIFT(71),
  [17] = {.entry = {.count = 1, .reusable = false}}, SHIFT(16),
  [19] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 1, 0, 0),
  [21] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 2, 0, 4),
  [23] = {.entry = {.count = 1, .reusable = true}}, SHIFT(21),
  [25] = {.entry = {.count = 1, .reusable = false}}, SHIFT(19),
  [27] = {.entry = {.count = 1, .reusable = true}}, SHIFT(53),
  [29] = {.entry = {.count = 1, .reusable = true}}, SHIFT(52),
  [31] = {.entry = {.count = 1, .reusable = true}}, SHIFT(25),
  [33] = {.entry = {.count = 1, .reusable = false}}, SHIFT(22),
  [35] = {.entry = {.count = 1, .reusable = true}}, SHIFT(32),
  [37] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0),
  [39] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(21),
  [42] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(19),
  [45] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(53),
  [48] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(52),
  [51] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(25),
  [54] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_block_expression_repeat1, 2, 0, 0), SHIFT_REPEAT(22),
  [57] = {.entry = {.count = 1, .reusable = true}}, SHIFT(35),
  [59] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_variable_reference, 1, 0, 0),
  [61] = {.entry = {.count = 1, .reusable = false}}, SHIFT(80),
  [63] = {.entry = {.count = 1, .reusable = false}}, SHIFT(29),
  [65] = {.entry = {.count = 1, .reusable = false}}, SHIFT(78),
  [67] = {.entry = {.count = 1, .reusable = false}}, SHIFT(79),
  [69] = {.entry = {.count = 1, .reusable = false}}, SHIFT(14),
  [71] = {.entry = {.count = 1, .reusable = false}}, SHIFT(8),
  [73] = {.entry = {.count = 1, .reusable = false}}, SHIFT(59),
  [75] = {.entry = {.count = 1, .reusable = false}}, SHIFT(11),
  [77] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 2, 0, 0),
  [79] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(77),
  [82] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0),
  [84] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(29),
  [87] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(78),
  [90] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(79),
  [93] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(14),
  [96] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0),
  [98] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(42),
  [101] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(75),
  [104] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(71),
  [107] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_template_body_repeat1, 2, 0, 0), SHIFT_REPEAT(15),
  [110] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_template_body, 1, 0, 0),
  [112] = {.entry = {.count = 1, .reusable = false}}, SHIFT(15),
  [114] = {.entry = {.count = 1, .reusable = false}}, SHIFT(21),
  [116] = {.entry = {.count = 1, .reusable = true}}, SHIFT(24),
  [118] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_license_header_repeat1, 2, 0, 0),
  [120] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_license_header_repeat1, 2, 0, 0), SHIFT_REPEAT(18),
  [123] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_license_header_repeat1, 2, 0, 0),
  [125] = {.entry = {.count = 1, .reusable = true}}, SHIFT(17),
  [127] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_variable_reference, 1, 0, 0),
  [129] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_license_header, 1, 0, 0),
  [131] = {.entry = {.count = 1, .reusable = false}}, SHIFT(18),
  [133] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_license_header, 1, 0, 0),
  [135] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_boolean, 1, 0, 0),
  [137] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_boolean, 1, 0, 0),
  [139] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_string_literal, 3, 0, 0),
  [141] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_string_literal, 3, 0, 0),
  [143] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_hash_param, 3, 0, 7),
  [145] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_hash_param, 3, 0, 7),
  [147] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_argument, 1, 0, 0),
  [149] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_argument, 1, 0, 0),
  [151] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 2, 0, 0), SHIFT_REPEAT(47),
  [154] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 2, 0, 0),
  [156] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 2, 0, 0), SHIFT_REPEAT(65),
  [159] = {.entry = {.count = 1, .reusable = false}}, SHIFT(47),
  [161] = {.entry = {.count = 1, .reusable = false}}, SHIFT(58),
  [163] = {.entry = {.count = 1, .reusable = false}}, SHIFT(65),
  [165] = {.entry = {.count = 1, .reusable = false}}, SHIFT(51),
  [167] = {.entry = {.count = 1, .reusable = true}}, SHIFT(68),
  [169] = {.entry = {.count = 1, .reusable = false}}, SHIFT(67),
  [171] = {.entry = {.count = 1, .reusable = false}}, SHIFT(7),
  [173] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_comment, 3, 0, 0),
  [175] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_block, 3, 0, 0),
  [177] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_block_expression, 4, 0, 2),
  [179] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_block, 3, 0, 0),
  [181] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_block, 2, 0, 0),
  [183] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_block_expression, 3, 0, 2),
  [185] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_block, 2, 0, 0),
  [187] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_close_block, 3, 0, 2),
  [189] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_close_block, 3, 0, 2),
  [191] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_frontmatter, 4, 0, 0),
  [193] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_frontmatter, 4, 0, 0),
  [195] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_handlebars_expression, 3, 0, 0),
  [197] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_frontmatter, 5, 0, 6),
  [199] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_frontmatter, 5, 0, 6),
  [201] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_expression, 3, 0, 0),
  [203] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_handlebars_comment, 3, 0, 0),
  [205] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_yaml_line, 3, 0, 5),
  [207] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_yaml_line, 4, 0, 8),
  [209] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_frontmatter_repeat1, 1, 0, 0),
  [211] = {.entry = {.count = 1, .reusable = false}}, SHIFT(45),
  [213] = {.entry = {.count = 1, .reusable = false}}, SHIFT(60),
  [215] = {.entry = {.count = 1, .reusable = true}}, SHIFT(44),
  [217] = {.entry = {.count = 1, .reusable = true}}, SHIFT(43),
  [219] = {.entry = {.count = 1, .reusable = true}}, SHIFT(40),
  [221] = {.entry = {.count = 1, .reusable = true}}, SHIFT(55),
  [223] = {.entry = {.count = 1, .reusable = true}}, SHIFT(54),
  [225] = {.entry = {.count = 1, .reusable = true}}, SHIFT(23),
  [227] = {.entry = {.count = 1, .reusable = true}}, SHIFT(37),
  [229] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 1, 0, 1),
  [231] = {.entry = {.count = 1, .reusable = true}}, SHIFT(38),
  [233] = {.entry = {.count = 1, .reusable = true}}, SHIFT(56),
  [235] = {.entry = {.count = 1, .reusable = true}}, SHIFT(46),
  [237] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_document, 3, 0, 0),
  [239] = {.entry = {.count = 1, .reusable = true}}, SHIFT(27),
  [241] = {.entry = {.count = 1, .reusable = true}}, SHIFT(48),
  [243] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 2, 0, 3),
  [245] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_content, 1, 0, 0),
  [247] = {.entry = {.count = 1, .reusable = true}}, SHIFT(66),
  [249] = {.entry = {.count = 1, .reusable = true}},  ACCEPT_INPUT(),
  [251] = {.entry = {.count = 1, .reusable = true}}, SHIFT(49),
  [253] = {.entry = {.count = 1, .reusable = true}}, SHIFT(39),
  [255] = {.entry = {.count = 1, .reusable = true}}, SHIFT(30),
  [257] = {.entry = {.count = 1, .reusable = true}}, SHIFT(64),
  [259] = {.entry = {.count = 1, .reusable = true}}, SHIFT(41),
  [261] = {.entry = {.count = 1, .reusable = true}}, SHIFT(6),
  [263] = {.entry = {.count = 1, .reusable = true}}, SHIFT(73),
  [265] = {.entry = {.count = 1, .reusable = true}}, SHIFT(74),
  [267] = {.entry = {.count = 1, .reusable = true}}, SHIFT(76),
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
