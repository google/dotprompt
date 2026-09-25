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

"""One case per Dart test the first file did not already assert."""

import pytest

from handlebars import Handlebars, SafeString, StrictModeError


def render(source, data=None, *, hb=None):
    hb = hb or Handlebars()
    return hb.compile(source)(data if data is not None else {})


def test_mixed_path_separators():
    assert render('{{a.b/c.d}}', {'a': {'b': {'c': {'d': 'value'}}}}) == 'value'


def test_helper_uppercases_its_argument():
    hb = Handlebars()
    hb.register_helper('upper', lambda args, options: str(args[0]).upper())
    assert render('{{upper name}}', {'name': 'world'}, hb=hb) == 'WORLD'


def test_helper_receives_a_string_literal():
    hb = Handlebars()
    hb.register_helper('greet', lambda args, options: f'Hello, {args[0]}!')
    assert render('{{greet "Alice"}}', {}, hb=hb) == 'Hello, Alice!'


def test_helper_receives_a_named_argument():
    hb = Handlebars()

    def link(args, options):
        return SafeString(f'<a href="{options.hash["url"]}">{args[0]}</a>')

    hb.register_helper('link', link)
    assert render('{{link "Go" url="https://example.com"}}', {}, hb=hb) == '<a href="https://example.com">Go</a>'


def test_if_without_else_prints_the_body_or_nothing():
    assert render('{{#if show}}visible{{/if}}', {'show': True}) == 'visible'
    assert render('{{#if show}}visible{{/if}}', {'show': False}) == ''


def test_each_over_an_object_prints_the_key():
    rendered = render('{{#each person}}{{@key}}={{.}} {{/each}}', {'person': {'name': 'Alice', 'age': '30'}})
    assert rendered in ('name=Alice age=30 ', 'age=30 name=Alice ')


def test_nested_each_prints_each_row():
    assert render('{{#each rows}}{{#each .}}{{.}}{{/each}}|{{/each}}', {'rows': [['a', 'b'], ['c', 'd']]}) == 'ab|cd|'


def test_each_else_prints_the_item_when_the_list_is_not_empty():
    assert render('{{#each items}}{{.}}{{else}}empty{{/each}}', {'items': ['a']}) == 'a'


def test_unless_equals_prints_the_else_body_when_the_values_match():
    hb = Handlebars()

    def unless_equals(args, options):
        return options.fn() if args[0] != args[1] else options.inverse()

    hb.register_helper('unlessEquals', unless_equals)
    source = '{{#unlessEquals status "active"}}Not Active{{else}}Active{{/unlessEquals}}'
    assert render(source, {'status': 'pending'}, hb=hb) == 'Not Active'
    assert render(source, {'status': 'active'}, hb=hb) == 'Active'


def test_partial_with_context_reads_that_object():
    hb = Handlebars()
    hb.register_partial('userCard', 'Name: {{name}}, Email: {{email}}')
    assert (
        render('{{> userCard user}}', {'user': {'name': 'Alice', 'email': 'alice@example.com'}}, hb=hb)
        == 'Name: Alice, Email: alice@example.com'
    )


def test_long_comment_is_ignored():
    assert render('Hello {{!-- long comment --}}World', {}) == 'Hello World'


def test_backslash_at_end_of_text_prints_braces():
    assert render(r'End: \{{', {}) == 'End: {{'


def test_tilde_strips_the_space_after_a_variable():
    assert render('{{name~}}   World!', {'name': 'Hello'}) == 'HelloWorld!'


def test_tilde_on_both_sides_strips_both_spaces():
    assert render('Hello   {{~name~}}   World', {'name': 'Beautiful'}) == 'HelloBeautifulWorld'


def test_tilde_around_an_if_strips_even_when_the_block_is_empty():
    source = 'Hello   {{~#if show}}Visible{{/if~}}   World'
    assert render(source, {'show': True}) == 'HelloVisibleWorld'
    assert render(source, {'show': False}) == 'HelloWorld'


def test_tilde_after_each_strips_the_space_before_done():
    assert render('Items: {{#each items}}{{.}}{{/each~}}   Done', {'items': ['a', 'b']}) == 'Items: abDone'


def test_nested_subexpression():
    hb = Handlebars()
    hb.register_helper('add', lambda args, options: args[0] + args[1])
    hb.register_helper('mult', lambda args, options: args[0] * args[1])
    assert render('{{mult (add 2 3) 4}}', {}, hb=hb) == '20'


def test_subexpression_with_a_named_argument():
    hb = Handlebars()
    hb.register_helper('format', lambda args, options: f'{options.hash["prefix"]}{args[0]}')
    hb.register_helper('wrap', lambda args, options: SafeString(f'<{args[0]}>'))
    assert render('{{wrap (format name prefix="Dr. ")}}', {'name': 'Smith'}, hb=hb) == '<Dr. Smith>'


def test_nested_each_has_its_own_index():
    source = '{{#each outer}}{{@index}}:[{{#each .}}{{@index}}{{/each}}]{{/each}}'
    assert render(source, {'outer': [['a'], ['b', 'c']]}) == '0:[0]1:[01]'


def test_parent_path_inside_with():
    assert render('{{#with person}}{{name}} works at {{../company}}{{/with}}', {'company': 'Acme', 'person': {'name': 'Alice'}}) == 'Alice works at Acme'


