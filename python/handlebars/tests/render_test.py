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

"""Comprehensive functional unit and edge-case tests for the Handlebars engine.

Covers syntax compilation, runtime evaluation, Handlebars 4.7.9 specification
rules (truthiness matrix, number/object stringification, call-site indentation),
built-in helpers, partials, strict mode contracts, and syntax error handling.
"""

from collections import UserDict, deque
from typing import Any

import pytest

from dotpromptz_handlebars import (
    Handlebars,
    HelperOptions,
    SafeString,
    StrictModeError,
    TemplateRecursionError,
)
from dotpromptz_handlebars._render import compile_template
from dotpromptz_handlebars._types import Block, Mustache, TagToken, Text


def render(source, data=None, *, hb=None, data_hash=None, strict=False):
    hb = hb or Handlebars(strict=strict)
    return hb.compile(source)(data if data is not None else {}, data=data_hash)


# ==============================================================================
# 1. Variables, Paths & Stringification
# ==============================================================================


def test_simple_variable():
    assert render('Hello {{name}}!', {'name': 'World'}) == 'Hello World!'


def test_dot_notation_path():
    assert render('Hello {{user.name}}!', {'user': {'name': 'Alice'}}) == 'Hello Alice!'


def test_slash_path_notation():
    assert render('{{user/name}}', {'user': {'name': 'Alice'}}) == 'Alice'


def test_bracket_path_reads_a_key_that_has_a_space():
    assert render('{{a.[b c]}}', {'a': {'b c': 'OK'}}) == 'OK'


def test_this_context_with_dot():
    assert render('Value: {{.}}', 'hello') == 'Value: hello'


def test_this_dot_reads_the_current_object():
    assert render('{{this.name}}|{{./name}}', {'name': 'N'}) == 'N|N'


def test_missing_variable_returns_empty():
    assert render('Hello {{name}}!', {}) == 'Hello !'


def test_boolean_values_render_as_lowercase():
    assert render('{{val}}', {'val': True}) == 'true'
    assert render('{{val}}', {'val': False}) == 'false'


def test_whole_number_prints_without_a_decimal():
    assert render('{{n}}', {'n': 1.0}) == '1'
    assert render('{{n}}', {'n': 1.5}) == '1.5'


def test_list_prints_values_separated_by_commas():
    assert render('{{items}}', {'items': [1, 2]}) == '1,2'


def test_object_prints_as_object_object():
    assert render('{{item}}', {'item': {'a': 1}}) == '[object Object]'


def test_tuples_and_custom_sequences_mappings():
    hb = Handlebars()
    # 1. Sequence iteration, printing, and indexing
    assert hb.compile('{{#each items}}{{this}}{{/each}}')({'items': (1, 2)}) == '12'
    assert hb.compile('{{items}}')({'items': (1, 2)}) == '1,2'
    assert hb.compile('{{items.[0]}}')({'items': (1, 2)}) == '1'

    # 2. Section repetition and empty sequence truthiness
    assert hb.compile('{{#items}}{{this}}{{/items}}')({'items': (1, 2)}) == '12'
    assert hb.compile('{{#if items}}yes{{else}}no{{/if}}')({'items': ()}) == 'no'
    assert hb.compile('{{#if items}}yes{{else}}no{{/if}}')({'items': (1,)}) == 'yes'

    # 3. Custom mappings and sequences
    custom_data = UserDict({'title': 'Catalog', 'entries': deque(['A', 'B'])})
    assert hb.compile('{{title}}: {{#each entries}}{{this}}{{/each}}')(custom_data) == 'Catalog: AB'
    assert hb.compile('{{entries.[1]}}')(custom_data) == 'B'


# ==============================================================================
# 2. HTML Escaping, Delimiters & Raw Outputs
# ==============================================================================


def test_escapes_html_by_default():
    assert render('{{content}}', {'content': "<script>alert('xss')</script>"}) == (
        '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;'
    )


def test_escape_includes_equals_and_backtick():
    assert render('{{v}}', {'v': 'a=`b'}) == 'a&#x3D;&#x60;b'


def test_triple_braces_disable_escaping():
    assert render('{{{content}}}', {'content': '<b>bold</b>'}) == '<b>bold</b>'


def test_ampersand_disables_escaping():
    assert render('{{&content}}', {'content': '<b>bold</b>'}) == '<b>bold</b>'


def test_escape_html_off_leaves_markup():
    hb = Handlebars(escape_html=False)
    assert render('{{content}}', {'content': '<b>bold</b>'}, hb=hb) == '<b>bold</b>'


