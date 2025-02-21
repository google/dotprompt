# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Smoke tests for package structure."""

import unittest

import js2py


class TestDependencies(unittest.TestCase):
    def test_js2py_basic_functionality(self) -> None:
        """Test basic functionality of js2py."""
        # Simple JavaScript code to be executed
        js_code = 'function add(a, b) { return a + b; }'
        # Create a JavaScript context
        context = js2py.EvalJs()
        # Execute the JavaScript code
        context.execute(js_code)
        # Call the JavaScript function and check the output
        result = context.add(3, 4)
        assert result == 7, 'Expected result is 7'
