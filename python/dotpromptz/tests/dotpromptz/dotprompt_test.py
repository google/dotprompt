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

import asyncio
import unittest
from collections.abc import Generator
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

import pytest

from dotpromptz.dotprompt import Dotprompt, _identify_partials
from dotpromptz.typing import ModelConfigT, ParsedPrompt, PromptMetadata, ToolDefinition
from handlebarrz import HelperFn, HelperOptions


@pytest.fixture
def mock_handlebars() -> Generator[Mock, None, None]:
    """Create a mock Handlebars instance."""
    with patch('dotpromptz.dotprompt.Handlebars') as mock_handlebars_class:
        mock_instance = Mock()
        mock_handlebars_class.return_value = mock_instance
        yield mock_instance


def test_init_default(mock_handlebars: Mock) -> None:
    """Test initializing Dotprompt with default options."""
    dotprompt = Dotprompt()

    assert dotprompt._handlebars == mock_handlebars
    assert dotprompt._known_helpers == {
        'history': True,
        'ifEquals': True,
        'json': True,
        'media': True,
        'role': True,
        'section': True,
        'unlessEquals': True,
    }
    assert dotprompt._default_model is None
    assert dotprompt._model_configs == {}
    assert dotprompt._tools == {}
    assert dotprompt._tool_resolver is None
    assert dotprompt._schemas == {}
    assert dotprompt._schema_resolver is None
    assert dotprompt._partial_resolver is None
    assert dotprompt._store is None


def test_init_with_options(mock_handlebars: Mock) -> None:
    """Test initializing Dotprompt with custom options."""

    def helper_fn(params: list[Any], options: HelperOptions) -> str:
        """Test helper."""
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
    def helper_fn(params: list[Any], options: HelperOptions) -> str:
        """Test helper."""
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
    tool_def = ToolDefinition(
        name='test_tool',
        description='A test tool',
        inputSchema={'type': 'object'},
    )

    result = dotprompt.define_tool(tool_def)

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

    tool_def = ToolDefinition(
        name='tool1',
        description='Tool 1',
        inputSchema={'type': 'object'},
    )

    def helper_fn(params: list[Any], options: HelperOptions) -> str:
        """Test helper."""
        return 'helper1'

    result = dotprompt.define_helper('helper1', helper_fn).define_partial('partial1', 'content').define_tool(tool_def)

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
    """Test that the identify_partials function works correctly."""
    assert _identify_partials(template) == expected


