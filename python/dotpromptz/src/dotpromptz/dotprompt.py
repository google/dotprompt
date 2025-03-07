#!/usr/bin/env python3
"""
Copyright 2024 Google LLC
SPDX-License-Identifier: Apache-2.0
"""

import asyncio
import json
import re
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    TypeVar,
    Union,
    cast,
)

from handlebars import Handlebars  # type: ignore

from dotpromptz.typing import ToolDefinition as BaseToolDefinition

from . import helpers, picoschema
from .helpers import hbs
from .parse import parse_document, to_messages
from .util import remove_undefined_fields

# Import the necessary modules
# from .helpers import *
# from .parse import parse_document, to_messages
# from .picoschema import picoschema
# from .util import remove_undefined_fields

T = TypeVar('T')
ModelConfig = TypeVar('ModelConfig', bound=Dict[str, Any])
Variables = TypeVar('Variables', bound=Dict[str, Any])

ToolDefinition = BaseToolDefinition

class DotpromptOptions:
    def __init__(
        self,
        default_model: Optional[str] = None,
        model_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        schemas: Optional[Dict[str, Dict[str, Any]]] = None,
        tools: Optional[Dict[str, Any]] = None,
        tool_resolver: Optional[Callable[[str], Any]] = None,
        schema_resolver: Optional[Callable[[str], Dict[str, Any]]] = None,
        partial_resolver: Optional[Callable[[str], str]] = None,
        helpers: Optional[Dict[str, Callable]] = None,
        partials: Optional[Dict[str, str]] = None
    ):
        self.default_model = default_model
        self.model_configs = model_configs or {}
        self.schemas = schemas or {}
        self.tools = tools or {}
        self.tool_resolver = tool_resolver
        self.schema_resolver = schema_resolver
        self.partial_resolver = partial_resolver
        self.helpers = helpers or {}
        self.partials = partials or {}