def test_grandparent_path():
    source = '{{#with level1}}{{#with level2}}{{value}}-{{../name}}-{{../../root}}{{/with}}{{/with}}'
    data = {'root': 'ROOT', 'level1': {'name': 'L1', 'level2': {'value': 'L2'}}}
    assert render(source, data) == 'L2-L1-ROOT'


def test_parent_path_next_to_a_primitive_item():
    source = '{{#each items}}Item {{.}} from {{../source}}; {{/each}}'
    assert render(source, {'source': 'data', 'items': ['a', 'b']}) == 'Item a from data; Item b from data; '


def test_lookup_reads_a_map_by_a_variable_key():
    data = {'person': {'Alice': 'Engineer', 'Bob': 'Manager'}, 'name': 'Alice'}
    assert render('{{lookup person name}}', data) == 'Engineer'


def test_lookup_reads_a_list_by_a_string_index():
    assert render('{{lookup items idx}}', {'items': ['a', 'b', 'c'], 'idx': '2'}) == 'c'


def test_log_prints_nothing_into_the_template():
    assert render('Value: {{log name}}end', {'name': 'test'}) == 'Value: end'


def test_each_block_param_is_the_item():
    assert render('{{#each items as |item|}}{{item}};{{/each}}', {'items': ['a', 'b', 'c']}) == 'a;b;c;'


def test_each_block_params_are_the_item_and_the_index():
    assert render('{{#each items as |item index|}}{{index}}:{{item}};{{/each}}', {'items': ['a', 'b', 'c']}) == '0:a;1:b;2:c;'


def test_each_block_params_over_an_object_are_the_value_and_the_key():
    assert render('{{#each obj as |val key|}}{{key}}={{val}};{{/each}}', {'obj': {'x': 1, 'y': 2}}) == 'x=1;y=2;'


def test_missing_partial_block_prints_its_body():
    assert render('{{#> missingPartial}}Default Content{{/missingPartial}}', {}) == 'Default Content'


def test_inline_partial_renders_where_it_is_included():
    source = '{{#*inline "myPartial"}}Hello {{name}}!{{/inline}}\n{{> myPartial}}'
    assert render(source, {'name': 'World'}).strip() == 'Hello World!'


def test_inline_partial_can_be_included_twice():
    source = '{{#*inline "greeting"}}Hi {{name}}{{/inline}}\n{{> greeting}} and {{> greeting}}'
    assert render(source, {'name': 'Alice'}).strip() == 'Hi Alice and Hi Alice'


def test_inline_partial_inside_each_reads_the_item():
    source = '{{#*inline "userCard"}}<div>{{name}}</div>{{/inline}}\n{{#each users}}{{> userCard}}{{/each}}'
    assert render(source, {'users': [{'name': 'Alice'}, {'name': 'Bob'}]}).strip() == '<div>Alice</div><div>Bob</div>'


def test_inline_partial_replaces_a_registered_partial():
    hb = Handlebars()
    hb.register_partial('myPartial', 'REGISTERED')
    source = '{{#*inline "myPartial"}}INLINE{{/inline}}\n{{> myPartial}}'
    assert render(source, {}, hb=hb).strip() == 'INLINE'


def test_true_literal_reaches_the_helper():
    hb = Handlebars()
    hb.register_helper('showBool', lambda args, options: 'yes' if args[0] is True else 'no')
    assert render('{{showBool true}}', {}, hb=hb) == 'yes'


def test_false_literal_reaches_the_helper():
    hb = Handlebars()
    hb.register_helper('showBool', lambda args, options: 'yes' if args[0] is False else 'no')
    assert render('{{showBool false}}', {}, hb=hb) == 'yes'


def test_two_number_literals_are_added():
    hb = Handlebars()
    hb.register_helper('add', lambda args, options: args[0] + args[1])
    assert render('{{add 10 20}}', {}, hb=hb) == '30'


def test_single_quoted_string_reaches_the_helper():
    hb = Handlebars()
    hb.register_helper('greet', lambda args, options: f'Hi {args[0]}!')
    assert render("{{greet 'world'}}", {}, hb=hb) == 'Hi world!'


def test_deeply_nested_path():
    data = {'a': {'b': {'c': {'d': {'e': 'deep'}}}}}
    assert render('{{a.b.c.d.e}}', data) == 'deep'


def test_else_then_a_nested_if():
    source = '{{#if a}}A{{else}}{{#if b}}B{{else}}C{{/if}}{{/if}}'
    assert render(source, {'a': True}) == 'A'
    assert render(source, {'b': True}) == 'B'
    assert render(source, {'a': False, 'b': False}) == 'C'


def test_empty_string_is_falsy():
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': ''}) == 'no'
    assert render('{{#if val}}yes{{else}}no{{/if}}', {'val': 'x'}) == 'yes'


def test_strict_mode_rejects_a_missing_name():
    hb = Handlebars(strict=True)
    with pytest.raises(StrictModeError):
        hb.compile('Hello {{name}}!')({})


def test_strict_mode_rejects_a_missing_nested_path():
    hb = Handlebars(strict=True)
    with pytest.raises(StrictModeError) as raised:
        hb.compile('{{user.profile.name}}')({'user': {}})
    assert raised.value.path == 'user.profile.name'
