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

## Key Operations

| Function              | Description                                                                |
|-----------------------|----------------------------------------------------------------------------|
| `resolve`             | Core async function to resolve a named object using a given resolver.      |
|                       | Handles both sync/async resolvers and sync functions returning awaitables. |
| `resolve_tool`        | Helper async function specifically for resolving tool names.               |
| `resolve_partial`     | Helper async function specifically for resolving partial names.            |
| `resolve_json_schema` | Helper async function specifically for resolving JSON schemas.             |

The `resolve` function handles both sync and async resolvers. If the resolver is
sync, it is run in a thread pool to avoid blocking the event loop. If the
resolver is async, it is awaited directly.

The `resolve_*` functions are convenience wrappers around `resolve` that handle
the specific types of resolvers for tools, partials, and schemas.
"""

import inspect
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import anyio

from dotpromptz.errors import ResolverFailedError
from dotpromptz.typing import (
    JsonSchema,
    PartialResolver,
    SchemaResolver,
    ToolDefinition,
    ToolResolver,
)

# For compatibility with Python 3.10.
ResolverCallable = Callable[[str], Awaitable[Any] | Any]
ResolverT = TypeVar('ResolverT', bound=ResolverCallable)
DefinitionT = TypeVar('DefinitionT')


# TODO: Python 3.12+:
# async def resolve[
#     ResolverT: ResolverCallable,
#     DefinitionT: Any,
# ](name: str, kind: str, resolver: ResolverT) -> DefinitionT:
async def resolve(name: str, kind: str, resolver: ResolverT | None) -> DefinitionT:
    """Resolves a single object using the provided resolver.

    If the resolver is synchronous, it is run in a thread pool to avoid
    blocking the event loop.

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

    try:
        # We need to check if the callable itself is async first, or if it returns an awaitable.
        #
        # ```ascii
        #         +---------------------------+
        #         | collections.abc.Awaitable |  (ABC: Can be `await`ed)
        #         +---------------------------+
        #            /|\             /|\
        #             |               | (Implements/Is-a)
        #     (Inherits/Is-a)         |
        #             |               |
        #     +----------------+  +---------------------+  <-+ (Returned by call to...)
        #     | asyncio.Future |  | types.CoroutineType |    |
        #     | (Low-level     |  | (Awaitable Object)  |    | +--------------------------+
        #     |  Awaitable)    |  | (from `async def`)  |    +-| collections.abc.Callable |
        #     +----------------+  +---------------------+      | (e.g. `async def` func)  |
        #             /|\                 ^                    +--------------------------+
        #              |                  | (Often wrapped by)
        #     (Inherits/Is-a)             |
        #              |                  |
        #     +----------------+          |
        #     |  asyncio.Task  |----------+
        #     | (Runs Coroutine|
        #     |  is a Future)  |
        #     +----------------+
        #                 ^
        #                 | (Managed by)
        #                 |
        #     +-------------------+
        #     | asyncio.TaskGroup |
        #     | (Context Manager) |
        #     +-------------------+
        # ```
        if inspect.iscoroutinefunction(resolver) or inspect.isasyncgenfunction(resolver):
            # If resolver is async, call it directly and await.
            #
            # NOTE(lint): Ignore type error: Static checker can't infer from the
            # `inspect` check that `resolver` is guaranteed to be async here,
            # but the runtime check ensures `resolver(name)` returns an
            # awaitable in this branch.
            obj = await resolver(name)  # type: ignore[misc]
        else:
            # If resolver is sync, run it in a thread pool and check the return
            # type after calling, as we don't know it yet. It might still return
            # an awaitable (e.g. sync function returning `asyncio.Future`) but
            # calling it sync first is necessary to check.
            result_or_awaitable = await anyio.to_thread.run_sync(resolver, name)
            if inspect.isawaitable(result_or_awaitable):
                obj = await result_or_awaitable
            else:
                obj = result_or_awaitable

    except Exception as e:
        # Catch errors from both await and sync execution in thread.
        raise ResolverFailedError(name, kind, str(e)) from e

    # TODO: Should we raise a LookupError if the resolver returns None?
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


async def resolve_json_schema(name: str, resolver: SchemaResolver | None) -> JsonSchema:
    """Resolve a JSON schema using the provided resolver.

    Args:
        name: The name of the JSON schema to resolve.
        resolver: The JSON schema resolver callable.

    Returns:
        The resolved JSON schema.

    Raises:
        LookupError: If the resolver returns None for the schema.
        ResolverFailedError: For exceptions raised by the resolver.
        TypeError: If the resolver is not callable or returns an invalid type.
    """
    return await resolve(name, 'schema', resolver)
