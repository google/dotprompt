# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from handlebarrz import HelperOptions, RuntimeOptions, Template


def test_input_and_runtime_data_are_separate_on_name_collision() -> None:
    template = Template()

    result = template.render_template(
        '{{name}}|{{@name}}|{{@profile.name}}|{{@profile.[display name]}}',
        {'name': 'input'},
        {'data': {'name': 'runtime', 'profile': {'name': 'Ada', 'display name': 'A'}}},
    )

    assert result == 'input|runtime|Ada|A'


def test_runtime_paths_work_in_escaped_and_unescaped_expressions() -> None:
    template = Template()
    options: RuntimeOptions = {'data': {'value': '<runtime>'}}

    result = template.render_template('{{@value}}|{{{@value}}}|{{&@value}}', {}, options)

    assert result == '&lt;runtime&gt;|<runtime>|<runtime>'


def test_runtime_paths_work_as_positional_hash_and_subexpression_arguments() -> None:
    template = Template()

    def inspect(params: list[Any], options: HelperOptions) -> str:
        return json.dumps([params, options.hash_value('named')], separators=(',', ':'))

    template.register_helper('inspect', inspect)

    result = template.render_template(
        '{{inspect @count (lookup @settings "enabled") named=@payload}}',
        {},
        {'data': {'count': 3, 'settings': {'enabled': False}, 'payload': {'id': 7}}},
    )

    assert result == '[[3,false],{"id":7}]'


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('{{#if @value}}yes{{else}}no{{/if}}', 'yes'),
        ('{{#unless @missing}}missing{{/unless}}', 'missing'),
        ('{{#with @profile}}{{name}}/{{@tenant}}{{/with}}', 'Ada/acme'),
        ('{{#each @items}}{{this}}:{{@tenant}};{{/each}}', 'a:acme;b:acme;'),
        ('{{#if (lookup @flags "ready")}}ready{{/if}}', 'ready'),
    ],
)
def test_runtime_paths_work_across_builtin_blocks(source: str, expected: str) -> None:
    template = Template()
    runtime_data = {
        'value': 1,
        'profile': {'name': 'Ada'},
        'tenant': 'acme',
        'items': ['a', 'b'],
        'flags': {'ready': True},
    }

    assert template.render_template(source, {}, {'data': runtime_data}) == expected


@pytest.mark.parametrize(
    'value',
    [
        None,
        False,
        True,
        0,
        '',
        'text',
        {},
        {'name': 'Ada'},
        [],
        [1, 2],
    ],
)
def test_runtime_direct_sections_match_input_sections_for_json_shapes(value: Any) -> None:
    template = Template()
    input_source = '{{#section}}[{{this}}/{{name}}/{{@index}}]{{else}}empty{{/section}}'
    runtime_source = '{{#@section}}[{{this}}/{{name}}/{{@index}}]{{else}}empty{{/@section}}'

    input_result = template.render_template(input_source, {'section': value})
    runtime_result = template.render_template(runtime_source, {}, {'data': {'section': value}})

    assert runtime_result == input_result


@pytest.mark.parametrize(
    'value',
    [
        None,
        False,
        True,
        0,
        '',
        'text',
        {},
        {'name': 'Ada'},
        [],
        [1, 2],
    ],
)
def test_runtime_inverted_sections_match_input_section_inverse_for_json_shapes(value: Any) -> None:
    template = Template()
    input_source = '{{#section}}{{else}}inverse{{/section}}'
    runtime_source = '{{^@section}}inverse{{/@section}}'

    input_result = template.render_template(input_source, {'section': value})
    runtime_result = template.render_template(runtime_source, {}, {'data': {'section': value}})

    assert runtime_result == input_result


def test_nested_runtime_direct_and_inverted_sections() -> None:
    template = Template()
    source = '{{#@outer~}}{{name}}:{{#@inner}}{{this}}{{else}}none{{/@inner}};{{~else~}}outer-empty{{~/@outer}}'
    inverse_source = '{{^@section}}inverse{{else}}present{{/@section}}'

    populated = template.render_template(
        source,
        {},
        {'data': {'outer': [{'name': 'a'}, {'name': 'b'}], 'inner': ['x', 'y']}},
    )
    empty = template.render_template(source, {}, {'data': {'outer': []}})
    inverse = template.render_template(inverse_source, {}, {'data': {'section': None}})
    inverse_else = template.render_template(inverse_source, {}, {'data': {'section': True}})

    assert populated == 'a:xy;b:xy;'
    assert empty == 'outer-empty'
    assert inverse == 'inverse'
    assert inverse_else == 'present'


