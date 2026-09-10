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

from typing import Any, cast

import pytest

from dotpromptz.dotprompt import Dotprompt
from dotpromptz.typing import DataArgument, PromptInputConfig, PromptMetadata, TextPart


def rendered_text(result: Any) -> str:
    part = result.messages[0].content[0]
    assert isinstance(part, TextPart)
    return part.text


@pytest.mark.asyncio
async def test_prompt_file_defaults_do_not_fill_variables_when_runtime_input_is_absent() -> None:
    source = """---
input:
  default:
    first: Ada
    last: Lovelace
---
{{first}} {{last}}"""

    result = await Dotprompt().render(source, DataArgument())

    assert result.messages == []


@pytest.mark.asyncio
async def test_empty_runtime_input_does_not_fill_prompt_file_defaults() -> None:
    source = """---
input:
  default:
    first: Ada
    last: Lovelace
---
{{first}} {{last}}"""

    result = await Dotprompt().render(source, DataArgument(input={}))

    assert result.messages == []


@pytest.mark.asyncio
async def test_partial_runtime_input_does_not_keep_prompt_file_default_siblings() -> None:
    source = """---
input:
  default:
    first: Ada
    last: Lovelace
---
{{first}} {{last}}"""

    result = await Dotprompt().render(source, DataArgument(input={'first': 'Grace'}))

    assert rendered_text(result) == 'Grace '


@pytest.mark.asyncio
async def test_call_defaults_fill_variables_and_prompt_file_defaults_do_not() -> None:
    source = """---
input:
  default:
    name: Ada
    city: Paris
---
{{name}} lives in {{city}}"""

    result = await Dotprompt().render(
        source,
        DataArgument(),
        PromptMetadata(input=PromptInputConfig(default={'city': 'Paris'})),
    )

    assert rendered_text(result) == ' lives in Paris'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (None, ''),
        (False, 'false'),
        (0, '0'),
        ('', ''),
    ],
    ids=['null', 'false', 'zero', 'empty-string'],
)
async def test_falsy_runtime_input_values_override_prompt_defaults(value: Any, expected: str) -> None:
    source = """---
input:
  default:
    value: default
---
[{{value}}]"""

    result = await Dotprompt().render(source, DataArgument(input={'value': value}))

    assert rendered_text(result) == f'[{expected}]'


@pytest.mark.asyncio
async def test_runtime_nested_object_replaces_default_object_without_deep_merge() -> None:
    source = """---
input:
  default:
    profile:
      name: Ada
      role: mathematician
    tenant: analytical-engine
---
{{profile.name}}|{{profile.role}}|{{tenant}}"""

    result = await Dotprompt().render(
        source,
        DataArgument(input={'profile': {'name': 'Grace'}}),
    )

    assert rendered_text(result) == 'Grace||'


@pytest.mark.asyncio
async def test_prompt_and_call_defaults_overlay_before_runtime_input() -> None:
    source = """---
input:
  default:
    name: prompt
    promptOnly: prompt
  schema:
    type: object
---
{{name}}/{{promptOnly}}/{{callOnly}}"""
    options = PromptMetadata(
        input=PromptInputConfig(default={'name': 'call', 'callOnly': 'call'}),
    )

    result = await Dotprompt().render(
        source,
        DataArgument(input={'name': 'runtime'}),
        options,
    )

    assert rendered_text(result) == 'runtime//call'
    assert result.input == PromptInputConfig(
        default={
            'name': 'call',
            'promptOnly': 'prompt',
            'callOnly': 'call',
        },
        schema={'type': 'object'},
    )


@pytest.mark.asyncio
async def test_call_schema_replaces_prompt_schema_without_inventing_defaults() -> None:
    source = """---
input:
  schema:
    type: object
---
Hello"""

    result = await Dotprompt().render(
        source,
        DataArgument(),
        PromptMetadata(
            input=PromptInputConfig(schema={'type': 'string'}),
        ),
    )

    assert result.input == PromptInputConfig(
        default=None,
        schema={'type': 'string'},
    )


@pytest.mark.asyncio
async def test_compile_schema_replaces_prompt_schema_while_defaults_still_overlay() -> None:
    source = """---
input:
  default:
    promptOnly: prompt
  schema:
    type: object
---
{{promptOnly}}/{{callOnly}}"""
    renderer = await Dotprompt().compile(
        source,
        PromptMetadata(
            input=PromptInputConfig(schema={'type': 'string'}),
        ),
    )

    result = await renderer(
        DataArgument(),
        PromptMetadata(
            input=PromptInputConfig(default={'callOnly': 'call'}),
        ),
    )

    assert rendered_text(result) == '/call'
    assert result.input == PromptInputConfig(
        default={'promptOnly': 'prompt', 'callOnly': 'call'},
        schema={'type': 'string'},
    )


