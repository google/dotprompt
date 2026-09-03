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

from typing import Any

import pytest

from dotpromptz.dotprompt import Dotprompt
from dotpromptz.typing import DataArgument, TextPart
from handlebarrz import HelperOptions


@pytest.mark.asyncio
async def test_context_is_separate_from_same_named_prompt_default() -> None:
    source = """---
input:
  default:
    name: default
---
{{name}}/{{@name}}"""

    result = await Dotprompt().render(
        source,
        DataArgument(input={}, context={'name': 'runtime'}),
    )

    assert result.messages[0].content == [TextPart(text='default/runtime')]


@pytest.mark.asyncio
async def test_input_override_and_context_collision_remain_separate() -> None:
    source = """---
input:
  default:
    name: default
---
{{name}}/{{@name}}"""

    result = await Dotprompt().render(
        source,
        DataArgument(input={'name': 'input'}, context={'name': 'runtime'}),
    )

    assert result.messages[0].content == [TextPart(text='input/runtime')]


@pytest.mark.asyncio
async def test_context_flows_through_dotprompt_partials_and_helpers() -> None:
    observed: list[Any] = []

    def inspect(params: list[Any], _: HelperOptions) -> str:
        observed.extend(params)
        return f'{params[0]}:{params[1]["name"]}'

    dotprompt = Dotprompt(
        helpers={'inspect': inspect},
        partials={'details': '{{inspect @count @profile}}'},
    )

    result = await dotprompt.render(
        '{{#with user}}{{> details}}{{/with}}',
        DataArgument(
            input={'user': {'present': True}},
            context={'count': 3, 'profile': {'name': 'Ada'}},
        ),
    )

    assert observed == [3, {'name': 'Ada'}]
    assert result.messages[0].content == [TextPart(text='3:Ada')]


@pytest.mark.asyncio
async def test_dotprompt_does_not_mutate_data_argument_mappings() -> None:
    input_data = {'name': 'input', 'nested': {'value': 1}}
    context = {'name': 'runtime', 'nested': {'value': 2}}
    data = DataArgument(input=input_data, context=context)

    await Dotprompt().render('{{name}}/{{@name}}/{{@nested.value}}', data)

    assert input_data == {'name': 'input', 'nested': {'value': 1}}
    assert context == {'name': 'runtime', 'nested': {'value': 2}}


@pytest.mark.asyncio
async def test_dotprompt_render_rejects_context_root_without_mutating_data_argument() -> None:
    input_data = {'name': 'input'}
    context = {'root': {'name': 'runtime'}, 'request_id': 'r1'}
    data = DataArgument(input=input_data, context=context)

    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        await Dotprompt().render('{{@root.name}}', data)

    assert input_data == {'name': 'input'}
    assert context == {'root': {'name': 'runtime'}, 'request_id': 'r1'}


@pytest.mark.asyncio
async def test_compiled_dotprompt_rejects_context_root_and_remains_reusable() -> None:
    renderer = await Dotprompt().compile('{{@root.name}}/{{@request_id}}')

    with pytest.raises(ValueError, match="runtime data key 'root' is reserved"):
        await renderer(
            DataArgument(
                input={'name': 'input'},
                context={'root': None, 'request_id': 'rejected'},
            )
        )

    result = await renderer(
        DataArgument(
            input={'name': 'input'},
            context={'request_id': 'r1'},
        )
    )

    assert result.messages[0].content == [TextPart(text='input/r1')]