def test_runtime_direct_sections_keep_closing_tags_matched() -> None:
    template = Template()

    with pytest.raises(ValueError, match='invalid handlebars syntax|mismatching helper'):
        template.render_template(
            '{{#@first}}content{{/@second}}',
            {},
            {'data': {'first': True, 'second': True}},
        )


def test_parent_local_spellings_match_across_nested_scopes() -> None:
    template = Template()
    source = (
        '{{#each groups}}'
        '{{#each values}}'
        '{{@../tenant}}={{../@tenant}}|'
        '{{@../../profile.name}}={{../../@profile.[display name]}}|'
        '{{@../index}}={{../@index}};'
        '{{/each}}'
        '{{/each}}'
    )

    result = template.render_template(
        source,
        {'groups': [{'values': ['a']}, {'values': ['b']}]},
        {
            'data': {
                'tenant': 'acme',
                'profile': {'name': 'Ada', 'display name': 'A'},
                'index': 'runtime-index',
            }
        },
    )

    assert result == 'acme=acme|Ada=A|0=0;acme=acme|Ada=A|1=1;'


def test_runtime_data_inherits_through_nested_array_and_object_scopes() -> None:
    template = Template()
    source = (
        '{{#each groups}}{{@index}}:'
        '{{#each this}}{{@key}}={{this}}/{{@tenant}}/{{@index}}/{{@first}}/{{@last}};'
        '{{/each}}{{/each}}'
    )

    result = template.render_template(
        source,
        {'groups': [{'a': 1, 'b': 2}]},
        {'data': {'tenant': 'acme', 'index': 'runtime-index', 'key': 'runtime-key'}},
    )

    assert result == '0:a=1/acme/0/true/false;b=2/acme/1/false/true;'


def test_builtin_local_metadata_shadows_same_named_runtime_data() -> None:
    template = Template()
    source = '{{#each values}}{{@index}}/{{@first}}/{{@last}}/{{@key}};{{/each}}'
    runtime_data = {'index': 99, 'first': 'runtime', 'last': 'runtime', 'key': 'runtime'}

    array_result = template.render_template(source, {'values': ['a']}, {'data': runtime_data})
    object_result = template.render_template(source, {'values': {'x': 'a'}}, {'data': runtime_data})

    assert array_result == '0/true/true/runtime;'
    assert object_result == '0/true/true/x;'


def test_root_always_reads_the_input_root() -> None:
    template = Template()

    result = template.render_template(
        '{{#with child}}{{@root.name}}/{{@name}}{{/with}}',
        {'name': 'input', 'child': {'present': True}},
        {'data': {'name': 'runtime'}},
    )

    assert result == 'input/runtime'


@pytest.mark.parametrize(
    'value',
    [None, False, 0, '', [], {}, {'name': 'runtime'}],
    ids=[
        'null',
        'false',
        'zero',
        'empty-string',
        'empty-array',
        'empty-object',
        'object',
    ],
)
def test_direct_render_rejects_falsy_and_populated_reserved_runtime_root(value: Any) -> None:
    template = Template()

    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        template.render_template('{{@root.name}}', {'name': 'input'}, {'data': {'root': value}})


def test_registered_render_rejects_reserved_runtime_root() -> None:
    template = Template()
    template.register_template('registered', '{{@root.name}}')
    options: RuntimeOptions = {'data': {'root': {'name': 'runtime'}}}

    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        template.render('registered', {'name': 'input'}, options)


def test_compiled_render_rejects_reserved_runtime_root() -> None:
    renderer = Template().compile('{{@root.name}}')
    options: RuntimeOptions = {'data': {'root': {'name': 'runtime'}}}

    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        renderer({'name': 'input'}, options)


def test_rejected_runtime_root_keeps_caller_data_and_renderer_reusable() -> None:
    template = Template()
    renderer = template.compile('{{@root.name}}/{{@name}}')
    input_data = {'name': 'input'}
    options: RuntimeOptions = {'data': {'root': None, 'name': 'rejected'}}

    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        renderer(input_data, options)

    assert input_data == {'name': 'input'}
    assert options == {'data': {'root': None, 'name': 'rejected'}}
    assert renderer(input_data, {'data': {'name': 'runtime'}}) == 'input/runtime'


def test_nested_root_key_remains_runtime_data() -> None:
    template = Template()

    result = template.render_template(
        '{{@profile.root}}/{{@root.name}}',
        {'name': 'input'},
        {'data': {'profile': {'root': 'nested'}}},
    )

    assert result == 'nested/input'


def test_registered_direct_and_compiled_renderers_match() -> None:
    template = Template()
    source = '{{name}}/{{@name}}/{{@nested.value}}'
    data = {'name': 'input'}
    options: RuntimeOptions = {'data': {'name': 'runtime', 'nested': {'value': 7}}}
    template.register_template('registered', source)

    direct = template.render_template(source, data, options)
    registered = template.render('registered', data, options)
    compiled = template.compile(source)(data, options)

    assert direct == registered == compiled == 'input/runtime/7'