@pytest.mark.asyncio
async def test_compile_and_call_defaults_overlay_in_order_before_runtime_input() -> None:
    source = """---
input:
  default:
    promptOnly: prompt
    shared: prompt
  schema:
    type: object
---
{{promptOnly}}/{{compileOnly}}/{{callOnly}}/{{runtimeOnly}}/{{shared}}"""
    compile_defaults = {'compileOnly': 'compile', 'shared': 'compile'}
    call_defaults = {'callOnly': 'call', 'shared': 'call'}
    runtime_input = {'runtimeOnly': 'runtime', 'shared': 'runtime'}
    compile_metadata = PromptMetadata(
        input=PromptInputConfig(default=compile_defaults),
    )
    call_metadata = PromptMetadata(
        input=PromptInputConfig(default=call_defaults),
    )
    renderer = await Dotprompt().compile(
        source,
        compile_metadata,
    )

    overridden = await renderer(
        DataArgument(input=runtime_input),
        call_metadata,
    )
    compiled_baseline = await renderer(DataArgument())

    assert rendered_text(overridden) == '//call/runtime/runtime'
    assert rendered_text(compiled_baseline) == '////'
    assert overridden.input is not None
    assert overridden.input.schema == {'type': 'object'}
    assert compile_defaults == {'compileOnly': 'compile', 'shared': 'compile'}
    assert call_defaults == {'callOnly': 'call', 'shared': 'call'}
    assert runtime_input == {'runtimeOnly': 'runtime', 'shared': 'runtime'}
    assert compile_metadata.input == PromptInputConfig(default=compile_defaults)
    assert call_metadata.input == PromptInputConfig(default=call_defaults)


@pytest.mark.asyncio
async def test_reused_compiled_renderer_does_not_leak_prior_runtime_input() -> None:
    source = """---
input:
  default:
    name: default
---
{{name}}"""
    renderer = await Dotprompt().compile(source)

    first = await renderer(DataArgument(input={'name': 'first'}))
    second = await renderer(DataArgument())
    third = await renderer(DataArgument(input={'name': 'third'}))

    assert rendered_text(first) == 'first'
    assert second.messages == []
    assert rendered_text(third) == 'third'


@pytest.mark.asyncio
async def test_instance_default_model_and_config_apply_when_prompt_omits_model() -> None:
    dotprompt = Dotprompt(
        default_model='gemini-default',
        model_configs={'gemini-default': {'temperature': 0.2}},
    )

    result = await dotprompt.render('Hello', DataArgument())

    assert result.model == 'gemini-default'
    assert result.config == {'temperature': 0.2}


@pytest.mark.asyncio
async def test_instance_default_model_survives_without_registered_config() -> None:
    result = await Dotprompt(default_model='gemini-default').render(
        'Hello',
        DataArgument(),
    )

    assert result.model == 'gemini-default'


@pytest.mark.asyncio
async def test_empty_instance_default_model_is_treated_as_absent() -> None:
    result = await Dotprompt(
        default_model='',
        model_configs={'': {'invalid': True}},
    ).render('Hello', DataArgument())

    assert result.model is None
    assert result.config != {'invalid': True}


@pytest.mark.asyncio
async def test_prompt_model_wins_instance_default_and_selects_its_config() -> None:
    source = """---
model: gemini-prompt
---
Hello"""
    dotprompt = Dotprompt(
        default_model='gemini-default',
        model_configs={
            'gemini-default': {'temperature': 0.2},
            'gemini-prompt': {'temperature': 0.4},
        },
    )

    result = await dotprompt.render(source, DataArgument())

    assert result.model == 'gemini-prompt'
    assert result.config == {'temperature': 0.4}


@pytest.mark.asyncio
async def test_call_model_override_wins_prompt_model_and_selects_its_config() -> None:
    source = """---
model: gemini-prompt
---
Hello"""
    dotprompt = Dotprompt(
        model_configs={
            'gemini-prompt': {'temperature': 0.4},
            'gemini-call': {'temperature': 0.8},
        },
    )

    result = await dotprompt.render(
        source,
        DataArgument(),
        PromptMetadata(model='gemini-call'),
    )

    assert result.model == 'gemini-call'
    assert result.config == {'temperature': 0.8}