class TestMergeMetadata(IsolatedAsyncioTestCase):
    """Tests for the _merge_metadata function."""

    async def test_merge_config_base_only(self) -> None:
        """Test merging config when only base has it."""
        base = PromptMetadata[dict[str, Any]](config={'temp': 0.5})
        merge = PromptMetadata[dict[str, Any]]()
        dotprompt = Dotprompt()
        result = await dotprompt._resolve_metadata(base, merge)
        self.assertEqual(result.config, {'temp': 0.5})

    async def test_merge_config_merge_only(self) -> None:
        """Test merging config when only merge has it."""
        base = PromptMetadata[dict[str, Any]]()
        merge = PromptMetadata[dict[str, Any]](config={'temp': 0.7})
        dotprompt = Dotprompt()
        result = await dotprompt._resolve_metadata(base, merge)
        self.assertEqual(result.config, {'temp': 0.7})

    async def test_merge_config_no_overlap(self) -> None:
        """Test merging config with no overlapping keys."""
        base = PromptMetadata[dict[str, Any]](config={'temp': 0.5})
        merge = PromptMetadata[dict[str, Any]](config={'top_k': 10})
        dotprompt = Dotprompt()
        result = await dotprompt._resolve_metadata(base, merge)
        self.assertEqual(result.config, {'temp': 0.5, 'top_k': 10})

    async def test_merge_config_overlap(self) -> None:
        """Test merging config with overlapping keys (merge overrides)."""
        base = PromptMetadata[dict[str, Any]](config={'temp': 0.5, 'top_k': 5})
        merge = PromptMetadata[dict[str, Any]](config={'temp': 0.8, 'top_p': 0.9})
        dotprompt = Dotprompt()
        result = await dotprompt._resolve_metadata(base, merge)
        # merge overrides temp, adds top_p, keeps top_k from base
        self.assertEqual(result.config, {'temp': 0.8, 'top_k': 5, 'top_p': 0.9})

    async def test_merge_lists_replace(self) -> None:
        """Test that lists like tools are replaced, not appended."""
        base = PromptMetadata[dict[str, Any]](tools=['tool_a'])
        merge = PromptMetadata[dict[str, Any]](tools=['tool_b', 'tool_c'])
        dotprompt = Dotprompt()
        result = await dotprompt._resolve_metadata(base, merge)
        self.assertEqual(result.tools, ['tool_b', 'tool_c'])

    async def test_merge_removes_none_fields(self) -> None:
        """Test that None fields in merge override existing fields."""
        base = PromptMetadata[dict[str, Any]](model='model-a', description='desc')
        # Pydantic V2: exclude_none=True in model_dump means None fields
        # in the merge object won't be present in merge_dict, so they
        # won't overwrite existing values in base.
        # To explicitly overwrite with None, it needs to be included.
        merge = PromptMetadata[dict[str, Any]](model='model-b', description=None)
        dotprompt = Dotprompt()
        result = await dotprompt._resolve_metadata(base, merge)

        # model gets updated, description from base remains
        expected = PromptMetadata[dict[str, Any]](model='model-b', description='desc')
        self.assertEqual(result.model, expected.model)

        # Description should NOT be None because merge.model_dump excludes None
        self.assertEqual(result.description, expected.description)


class TestResolveTools(IsolatedAsyncioTestCase):
    """Test the resolve_tools method."""

    async def test_resolve_returns_correct_tool_when_registered(self) -> None:
        """Should resolve registered tools."""
        dotprompt = Dotprompt()

        tool_def = ToolDefinition.model_validate({
            'name': 'testTool',
            'description': 'A test tool',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'param1': {'type': 'string'},
                },
            },
        })

        dotprompt.define_tool(tool_def)
        metadata: PromptMetadata[dict[str, Any]] = PromptMetadata[dict[str, Any]].model_validate({
            'tools': ['testTool', 'unknownTool']
        })

        result = await dotprompt._resolve_tools(metadata)

        assert result.tool_defs is not None
        assert len(result.tool_defs) == 1
        assert result.tool_defs[0] == tool_def
        assert result.tools == ['unknownTool']

    async def test_resolve_raises_error_for_unregistered_tool(self) -> None:
        """Should raise an error for unregistered tools."""
        tool_def = ToolDefinition.model_validate({
            'name': 'resolvedTool',
            'description': 'A test tool',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'param1': {'type': 'string'},
                },
            },
        })

        resolve_metadata_mock = AsyncMock(return_value=tool_def)
        dotprompt = Dotprompt(tool_resolver=resolve_metadata_mock)
        metadata: PromptMetadata[dict[str, Any]] = PromptMetadata[dict[str, Any]](tools=['resolvedTool'])
        result = await dotprompt._resolve_tools(metadata)
        resolve_metadata_mock.assert_called_with('resolvedTool')
        assert result.tool_defs is not None
        assert len(result.tool_defs) == 1
        assert result.tool_defs[0] == tool_def
        assert result.tools == []


