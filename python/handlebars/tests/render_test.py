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

"""Core functional unit tests for the Handlebars compiler and runtime.

Covers standard template syntax: variable interpolation, HTML escaping,
built-in block helpers (if, unless, each, with), partials, subexpressions,
and helper registrations.
"""

import pytest

from handlebars import Handlebars, SafeString, StrictModeError


def render(source, data=None, *, hb=None, data_hash=None):
    hb = hb or Handlebars()
    return hb.compile(source)(data if data is not None else {}, data=data_hash)


# ==============================================================================
# 1. Variables & Paths
# ==============================================================================


def test_simple_variable():
    assert render('Hello {{name}}!', {'name': 'World'}) == 'Hello World!'


def test_dot_notation_path():
    assert render('Hello {{user.name}}!', {'user': {'name': 'Alice'}}) == 'Hello Alice!'


def test_missing_variable_returns_empty():
    assert render('Hello {{name}}!', {}) == 'Hello !'


def test_this_context_with_dot():
    assert render('Value: {{.}}', 'hello') == 'Value: hello'


def test_slash_path_notation():
    assert render('{{user/name}}', {'user': {'name': 'Alice'}}) == 'Alice'


def test_boolean_values_render_as_lowercase():
    assert render('{{val}}', {'val': True}) == 'true'
    assert render('{{val}}', {'val': False}) == 'false'


# ==============================================================================
# 2. HTML Escaping & Raw Outputs
# ==============================================================================


def test_escapes_html_by_default():
    assert render('{{content}}', {'content': "<script>alert('xss')</script>"}) == (
        '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;'
    )


def test_triple_braces_disable_escaping():
    assert render('{{{content}}}', {'content': '<b>bold</b>'}) == '<b>bold</b>'


def test_ampersand_disables_escaping():
    assert render('{{&content}}', {'content': '<b>bold</b>'}) == '<b>bold</b>'


def test_escape_html_off_leaves_markup():
    hb = Handlebars(escape_html=False)
    assert render('{{content}}', {'content': '<b>bold</b>'}, hb=hb) == '<b>bold</b>'


# ==============================================================================
# 3. Conditionals & Iteration
# ==============================================================================


def test_if_else_and_falsy_values():
    assert render('{{#if show}}yes{{else}}no{{/if}}', {'show': True}) == 'yes'
    assert render('{{#if show}}yes{{else}}no{{/if}}', {'show': False}) == 'no'
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': ''}) == 'no'
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': 0}) == 'no'
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': None}) == 'no'
    assert render('{{#if items}}yes{{else}}no{{/if}}', {'items': []}) == 'no'
    assert render('{{#if items}}yes{{else}}no{{/if}}', {'items': [1]}) == 'yes'


def test_else_if_picks_the_matching_branch():
    source = '{{#if a}}A{{else if b}}B{{else}}C{{/if}}'
    assert render(source, {'a': True}) == 'A'
    assert render(source, {'b': True}) == 'B'
    assert render(source, {'a': False, 'b': False}) == 'C'


def test_unless_block():
    assert render('{{#unless hidden}}visible{{/unless}}', {'hidden': False}) == 'visible'
    assert render('{{#unless hidden}}visible{{/unless}}', {'hidden': True}) == ''


def test_each_list_index_and_empty():
    assert render('{{#each items}}{{.}} {{/each}}', {'items': ['a', 'b', 'c']}) == 'a b c '
    assert render('{{#each items}}{{@index}}:{{.}} {{/each}}', {'items': ['a', 'b']}) == '0:a 1:b '
    assert render('{{#each items}}{{.}}{{else}}empty{{/each}}', {'items': []}) == 'empty'
    assert render('{{#each items}}{{.}}{{#unless @last}},{{/unless}}{{/each}}', {'items': ['a', 'b']}) == 'a,b'


def test_each_first_last_and_parent():
    source = '{{#each items}}{{#if @first}}[{{/if}}{{.}}{{#if @last}}]{{/if}}{{/each}}'
    assert render(source, {'items': ['a', 'b', 'c']}) == '[abc]'
    assert render('{{#each items}}{{.}}-{{../prefix}}{{/each}}', {'prefix': 'X', 'items': ['a', 'b']}) == 'a-Xb-X'