@pytest.mark.asyncio
async def test_compile_model_override_wins_prompt_model_and_selects_its_config() -> None:
    source = """---
model: gemini-prompt
---
Hello"""
    dotprompt = Dotprompt(
        model_configs={
            'gemini-prompt': {'temperature': 0.4},
            'gemini-compile': {'temperature': 0.6},
        },
    )
    renderer = await dotprompt.compile(
        source,
        PromptMetadata(model='gemini-compile'),
    )

    result = await renderer(DataArgument())

    assert result.model == 'gemini-compile'
    assert result.config == {'temperature': 0.6}


@pytest.mark.asyncio
async def test_empty_prompt_model_uses_instance_default_and_matching_config() -> None:
    source = """---
model: ""
---
Hello"""
    dotprompt = Dotprompt(
        default_model='gemini-default',
        model_configs={'gemini-default': {'temperature': 0.2}},
    )

    result = await dotprompt.render(source, DataArgument())

    assert result.model == 'gemini-default'
    assert result.config == {'temperature': 0.2}


@pytest.mark.asyncio
async def test_empty_call_model_keeps_prompt_model_and_matching_config() -> None:
    source = """---
model: gemini-prompt
---
Hello"""
    dotprompt = Dotprompt(
        model_configs={'gemini-prompt': {'temperature': 0.4}},
    )

    result = await dotprompt.render(
        source,
        DataArgument(),
        PromptMetadata(model=''),
    )

    assert result.model == 'gemini-prompt'
    assert result.config == {'temperature': 0.4}


@pytest.mark.asyncio
async def test_empty_compile_model_keeps_prompt_model_and_matching_config() -> None:
    source = """---
model: gemini-prompt
---
Hello"""
    dotprompt = Dotprompt(
        model_configs={'gemini-prompt': {'temperature': 0.4}},
    )
    renderer = await dotprompt.compile(
        source,
        PromptMetadata(model=''),
    )

    result = await renderer(DataArgument())

    assert result.model == 'gemini-prompt'
    assert result.config == {'temperature': 0.4}


@pytest.mark.asyncio
async def test_selected_model_config_prompt_config_and_call_config_merge_in_order() -> None:
    source = """---
model: gemini-prompt
config:
  temperature: 0.4
  topK: 10
---
Hello"""
    dotprompt = Dotprompt(
        model_configs={
            'gemini-prompt': {
                'temperature': 0.2,
                'topK': 5,
                'topP': 0.5,
            }
        },
    )

    result = await dotprompt.render(
        source,
        DataArgument(),
        PromptMetadata(config={'topK': 20}),
    )

    assert result.model == 'gemini-prompt'
    assert result.config == {
        'temperature': 0.4,
        'topK': 20,
        'topP': 0.5,
    }


@pytest.mark.asyncio
async def test_compile_and_call_model_metadata_merge_in_order() -> None:
    source = """---
model: gemini-prompt
config:
  promptOnly: prompt
  shared: prompt
---
Hello"""
    dotprompt = Dotprompt(
        default_model='gemini-default',
        model_configs={
            'gemini-default': {'selected': 'default-model'},
            'gemini-prompt': {'selected': 'prompt-model'},
            'gemini-compile': {'selected': 'compile-model'},
            'gemini-call': {
                'selected': 'call-model',
                'shared': 'model',
            },
        },
    )
    renderer = await dotprompt.compile(
        source,
        PromptMetadata(
            model='gemini-compile',
            config={'compileOnly': 'compile', 'shared': 'compile'},
        ),
    )

    result = await renderer(
        DataArgument(),
        PromptMetadata(
            model='gemini-call',
            config={'callOnly': 'call', 'shared': 'call'},
        ),
    )

    assert result.model == 'gemini-call'
    assert result.config == {
        'selected': 'call-model',
        'promptOnly': 'prompt',
        'compileOnly': 'compile',
        'callOnly': 'call',
        'shared': 'call',
    }


@pytest.mark.asyncio
async def test_render_rejects_plain_dictionary_instead_of_treating_it_as_data_argument() -> None:
    with pytest.raises(TypeError, match='data must be a DataArgument'):
        await Dotprompt().render(
            '{{name}}',
            cast(Any, {'input': {'name': 'Ada'}}),
        )