class TestRenderPicoSchema(IsolatedAsyncioTestCase):
    """Test the render_picoschema method."""

    @patch(
        'dotpromptz.dotprompt.picoschema_to_json_schema',
        return_value={'type': 'object', 'properties': {'expanded': True}},
    )
    async def test_process_valid_picoschema_definition(self, _: Mock) -> None:
        """Should process picoschema definitions."""
        dotprompt = Dotprompt()

        metadata: PromptMetadata[dict[str, Any]] = PromptMetadata[dict[str, Any]].model_validate({
            'input': {
                'schema': {'type': 'string'},
            },
            'output': {
                'schema': {'type': 'number'},
            },
        })
        values_assert = {'type': 'object', 'properties': {'expanded': True}}
        # Now call the function that uses picoschema.picoschema internally
        result: PromptMetadata[dict[str, Any]] = await dotprompt._render_picoschema(metadata)
        assert result.input is not None
        assert result.input.schema_ == values_assert
        assert result.output is not None
        assert result.output.schema_ == values_assert

    async def test_returns_original_metadata_when_no_schemas_present(self) -> None:
        """Test that the original metadata is returned unchanged when no schemas are present."""
        dotprompt = Dotprompt()

        metadata: PromptMetadata[dict[str, Any]] = PromptMetadata[dict[str, Any]].model_validate({
            'input': {
                'schema': {'type': 'string'},
            },
            'output': {
                'schema': {'type': 'number'},
            },
            'model': 'gemini-1.5-pro',
        })
        result: PromptMetadata[dict[str, Any]] = await dotprompt._render_picoschema(metadata)
        assert result == metadata


class TestWrappedSchemaResolver(IsolatedAsyncioTestCase):
    """Test the wrapped schema resolver."""

    async def test_resolves_schemas_from_registered_schemas(self) -> None:
        """Should resolve schemas from the registered schemas."""
        schemas: dict[str, dict[str, str | dict[str, dict[str, str]]]] = {
            'test-schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                },
            },
        }

        dotprompt = Dotprompt(schemas=schemas)

        result = await dotprompt._wrapped_schema_resolver('test-schema')

        self.assertEqual(result, schemas['test-schema'])

    async def test_uses_schema_resolver_for_unregistered_schemas(self) -> None:
        """Should use the schema resolver for unregistered schemas."""
        schema_resolver_mock = AsyncMock(
            return_value={'type': 'object', 'properties': {'resolved': {'type': 'boolean'}}}
        )

        dotprompt = Dotprompt(schema_resolver=schema_resolver_mock)

        result = await dotprompt._wrapped_schema_resolver('external-schema')
        schema_resolver_mock.assert_called_with('external-schema')

        self.assertEqual(result, {'type': 'object', 'properties': {'resolved': {'type': 'boolean'}}})

    async def test_returns_none_if_schema_not_found_and_no_resolver(self) -> None:
        """Should return None if schema not found and no resolver."""
        dotprompt = Dotprompt()

        result = await dotprompt._wrapped_schema_resolver('non-existent-schema')
        self.assertIsNone(result)


