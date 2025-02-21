# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Dotprompt implementation in Python."""

from collections.abc import Callable
from typing import Any, TypedDict, TypeVar

import handlebarz

from dotpromptz import helpers
from dotpromptz.interfaces import (
    DataArgument,
    JSONSchema,
    ParsedPrompt,
    PromptFunction,
    PromptMetadata,
    PromptStore,
    RenderedPrompt,
    SchemaResolver,
    ToolDefinition,
    ToolResolver,
)
from dotpromptz.parse import parse_document, to_messages
from dotpromptz.picoschema import picoschema
from dotpromptz.util import remove_undefined_fields

# Type variables
Variables = TypeVar('Variables', bound=dict[str, Any])
ModelConfig = TypeVar('ModelConfig', bound=dict[str, Any])

# Type aliases
PartialResolver = Callable[[str], str | None]
HelperDelegate = Callable[..., Any]


class DotpromptOptions(TypedDict, total=False):
    """Options for Dotprompt initialization."""

    default_model: str | None
    model_configs: dict[str, Any] | None
    helpers: dict[str, HelperDelegate] | None
    partials: dict[str, str] | None
    tools: dict[str, ToolDefinition] | None
    tool_resolver: ToolResolver | None
    schemas: dict[str, JSONSchema] | None
    schema_resolver: SchemaResolver | None
    partial_resolver: PartialResolver | None


class Dotprompt:
    """Main Dotprompt class for template rendering and prompt management."""

    def __init__(self, options: DotpromptOptions | None = None):
        """Initialize Dotprompt with optional configuration.

        Args:
            options: Configuration options for Dotprompt.
        """
        options = options or {}
        self._known_helpers: dict[str, bool] = {}
        self._default_model = options.get('default_model')
        self._model_configs = options.get('model_configs', {})
        self._tools = options.get('tools', {})
        self._tool_resolver = options.get('tool_resolver')
        self._schemas = options.get('schemas', {})
        self._schema_resolver = options.get('schema_resolver')
        self._partial_resolver = options.get('partial_resolver')
        self._store: PromptStore | None = None
        self._partials: dict[str, str] = {}
        self._helpers: dict[str, Callable] = {}

        # Register built-in helpers
        for name, fn in helpers.__dict__.items():
            if callable(fn) and not name.startswith('_'):
                self.define_helper(name, fn)

        # Register user-provided helpers
        if options.get('helpers'):
            for name, fn in options['helpers'].items():
                self.define_helper(name, fn)

        # Register partials
        if options.get('partials'):
            for name, source in options['partials'].items():
                self.define_partial(name, source)

    def define_helper(self, name: str, fn: HelperDelegate) -> 'Dotprompt':
        """Define a new helper function.

        Args:
            name: Name of the helper.
            fn: Helper function implementation.

        Returns:
            Self for chaining.
        """
        self._known_helpers[name] = True
        return self

    def define_partial(self, name: str, source: str) -> 'Dotprompt':
        """Define a new partial template.

        Args:
            name: Name of the partial.
            source: Partial template source.

        Returns:
            Self for chaining.
        """
        self._partials[name] = source
        return self

    def define_tool(self, def_: ToolDefinition) -> 'Dotprompt':
        """Define a new tool.

        Args:
            def_: Tool definition.

        Returns:
            Self for chaining.
        """
        self._tools[def_['name']] = def_
        return self

    def parse(self, source: str) -> ParsedPrompt:
        """Parse a template source into a parsed prompt.

        Args:
            source: Template source to parse.

        Returns:
            Parsed prompt object.
        """
        return parse_document(source)

    def render(
        self,
        source: str,
        data: DataArgument | None = None,
        options: PromptMetadata | None = None,
    ) -> RenderedPrompt:
        """Render a template with data and options.

        Args:
            source: Template source to render.
            data: Data to use for rendering.
            options: Rendering options and metadata.

        Returns:
            Rendered prompt result.
        """
        renderer = self.compile(source)
        return renderer(data or {}, options)

    def render_metadata(
        self,
        source: str,
        options: PromptMetadata | None = None,
    ) -> PromptMetadata:
        """Render metadata for a template.

        Args:
            source: Template source.
            options: Metadata options.

        Returns:
            Rendered metadata.
        """
        parsed = self.parse(source)
        return self._resolve_metadata(parsed.metadata, options)

    def compile(self, source: str) -> PromptFunction:
        """Compile a template into a reusable function.

        Args:
            source: Template source to compile.

        Returns:
            Compiled prompt function.
        """
        parsed = self.parse(source)

        def renderer(
            data: DataArgument | None = None,
            options: PromptMetadata | None = None,
        ) -> RenderedPrompt:
            data = data or {}
            metadata = self._resolve_metadata(parsed.metadata, options)

            # Render the template
            rendered = handlebarz.render(
                template=parsed.template,
                data=data,
                partials=self._partials,
                helpers=self._helpers,
            )

            return {
                'raw': rendered,
                'messages': to_messages(rendered),
                'ext': metadata.get('ext', {}),
                'config': metadata.get('config', {}),
                'metadata': metadata.get('metadata', {}),
            }

        return renderer

    def _resolve_metadata(
        self,
        metadata: PromptMetadata,
        options: PromptMetadata | None = None,
    ) -> PromptMetadata:
        """Resolve metadata with options.

        Args:
            metadata: Base metadata to resolve.
            options: Options to apply.

        Returns:
            Resolved metadata.
        """
        options = options or {}
        result = metadata | options

        # Resolve model configuration
        model = result.get('model', self._default_model)
        if model and model in self._model_configs:
            result['config'] = self._model_configs[model] | result.get(
                'config', {}
            )

        # Resolve tool definitions
        tools = {}
        for name in result.get('tools', []):
            if name in self._tools:
                tools[name] = self._tools[name]
            elif self._tool_resolver:
                tool = self._tool_resolver(name)
                if tool:
                    tools[name] = tool

        if tools:
            result['ext'] = result.get('ext', {}) | {'tools': tools}

        # Resolve schema definitions
        schemas = {}
        for name, schema in result.get('schemas', {}).items():
            if isinstance(schema, str):
                if schema in self._schemas:
                    schemas[name] = self._schemas[schema]
                elif self._schema_resolver:
                    resolved = self._schema_resolver(schema)
                    if resolved:
                        schemas[name] = resolved
            else:
                schemas[name] = schema

        if schemas:
            result['ext'] = result.get('ext', {}) | {'schemas': schemas}

        return remove_undefined_fields(result)
