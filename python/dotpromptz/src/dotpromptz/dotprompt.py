# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0
"""
This module provides classes and utilities designed to work with the `Dotprompt` system for template rendering,
dynamic partial resolution, tools integration, and schema configuration. The main classes are `DotpromptOptions`
and `Dotprompt`.

Classes:
    1. DotpromptOptions:
    2. Dotprompt:
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set, TypeVar, Union

from handlebarrz import Handlebars, Template

from .helpers import register_all_helpers
from .parse import parse_document, to_messages
from .typing import (
    DataArgument,
    ParsedPrompt,
    PromptMetadata,
    RenderedPrompt,
    T,
    ToolDefinition,
)

# Regular expression pattern for finding partials
PARTIAL_PATTERN = re.compile(r'\{\{>\s*([A-Za-z0-9_-]+)\s*\}\}')


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
        metadata: Optional[PromptMetadata[T]] = None,
    ) -> Callable[
        [DataArgument[Any], Optional[PromptMetadata[T]]], RenderedPrompt[T]
    ]:
        """
        Compiles a given source (template or pre-parsed prompt) into a render function.

        Args:
            source: The source to be compiled, which can either be a raw template string or an already parsed prompt.
            metadata: Optional prompt metadata to be associated with the compilation.

        Returns:
            A callable render function that takes input data and optional metadata. This function produces a RenderedPrompt by rendering the source template with the provided data and metadata
        """
        parsed = (
            source if isinstance(source, ParsedPrompt) else self.parse(source)
        )
        self.resolve_partials(parsed.template)

        # Generate a unique template name
        template_name = f'template_{id(parsed.template)}'

        # Register the template instead of trying to compile it
        self.handlebars.register_template(template_name, parsed.template)

        def render_function(
            data: DataArgument[Any], options: Optional[PromptMetadata[T]] = None
        ) -> RenderedPrompt[T]:
            """
            This class is responsible for compiling prompt templates and subsequently rendering them with provided data and optional metadata, leveraging pre-defined handles and context preparation steps.

            Args:
            - source: A source object, which may be a string or a pre-parsed prompt template. Represents the input template to be rendered.
            - metadata: Optional metadata that can provide additional context or override behavior during the prompt rendering process.

            Returns:
            Returns a callable render function. The render function accepts data and optional metadata, which it uses to generate a rendered prompt object.

            Attributes:
            - render_function: A function that combines provided data and metadata with the compiled template, producing a final structured and rendered prompt.
                - data: Input data object to populate the template placeholders during rendering.
                - options: Additional optional metadata that may modify or extend the behavior during rendering.
                - merged_meta: Resulting metadata after merging the provided metadata options with the actual parsed template's metadata.
                - context: Prepared context dictionary, synthesizing the provided data and metadata for rendering purposes.
                - rendered: Interpolated template string generated using the rendered context.

            Raises:
            - Ensures template rendering stability by utilizing compiled metadata and source context.

            Purpose:
            The main aim is to streamline the process of combining raw templates, input data, and supporting metadata into a final, coherent prompt that can be output as structured content.
            """
            merged_meta = self.render_metadata(parsed, options)
            context = self._prepare_context(data, merged_meta)

            # Render the template using the registered name
            rendered = self.handlebars.render(template_name, context)

            return RenderedPrompt[T].model_construct(
                messages=to_messages(rendered, data),
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
            '@input': data.get('input', {})
            if isinstance(data, dict)
            else getattr(data, 'input', {}) or {},
            '@context': data.get('context', {})
            if isinstance(data, dict)
            else getattr(data, 'context', {}) or {},
            '@metadata': {
                'prompt': metadata.model_dump(),
                'docs': data.get('docs', [])
                if isinstance(data, dict)
                else getattr(data, 'docs', []),
                'messages': data.get('messages', [])
                if isinstance(data, dict)
                else getattr(data, 'messages', []),
            },
        }
