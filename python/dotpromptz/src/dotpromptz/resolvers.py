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

"""Utilities for resolving tools and partials.

A well-defined object resolver is a callable that takes a name and returns
either an object or an awaitable (such as a future or coroutine) that returns an
object.
"""

import inspect
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from dotpromptz.errors import ResolverFailedError
from dotpromptz.typing import PartialResolver, ToolDefinition, ToolResolver

# For compatibility with Python 3.10.
ResolverCallable = Callable[[str], Awaitable[Any] | Any]
ResolverT = TypeVar('ResolverT', bound=ResolverCallable)
DefinitionT = TypeVar('DefinitionT')


# TODO: Python 3.12+:
# async def resolve[
#     ResolverT: ResolverCallable,
#     DefinitionT: Any,
# ](name: str, kind: str, resolver: ResolverT | None) -> DefinitionT:
async def resolve(name: str, kind: str, resolver: ResolverT | None) -> DefinitionT:
    """Resolves a single object using the provided resolver.

    Args:
        name: The name of the object to resolve.
        kind: The kind of object to resolve.
        resolver: The object resolver callable.

    Returns:
        The resolved object.

    Raises:
        LookupError: If the resolver returns None for the object.
        ResolverFailedError: For exceptions raised by the resolver.
        TypeError: If the resolver is not callable or returns an invalid type.
        ValueError: If the resolver is not defined.
    """
    obj: DefinitionT | None = None

    if resolver is None:
        raise ValueError(f'{kind} resolver is not defined')

    if not callable(resolver):
        raise TypeError(f"{kind} resolver for '{name}' is not callable")

    maybe_fut = resolver(name)
    if inspect.isawaitable(maybe_fut):
        try:
            obj = await maybe_fut
        except Exception as e:
            raise ResolverFailedError(name, kind, str(e)) from e
    else:
        obj = maybe_fut

    if obj is None:
        raise LookupError(f"{kind} resolver for '{name}' returned None")

    return obj


async def resolve_tool(name: str, resolver: ToolResolver | None) -> ToolDefinition:
    """Resolve a tool using the provided resolver.

    Args:
        name: The name of the tool to resolve.
        resolver: The tool resolver callable (sync or async).

    Returns:
        The resolved tool definition.

    Raises:
        LookupError: If the resolver returns None for the tool.
        ResolverFailedError: For exceptions raised by the resolver.
        TypeError: If the resolver is not callable or returns an invalid type.
        ValueError: If the resolver is not defined.
    """
    return await resolve(name, 'tool', resolver)


async def resolve_partial(name: str, resolver: PartialResolver | None) -> str:
    """Resolve a partial using the provided resolver.

    Args:
        name: The name of the partial to resolve.
        resolver: The partial resolver callable.

    Returns:
        The resolved partial.

    Raises:
        LookupError: If the resolver returns None for the partial.
        ResolverFailedError: For exceptions raised by the resolver.
        TypeError: If the resolver is not callable or returns an invalid type.
        ValueError: If the resolver is not defined.
    """
    return await resolve(name, 'partial', resolver)
