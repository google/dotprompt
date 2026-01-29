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

"""Custom exception classes for the dotpromptz package.

This module defines domain-specific exceptions that provide meaningful error
messages and structured error information for debugging and error handling.

## Exception Hierarchy

```
BaseException
    │
    └── Exception
            │
            └── RuntimeError
                    │
                    └── ResolverFailedError
                            (Tool, schema, or partial resolution failed)
```

## Exception Types

| Exception              | Raised When                                        |
|------------------------|----------------------------------------------------|
| `ResolverFailedError`  | A resolver function raises an exception while      |
|                        | attempting to resolve a tool, schema, or partial   |

## Usage Example

```python
from dotpromptz.errors import ResolverFailedError

try:
    tool = await resolve_tool('my_tool', resolver)
except ResolverFailedError as e:
    print(f"Failed to resolve {e.kind} '{e.name}': {e.reason}")
    # Output: Failed to resolve tool 'my_tool': Connection timeout
```

## Error Handling Best Practices

When catching dotpromptz exceptions:

1. **Be specific**: Catch `ResolverFailedError` rather than generic `Exception`
2. **Log context**: Use the `name`, `kind`, and `reason` attributes for logging
3. **Provide fallbacks**: Consider default values or graceful degradation
4. **Re-raise appropriately**: Wrap in application-specific exceptions if needed

```python
try:
    rendered = await dotprompt.render(source, data)
except ResolverFailedError as e:
    logger.error(f'Resolution failed: {e.kind}={e.name}', exc_info=True)
    # Decide: retry, use fallback, or propagate
    raise
```
"""


class ResolverFailedError(RuntimeError):
    """Raised when a resolver function fails to resolve an object.

    This exception wraps errors that occur during the resolution of tools,
    schemas, or partials. It preserves the original error context while
    providing structured access to error details.

    Attributes:
        name: The name of the object that failed to resolve (e.g., tool name).
        kind: The category of object ('tool', 'schema', or 'partial').
        reason: A human-readable description of why resolution failed.

    Example:
        ```python
        try:
            tool = await resolve_tool('calculator', my_resolver)
        except ResolverFailedError as e:
            print(f'Could not find {e.kind}: {e.name}')
            print(f'Reason: {e.reason}')
        ```
    """

    def __init__(self, name: str, kind: str, reason: str) -> None:
        """Initialize the error with resolution context.

        Args:
            name: The name of the object that failed to resolve.
            kind: The kind of object that failed to resolve
                  ('tool', 'schema', or 'partial').
            reason: The reason the object resolver failed.
        """
        self.name = name
        self.kind = kind
        self.reason = reason
        super().__init__(f'{kind} resolver failed for {name}; {reason}')

    def __str__(self) -> str:
        """Return a human-readable error message.

        Returns:
            A formatted string describing the resolution failure.
        """
        return f'{self.kind} resolver failed for {self.name}; {self.reason}'

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            A formatted string with full error details.
        """
        return f'ResolverFailedError(name={self.name!r}, kind={self.kind!r}, reason={self.reason!r})'
