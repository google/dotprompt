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

// Handlebars Lexer Grammar for ANTLR4
// Converted from the official Handlebars.js 4.x Jison grammar
// Source: https://github.com/handlebars-lang/handlebars.js/tree/4.x/src

lexer grammar HandlebarsLexer;

// ============================================================================
// Default Mode: Text content between mustache expressions
// ============================================================================

// Escaped mustache: \{{ outputs literal {{
ESC_VAR
    : '\\{{' -> type(CONTENT)
    ;

// Raw block opening: {{{{
OPEN_RAW_BLOCK
    : '{{{{' -> pushMode(MUSTACHE)
    ;

// End raw block: {{{{/
END_RAW_BLOCK
    : '{{{{/' -> pushMode(MUSTACHE)
    ;

// Triple mustache (unescaped): {{{
OPEN_UNESCAPED
    : '{{{' -> pushMode(MUSTACHE)
    ;

// Partial block: {{#>
OPEN_PARTIAL_BLOCK
    : '{{' '~'? '#>' -> pushMode(MUSTACHE)
    ;

// Block: {{# or {{#*
OPEN_BLOCK
    : '{{' '~'? '#' '*'? -> pushMode(MUSTACHE)
    ;

// End block: {{/
OPEN_ENDBLOCK
    : '{{' '~'? '/' -> pushMode(MUSTACHE)
    ;

// Inverse (standalone): {{^}} or {{else}}
INVERSE
    : '{{' '~'? '^' WS_CHARS* '~'? '}}'
    | '{{' '~'? WS_CHARS* 'else' WS_CHARS* '~'? '}}'
    ;

// Inverse block: {{^
OPEN_INVERSE
    : '{{' '~'? '^' -> pushMode(MUSTACHE)
    ;

// Inverse chain: {{else
OPEN_INVERSE_CHAIN
    : '{{' '~'? WS_CHARS* 'else' -> pushMode(MUSTACHE)
    ;

// Partial: {{>
OPEN_PARTIAL
    : '{{' '~'? '>' -> pushMode(MUSTACHE)
    ;

// Long comment: {{!-- ... --}}
COMMENT_LONG
    : '{{' '~'? '!--' .*? '--' '~'? '}}' -> type(COMMENT)
    ;

// Short comment: {{! ... }}
COMMENT
    : '{{' '~'? '!' ~[-].*? '}}'
    ;

// Ampersand unescaped: {{&
OPEN_AMP
    : '{{' '~'? '&' -> pushMode(MUSTACHE), type(OPEN_UNESCAPED)
    ;

// Regular mustache: {{ or {{*
OPEN
    : '{{' '~'? '*'? -> pushMode(MUSTACHE)
    ;

// Text content (anything not starting a mustache)
CONTENT
    : (~[{\\] | '{' ~[{] | '\\' ~[{])+
    ;

// Standalone backslash or brace at end
CONTENT_CHAR
    : [\\{] -> type(CONTENT)
    ;

// Whitespace characters (fragment for use in rules)
fragment WS_CHARS : [ \t\r\n];

// ============================================================================
// MUSTACHE Mode: Inside {{ }}
// ============================================================================
mode MUSTACHE;

// Raw block close: }}}}
CLOSE_RAW_BLOCK
    : '}}}}' -> popMode
    ;

// Triple mustache close: }}}
CLOSE_UNESCAPED
    : '~'? '}}}' -> popMode
    ;

// Regular close: }}
CLOSE
    : '~'? '}}' -> popMode
    ;

// Subexpression delimiters
OPEN_SEXPR  : '(';
CLOSE_SEXPR : ')';

// Block params: as |item index|
OPEN_BLOCK_PARAMS  : 'as' WS+ '|';
CLOSE_BLOCK_PARAMS : '|';

// Path separators
SEP : [./];

// Equals for hash params
EQUALS : '=';

// String literals
STRING
    : '"' ('\\' . | ~["\\])* '"'
    | '\'' ('\\' . | ~['\\])* '\''
    ;

// Number literals
NUMBER
    : '-'? [0-9]+ ('.' [0-9]+)?
    ;

// Boolean literals
BOOLEAN
    : 'true'
    | 'false'
    ;

// Special literals
UNDEFINED : 'undefined';
NULL_LIT  : 'null';

// Data variable prefix
DATA : '@';

// Identifiers (including paths like ../foo)
ID
    : '..'
    | '.'
    | ID_START ID_PART*
    | '[' (~[\]\\] | '\\' .)* ']'
    ;

fragment ID_START
    : [a-zA-Z_$]
    | [\u00C0-\u00FF]
    ;

fragment ID_PART
    : ID_START
    | [0-9]
    | '-'
    ;

// Whitespace (skip inside mustaches)
WS : [ \t\r\n]+ -> skip;