class TestResolveMetaData(IsolatedAsyncioTestCase):
    """Test the resolve_metadata method."""

    async def test_merge_multiple_metadata(self) -> None:
        """Should merge multiple metadata objects."""
        dotprompt = Dotprompt()

        base: PromptMetadata[dict[str, Any]] = PromptMetadata.model_validate({
            'model': 'gemini-1.5-pro',
            'config': {
                'temperature': 0.7,
            },
        })

        merge1: PromptMetadata[dict[str, Any]] = PromptMetadata.model_validate({
            'config': {
                'top_p': 0.9,
            },
            'tools': ['tool1'],
        })

        merge2: PromptMetadata[dict[str, Any]] = PromptMetadata.model_validate({
            'model': 'gemini-2.0-flash',
            'config': {
                'max_tokens': 2000,
            },
        })
        render_pico_mock = AsyncMock(side_effect=lambda arg: arg)
        resolve_tools_mock = AsyncMock(side_effect=lambda arg: arg)
        with (
            patch.object(dotprompt, '_resolve_tools', resolve_tools_mock),
            patch.object(dotprompt, '_render_picoschema', render_pico_mock),
        ):
            result = await dotprompt._resolve_metadata(base, merge1, merge2)
            self.assertEqual(result.model, 'gemini-2.0-flash')
            self.assertEqual(
                result.config,
                {
                    'top_p': 0.9,
                    'max_tokens': 2000,
                    'temperature': 0.7,
                },
            )

            self.assertEqual(result.tools, ['tool1'])
            render_pico_mock.assert_called()
            resolve_tools_mock.assert_called()

    async def test_handle_undefined_merges(self) -> None:
        """Should handle undefined merges."""
        dotprompt = Dotprompt()

        base: PromptMetadata[dict[str, Any]] = PromptMetadata[dict[str, Any]].model_validate({
            'model': 'gemini-1.5-pro',
            'config': {
                'temperature': 0.7,
            },
        })

        render_pico_mock = AsyncMock(side_effect=lambda arg: arg)
        resolve_tools_mock = AsyncMock(side_effect=lambda arg: arg)

        with (
            patch.object(dotprompt, '_resolve_tools', resolve_tools_mock),
            patch.object(dotprompt, '_render_picoschema', render_pico_mock),
        ):
            result = await dotprompt._resolve_metadata(base)

            self.assertEqual(result.model, 'gemini-1.5-pro')
            self.assertEqual(
                result.config,
                {
                    'temperature': 0.7,
                },
            )


def test_render_metadata() -> None:
    """Test the render_metadata method."""
    dotprompt = Dotprompt()

    parsed_source: ParsedPrompt[dict[str, Any]] = ParsedPrompt[dict[str, Any]](
        template='Template content', model='gemini-1.5-pro'
    )
    resolve_metadata_mock = AsyncMock(
        return_value=PromptMetadata(
            model='gemini-1.5-pro',
        )
    )

    with patch.object(dotprompt, '_resolve_metadata', resolve_metadata_mock):
        result = asyncio.run(dotprompt.render_metadata(parsed_source))

        resolve_metadata_mock.assert_called_with(
            PromptMetadata(),
            ParsedPrompt(
                model='gemini-1.5-pro',
                template='Template content',
            ),
            None,
        )
        assert result == PromptMetadata(model='gemini-1.5-pro')


def test_default_model_when_null() -> None:
    """Should use the default model when no model is specified."""
    dotprompt = Dotprompt()

    parsed_source: ParsedPrompt[dict[str, Any]] = ParsedPrompt[dict[str, Any]](
        template='Template content',
    )
    resolve_metadata_mock = AsyncMock(
        return_value=PromptMetadata(
            model='default-model',
        )
    )

    with patch.object(dotprompt, '_resolve_metadata', resolve_metadata_mock):
        result = asyncio.run(dotprompt.render_metadata(parsed_source))
        resolve_metadata_mock.assert_called()

    assert result == PromptMetadata(
        model='default-model',
    )


def test_use_available_model_config() -> None:
    """Should use model configs when available."""
    model_configs = {
        'gemini-1.5-pro': {'temperature': 0.7},
    }
    dotprompt = Dotprompt(model_configs=model_configs)

    parsed_source: ParsedPrompt[dict[str, Any]] = ParsedPrompt[dict[str, Any]](
        template='Template content',
        model='gemini-1.5-pro',
    )

    def wrapper(
        base: PromptMetadata[ModelConfigT], *merges: PromptMetadata[ModelConfigT]
    ) -> PromptMetadata[ModelConfigT]:
        return PromptMetadata.model_validate({**merges[0].model_dump(), 'config': base.config})

    resolve_metadata_mock = AsyncMock(side_effect=wrapper)

    with patch.object(dotprompt, '_resolve_metadata', resolve_metadata_mock):
        result = asyncio.run(dotprompt.render_metadata(parsed_source))
        resolve_metadata_mock.assert_called_with(PromptMetadata(config={'temperature': 0.7}), parsed_source, None)

        assert result.config == {'temperature': 0.7}


if __name__ == '__main__':
    unittest.main()
