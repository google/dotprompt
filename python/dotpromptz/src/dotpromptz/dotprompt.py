# Copyright 2025 Google LLC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, TypeVar, Union

from handlebarrz import Handlebars

from .helpers import register_all_helpers
from .parse import parse_document, to_messages
from .typing import (
    DataArgument,
    ParsedPrompt,
    PromptMetadata,
    RenderedPrompt,
    ToolDefinition,
)

# Regular expression pattern for finding partials
PARTIAL_PATTERN = re.compile(r'\{\{>\s*([A-Za-z0-9_-]+)\s*\}\}')

T = TypeVar('T')
PartialResolver = Callable[[str], str | None]
ToolResolver = Callable[[str], ToolDefinition | None]
SchemaResolver = Callable[[str], dict[str, Any] | None]


class DotpromptOptions:
    """Configuration options for Dotprompt

    Args:
        default_model: Default model to use if not specified in prompt
        model_configs: Configuration options for different models
        helpers: Custom helper functions for handlebars
        partials: Predefined partials
        tools: Tool definitions
        tool_resolver: Function to resolve tool names to definitions
        schemas: JSON schemas
        schema_resolver: Function to resolve schema references
        partial_resolver: Function to resolve partial references
    """

    def __init__(
        self,
        default_model: str | None = None,
        model_configs: dict[str, Any] | None = None,
        helpers: dict[str, Callable[..., Any]] | None = None,
        partials: dict[str, str] | None = None,
        tools: dict[str, ToolDefinition] | None = None,
        tool_resolver: ToolResolver | None = None,
        schemas: dict[str, dict[str, Any]] | None = None,
        schema_resolver: SchemaResolver | None = None,
        partial_resolver: PartialResolver | None = None,
    ):
        self.default_model = default_model
        self.model_configs = model_configs or {}
        self.helpers = helpers or {}
        self.partials = partials or {}
        self.tools = tools or {}
        self.tool_resolver = tool_resolver
        self.schemas = schemas or {}
        self.schema_resolver = schema_resolver
        self.partial_resolver = partial_resolver


class Dotprompt:
    """Main Dotprompt template engine

    Args:
        options: Configuration options for the engine
    """

    def __init__(self, options: DotpromptOptions | None = None):
        self.handlebars = Handlebars()
        self.options = options or DotpromptOptions()
        self.known_helpers: Set[str] = set()
        self.known_partials: Set[str] = set()

        register_all_helpers(self.handlebars)

        for name, helper in self.options.helpers.items():
            self.define_helper(name, helper)

        for name, partial in self.options.partials.items():
            self.define_partial(name, partial)

    def define_helper(self, name: str, helper: Callable[..., Any]) -> None:
        """Register a helper function

        Args:
            name: Name of the helper
            helper: Helper function implementation
        """
        if name not in self.known_helpers:
            self.handlebars.register_helper(name, helper)
            self.known_helpers.add(name)

    def define_partial(self, name: str, source: str) -> None:
        """Register a partial template

        Args:
            name: Name of the partial
            source: Template content
        """
        if name not in self.known_partials:
            self.handlebars.register_partial(name, source)
            self.known_partials.add(name)

    def resolve_partials(self, template: str) -> None:
        """Recursively resolve partials in a template

        Args:
            template: Template string to process
        """
        if not self.options.partial_resolver:
            return

        for name in self._identify_partials(template):
            if name not in self.known_partials:
                if content := self.options.partial_resolver(name):
                    self.define_partial(name, content)
                    self.resolve_partials(content)

    def _identify_partials(self, template: str) -> Set[str]:
        """Find all partial references in a template

        Args:
            template: Template string to scan

        Returns:
            Set of partial names referenced in the template
        """
        return set(PARTIAL_PATTERN.findall(template))

    def parse(self, source: str) -> ParsedPrompt[Any]:
        """Parse a template string into a structured format

        Args:
            source: Template string

        Returns:
            Parsed prompt structure
        """
        return parse_document(source)

    def compile(
        self,
        source: Union[str, ParsedPrompt[T]],
        metadata: PromptMetadata[T] | None = None,
    ) -> Callable[
        [DataArgument[Any], PromptMetadata[T] | None], RenderedPrompt[T]
    ]:
        """Compile a template for repeated rendering

        Args:
            source: Template string or parsed prompt
            metadata: Additional metadata

        Returns:
            Render function for the compiled template
        """
        parsed = (
            source if isinstance(source, ParsedPrompt) else self.parse(source)
        )

        self.resolve_partials(parsed.template)
        # Add type ignore for Handlebars compile method
        template = self.handlebars.compile(parsed.template)  # type: ignore[attr-defined]

        def render_function(
            data: DataArgument[Any], options: PromptMetadata[T] | None = None
        ) -> RenderedPrompt[T]:
            merged_meta = self.render_metadata(parsed, options)
            context = self._prepare_context(data, merged_meta)
            return RenderedPrompt[T].model_construct(
                messages=to_messages(template(context), data),
                **merged_meta.model_dump(by_alias=True, exclude_unset=True),
            )

        return render_function

    def render_metadata(
        self,
        parsed: ParsedPrompt[T],
        additional: PromptMetadata[T] | None = None,
    ) -> PromptMetadata[T]:
        """Merge and process metadata

        Args:
            parsed: Parsed prompt with metadata
            additional: Additional metadata to merge

        Returns:
            Combined metadata
        """
        # Initialize with explicit toolDefs alias if creating new instance
        base_meta = (
            parsed.model_copy()
            if parsed
            else PromptMetadata[T](toolDefs=None)  # Use alias with default
        )

        if additional:
            base_meta = base_meta.model_copy(
                update=additional.model_dump(exclude_unset=True)
            )

        base_meta.model = base_meta.model or self.options.default_model
        if base_meta.model:
            base_meta.config = self.options.model_configs.get(base_meta.model)

        if base_meta.tools:
            base_meta.tool_defs = [
                tool
                for name in base_meta.tools
                if (tool := self._resolve_tool(name)) is not None
            ]

        return base_meta

    def render(
        self,
        source: str,
        data: DataArgument[Any],
        options: PromptMetadata[Any] | None = None,
    ) -> RenderedPrompt[Any]:
        """Render a template with data

        Args:
            source: Template string
            data: Data for template rendering
            options: Additional metadata options

        Returns:
            Rendered prompt with messages
        """
        renderer: Callable[
            [DataArgument[Any], PromptMetadata[Any] | None],
            RenderedPrompt[Any],
        ] = self.compile(source)
        return renderer(data, options)

    def _resolve_tool(self, name: str) -> ToolDefinition | None:
        """Resolve a tool by name

        Args:
            name: Tool name to resolve

        Returns:
            Tool definition or None if not found
        """
        if tool := self.options.tools.get(name):
            return tool
        if self.options.tool_resolver:
            return self.options.tool_resolver(name)
        return None

    def _prepare_context(
        self, data: DataArgument[Any], metadata: PromptMetadata[Any]
    ) -> dict[str, Any]:
        """Prepare context for template rendering

        Args:
            data: Input data
            metadata: Prompt metadata

        Returns:
            Context dictionary for template rendering
        """
        return {
            '@input': data.input or {},
            '@context': data.context or {},
            '@metadata': {
                'prompt': metadata.model_dump(),
                'docs': data.docs,
                'messages': data.messages,
            },
        }