def test_block_params():
    source = '{{#each items as |item index|}}{{index}}:{{item}};{{/each}}'
    assert render(source, {'items': ['a', 'b']}) == '0:a;1:b;'


# ==============================================================================
# 4. Context Frames & @root Data
# ==============================================================================


def test_with_block_and_root():
    assert render('{{#with user}}{{name}}{{/with}}', {'user': {'name': 'Alice'}}) == 'Alice'
    source = '{{#with user}}{{name}} from {{@root.company}}{{/with}}'
    assert render(source, {'user': {'name': 'Alice'}, 'company': 'Acme'}) == 'Alice from Acme'


def test_at_data_is_separate_from_input():
    source = '{{name}} {{@name}}'
    assert render(source, {'name': 'input'}, data_hash={'name': 'context'}) == 'input context'


def test_data_root_replaces_at_root():
    assert render('{{@root.name}}', {'name': 'Ada'}, data_hash={'root': {'name': 'runtime'}}) == 'runtime'
    assert render('{{@root.company}}', {'company': 'Acme'}, data_hash={'name': 'ctx'}) == 'Acme'


def test_at_data_whitespace_and_deep_paths():
    assert render('Hello {{ @name }}!', data_hash={'name': 'Ada'}) == 'Hello Ada!'
    assert render('Hello {{   @name   }}!', data_hash={'name': 'Ada'}) == 'Hello Ada!'
    source = '{{@auth.user.email}}'
    assert render(source, data_hash={'auth': {'user': {'email': 'ada@example.com'}}}) == 'ada@example.com'


def test_at_data_in_conditionals_and_helpers():
    hb = Handlebars()
    hb.register_helper('upper', lambda args, opt: str(args[0]).upper())
    assert render('{{#if @isAdmin}}admin{{else}}user{{/if}}', data_hash={'isAdmin': True}) == 'admin'
    assert render('{{#if @isAdmin}}admin{{else}}user{{/if}}', data_hash={'isAdmin': False}) == 'user'
    assert render('{{upper @role}}', hb=hb, data_hash={'role': 'engineer'}) == 'ENGINEER'


# ==============================================================================
# 5. Partials & Template Composition
# ==============================================================================


def test_partials_and_missing_partial():
    hb = Handlebars()
    hb.register_partial('greeting', 'Hello {{name}}!')
    assert render('{{> greeting}}', {'name': 'World'}, hb=hb) == 'Hello World!'
    hb.register_partial('userCard', 'Name: {{name}}')
    assert render('{{> userCard user}}', {'user': {'name': 'Alice'}}, hb=hb) == 'Name: Alice'
    with pytest.raises(ValueError, match='could not be found'):
        render('{{> missing}}', {}, hb=hb)


def test_partial_block_falls_back_to_its_body():
    assert render('{{#> missing}}Default{{/missing}}', {}) == 'Default'
    hb = Handlebars()
    hb.register_partial('myPartial', 'PARTIAL CONTENT')
    assert render('{{#> myPartial}}Default{{/myPartial}}', {}, hb=hb) == 'PARTIAL CONTENT'


def test_inline_partial():
    source = '{{#*inline "myPartial"}}Hello {{name}}!{{/inline}}{{> myPartial}}'
    assert render(source, {'name': 'World'}).strip() == 'Hello World!'


def test_recursive_partial_raises_recursion_error():
    hb = Handlebars()
    hb.register_partial('loop', '{{> loop}}')
    with pytest.raises(RecursionError):
        hb.compile('{{> loop}}')({})


# ==============================================================================
# 6. Whitespace Control & Comments
# ==============================================================================


def test_comments_whitespace_and_literal_braces():
    assert render('Hello {{! this is a comment }}World', {}) == 'Hello World'
    assert render('Hello   {{~name}}!', {'name': 'World'}) == 'HelloWorld!'
    assert render(r'Show \{{name}} literally', {'name': 'World'}) == 'Show {{name}} literally'
    assert render(r'\\{{name}}', {'name': 'World'}) == '\\World'


