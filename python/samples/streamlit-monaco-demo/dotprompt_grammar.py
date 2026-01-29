# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

LANGUAGE_ID = 'dotprompt'

# Monarch tokenizer for Dotprompt syntax highlighting.
# Handles YAML frontmatter, Handlebars templates, and Dotprompt markers.
monarch_language = {
    'defaultToken': '',
    'tokenPostfix': '.dotprompt',
    # Handlebars keywords
    'keywords': ['if', 'unless', 'each', 'with', 'else', 'log', 'lookup'],
    # Dotprompt-specific helpers
    'dotpromptHelpers': [
        'json',
        'role',
        'history',
        'section',
        'media',
        'ifEquals',
        'unlessEquals',
    ],
    # YAML frontmatter keys
    'yamlKeys': [
        'model',
        'config',
        'input',
        'output',
        'tools',
        'metadata',
        'default',
        'schema',
        'format',
        'temperature',
        'maxOutputTokens',
        'topP',
        'topK',
    ],
    # Operators and brackets
    'brackets': [
        {'open': '{{', 'close': '}}', 'token': 'delimiter.handlebars'},
        {'open': '{{#', 'close': '}}', 'token': 'delimiter.handlebars.block'},
        {'open': '{{/', 'close': '}}', 'token': 'delimiter.handlebars.block'},
        {'open': '{', 'close': '}', 'token': 'delimiter.curly'},
        {'open': '[', 'close': ']', 'token': 'delimiter.square'},
    ],
    'tokenizer': {
        'root': [
            # License header comments (lines starting with #)
            [r'^#.*$', 'comment.line'],
            # Frontmatter delimiter
            [r'^---\s*$', {'token': 'delimiter.frontmatter', 'next': '@frontmatter'}],
            # Dotprompt markers <<<dotprompt:...>>>
            [r'<<<dotprompt:[^>]+>>>', 'keyword.marker'],
            # Include template tokens
            {'include': '@template'},
        ],
        'frontmatter': [
            # End of frontmatter
            [r'^---\s*$', {'token': 'delimiter.frontmatter', 'next': '@root'}],
            # YAML comments
            [r'#.*$', 'comment.yaml'],
            # YAML keys
            [
                r'([a-zA-Z_][a-zA-Z0-9_-]*)(\s*)(:)',
                [
                    {
                        'cases': {
                            '@yamlKeys': 'keyword.yaml',
                            '@default': 'variable.yaml',
                        },
                    },
                    '',
                    'delimiter.colon',
                ],
            ],
            # YAML strings
            [r'"([^"\\]|\\.)*$', 'string.invalid'],  # non-terminated string
            [r'"', {'token': 'string.quote', 'next': '@yamlDoubleString'}],
            [r"'", {'token': 'string.quote', 'next': '@yamlSingleString'}],
            # YAML numbers
            [r'\d+(\.\d+)?', 'number'],
            # YAML booleans
            [r'\b(true|false|null)\b', 'constant.language'],
            # Everything else in frontmatter
            [r'.', 'source.yaml'],
        ],
        'yamlDoubleString': [
            [r'[^\\"]+', 'string'],
            [r'\\.', 'string.escape'],
            [r'"', {'token': 'string.quote', 'next': '@pop'}],
        ],
        'yamlSingleString': [
            [r"[^\\']+", 'string'],
            [r'\\.', 'string.escape'],
            [r"'", {'token': 'string.quote', 'next': '@pop'}],
        ],
        'template': [
            # Handlebars comments {{! ... }}
            [r'\{\{!--', {'token': 'comment.block', 'next': '@handlebarsBlockComment'}],
            [r'\{\{!+', {'token': 'comment.block', 'next': '@handlebarsComment'}],
            # Handlebars block start {{#helper ...}}
            [
                r'(\{\{#)(\s*)(\w+)',
                [
                    'delimiter.handlebars.block',
                    '',
                    {
                        'cases': {
                            '@keywords': 'keyword.handlebars',
                            '@dotpromptHelpers': 'keyword.dotprompt',
                            '@default': 'variable.handlebars',
                        },
                    },
                ],
            ],
            # Handlebars block end {{/helper}}
            [
                r'(\{\{\/)(\s*)(\w+)(\s*)(\}\})',
                [
                    'delimiter.handlebars.block',
                    '',
                    {
                        'cases': {
                            '@keywords': 'keyword.handlebars',
                            '@dotpromptHelpers': 'keyword.dotprompt',
                            '@default': 'variable.handlebars',
                        },
                    },
                    '',
                    'delimiter.handlebars.block',
                ],
            ],
            # Handlebars else {{else}}
            [r'\{\{else\}\}', 'keyword.handlebars'],
            # Partials {{> partialName}}
            [
                r'(\{\{>)(\s*)([a-zA-Z_][a-zA-Z0-9_-]*)(\s*)(\}\})',
                [
                    'delimiter.handlebars',
                    '',
                    'variable.partial',
                    '',
                    'delimiter.handlebars',
                ],
            ],
            # Handlebars expressions {{ ... }}
            [
                r'\{\{',
                {'token': 'delimiter.handlebars', 'next': '@handlebarsExpression'},
            ],
            # Plain text
            [r'[^{<]+', ''],
            [r'.', ''],
        ],
        'handlebarsExpression': [
            # Close expression
            [r'\}\}', {'token': 'delimiter.handlebars', 'next': '@pop'}],
            # Helpers
            [
                r'\b(\w+)\b',
                {
                    'cases': {
                        '@keywords': 'keyword.handlebars',
                        '@dotpromptHelpers': 'keyword.dotprompt',
                        '@default': 'variable',
                    },
                },
            ],
            # Strings in expressions
            [r'"([^"\\]|\\.)*"', 'string'],
            [r"'([^'\\]|\\.)*'", 'string'],
            # Numbers
            [r'\d+', 'number'],
            # Operators
            [r'[=]', 'operator'],
            # Dotted paths
            [r'\.', 'delimiter.dot'],
            # @ variables (@index, @first, etc.)
            [r'@\w+', 'variable.special'],
            # Whitespace
            [r'\s+', ''],
        ],
        'handlebarsComment': [
            [r'\}\}', {'token': 'comment.block', 'next': '@pop'}],
            [r'.', 'comment.block'],
        ],
        'handlebarsBlockComment': [
            [r'--\}\}', {'token': 'comment.block', 'next': '@pop'}],
            [r'.', 'comment.block'],
        ],
    },
}

# Language configuration for Dotprompt.
# Provides bracket matching, auto-closing, and comment toggling.
language_configuration = {
    'comments': {
        'blockComment': ['{{!', '}}'],
    },
    'brackets': [
        ['{{', '}}'],
        ['{{#', '}}'],
        ['{{/', '}}'],
        ['{', '}'],
        ['[', ']'],
        ['(', ')'],
    ],
    'autoClosingPairs': [
        {'open': '{{', 'close': '}}'},
        {'open': '{', 'close': '}'},
        {'open': '[', 'close': ']'},
        {'open': '(', 'close': ')'},
        {'open': '"', 'close': '"'},
        {'open': "'", 'close': "'"},
    ],
    'surroundingPairs': [
        {'open': '{{', 'close': '}}'},
        {'open': '{', 'close': '}'},
        {'open': '[', 'close': ']'},
        {'open': '(', 'close': ')'},
        {'open': '"', 'close': '"'},
        {'open': "'", 'close': "'"},
    ],
    # Folding and Indentation rules are regex-heavy and might not transfer easily via JSON without
    # manual regex object reconstruction on JS side. We limit to basic configuration for now.
    # If the Streamlit component supports regex strings for these, we could add them.
}
