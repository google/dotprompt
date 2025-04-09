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

"""Unit tests for the Dotprompt class.

Dotprompt extends Handlebars templates for use with Gen AI prompts.

The tests cover:

1. Initialization with default and custom options.
2. Registration of helpers and partials.
3. Definition of helpers, partials, tools, and schemas.
4. Prompt parsing functionality.
5. Method chaining interface.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any, cast
from unittest.mock import Mock, patch

import pytest

from dotpromptz.dotprompt import Dotprompt, Options
from dotpromptz.typing import ParsedPrompt, ToolDefinition
from handlebarrz import HelperFn


@pytest.fixture
def mock_handlebars() -> Generator[Mock, None, None]:
    """Create a mock Handlebars instance."""
    with patch('dotpromptz.dotprompt.Handlebars') as mock_handlebars_class:
        mock_instance = Mock()
        mock_handlebars_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_register_all_helpers() -> Generator[Mock, None, None]:
    """Create a mock for the register_all_helpers function."""
    with patch('dotpromptz.dotprompt.register_all_helpers') as mock:
        yield mock


def test_init_default(mock_handlebars: Mock, mock_register_all_helpers: Mock) -> None:
    """Test initializing Dotprompt with default options."""
    dotprompt = Dotprompt()

    assert dotprompt._handlebars == mock_handlebars

    mock_register_all_helpers.assert_called_once_with(mock_handlebars)

    assert dotprompt._known_helpers == {}
    assert dotprompt._default_model is None
    assert dotprompt._model_configs == {}
    assert dotprompt._tools == {}
    assert dotprompt._tool_resolver is None
    assert dotprompt._schemas == {}
    assert dotprompt._schema_resolver is None
    assert dotprompt._partial_resolver is None
    assert dotprompt._store is None


def test_init_with_options(mock_handlebars: Mock, mock_register_all_helpers: Mock) -> None:
    """Test initializing Dotprompt with custom options."""

    def helper_fn(params: list[Any], hash_args: dict[str, Any], ctx: dict[str, Any]) -> str:
        return 'test_helper'

    helpers: dict[str, HelperFn] = {'helper1': helper_fn}
    partials: dict[str, str] = {'partial1': 'partial template'}

    _ = Dotprompt(
        helpers=helpers,
        partials=partials,
    )

    mock_handlebars.register_helper.assert_called_with('helper1', helpers['helper1'])
    mock_handlebars.register_partial.assert_called_with('partial1', partials['partial1'])


def test_define_helper(mock_handlebars: Mock) -> None:
    """Test defining a helper function."""

    # This should match the signature of HelperFn.
    def helper_fn(params: list[Any], hash_args: dict[str, Any], ctx: dict[str, Any]) -> str:
        return 'test_helper'

    dotprompt = Dotprompt()
    mock_handlebars.register_helper.reset_mock()
    result = dotprompt.define_helper('test_helper', helper_fn)

    mock_handlebars.register_helper.assert_called_once_with('test_helper', helper_fn)
    assert dotprompt._known_helpers.get('test_helper') is True

    # Ensure chaining works.
    assert result == dotprompt


def test_define_partial(mock_handlebars: Mock) -> None:
    """Test defining a partial template."""
    dotprompt = Dotprompt()
    mock_handlebars.register_partial.reset_mock()

    result = dotprompt.define_partial('test_partial', 'partial content')

    mock_handlebars.register_partial.assert_called_once_with('test_partial', 'partial content')

    # Ensure chaining works.
    assert result == dotprompt


def test_define_tool(mock_handlebars: Mock) -> None:
    """Test defining a tool."""
    dotprompt = Dotprompt()
    tool_def = cast(
        ToolDefinition,
        {
            'name': 'test_tool',
            'description': 'A test tool',
            'input_schema': {'type': 'object'},
        },
    )

    result = dotprompt.define_tool('test_tool', tool_def)

    assert dotprompt._tools['test_tool'] == tool_def

    # Ensure chaining works.
    assert result == dotprompt


@patch('dotpromptz.dotprompt.parse_document')
def test_parse(mock_parse_document: Mock, mock_handlebars: Mock) -> None:
    """Test parsing a prompt."""
    mock_parse_document.return_value = ParsedPrompt(template='Hello {{name}}', toolDefs=None)

    dotprompt = Dotprompt()
    result: ParsedPrompt[dict[str, Any]] = dotprompt.parse('source string')

    mock_parse_document.assert_called_once_with('source string')

    # Ensure chaining works.
    assert result == ParsedPrompt(template='Hello {{name}}', toolDefs=None)


def test_chainable_interface(mock_handlebars: Mock) -> None:
    """Test that the methods can be chained."""
    dotprompt = Dotprompt()
    mock_handlebars.register_helper.reset_mock()
    mock_handlebars.register_partial.reset_mock()

    tool_def = cast(
        ToolDefinition,
        {
            'name': 'tool1',
            'description': 'Tool 1',
            'input_schema': {'type': 'object'},
        },
    )

    def helper_fn(params: list[Any], hash_args: dict[str, Any], ctx: dict[str, Any]) -> str:
        return 'helper1'

    result = (
        dotprompt.define_helper('helper1', helper_fn)
        .define_partial('partial1', 'content')
        .define_tool('tool1', tool_def)
    )

    mock_handlebars.register_helper.assert_called_once()
    mock_handlebars.register_partial.assert_called_once()
    assert dotprompt._tools['tool1'] == tool_def

    # Ensure chaining works.
    assert result == dotprompt


@pytest.mark.parametrize(
    'template,expected',
    [
        # No partials.
        ('Hello {{name}}', set()),
        # One partial.
        ('Hello {{> header}}', {'header'}),
        # Multiple partials.
        (
            'Hello {{> header}} {{> footer}} {{> sidebar}}',
            {'header', 'footer', 'sidebar'},
        ),
        # Partial with dash and underscore.
        ('Hello {{> header-component_name}}', {'header-component_name'}),
    ],
)
def test_identify_partials(template: str, expected: set[str]) -> None:
    """Test the identify_partials method with various templates."""
    dotprompt = Dotprompt()
    partials = dotprompt.identify_partials(template)
    assert partials == expected