class Dotprompt:
    #partial_resolver: Callable[[str], str] | None

    def __init__(self, options: Optional[DotpromptOptions] = None):
        options = options or DotpromptOptions()
        self.handlebars = hbs  # Use the updated Handlebars instance from helpers
        self.known_helpers = {}
        self.store = {}
        self.default_model = options.default_model
        self.model_configs = options.model_configs
        self.tools = options.tools
        self.tool_resolver = options.tool_resolver
        self.schemas = options.schemas
        self.schema_resolver = options.schema_resolver
        self.partial_resolver = options.partial_resolver
        custom_helpers = options.helpers
        custom_partials = options.partials

        # Register custom helpers
        if custom_helpers:
            for key, helper in custom_helpers.items():
                self.handlebars.helpers[key] = helper

        # Register partials
        if custom_partials:
            for key, partial in custom_partials.items():
                self.handlebars.partials[key] = partial

    async def render(self, source: str, data=None, options=None) -> str:
        """Render the template with provided data."""
        data = data or {}
        compiled_template = self.resolve_partials(source)

        # Ensure the data is converted to a standard Python dict if needed
        if hasattr(data, "to_dict"):
            data = data.to_dict()

        return compiled_template(data)


    def define_tool(self, def_: Dict[str, Any]) -> "Dotprompt":
        self.tools[def_["name"]] = def_
        return self

    def define_helper(self, name: str, fn: Callable):
        self.handlebars.register(name, fn)
        self.known_helpers[name] = True
        return self

    def define_partial(self, name: str, source: str):
        self.handlebars.register_partial(name, source)
        return self

    async def resolve_partials(self, template: str):
        """Ensure the function returns an awaitable."""
        resolved = self._resolve_partials(template)

        # Convert JsObjectWrapper to a Python string (if needed)
        if hasattr(resolved, "to_python"):
            return resolved.to_python()

        return resolved

    def _resolve_partials(self, template: str) -> Any:
        """Resolve all partials in the template."""
        # Identify all partials used in the template
        partials = self.identify_partials(template)

        # Resolve each partial if needed
        for partial_name in partials:
            if partial_name not in self.handlebars.partials:
                if self.partial_resolver:
                    partial_content = asyncio.run(
                        self.partial_resolver(partial_name))
                    if partial_content:
                        self.handlebars.partials[partial_name] = partial_content

        # Compile the template with resolved partials
        return self.handlebars.compile(template)

    def parse(self, source: str) -> Dict[str, Any]:
        return parse_document(source)

    async def render_picoschema(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        if not (
            meta.get('output', {}).get('schema') or meta.get('input', {}).get(
            'schema')):
            return meta

        new_meta = meta.copy()

        if meta.get('input', {}).get('schema'):
            new_meta['input'] = {
                **(meta.get('input', {})),
                'schema': await picoschema(meta['input']['schema'], {
                    'schema_resolver': self.wrapped_schema_resolver
                })
            }

        if meta.get('output', {}).get('schema'):
            new_meta['output'] = {
                **(meta.get('output', {})),
                'schema': await picoschema(meta['output']['schema'], {
                    'schema_resolver': self.wrapped_schema_resolver
                })
            }

        return new_meta

    async def wrapped_schema_resolver(self, name: str) -> Optional[
        Dict[str, Any]]:
        if name in self.schemas:
            return self.schemas[name]
        if self.schema_resolver:
            return await self.schema_resolver(name)
        return None

    async def resolve_metadata(self, base: Dict[str, Any], *merges) -> Dict[str, Any]:
        out = base.copy()
        for merge in merges:
            if merge:
                out.update(merge)
        return remove_undefined_fields(out)


    async def resolve_tools(self, base: Dict[str, Any]) -> Dict[str, Any]:
        out = base.copy()

        if out.get('tools'):
            out_tools = []
            out['tool_defs'] = out.get('tool_defs', [])

            for tool_name in out['tools']:
                if tool_name in self.tools:
                    out['tool_defs'].append(self.tools[tool_name])
                elif self.tool_resolver:
                    resolved_tool = await self.tool_resolver(tool_name)
                    if not resolved_tool:
                        raise Exception(
                            f"Dotprompt: Unable to resolve tool '{tool_name}' to a recognized tool definition.")
                    out['tool_defs'].append(resolved_tool)
                else:
                    out_tools.append(tool_name)

            out['tools'] = out_tools

        return out

    def identify_partials(self, template: str) -> Set[str]:
        # This is a simplified version - in Python we'd need to parse the template
        # and extract partial names, which is more complex
        partials = set()
        # Implementation would depend on how handlebars library exposes AST
        # For now, using a simple regex approach (not ideal but functional)
        import re
        partial_matches = re.findall(r'{{>\s*([a-zA-Z0-9_-]+)\s*}}', template)
        partials.update(partial_matches)
        return partials


    async def compile(self, source: Union[str, Dict[str, Any]],
                      additional_metadata=None) -> Callable:
        if isinstance(source, str):
            source = self.parse(source)

        if additional_metadata:
            source = {**source, **additional_metadata}

        # Resolve all partials before compilation
        # Check if source is a ParsedPrompt object or a dict
        if hasattr(source, 'template'):
            # It's a ParsedPrompt object
            await self.resolve_partials(source.template)
            template_str = source.template
        else:
            # It's a dictionary
            await self.resolve_partials(source['template'])
            template_str = source['template']

        render_string = self.handlebars.compile(template_str)

        async def render_func(data, options=None):
            options = options or {}
            # Discard the input schema as once rendered it doesn't make sense
            merged_metadata = await self.render_metadata(source)
            input_schema = merged_metadata.pop('input', {})
            context = {
                **(options.get('input', {}).get('default', {})),
                **(data.get('input', {}))
            }

            metadata_context = {
                'metadata': {
                    'prompt': merged_metadata,
                    'docs': data.get('docs'),
                    'messages': data.get('messages')
                },
                **(data.get('context', {}))
            }

            rendered_string = render_string(context, metadata_context)
            return {
                **merged_metadata,
                'messages': to_messages(rendered_string, data)
            }

        render_func.prompt = source
        return render_func

    async def render_metadata(self, source: Union[str, Dict[str, Any]],
                              additional_metadata=None) -> Dict[str, Any]:
        if isinstance(source, str):
            source = self.parse(source)

        # Handle ParsedPrompt objects
        if hasattr(source, 'model'):
            selected_model = (additional_metadata or {}).get(
                'model') or source.model or self.default_model
        else:
            selected_model = (additional_metadata or {}).get(
                'model') or source.get('model') or self.default_model

        model_config = self.model_configs.get(selected_model,
                                              {}) if selected_model else {}

        return await self.resolve_metadata(
            {'config': model_config} if model_config else {},
            source,
            additional_metadata
        )
