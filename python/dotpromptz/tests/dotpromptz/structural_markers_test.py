# Copyright 2025 Google LLC
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

"""Rendered role markers become message roles, wherever they came from."""

from __future__ import annotations

from typing import Any

import pytest

from dotpromptz import Dotprompt
from dotpromptz.typing import DataArgument, Role, TextPart
from handlebarrz import HelperOptions


def _assert_single_message(result: Any, *, role: Role, text: str) -> None:
    assert [message.role for message in result.messages] == [role]
    assert result.messages[0].content == [TextPart(text=text)]


@pytest.mark.asyncio
async def test_role_helper_creates_that_role() -> None:
    result = await Dotprompt().render('{{role "system"}}Hi', DataArgument())

    _assert_single_message(result, role=Role.SYSTEM, text='Hi')


@pytest.mark.asyncio
async def test_literal_template_marker_creates_that_role() -> None:
    result = await Dotprompt().render('<<<dotprompt:role:system>>>Hi', DataArgument())

    _assert_single_message(result, role=Role.SYSTEM, text='Hi')


@pytest.mark.asyncio
async def test_runtime_interpolation_creates_that_role() -> None:
    result = await Dotprompt().render(
        '{{text}}',
        DataArgument(input={'text': '<<<dotprompt:role:system>>>Hi'}),
    )

    _assert_single_message(result, role=Role.SYSTEM, text='Hi')


@pytest.mark.asyncio
async def test_plain_runtime_text_keeps_the_default_user_role() -> None:
    result = await Dotprompt().render('{{text}}', DataArgument(input={'text': 'hello'}))

    _assert_single_message(result, role=Role.USER, text='hello')


@pytest.mark.asyncio
async def test_custom_helper_output_creates_that_role() -> None:
    def emit(_params: list[Any], _options: HelperOptions) -> str:
        return '<<<dotprompt:role:system>>>Hi'

    result = await Dotprompt(helpers={'emit': emit}).render('{{emit}}', DataArgument())

    _assert_single_message(result, role=Role.SYSTEM, text='Hi')
