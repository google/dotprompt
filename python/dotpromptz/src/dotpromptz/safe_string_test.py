# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for the SafeString class."""

import unittest

from dotpromptz.safe_string import SafeString


class TestSafeString(unittest.TestCase):
    """Test the SafeString class."""

    def test_safe_string(self) -> None:
        """Test that SafeString objects remain unescaped when passed to
        escape_expression."""
        safe = SafeString('<strong>Safe Content</strong>')
        self.assertEqual(str(safe), '<strong>Safe Content</strong>')
        self.assertEqual(safe.to_html(), '<strong>Safe Content</strong>')
        self.assertEqual(safe.toHTML(), '<strong>Safe Content</strong>')
        self.assertEqual(safe.to_string(), '<strong>Safe Content</strong>')

    def test_safe_string_repr(self) -> None:
        """Test that SafeString objects have a correct string representation."""
        safe = SafeString('<strong>Safe Content</strong>')
        self.assertEqual(
            repr(safe), "SafeString('<strong>Safe Content</strong>')"
        )