def test_safe_string_skips_escaping():
    hb = Handlebars()
    hb.register_helper('bold', lambda args, options: SafeString(f'<b>{args[0]}</b>'))
    assert render('{{bold name}}', {'name': 'test'}, hb=hb) == '<b>test</b>'


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


def test_field_named_raw_renders_as_variable():
    hb = Handlebars()
    assert hb.compile('{{raw}}')({'raw': 'prompt_value'}) == 'prompt_value'
    assert hb.compile('{{#raw}}yes{{/raw}}')({'raw': True}) == 'yes'
    assert hb.compile('{{#raw}}yes{{/raw}}')({'raw': False}) == ''


# ==============================================================================
# 3. Truthiness & Branching Matrix (if, unless, with, each, sections)
# ==============================================================================


def test_if_else_and_falsy_values():
    assert render('{{#if show}}yes{{else}}no{{/if}}', {'show': True}) == 'yes'
    assert render('{{#if show}}yes{{else}}no{{/if}}', {'show': False}) == 'no'
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': ''}) == 'no'
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': 0}) == 'no'
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': None}) == 'no'
    assert render('{{#if items}}yes{{else}}no{{/if}}', {'items': []}) == 'no'
    assert render('{{#if items}}yes{{else}}no{{/if}}', {'items': [1]}) == 'yes'


def test_zero_skips_if_and_enters_with():
    assert render('{{#if z}}I{{else}}no{{/if}}', {'z': 0}) == 'no'
    assert render('{{#with z}}[{{.}}]{{else}}no{{/with}}', {'z': 0}) == '[0]'


def test_include_zero_makes_if_enter_on_zero():
    assert render('{{#if z includeZero=true}}yes{{else}}no{{/if}}', {'z': 0}) == 'yes'


def test_empty_string_skips_with():
    assert render('{{#with s}}yes{{else}}no{{/with}}', {'s': ''}) == 'no'


def test_empty_object_enters_if_and_with_and_each_takes_else():
    assert render('{{#if o}}yes{{else}}no{{/if}}', {'o': {}}) == 'yes'
    assert render('{{#with o}}yes{{else}}no{{/with}}', {'o': {}}) == 'yes'
    assert render('{{#each o}}x{{else}}empty{{/each}}', {'o': {}}) == 'empty'


def test_each_on_a_number_takes_the_else_branch():
    assert render('{{#each n}}x{{else}}empty{{/each}}', {'n': 5}) == 'empty'


def test_else_if_picks_the_matching_branch():
    source = '{{#if a}}A{{else if b}}B{{else}}C{{/if}}'
    assert render(source, {'a': True}) == 'A'
    assert render(source, {'b': True}) == 'B'
    assert render(source, {'a': False, 'b': False}) == 'C'


def test_else_unless_skips_the_branch_when_the_value_is_set():
    source = '{{#if a}}A{{else unless b}}notB{{else}}B{{/if}}'
    assert render(source, {'a': False, 'b': False}) == 'notB'
    assert render(source, {'a': False, 'b': True}) == 'B'


def test_unless_block():
    assert render('{{#unless hidden}}visible{{/unless}}', {'hidden': False}) == 'visible'
    assert render('{{#unless hidden}}visible{{/unless}}', {'hidden': True}) == ''


def test_section_repeats_a_list_and_enters_an_object():
    assert render('{{#items}}{{.}}{{/items}}', {'items': ['a', 'b']}) == 'ab'
    assert render('{{#user}}{{name}}{{/user}}', {'user': {'name': 'A'}}) == 'A'


def test_section_on_zero_enters_and_on_false_takes_else():
    assert render('{{#z}}yes{{else}}no{{/z}}', {'z': 0}) == 'yes'
    assert render('{{#z}}yes{{else}}no{{/z}}', {'z': False}) == 'no'


def test_inverse_section_prints_when_the_list_is_empty():
    assert render('{{^items}}none{{/items}}', {'items': []}) == 'none'
    assert render('{{^items}}none{{/items}}', {'items': ['a']}) == ''


# ==============================================================================
# 4. Iteration, Block Params & Lexical Scopes
# ==============================================================================


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
    obj_source = '{{#each obj as |val key|}}{{key}}={{val}};{{/each}}'
    assert render(obj_source, {'obj': {'x': 1, 'y': 2}}) == 'x=1;y=2;'


