# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Safe string implementation for Handlebarz.

This module provides a SafeString class that marks strings as safe for HTML
output, meaning they will not be escaped when rendered in templates.
"""


class SafeString:
    """A string that should not be escaped when rendered in templates.

    It enables the user to mark a string as safe and its contents
    will not be escaped when rendered in templates.
    """

    def __init__(self, value: str) -> None:
        """Initialize a SafeString.

        Args:
            value: The value to wrap.
        """
        self._s = value

    def __str__(self) -> str:
        """Convert to string.

        Returns:
            The unescaped string content.
        """
        return str(self._s)

    def __repr__(self) -> str:
        """Convert to a Python string representation.

        Returns:
            The unescaped string content.
        """
        return f'SafeString({self._s!r})'

    def __html__(self) -> str:
        """Mark the string as safe for HTML output."""
        return self._s

    def to_string(self) -> str:
        """Convert to string.

        Returns:
            The unescaped string content.
        """
        return str(self._s)

    def to_html(self) -> str:
        """Convert to HTML.

        Returns:
            The unescaped string content.
        """
        return str(self._s)

    def toHTML(self) -> str:  # noqa: N802
        """Convert to HTML.

        This function is named 'toHTML' to satisfy the Handlebars.js JS2PY API
        expectation that any type that exposes this method would be treated as a
        safe string and not escaped by the Handlebars.js engine.

        Returns:
            The unescaped string content.
        """
        return str(self._s)

    def __pybars__(self) -> str:
        """Method recognized by pybars to indicate a safe string."""
        return self._s

        # This is the key method for pybars compatibility

    def toString(self) -> str:
        return str(self._s)
