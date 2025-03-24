# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Dotpromptz is a library for generating prompts using Handlebars templates."""

from __future__ import annotations

from typing import Any, TypedDict

from dotpromptz.helpers import register_all_helpers
from dotpromptz.parse import parse_document
from dotpromptz.typing import (
    DataArgument,
    JsonSchema,
    ModelConfig,
    ParsedPrompt,
    PartialResolver,
    PromptMetadata,
    PromptStore,
    SchemaResolver,
    ToolDefinition,
    ToolResolver,
)
from handlebarrz import Handlebars, HelperFn


class Options(TypedDict, total=False):
    """Options for dotprompt."""

    # The default model to use for the prompt when not specified in the
    # template.
    default_model: str | None
    # Assign a set of default configuration options to be used with a particular
    # model.
    model_configs: dict[str, Any] | None
    # Helpers to pre-register.
    helpers: dict[str, HelperFn] | None
    # Partials to pre-register.
    partials: dict[str, str] | None
    # Provide a static mapping of tool definitions that should be used when
    # resolving tool names.
    tools: dict[str, ToolDefinition] | None
    # Provide a lookup implementation to resolve tool names to definitions.
    tool_resolver: ToolResolver | None
    # Provide a static mapping of schema names to their JSON schema definitions.
    schemas: dict[str, JsonSchema] | None
    # Provide a lookup implementation to resolve schema names to JSON schema
    # definitions.
    schema_resolver: SchemaResolver | None
    # Provide a lookup implementation to resolve partial names to their content.
    partial_resolver: PartialResolver | None


class Dotprompt:
    """Dotprompt extends a Handlebars template for use with Gen AI prompts."""

    def __init__(self, options: Options | None = None) -> None:
        """Initialize Dotprompt with a Handlebars template.

        Args:
            options: Options for Dotprompt.
        """
        self._options: Options = options or {}
        self._handlebars: Handlebars = Handlebars()
        self._known_helpers: dict[str, bool] = {}
        self._default_model: str | None = None
        self._model_configs: dict[str, Any] = {}
        self._tools: dict[str, ToolDefinition] = {}
        self._tool_resolver: ToolResolver | None = None
        self._schemas: dict[str, JsonSchema] = {}
        self._schema_resolver: SchemaResolver | None = None
        self._partial_resolver: PartialResolver | None = None
        self._store: PromptStore | None = None

        self._register_initial_helpers()
        self._register_initial_partials()

    def _register_initial_helpers(self) -> None:
        """Register the initial helpers."""
        register_all_helpers(self._handlebars)
        for name, fn in (self._options.get('helpers') or {}).items():
            self._handlebars.register_helper(name, fn)

    def _register_initial_partials(self) -> None:
        """Register the initial partials."""
        for name, source in (self._options.get('partials') or {}).items():
            self._handlebars.register_partial(name, source)

    def define_helper(self, name: str, fn: HelperFn) -> Dotprompt:
        """Define a helper function for the template.

        Args:
            name: The name of the helper function.
            fn: The function to be called when the helper is used in the
                template.

        Returns:
            The Dotprompt instance.
        """
        self._handlebars.register_helper(name, fn)
        self._known_helpers[name] = True
        return self

    def define_partial(self, name: str, source: str) -> Dotprompt:
        """Define a partial template for the template.

        Args:
            name: The name of the partial template.
            source: The source code for the partial.

        Returns:
            The Dotprompt instance.
        """
        self._handlebars.register_partial(name, source)
        return self

    def define_tool(self, name: str, definition: ToolDefinition) -> Dotprompt:
        """Define a tool for the template.

        Args:
            name: The name of the tool.
            definition: The definition of the tool.
        """
        self._tools[name] = definition
        return self

    def parse[ModelConfig](self, source: str) -> ParsedPrompt[ModelConfig]:
        """Parse a prompt from a string.

        Args:
            source: The source code for the prompt.

        Returns:
            The parsed prompt.
        """
        return parse_document(source)
