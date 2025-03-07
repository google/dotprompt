#!/usr/bin/env python3
"""
Copyright 2024 Google LLC
SPDX-License-Identifier: Apache-2.0
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from handlebars import Handlebars  # type: ignore

from dotpromptz.helpers import register_helpers
from dotpromptz.parse import to_messages

# ---------------------------------------------------------------------------
# external dependencies and helper functions/types
# ---------------------------------------------------------------------------

# Type definitions
DataArgument = dict[str, Any]
JSONSchema = dict[str, Any]
ParsedPrompt = dict[str, Any]
PromptMetadata = dict[str, Any]
RenderedPrompt = dict[str, Any]

# Generic type variables for templates
Variables = TypeVar('Variables', bound=dict[str, Any])
ModelConfig = TypeVar('ModelConfig', bound=dict[str, Any])

if TYPE_CHECKING:
    pass


# ToolDefinition type as a dataclass
class ToolDefinition:
    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.__dict__.update(kwargs)


# Type aliases for resolvers and prompt functions
ToolResolver = Callable[[str], Awaitable[ToolDefinition | None]]
SchemaResolver = Callable[[str], Awaitable[JSONSchema | None]]
PartialResolver = Callable[[str], str | None | Awaitable[str | None]]
PromptFunction = Callable[
    [DataArgument, PromptMetadata | None], Awaitable[RenderedPrompt]
]
PromptStore = Any  # This should implement a method loadPartial(name: str) returning an object with a 'source' attribute.


async def picoschema(schema: Any, options: dict[str, Any]) -> Any:
    """
    Asynchronously process a schema using picoschema.
    """
    # In a full implementation, this would validate or transform the schema.
    return schema


def parseDocument(source: str) -> ParsedPrompt:
    """
    Parses a document containing YAML frontmatter and template content.

    Args:
        source: The source document containing frontmatter and template

    Returns:
        Parsed prompt with metadata and template content
    """
    # Dummy implementation: return a dict with template set to source.
    return {'template': source}


def removeUndefinedFields(obj: dict[str, Any]) -> dict[str, Any]:
    """
    Removes keys with value None from the dictionary.

    Args:
        obj: The dictionary to be cleaned.

    Returns:
        A new dictionary with keys having non-None values.
    """
    return {k: v for k, v in obj.items() if v is not None}


# ---------------------------------------------------------------------------
# DotpromptOptions type definition as a simple dictionary type.
# ---------------------------------------------------------------------------


class DotpromptOptions:
    """
    Options for configuring the Dotprompt engine.

    Attributes:
        defaultModel: A default model to use if none is supplied.
        modelConfigs: A mapping of model names to their default configuration objects.
        helpers: A mapping of helper names to their helper functions.
        partials: A mapping of partial names to template strings.
        tools: A mapping of tool names to their tool definitions.
        toolResolver: A function to resolve tool names into tool definitions.
        schemas: A mapping of schema names to JSON Schema definitions.
        schemaResolver: A function to resolve schema names into JSON Schema definitions.
        partialResolver: A function to resolve partial names to their content.
    """

    def __init__(
        self,
        defaultModel: str | None = None,
        modelConfigs: dict[str, object] | None = None,
        helpers: dict[str, Callable[..., Any]] | None = None,
        partials: dict[str, str] | None = None,
        tools: dict[str, ToolDefinition] | None = None,
        toolResolver: ToolResolver | None = None,
        schemas: dict[str, JSONSchema] | None = None,
        schemaResolver: SchemaResolver | None = None,
        partialResolver: PartialResolver | None = None,
    ) -> None:
        self.defaultModel = defaultModel
        self.modelConfigs = modelConfigs or {}
        self.helpers = helpers or {}
        self.partials = partials or {}
        self.tools = tools or {}
        self.toolResolver = toolResolver
        self.schemas = schemas or {}
        self.schemaResolver = schemaResolver
        self.partialResolver = partialResolver


# ---------------------------------------------------------------------------
# Dotprompt class implementation
# ---------------------------------------------------------------------------


class Dotprompt:
    """
    A class to handle prompt rendering, helpers, partials, and metadata.
    """

    def __init__(self, options: DotpromptOptions | None = None) -> None:
        """
        Initializes a new instance of Dotprompt.

        Args:
            options: An optional DotpromptOptions object for configuration.
        """

        self.handlebars = Handlebars
        self.knownHelpers: dict[str, bool] = {}
        self.defaultModel: str | None = None
        self.modelConfigs: dict[str, object] = {}
        self.tools: dict[str, ToolDefinition] = {}
        self.toolResolver: ToolResolver | None = None
        self.schemas: dict[str, JSONSchema] = {}
        self.schemaResolver: SchemaResolver | None = None
        self.partialResolver: PartialResolver | None = None
        self.store: PromptStore | None = None

        if options:
            self.modelConfigs = options.modelConfigs or self.modelConfigs
            self.defaultModel = options.defaultModel
            self.tools = options.tools or {}
            self.toolResolver = options.toolResolver
            self.schemas = options.schemas or {}
            self.schemaResolver = options.schemaResolver
            self.partialResolver = options.partialResolver

        # Register default helpers from the helpers module.
        # for key, helper_func in helpers.items():
        #     self.defineHelper(key, helper_func)

        # Register additional helpers if provided.
        if options and options.helpers:
            for key, helper_func in options.helpers.items():
                self.defineHelper(key, helper_func)

        # Register built-in helpers
        register_helpers(self.handlebars)

        # Register partials if provided.
        if options and options.partials:
            for key in options.partials:
                self.definePartial(key, options.partials[key])

    def render(
        self, template: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        compiled = self.handlebars.compile(template)
        rendered = compiled(data or {})
        messages = to_messages(rendered, data or {})
        return {'messages': messages, 'raw': rendered}

    def defineHelper(self, name: str, fn: Callable[..., Any]) -> 'Dotprompt':
        """
        Registers a helper function and marks it as known.

        Args:
            name: The name of the helper.
            fn: The helper function.

        Returns:
            The current instance for chaining.
        """
        self.handlebars.register_helper(name, fn)
        self.knownHelpers[name] = True
        return self

    def definePartial(self, name: str, source: str) -> 'Dotprompt':
        """
        Registers a partial template with Handlebars.

        Args:
            name: The name of the partial.
            source: The template source for the partial.

        Returns:
            The current instance for chaining.
        """
        self.handlebars.registerPartial(name, source)
        return self

    def defineTool(self, defn: ToolDefinition) -> 'Dotprompt':
        """
        Registers a tool definition.

        Args:
            defn: The tool definition.

        Returns:
            The current instance for chaining.
        """
        self.tools[defn.name] = defn
        return self

    def parse(self, source: str) -> ParsedPrompt:
        """
        Parses a document containing YAML frontmatter and template content.

        Args:
            source: The source document containing frontmatter and template.

        Returns:
            A parsed prompt containing metadata and template content.
        """
        return parseDocument(source)

    async def renderMetadata(
        self, base: PromptMetadata, *merges: PromptMetadata | None
    ) -> PromptMetadata:
        """
        Merges multiple metadata objects and resolves tools and schemas.

        Args:
            base: The base metadata.
            merges: Additional metadata objects for merging.

        Returns:
            The fully resolved metadata.
        """
        out = base.copy()
        for merge in merges:
            if not merge:
                continue
            config = out.get('config', {})
            out = {**out, **merge}
            out['config'] = {**config, **(merge.get('config') or {})}
            if 'template' in out:
                del out['template']
        out = removeUndefinedFields(out)
        out = await self._resolveTools(out)
        return out

    async def _resolveTools(self, base: PromptMetadata) -> PromptMetadata:
        """
        Resolves tool definitions based on tool names present in metadata.

        Args:
            base: The base prompt metadata.

        Returns:
            The metadata with resolved tool definitions.
        """
        out = base.copy()
        if out.get('tools'):
            outTools: list[str] = []
            out['toolDefs'] = out.get('toolDefs', [])

            async def resolve_tool(toolName: str) -> None:
                if toolName in self.tools:
                    out['toolDefs'].append(self.tools[toolName])
                elif self.toolResolver:
                    resolvedTool = await self.toolResolver(toolName)
                    if not resolvedTool:
                        raise Exception(
                            f"Dotprompt: Unable to resolve tool '{toolName}' to a recognized tool definition."
                        )
                    out['toolDefs'].append(resolvedTool)
                else:
                    outTools.append(toolName)

            await asyncio.gather(
                *(resolve_tool(toolName) for toolName in out['tools'])
            )
            out['tools'] = outTools
        return out

    def identifyPartials(self, template: str) -> set[str]:
        ast = self.handlebars.parse(template)
        partials: set[str] = set()

        class PartialVisitor(Visitor):
            def __init__(self, partials: set[str]) -> None:
                self.partials = partials
                super().__init__()

            def PartialStatement(self, partial: Any) -> None:
                if 'original' in partial.get('name', {}):
                    self.partials.add(partial['name']['original'])

        visitor = PartialVisitor(partials)
        if ast is not None:  # Check if AST is valid
            visitor.accept(ast)
        return partials

    async def resolvePartials(self, template: str) -> None:
        if not self.partialResolver and not self.store:
            return

        partials = self.identifyPartials(template)

        async def resolve_partial(name: str) -> None:
            if name not in self.handlebars.partials:
                content: str | None = None
                if self.partialResolver:
                    result = self.partialResolver(name)
                    if asyncio.iscoroutine(result):
                        content = await result
                    else:
                        content = result  # type: ignore
                if (
                    not content
                    and self.store
                    and hasattr(self.store, 'loadPartial')
                ):
                    loaded = await self.store.loadPartial(name)
                    if loaded and 'source' in loaded:
                        content = loaded['source']
                if content:
                    self.definePartial(name, content)
                    await self.resolvePartials(content)

        await asyncio.gather(*(resolve_partial(name) for name in partials))

    async def compile(
        self,
        source: str | ParsedPrompt,
        additionalMetadata: PromptMetadata | None = None,
    ) -> PromptFunction:
        """
        Compiles a prompt template into a render function.

        Args:
            source: The prompt template or its parsed representation.
            additionalMetadata: Additional metadata to merge with the prompt.

        Returns:
            A function that renders the prompt with provided data.
        """
        if isinstance(source, str):
            source = self.parse(source)

        if additionalMetadata:
            source = {**source, **additionalMetadata}

        # Resolve all partials before compilation.
        await self.resolvePartials(source['template'])

        renderString = self.handlebars.compile(
            source['template'],
            {'knownHelpers': self.knownHelpers, 'knownHelpersOnly': True},
        )

        async def renderFunc(
            data: DataArgument | None, options: PromptMetadata | None = None
        ) -> RenderedPrompt:
            metadata: PromptMetadata = await self.renderMetadata(
                source, options
            )
            options_dict = options or {}
            data_dict = data or {}

            # Build context and extra safely
            context = {
                **options_dict.get('input', {}).get('default', {}),
                **data_dict.get('input', {}),
            }
            extra = {
                'data': {
                    'metadata': metadata,
                    'docs': data_dict.get('docs'),
                    'messages': data_dict.get('messages'),
                }
            }

            rendered_string: str = renderString(context, extra)

            # Pass the structured data to to_messages
            return {
                'messages': to_messages(rendered_string, data_dict),
                **metadata,
            }

        return renderFunc

    def removeUndefinedFieldsFromDict(
        self, obj: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Removes keys with value None from the dictionary.

        Args:
            obj: The dictionary to be cleaned.

        Returns:
            A new dictionary with keys having non-None values.
        """
        return {k: v for k, v in obj.items() if v is not None}


class Visitor:
    def accept(self, ast: dict[str, Any]) -> None:
        partials = ast.get('partials', [])  # Use .get with default
        for partial in partials:
            self.PartialStatement(partial)

    def PartialStatement(self, partial: Any) -> None:
        """
        Processes a partial statement from the AST.

        Args:
            partial: The partial statement.
        """
        return None