def test_block_param_names_the_item_and_this_is_still_the_item():
    source = '{{#each items as |it|}}{{name}}/{{it.name}}/{{../name}};{{/each}}'
    assert render(source, {'name': 'OUTER', 'items': [{'name': 'I1'}]}) == 'I1/I1/OUTER;'


def test_nested_each_parent_index():
    source = '{{#each outer}}{{#each .}}{{@../index}}{{/each}}{{/each}}'
    assert render(source, {'outer': [['a'], ['b', 'c']]}) == '011'


# ==============================================================================
# 5. Context Frames & @root / @data
# ==============================================================================


def test_with_block_and_root():
    assert render('{{#with user}}{{name}}{{/with}}', {'user': {'name': 'Alice'}}) == 'Alice'
    source = '{{#with user}}{{name}} from {{@root.company}}{{/with}}'
    assert render(source, {'user': {'name': 'Alice'}, 'company': 'Acme'}) == 'Alice from Acme'
    grandparent = '{{#with l1}}{{#with l2}}{{val}}-{{../../root}}{{/with}}{{/with}}'
    assert render(grandparent, {'root': 'R', 'l1': {'l2': {'val': 'V'}}}) == 'V-R'


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


def test_reserved_data_keys_rejects_only_when_template_resolves_key():
    hb = Handlebars(reserved_data_keys={'root'})
    hb.register_helper('h', lambda args, opt: f'h:{args[0]}')
    hb.register_helper('s', lambda args, opt: f's:{opt.hash.get("k")}')

    # Allowed when data does not contain reserved key
    assert hb.compile('{{@root.name}}')({'name': 'Ada'}, {'data': {}}) == 'Ada'

    # Allowed when data contains reserved key but template does not access it
    assert hb.compile('Hello {{name}}')({'name': 'Ada'}, {'data': {'root': 'custom'}}) == 'Hello Ada'

    # Direct access to @root with reserved key in data raises ValueError
    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        hb.compile('{{@root}}')({'name': 'Ada'}, {'data': {'root': 'custom'}})

    # Nested access to @root.name with reserved key in data raises ValueError
    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        hb.compile('{{@root.name}}')({'name': 'Ada'}, {'data': {'root': 'custom'}})

    # Subexpression {{h (s k=@root)}} with reserved key in data raises ValueError
    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        hb.compile('{{h (s k=@root)}}')({'name': 'Ada'}, {'data': {'root': 'custom'}})

    # Parent path {{@../root}} with reserved key in data raises ValueError
    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        hb.compile('{{#each list}}{{@../root}}{{/each}}')({'list': ['item']}, {'data': {'root': 'custom'}})


# ==============================================================================
# 6. Partials, Blocks & Call-Site Indentation
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


def test_partial_block_inserts_its_body_where_the_partial_asks():
    hb = Handlebars()
    hb.register_partial('wrap', 'X{{> @partial-block}}Y')
    assert render('{{#> wrap}}IN{{/wrap}}', {}, hb=hb) == 'XINY'


def test_inline_partial():
    source = '{{#*inline "myPartial"}}Hello {{name}}!{{/inline}}{{> myPartial}}'
    assert render(source, {'name': 'World'}).strip() == 'Hello World!'


def test_partial_does_not_see_the_caller_parent():
    hb = Handlebars()
    hb.register_partial('card', '[{{../x}}{{y}}]')
    assert render('{{#with o}}{{> card}}{{/with}}', {'x': 'PARENT', 'o': {'y': 'Y'}}, hb=hb) == '[Y]'


def test_partial_keeps_the_each_index():
    hb = Handlebars()
    hb.register_partial('row', '[{{@index}}]')
    assert render('{{#each xs}}{{> row}}{{/each}}', {'xs': ['a', 'b']}, hb=hb) == '[0][1]'


def test_partial_indents_to_the_call_site():
    hb = Handlebars()
    hb.register_partial('card', 'a\nb\n')
    assert render('  {{> card}}\n', {}, hb=hb) == '  a\n  b\n'


def test_dynamic_partial_uses_the_helper_result_as_the_name():
    hb = Handlebars()
    hb.register_helper('which', lambda args, options: 'card')
    hb.register_partial('card', 'DYN')
    assert render('{{> (which)}}', {}, hb=hb) == 'DYN'


def test_partial_hash_replaces_a_string_context():
    hb = Handlebars()
    hb.register_partial('card', '{{who}}|{{.}}')
    assert render('{{> card "x" who="W"}}', {}, hb=hb) == 'W|[object Object]'