def test_registered_nested_partials_inherit_runtime_data() -> None:
    template = Template()
    template.register_partial('inner', '{{@tenant}}/{{@profile.name}}')
    template.register_partial('outer', '{{#with user}}{{> inner}}{{/with}}')
    template.register_template('main', '{{#each users}}{{> outer}}{{/each}}')

    result = template.render(
        'main',
        {'users': [{'user': {'present': True}}, {'user': {'present': True}}]},
        {'data': {'tenant': 'acme', 'profile': {'name': 'Ada'}}},
    )

    assert result == 'acme/Adaacme/Ada'


def test_template_file_dev_reload_preserves_runtime_data(tmp_path: Path) -> None:
    source = tmp_path / 'prompt.hbs'
    source.write_text('{{@name}}', encoding='utf-8')
    template = Template(dev_mode=True)
    template.register_template_file('prompt', source)

    assert template.render('prompt', {}, {'data': {'name': 'first'}}) == 'first'
    source.write_text('[{{@name}}]', encoding='utf-8')
    assert template.render('prompt', {}, {'data': {'name': 'second'}}) == '[second]'


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (None, ''),
        (False, 'false'),
        (0, '0'),
        ('', ''),
        ([], '[]'),
        ({}, '[object]'),
    ],
)
def test_runtime_values_keep_their_json_types(value: Any, expected: str) -> None:
    template = Template()

    assert template.render_template('{{@value}}', {}, {'data': {'value': value}}) == expected


def test_missing_and_empty_runtime_context_keep_non_strict_behavior() -> None:
    template = Template()

    assert template.render_template('x{{@missing}}y', {}, None) == 'xy'
    assert template.render_template('x{{@missing}}y', {}, {}) == 'xy'
    assert template.render_template('x{{@missing}}y', {}, {'data': None}) == 'xy'


@pytest.mark.parametrize(
    'source',
    ['{{@missing}}', '{{{@missing}}}', '{{&@missing}}'],
    ids=['escaped', 'triple-stash', 'ampersand'],
)
def test_strict_mode_rejects_missing_runtime_interpolations(source: str) -> None:
    template = Template(strict_mode=True)

    with pytest.raises(ValueError, match='strict mode'):
        template.render_template(source, {}, {'data': {}})


@pytest.mark.parametrize(
    ('source', 'runtime_data'),
    [
        ('{{@profile.missing}}', {'profile': {}}),
        ('{{@missing.name}}', {}),
        ('{{@profile.[missing key]}}', {'profile': {}}),
    ],
    ids=['missing-leaf', 'missing-parent', 'missing-bracket-key'],
)
def test_strict_mode_rejects_missing_nested_runtime_paths(source: str, runtime_data: dict[str, Any]) -> None:
    template = Template(strict_mode=True)

    with pytest.raises(ValueError, match='strict mode'):
        template.render_template(source, {}, {'data': runtime_data})


@pytest.mark.parametrize(
    'source',
    [
        '{{#each items}}{{@../missing}}{{/each}}',
        '{{#each items}}{{../@missing}}{{/each}}',
    ],
    ids=['local-before-parent', 'parent-before-local'],
)
def test_strict_mode_rejects_missing_parent_runtime_paths(source: str) -> None:
    template = Template(strict_mode=True)

    with pytest.raises(ValueError, match='strict mode'):
        template.render_template(source, {'items': [1]}, {'data': {}})


def test_strict_mode_rejects_missing_runtime_path_in_subexpression() -> None:
    template = Template(strict_mode=True)

    with pytest.raises(ValueError, match='strict mode'):
        template.render_template('{{lookup @missing "key"}}', {}, {'data': {}})


def test_strict_mode_missing_helper_arguments_match_missing_input_arguments() -> None:
    template = Template(strict_mode=True)

    def inspect(params: list[Any], options: HelperOptions) -> str:
        return json.dumps([params, options.hash_value('named')], separators=(',', ':'))

    template.register_helper('inspect', inspect)

    input_result = template.render_template('{{inspect missing named=missing}}', {})
    runtime_result = template.render_template('{{inspect @missing named=@missing}}', {}, {'data': {}})

    assert runtime_result == input_result == '[[null],null]'


