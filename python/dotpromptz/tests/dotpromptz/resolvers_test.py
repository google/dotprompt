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

"""Unit tests for resolver utilities using unittest.

## `resolve`

*   Successful resolution with synchronous resolvers.
*   Successful resolution with asynchronous resolvers.
*   Successful resolution with synchronous resolvers returning awaitables.
*   Handling non-callable resolver raising `TypeError`.
*   Handling resolvers (sync, async, sync-returning-awaitable) returning `None`
    raising `LookupError`.
*   Correctly wrapping exceptions from sync resolvers in `ResolverFailedError`.
*   Correctly wrapping exceptions from async resolvers in `ResolverFailedError`.
*   Handling synchronous resolvers returning an `asyncio.Future`.
*   Handling missing resolvers raising `ValueError`.

## `resolve_*` functions

*   Successful resolution to the correct type via the core `resolve` function.
*   Correct propagation of errors (e.g., `ResolverFailedError`, `LookupError`)
    from the core `resolve` function.
"""

import asyncio
import unittest
from collections.abc import Awaitable
from typing import Any

from dotpromptz.errors import ResolverFailedError
from dotpromptz.resolvers import resolve, resolve_json_schema, resolve_partial, resolve_tool
from dotpromptz.typing import JsonSchema, ToolDefinition


class MockSyncResolver:
    """Mock sync resolver callable."""

    def __init__(self, data: dict[str, Any], error: Exception | None = None) -> None:
        """Initialize the mock sync resolver."""
        self._data = data
        self._error = error

    def __call__(self, name: str) -> Any:
        """Mock sync resolver callable."""
        if self._error:
            raise self._error
        return self._data.get(name)


async def _async_helper(value: Any) -> Any:
    """Simple async helper to return a value after a tiny sleep."""
    await asyncio.sleep(0)
    return value


class MockSyncReturningAwaitableResolver:
    """Mock sync resolver that returns an awaitable (coroutine)."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize the mock resolver."""
        self._data = data

    def __call__(self, name: str) -> Awaitable[Any] | None:
        """Return a coroutine object if name is found."""
        value = self._data.get(name)
        if value is not None:
            # Calling the async helper returns the awaitable coroutine
            return _async_helper(value)
        return None


class MockSyncReturningFutureResolver:
    """Mock sync resolver that returns an asyncio.Future."""

    def __init__(self, data: dict[str, Any], loop: asyncio.AbstractEventLoop) -> None:
        """Initialize the mock resolver."""
        self._data = data
        self._loop = loop

    def __call__(self, name: str) -> asyncio.Future[Any] | None:
        """Return a future object if name is found."""
        value = self._data.get(name)
        if value is not None:
            future: asyncio.Future[Any] = self._loop.create_future()
            # Use call_soon_threadsafe to set the result in the event loop.
            self._loop.call_soon_threadsafe(future.set_result, value)
            return future
        return None


class MockAsyncResolver:
    """Mock async resolver callable."""

    def __init__(self, data: dict[str, Any], error: Exception | None = None) -> None:
        """Initialize the mock async resolver."""
        self._data = data
        self._error = error

    async def __call__(self, name: str) -> Any:
        """Mock async resolver callable."""
        if self._error:
            raise self._error
        # Simulate async operation.
        await asyncio.sleep(0.1)
        return self._data.get(name)


mock_tool_def = ToolDefinition(name='test_tool', inputSchema={})
mock_partial_content = 'This is a partial.'
mock_json_schema: JsonSchema = {'type': 'string', 'description': 'A test schema'}