def test_recursive_partial_raises_recursion_error():
    hb = Handlebars()
    hb.register_partial('loop', '{{> loop}}')
    with pytest.raises(TemplateRecursionError, match=r'maximum template depth exceeded \(100\)'):
        hb.compile('{{> loop}}')({})


def test_custom_max_depth_guard_raises():
    hb = Handlebars(max_depth=5)
    hb.register_partial('loop', '{{> loop}}')
    with pytest.raises(TemplateRecursionError, match=r'maximum template depth exceeded \(5\)'):
        hb.compile('{{> loop}}')({})


def test_deeply_nested_blocks_exceeding_max_depth_raises():
    nested = '{{#if true}}' * 150 + 'deep' + '{{/if}}' * 150
    hb = Handlebars()
    with pytest.raises(TemplateRecursionError, match=r'maximum template depth exceeded \(100\)'):
        hb.compile(nested)({})


# ==============================================================================
# 7. Whitespace Control, Comments & String Literals
# ==============================================================================


def test_comments_whitespace_and_literal_braces():
    assert render('Hello {{! this is a comment }}World', {}) == 'Hello World'
    assert render('Hello   {{~name}}!', {'name': 'World'}) == 'HelloWorld!'
    assert render(r'Show \{{name}} literally', {'name': 'World'}) == 'Show {{name}} literally'
    assert render(r'\\{{name}}', {'name': 'World'}) == r'\World'


def test_three_backslashes_leave_two_and_render_the_variable():
    assert render(r'\\\{{name}}', {'name': 'World'}) == r'\\World'


def test_backslash_n_inside_a_string_stays_a_backslash():
    hb = Handlebars()
    seen = {}

    def grab(args, options):
        seen['value'] = args[0]
        return ''

    hb.register_helper('grab', grab)
    render('{{grab "a\nb"}}', {}, hb=hb)
    assert seen['value'] == 'a\nb'


def test_escaped_quote_inside_a_string_is_a_quote():
    hb = Handlebars()
    seen = {}

    def grab(args, options):
        seen['value'] = args[0]
        return ''

    hb.register_helper('grab', grab)
    render('{{grab "a"b"}}', {}, hb=hb)
    assert seen['value'] == 'a"b'


def test_tilde_triple_stash_trims_whitespace_and_preserves_raw():
    assert render('Hello  {{~{name}~}}  World', {'name': '<b>Beautiful</b>'}) == 'Hello<b>Beautiful</b>World'
    assert render('Hello   {{~{name}}} World', {'name': '<b>Beautiful</b>'}) == 'Hello<b>Beautiful</b> World'
    assert render('Hello {{{name}~}}   World', {'name': '<b>Beautiful</b>'}) == 'Hello <b>Beautiful</b>World'


def test_multibyte_utf8_identifiers_and_comments():
    source = 'Hola {{año}}, こんにちは {{名前}}! {{! 注释 }} {{!-- 详细注释 --}}'
    assert render(source, {'año': 2026, '名前': '太郎'}) == 'Hola 2026, こんにちは 太郎!  '
    assert render('{{{año}}}', {'año': '<b>2026</b>'}) == '<b>2026</b>'


# ==============================================================================
# 8. Custom Helpers, HelperOptions & Subexpressions
# ==============================================================================


def test_subexpression_and_literals():
    hb = Handlebars()
    hb.register_helper('upper', lambda args, options: str(args[0]).upper())
    hb.register_helper('wrap', lambda args, options: f'[{args[0]}]')
    hb.register_helper('add', lambda args, options: args[0] + args[1])
    hb.register_helper('mult', lambda args, options: args[0] * args[1])
    hb.register_helper('format', lambda args, options: options.hash.get('prefix', '') + args[0])
    hb.register_helper('tag', lambda args, options: f'<{options.hash.get("text", "")}>')

    assert render('{{wrap (upper name)}}', {'name': 'hello'}, hb=hb) == '[HELLO]'
    assert render('{{add 10 -5}}', {}, hb=hb) == '5'
    assert render('{{mult (add 2 3) 4}}', {}, hb=hb) == '20'
    assert render('{{wrap (format name prefix="Dr. ")}}', {'name': 'Who'}, hb=hb) == '[Dr. Who]'
    assert render('{{{tag text=(format name prefix="Dr. ")}}}', {'name': 'Who'}, hb=hb) == '<Dr. Who>'


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