@pytest.mark.parametrize(
    ('input_source', 'runtime_source', 'expected'),
    [
        ('{{#if missing}}yes{{else}}no{{/if}}', '{{#if @missing}}yes{{else}}no{{/if}}', 'no'),
        ('{{#unless missing}}yes{{else}}no{{/unless}}', '{{#unless @missing}}yes{{else}}no{{/unless}}', 'yes'),
        ('{{#with missing}}yes{{else}}no{{/with}}', '{{#with @missing}}yes{{else}}no{{/with}}', 'no'),
        ('{{#each missing}}yes{{else}}no{{/each}}', '{{#each @missing}}yes{{else}}no{{/each}}', 'no'),
        ('{{#missing}}yes{{else}}no{{/missing}}', '{{#@missing}}yes{{else}}no{{/@missing}}', 'no'),
        ('{{#missing}}no{{else}}yes{{/missing}}', '{{^@missing}}yes{{else}}no{{/@missing}}', 'yes'),
    ],
    ids=['if', 'unless', 'with', 'each', 'direct-section', 'inverted-section'],
)
def test_strict_mode_missing_runtime_sections_match_missing_input_sections(
    input_source: str,
    runtime_source: str,
    expected: str,
) -> None:
    template = Template(strict_mode=True)

    input_result = template.render_template(input_source, {})
    runtime_result = template.render_template(runtime_source, {}, {'data': {}})

    assert runtime_result == input_result == expected


def test_strict_mode_rejects_missing_runtime_path_inside_partial() -> None:
    template = Template(strict_mode=True)
    template.register_partial('details', '{{@missing}}')

    with pytest.raises(ValueError, match='strict mode'):
        template.render_template('{{> details}}', {}, {'data': {}})


def test_strict_mode_rejects_missing_runtime_path_for_registered_and_compiled_renderers() -> None:
    template = Template(strict_mode=True)
    template.register_template('registered', '{{@missing}}')
    compiled = template.compile('{{@missing}}')

    with pytest.raises(ValueError, match='strict mode'):
        template.render('registered', {}, {'data': {}})
    with pytest.raises(ValueError, match='strict mode'):
        compiled({}, {'data': {}})


def test_strict_mode_renders_present_runtime_values_across_expression_forms() -> None:
    template = Template(strict_mode=True)
    template.register_partial('details', '{{@profile.name}}')
    source = '{{@name}}/{{lookup @profile "name"}}/{{#if @ready}}{{> details}}{{/if}}'
    runtime_data = {'name': 'Ada', 'profile': {'name': 'Grace'}, 'ready': True}

    assert template.render_template(source, {}, {'data': runtime_data}) == 'Ada/Grace/Grace'


def test_input_and_runtime_mappings_are_not_mutated_on_success() -> None:
    template = Template()
    data = {'name': 'input', 'nested': {'value': 1}}
    runtime_data = {'name': 'runtime', 'nested': {'value': 2}}
    original_data = json.loads(json.dumps(data))
    original_runtime_data = json.loads(json.dumps(runtime_data))

    template.render_template('{{name}}/{{@name}}/{{@nested.value}}', data, {'data': runtime_data})

    assert data == original_data
    assert runtime_data == original_runtime_data


def test_input_and_runtime_mappings_are_not_mutated_on_failure() -> None:
    template = Template()
    data = {'name': 'input'}
    runtime_data = {'name': 'runtime'}

    with pytest.raises(ValueError):
        template.render_template('{{#if @name}}', data, {'data': runtime_data})

    assert data == {'name': 'input'}
    assert runtime_data == {'name': 'runtime'}


def test_repeated_calls_do_not_leak_runtime_data() -> None:
    renderer = Template().compile('{{@request_id}}')

    assert renderer({}, {'data': {'request_id': 'first'}}) == 'first'
    assert renderer({}, {'data': {'request_id': 'second'}}) == 'second'
    assert renderer({}, None) == ''


def test_concurrent_calls_do_not_leak_runtime_data() -> None:
    renderer = Template().compile('{{@request.id}}')

    def render(value: int) -> str:
        return renderer({}, {'data': {'request': {'id': value}}})

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(render, range(40)))

    assert results == [str(value) for value in range(40)]


@pytest.mark.parametrize(
    ('data', 'options', 'message'),
    [
        ({'bad': object()}, None, 'template input must contain only JSON-serializable values'),
        ({}, {'data': {'bad': object()}}, 'runtime data must contain only JSON-serializable values'),
    ],
)
def test_non_json_values_raise_clear_serialization_errors(
    data: dict[str, Any],
    options: RuntimeOptions | None,
    message: str,
) -> None:
    template = Template()

    with pytest.raises(ValueError, match=message):
        template.render_template('{{bad}}{{@bad}}', data, options)


def test_whitespace_control_comments_and_raw_blocks_are_preserved() -> None:
    template = Template()
    source = 'A {{~@profile.name~}} B{{! @ignored }}{{{{raw}}}}{{@raw}}{{{{/raw}}}}'

    result = template.render_template(source, {}, {'data': {'profile': {'name': 'X'}, 'raw': 'changed'}})

    assert result == 'AXB{{@raw}}'