def test_multibyte_utf8_identifiers_and_comments():
    source = 'Hola {{año}}, こんにちは {{名前}}! {{! 注释 }} {{!-- 详细注释 --}}'
    assert render(source, {'año': 2026, '名前': '太郎'}) == 'Hola 2026, こんにちは 太郎!  '
    assert render('{{{año}}}', {'año': '<b>2026</b>'}) == '<b>2026</b>'


# ==============================================================================
# 7. Custom Helpers & Subexpressions
# ==============================================================================


def test_subexpression_and_literals():
    hb = Handlebars()
    hb.register_helper('upper', lambda args, options: str(args[0]).upper())
    hb.register_helper('wrap', lambda args, options: f'[{args[0]}]')
    hb.register_helper('add', lambda args, options: args[0] + args[1])
    assert render('{{wrap (upper name)}}', {'name': 'hello'}, hb=hb) == '[HELLO]'
    assert render('{{add 10 -5}}', {}, hb=hb) == '5'


def test_helper_passes_through_keyboard_interrupt():
    hb = Handlebars()
    hb.register_helper('interrupt', lambda args, opt: (_ for _ in ()).throw(KeyboardInterrupt))
    with pytest.raises(KeyboardInterrupt):
        hb.compile('{{interrupt}}')({})


def test_lookup_helper():
    assert render('{{lookup items 1}}', {'items': ['a', 'b', 'c']}) == 'b'
    assert render('{{lookup person missing}}', {'person': {'name': 'Alice'}, 'missing': 'nope'}) == ''


def test_custom_block_helper():
    hb = Handlebars()

    def if_equals(args, options):
        return options.fn() if args[0] == args[1] else options.inverse()

    hb.register_helper('ifEquals', if_equals)
    source = '{{#ifEquals status "active"}}Active{{else}}Inactive{{/ifEquals}}'
    assert render(source, {'status': 'active'}, hb=hb) == 'Active'
    assert render(source, {'status': 'pending'}, hb=hb) == 'Inactive'


def test_safe_string_skips_escaping():
    hb = Handlebars()
    hb.register_helper('bold', lambda args, options: SafeString(f'<b>{args[0]}</b>'))
    assert render('{{bold name}}', {'name': 'test'}, hb=hb) == '<b>test</b>'


# ==============================================================================
# 8. Strict Mode & Error Handling
# ==============================================================================


def test_raw_block_outputs_content_literally():
    hb = Handlebars()
    assert hb.compile('Before {{{{raw}}}}{{name}} is literal{{{{/raw}}}} After')({'name': 'World'}) == (
        'Before {{name}} is literal After'
    )


def test_raw_block_standalone_line_trimming():
    hb = Handlebars()
    source = 'Before\n{{{{raw}}}}\n{{name}}\n{{{{/raw}}}}\nAfter'
    assert hb.compile(source)({'name': 'World'}) == 'Before\n{{name}}\nAfter'


def test_custom_raw_block_helper():
    hb = Handlebars()
    hb.register_helper('wrap', lambda args, opt: f'[{opt.fn()}]')
    assert hb.compile('{{{{wrap}}}}{{name}}{{{{/wrap}}}}')({'name': 'World'}) == '[{{name}}]'


def test_unclosed_raw_block_raises():
    with pytest.raises(ValueError, match='unclosed raw block'):
        Handlebars().compile('{{{{raw}}}}{{name}}')


def test_unclosed_block_raises():
    with pytest.raises(ValueError):
        Handlebars().compile('{{#if show}}yes')


def test_strict_mode_names_the_missing_path():
    hb = Handlebars(strict=True)
    with pytest.raises(StrictModeError) as raised:
        hb.compile('{{user.name}}')({})
    assert raised.value.path == 'user.name'
    assert 'is not defined' in str(raised.value)
    assert hb.compile('{{#if name}}yes{{else}}no{{/if}}')({'name': None}) == 'no'