def test_typed_helper_options_and_block_fn():
    hb = Handlebars()

    def custom_section(args: list[Any], options: HelperOptions) -> SafeString:
        assert isinstance(options, HelperOptions)
        assert isinstance(options.hash, dict)
        assert isinstance(options.data, dict)
        assert options.is_block is True
        prefix = options.hash_value('prefix')
        body = options.fn(options.context)
        return SafeString(f'{prefix}{body}')

    hb.register_helper('customSection', custom_section)
    result = hb.compile('{{#customSection prefix="-->"}}{{item}}{{/customSection}}')({'item': 'value'})
    assert result == '-->value'


def test_context_callable_backward_compat():
    hb = Handlebars()

    def legacy_helper(args: list[Any], options: HelperOptions) -> str:
        # Legacy handlebarrz syntax called options.context() as a method
        ctx = options.context()
        assert isinstance(ctx, dict)
        # Modern attribute access also works
        assert options.context['user'] == 'Alice'
        return f'Hello {ctx.get("user", "")}!'

    hb.register_helper('legacy', legacy_helper)
    assert hb.compile('{{legacy}}')({'user': 'Alice'}) == 'Hello Alice!'


def test_missing_helper_raises():
    with pytest.raises(ValueError, match='Missing helper: "nohelper"'):
        render('{{nohelper name}}', {'name': 'x'})


def test_input_function_raises():
    with pytest.raises(ValueError, match='register it as a helper'):
        render('{{name}}', {'name': lambda: 'called'})


# ==============================================================================
# 9. Strict Mode & Syntax Rejections
# ==============================================================================


def test_strict_mode_names_the_missing_path():
    hb = Handlebars(strict=True)
    with pytest.raises(StrictModeError) as raised:
        hb.compile('{{user.name}}')({})
    assert raised.value.path == 'user.name'
    assert 'is not defined' in str(raised.value)
    assert hb.compile('{{#if name}}yes{{else}}no{{/if}}')({'name': None}) == 'no'


def test_strict_if_on_a_missing_name_takes_the_else_branch():
    assert render('{{#if missing}}yes{{else}}no{{/if}}', {}, strict=True) == 'no'


def test_strict_section_on_a_missing_name_raises():
    with pytest.raises(StrictModeError) as raised:
        render('{{#missing}}yes{{else}}no{{/missing}}', {}, strict=True)
    assert raised.value.path == 'missing'


def test_strict_helper_argument_may_be_missing():
    hb = Handlebars(strict=True)
    hb.register_helper('show', lambda args, options: 'yes' if args[0] is None else 'no')
    assert render('{{show missing}}', {}, hb=hb) == 'yes'


def test_unclosed_raw_block_raises():
    with pytest.raises(ValueError, match='unclosed raw block'):
        Handlebars().compile('{{{{raw}}}}{{name}}')


def test_unclosed_block_raises():
    with pytest.raises(ValueError):
        Handlebars().compile('{{#if show}}yes')


def test_leading_dot_number_raises():
    with pytest.raises(ValueError, match='not a valid number'):
        render('{{.5}}', {})


def test_decorator_raises():
    with pytest.raises(ValueError, match='decorators are not supported'):
        Handlebars().compile('{{* foo}}x')


def test_if_without_an_argument_raises():
    with pytest.raises(ValueError, match='#if requires exactly one argument'):
        render('{{#if}}x{{/if}}', {})


def test_ast_node_dataclasses_and_tag_tokens():
    nodes = compile_template('Hello {{name}}! {{#if active}}Active{{else}}Inactive{{/if}}')
    assert len(nodes) == 4
    assert isinstance(nodes[0], Text)
    assert nodes[0].value == 'Hello '
    assert isinstance(nodes[1], Mustache)
    assert nodes[1].call['name'] == 'name'
    assert isinstance(nodes[2], Text)
    assert isinstance(nodes[3], Block)
    assert nodes[3].call['name'] == 'if'
    assert len(nodes[3].body) == 1
    assert isinstance(nodes[3].body[0], Text)
    assert nodes[3].body[0].value == 'Active'
    assert len(nodes[3].inverse) == 1
    assert isinstance(nodes[3].inverse[0], Text)
    assert nodes[3].inverse[0].value == 'Inactive'

    token = TagToken(body='name', triple=True, strip_before=True, strip_after=False, indent='  ')
    assert token.body == 'name'
    assert token.triple is True
    assert token.strip_before is True
    assert token.indent == '  '
    assert token.raw_block is False

    raw_nodes = compile_template('{{{{raw}}}}{{name}}{{{{/raw}}}}')
    assert raw_nodes == [Text(value='{{name}}')]
