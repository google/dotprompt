# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

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

T = TypeVar('T')
PartialResolver = Callable[[str], Optional[str]]
ToolResolver = Callable[[str], Optional[ToolDefinition]]
SchemaResolver = Callable[[str], Optional[Dict[str, Any]]]


class DotpromptOptions:
    def __init__(
        self,
        default_model: Optional[str] = None,
        model_configs: Optional[Dict[str, Any]] = None,
        helpers: Optional[Dict[str, Callable[..., Any]]] = None,
        # Fixed Callable type
        partials: Optional[Dict[str, str]] = None,
        tools: Optional[Dict[str, ToolDefinition]] = None,
        # Enforce ToolDefinition type
        tool_resolver: Optional[ToolResolver] = None,
        schemas: Optional[Dict[str, Dict[str, Any]]] = None,
        schema_resolver: Optional[SchemaResolver] = None,
        partial_resolver: Optional[PartialResolver] = None,
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
    def __init__(self, options: Optional[DotpromptOptions] = None):
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
        if name not in self.known_helpers:
            self.handlebars.register_helper(name, helper)
            self.known_helpers.add(name)

    def define_partial(self, name: str, source: str) -> None:
        if name not in self.known_partials:
            self.handlebars.register_partial(name, source)
            self.known_partials.add(name)

    def resolve_partials(self, template: str) -> None:
        if not self.options.partial_resolver:
            return

        for name in self._identify_partials(template):
            if name not in self.known_partials:
                if content := self.options.partial_resolver(name):
                    self.define_partial(name, content)
                    self.resolve_partials(content)

    def _identify_partials(self, template: str) -> Set[str]:
        return set(re.findall(r'\{\{>\s*([A-Za-z0-9_-]+)\s*\}\}', template))

    def parse(self, source: str) -> ParsedPrompt[Any]:
        return parse_document(source)

    def compile(
        self,
        source: Union[str, ParsedPrompt[T]],
        metadata: Optional[PromptMetadata[T]] = None,
    ) -> Callable[
        [DataArgument[Any], Optional[PromptMetadata[T]]], RenderedPrompt[T]
    ]:
        parsed = (
            source if isinstance(source, ParsedPrompt) else self.parse(source)
        )
        self.resolve_partials(parsed.template)

        # Add type ignore for Handlebars compile method
        template = self.handlebars.compile(parsed.template)  # type: ignore[attr-defined]

        def render_function(
            data: DataArgument[Any], options: Optional[PromptMetadata[T]] = None
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
        additional: Optional[PromptMetadata[T]] = None,
    ) -> PromptMetadata[T]:
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
        options: Optional[PromptMetadata[Any]] = None,
    ) -> RenderedPrompt[Any]:
        renderer: Callable[
            [DataArgument[Any], Optional[PromptMetadata[Any]]],
            RenderedPrompt[Any],
        ] = self.compile(source)
        return renderer(data, options)

    def _resolve_tool(self, name: str) -> Optional[ToolDefinition]:
        if tool := self.options.tools.get(name):
            return tool
        if self.options.tool_resolver:
            return self.options.tool_resolver(name)
        return None

    def _prepare_context(
        self, data: DataArgument[Any], metadata: PromptMetadata[Any]
    ) -> Dict[str, Any]:
        return {
            '@input': data.input or {},
            '@context': data.context or {},
            '@metadata': {
                'prompt': metadata.model_dump(),
                'docs': data.docs,
                'messages': data.messages,
            },
        }
