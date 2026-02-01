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

// Handlebars Parser Grammar for ANTLR4
// Converted from the official Handlebars.js 4.x Jison grammar
// Source: https://github.com/handlebars-lang/handlebars.js/tree/4.x/src

parser grammar HandlebarsParser;

options {
    tokenVocab = HandlebarsLexer;
}

// ============================================================================
// Parser Rules
// ============================================================================

root
    : program EOF
    ;

program
    : statement*
    ;

statement
    : mustache
    | block
    | rawBlock
    | partial
    | partialBlock
    | content
    | comment
    // Note: 'inverse' (standalone {{else}} or {{^}}) is NOT a valid statement.
    // The INVERSE token is only valid within a block's inverseChain.
    // This prevents the parser from consuming {{else}} as a statement
    // when it should be the start of an inverse chain.
    ;

content
    : CONTENT
    ;

comment
    : COMMENT
    ;

// Raw blocks: {{{{raw}}}}...{{{{/raw}}}}
rawBlock
    : openRawBlock program END_RAW_BLOCK helperName CLOSE_RAW_BLOCK
    ;

openRawBlock
    : OPEN_RAW_BLOCK helperName param* hash? CLOSE_RAW_BLOCK
    ;

// Block helpers: {{#if}}...{{/if}}
block
    : openBlock program inverseChain? closeBlock
    | openInverse program inverseAndProgram? closeBlock
    ;

openBlock
    : OPEN_BLOCK helperName param* hash? blockParams? CLOSE
    ;

openInverse
    : OPEN_INVERSE helperName param* hash? blockParams? CLOSE
    ;

openInverseChain
    : OPEN_INVERSE_CHAIN helperName param* hash? blockParams? CLOSE
    ;

inverseAndProgram
    : INVERSE program
    ;

inverseChain
    : openInverseChain program inverseChain?
    | inverseAndProgram
    ;

closeBlock
    : OPEN_ENDBLOCK helperName CLOSE
    ;

// Mustache expressions: {{name}} or {{{unescaped}}}
mustache
    : OPEN helperName param* hash? CLOSE
    | OPEN_UNESCAPED helperName param* hash? CLOSE_UNESCAPED
    ;

// Partials: {{> partialName}}
partial
    : OPEN_PARTIAL partialName param* hash? CLOSE
    ;

// Partial blocks: {{#> partialName}}...{{/partialName}}
partialBlock
    : openPartialBlock program closeBlock
    ;

openPartialBlock
    : OPEN_PARTIAL_BLOCK partialName param* hash? CLOSE
    ;

// Parameters
param
    : helperName
    | sexpr
    ;

// Subexpressions: (helper arg1 arg2)
sexpr
    : OPEN_SEXPR helperName param* hash? CLOSE_SEXPR
    ;

// Hash parameters: key=value
hash
    : hashSegment+
    ;

hashSegment
    : ID EQUALS param
    ;

// Block parameters: as |item index|
blockParams
    : OPEN_BLOCK_PARAMS ID+ CLOSE_BLOCK_PARAMS
    ;

// Helper name (path, literal, or data variable)
helperName
    : path
    | dataName
    | STRING
    | NUMBER
    | BOOLEAN
    | UNDEFINED
    | NULL_LIT
    ;

// Partial name
partialName
    : helperName
    | sexpr
    ;

// Data variables: @root, @index, etc.
dataName
    : DATA pathSegments
    ;

// Path expressions: foo.bar, ../parent, ./current
path
    : pathSegments
    ;

pathSegments
    : ID (SEP ID)*
    ;
