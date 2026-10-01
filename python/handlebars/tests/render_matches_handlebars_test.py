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

"""Edge-case semantics verified against Handlebars 4.7.8.

Documents and asserts non-obvious Handlebars behaviors that prompt authors
encounter—such as zero falsiness in {{#if}} vs truthiness in {{#with}},
array and object stringification, call-site partial indentation, and scope boundaries.
"""

import pytest

from handlebars import Handlebars, StrictModeError


def render(source, data=None, *, hb=None, strict=False):
    hb = hb or Handlebars(strict=strict)
    return hb.compile(source)(data if data is not None else {})


# ==============================================================================
# 1. Truthiness & Branching Matrix
# ==============================================================================


def test_zero_skips_if_and_enters_with():
    assert render('{{#if z}}I{{else}}no{{/if}}', {'z': 0}) == 'no'
    assert render('{{#with z}}[{{.}}]{{else}}no{{/with}}', {'z': 0}) == '[0]'


def test_include_zero_makes_if_enter_on_zero():
    assert render('{{#if z includeZero=true}}yes{{else}}no{{/if}}', {'z': 0}) == 'yes'


def test_empty_string_skips_with():
    assert render('{{#with s}}yes{{else}}no{{/with}}', {'s': ''}) == 'no'


def test_empty_object_enters_if_and_each_takes_else():
    assert render('{{#if o}}yes{{else}}no{{/if}}', {'o': {}}) == 'yes'
    assert render('{{#each o}}x{{else}}empty{{/each}}', {'o': {}}) == 'empty'


def test_each_on_a_number_takes_the_else_branch():
    assert render('{{#each n}}x{{else}}empty{{/each}}', {'n': 5}) == 'empty'


# ==============================================================================
# 2. Type Formatting & Output Escaping
# ==============================================================================


def test_list_prints_values_separated_by_commas():
    assert render('{{items}}', {'items': [1, 2]}) == '1,2'


def test_object_prints_as_object_object():
    assert render('{{item}}', {'item': {'a': 1}}) == '[object Object]'


def test_whole_number_prints_without_a_decimal():
    assert render('{{n}}', {'n': 1.0}) == '1'
    assert render('{{n}}', {'n': 1.5}) == '1.5'


def test_escape_includes_equals_and_backtick():
    assert render('{{v}}', {'v': 'a=`b'}) == 'a&#x3D;&#x60;b'


# ==============================================================================
# 3. Block Parameters & Lexical Scopes
# ==============================================================================


def test_block_param_names_the_item_and_this_is_still_the_item():
    source = '{{#each items as |it|}}{{name}}/{{it.name}}/{{../name}};{{/each}}'
    assert render(source, {'name': 'OUTER', 'items': [{'name': 'I1'}]}) == 'I1/I1/OUTER;'


# ==============================================================================
# 4. Partials & Call-Site Indentation
# ==============================================================================


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


def test_nested_each_parent_index():
    source = '{{#each outer}}{{#each .}}{{@../index}}{{/each}}{{/each}}'
    assert render(source, {'outer': [['a'], ['b', 'c']]}) == '011'


def test_dynamic_partial_uses_the_helper_result_as_the_name():
    hb = Handlebars()
    hb.register_helper('which', lambda args, options: 'card')
    hb.register_partial('card', 'DYN')
    assert render('{{> (which)}}', {}, hb=hb) == 'DYN'


def test_partial_block_inserts_its_body_where_the_partial_asks():
    hb = Handlebars()
    hb.register_partial('wrap', 'X{{> @partial-block}}Y')
    assert render('{{#> wrap}}IN{{/wrap}}', {}, hb=hb) == 'XINY'


def test_partial_hash_replaces_a_string_context():
    hb = Handlebars()
    hb.register_partial('card', '{{who}}|{{.}}')
    assert render('{{> card "x" who="W"}}', {}, hb=hb) == 'W|[object Object]'


# ==============================================================================
# 5. Sections & Block Inversion
# ==============================================================================


def test_missing_helper_raises():
    with pytest.raises(ValueError, match='Missing helper: "nohelper"'):
        render('{{nohelper name}}', {'name': 'x'})


def test_section_repeats_a_list_and_enters_an_object():
    assert render('{{#items}}{{.}}{{/items}}', {'items': ['a', 'b']}) == 'ab'
    assert render('{{#user}}{{name}}{{/user}}', {'user': {'name': 'A'}}) == 'A'


def test_section_on_zero_enters_and_on_false_takes_else():
    assert render('{{#z}}yes{{else}}no{{/z}}', {'z': 0}) == 'yes'
    assert render('{{#z}}yes{{else}}no{{/z}}', {'z': False}) == 'no'


def test_inverse_section_prints_when_the_list_is_empty():
    assert render('{{^items}}none{{/items}}', {'items': []}) == 'none'
    assert render('{{^items}}none{{/items}}', {'items': ['a']}) == ''


def test_else_unless_skips_the_branch_when_the_value_is_set():
    source = '{{#if a}}A{{else unless b}}notB{{else}}B{{/if}}'
    assert render(source, {'a': False, 'b': False}) == 'notB'
    assert render(source, {'a': False, 'b': True}) == 'B'


# ==============================================================================
# 6. Paths & Bracket Syntax
# ==============================================================================


def test_bracket_path_reads_a_key_that_has_a_space():
    assert render('{{a.[b c]}}', {'a': {'b c': 'OK'}}) == 'OK'


def test_this_dot_reads_the_current_object():
    assert render('{{this.name}}|{{./name}}', {'name': 'N'}) == 'N|N'


# ==============================================================================
# 7. Strict Mode Contracts
# ==============================================================================


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


# ==============================================================================
# 8. Literal Delimiter & String Escaping
# ==============================================================================


def test_three_backslashes_leave_two_and_render_the_variable():
    assert render('\\\\\\{{name}}', {'name': 'World'}) == '\\\\World'


def test_backslash_n_inside_a_string_stays_a_backslash():
    hb = Handlebars()
    seen = {}

    def grab(args, options):
        seen['value'] = args[0]
        return ''

    hb.register_helper('grab', grab)
    render('{{grab "a\\nb"}}', {}, hb=hb)
    assert seen['value'] == 'a\\nb'


def test_escaped_quote_inside_a_string_is_a_quote():
    hb = Handlebars()
    seen = {}

    def grab(args, options):
        seen['value'] = args[0]
        return ''

    hb.register_helper('grab', grab)
    render('{{grab "a\\"b"}}', {}, hb=hb)
    assert seen['value'] == 'a"b'


# ==============================================================================
# 9. Explicit Syntax Rejections (Compile / Runtime Rejections)
# ==============================================================================


def test_leading_dot_number_raises():
    with pytest.raises(ValueError, match='not a valid number'):
        render('{{.5}}', {})


def test_decorator_raises():
    with pytest.raises(ValueError, match='decorators are not supported'):
        Handlebars().compile('{{* foo}}x')


def test_if_without_an_argument_raises():
    with pytest.raises(ValueError, match='#if requires exactly one argument'):
        render('{{#if}}x{{/if}}', {})


def test_input_function_raises():
    with pytest.raises(ValueError, match='register it as a helper'):
        render('{{name}}', {'name': lambda: 'called'})