class TestResolve(unittest.IsolatedAsyncioTestCase):
    """Tests for resolver functions."""

    async def test_resolve_resolver_none(self) -> None:
        """Test ValueError when resolver is None."""
        with self.assertRaisesRegex(ValueError, 'test resolver is not defined'):
            await resolve('obj', 'test', None)

    async def test_resolve_sync_success(self) -> None:
        """Test successful resolution with a sync resolver."""
        resolver = MockSyncResolver({'obj1': 'value1'})
        result: Any = await resolve('obj1', 'test', resolver)
        self.assertEqual(result, 'value1')

    async def test_resolve_async_success(self) -> None:
        """Test successful resolution with an async resolver."""
        resolver = MockAsyncResolver({'obj2': 'value2'})
        result: Any = await resolve('obj2', 'test', resolver)
        self.assertEqual(result, 'value2')

    async def test_resolve_sync_resolver_returns_awaitable(self) -> None:
        """Test successful resolution with a sync resolver returning an awaitable."""
        resolver = MockSyncReturningAwaitableResolver({'obj_await': 'value_await'})
        result: Any = await resolve('obj_await', 'test', resolver)
        self.assertEqual(result, 'value_await')

        # Test case where the sync resolver returns None via awaitable
        resolver_none = MockSyncReturningAwaitableResolver({})
        with self.assertRaisesRegex(LookupError, "test resolver for 'not_found' returned None"):
            await resolve('not_found', 'test', resolver_none)

    async def test_resolve_resolver_not_callable(self) -> None:
        """Test TypeError when resolver is not callable."""
        with self.assertRaisesRegex(TypeError, "test resolver for 'obj' is not callable"):
            await resolve('obj', 'test', 'not_a_callable')  # type: ignore

    async def test_resolve_resolver_returns_none(self) -> None:
        """Test LookupError when resolver returns None."""
        resolver_sync = MockSyncResolver({})
        resolver_async = MockAsyncResolver({})
        with self.assertRaisesRegex(LookupError, "test resolver for 'not_found' returned None"):
            await resolve('not_found', 'test', resolver_sync)
        with self.assertRaisesRegex(LookupError, "test resolver for 'not_found' returned None"):
            await resolve('not_found', 'test', resolver_async)

    async def test_resolve_sync_resolver_raises_error(self) -> None:
        """Test ResolverFailedError when sync resolver raises an error."""
        original_error = ValueError('Sync resolver error')
        resolver = MockSyncResolver({}, error=original_error)
        with self.assertRaisesRegex(ResolverFailedError, r'test resolver failed for obj; Sync resolver error') as cm:
            await resolve('obj', 'test', resolver)
        self.assertIs(cm.exception.__cause__, original_error)

    async def test_resolve_async_resolver_raises_error(self) -> None:
        """Test ResolverFailedError when async resolver raises an error."""
        original_error = KeyError('Async resolver error')
        resolver = MockAsyncResolver({}, error=original_error)
        with self.assertRaisesRegex(ResolverFailedError, r"test resolver failed for obj; 'Async resolver error'") as cm:
            await resolve('obj', 'test', resolver)
        self.assertIs(cm.exception.__cause__, original_error)

    async def test_resolve_sync_resolver_returns_future(self) -> None:
        """Test successful resolution with a sync resolver returning a Future."""
        loop = asyncio.get_running_loop()
        resolver = MockSyncReturningFutureResolver({'obj_future': 'value_future'}, loop)
        result: str = await resolve('obj_future', 'test', resolver)
        self.assertEqual(result, 'value_future')


class TestResolveTool(unittest.IsolatedAsyncioTestCase):
    """Tests for tool resolver functions."""

    async def test_resolve_tool_success(self) -> None:
        """Test successful tool resolution."""
        resolver = MockAsyncResolver({'my_tool': mock_tool_def})
        result = await resolve_tool('my_tool', resolver)
        self.assertEqual(result, mock_tool_def)

    async def test_resolve_tool_fails(self) -> None:
        """Test failing tool resolution propagates error."""
        resolver = MockAsyncResolver({}, error=ValueError('Tool fail'))
        with self.assertRaisesRegex(ResolverFailedError, r'tool resolver failed for bad_tool; Tool fail'):
            await resolve_tool('bad_tool', resolver)


class TestResolvePartial(unittest.IsolatedAsyncioTestCase):
    """Tests for partial resolver functions."""

    async def test_resolve_partial_success(self) -> None:
        """Test successful partial resolution."""
        resolver = MockSyncResolver({'my_partial': mock_partial_content})
        result = await resolve_partial('my_partial', resolver)
        self.assertEqual(result, mock_partial_content)

    async def test_resolve_partial_fails(self) -> None:
        """Test failing partial resolution propagates error."""
        with self.assertRaisesRegex(LookupError, "partial resolver for 'missing_partial' returned None"):
            await resolve_partial('missing_partial', MockSyncResolver({}))


class TestResolveJsonSchema(unittest.IsolatedAsyncioTestCase):
    """Tests for JSON schema resolver function."""

    async def test_resolve_json_schema_success_sync(self) -> None:
        """Test successful schema resolution with sync resolver."""
        resolver = MockSyncResolver({'MySchema': mock_json_schema})
        result = await resolve_json_schema('MySchema', resolver)
        self.assertEqual(result, mock_json_schema)

    async def test_resolve_json_schema_success_async(self) -> None:
        """Test successful schema resolution with async resolver."""
        resolver = MockAsyncResolver({'MySchema': mock_json_schema})
        result = await resolve_json_schema('MySchema', resolver)
        self.assertEqual(result, mock_json_schema)

    async def test_resolve_json_schema_fails_error(self) -> None:
        """Test failing schema resolution propagates error."""
        resolver = MockSyncResolver({}, error=TypeError('Schema Error'))
        with self.assertRaisesRegex(ResolverFailedError, r'schema resolver failed for bad_schema; Schema Error'):
            await resolve_json_schema('bad_schema', resolver)

    async def test_resolve_json_schema_fails_none(self) -> None:
        """Test failing schema resolution propagates error when None is returned."""
        resolver = MockAsyncResolver({})
        with self.assertRaisesRegex(LookupError, r"schema resolver for 'missing_schema' returned None"):
            await resolve_json_schema('missing_schema', resolver)


if __name__ == '__main__':
    unittest.main()
