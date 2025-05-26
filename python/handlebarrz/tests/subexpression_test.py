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

import unittest
from typing import Any

from handlebarrz import HelperOptions, Template


class SubexpressionTest(unittest.TestCase):
    def test_subexpression_basic(self) -> None:
        """Test basic subexpressions for comparison and logical operations."""
        template = Template()

        # Register comparison helpers
        def gt_helper(params: list[str], options: HelperOptions) -> str:
            """Test greater helper."""
            if len(params) < 2:
                return 'false'
            try:
                return 'true' if float(params[0]) > float(params[1]) else 'false'
            except (ValueError, TypeError):
                return 'false'

        def not_helper(params: list[str], options: HelperOptions) -> str:
            """Test not helper."""
            if len(params) < 1:
                return 'false'
            value = params[0]
            # Convert string representations to Python booleans
            if value == 'true':
                return 'false'
            elif value == 'false':
                return 'true'
            else:
                # Try to interpret as a boolean context
                return 'false' if value else 'true'

        # Register helpers
        template.register_helper('gt', gt_helper)
        template.register_helper('not', not_helper)

        # Register test templates
        template.register_template('gt-test', '{{#if (gt a b)}}Success{{else}}Failed{{/if}}')
        template.register_template('not-test', '{{#if (not (gt a c))}}Success{{else}}Failed{{/if}}')
        template.register_template('literal-test', '{{#if (not true)}}Success{{else}}Failed{{/if}}')

        # Data to render
        data = {'a': 1, 'b': 0, 'c': 2}

        # Test gt subexpression
        result_gt = template.render('gt-test', data)
        self.assertEqual(result_gt, 'Success')

        # Test not with nested subexpression
        result_not = template.render('not-test', data)
        self.assertEqual(result_not, 'Success')

        # Test with literal value
        result_literal = template.render('literal-test', {})
        self.assertEqual(result_literal, 'Success')

    def test_nested_subexpressions(self) -> None:
        """Test deeply nested subexpressions."""
        template = Template()

        def add_helper(params: list[str], options: HelperOptions) -> str:
            """Test arithmetic helpers."""
            if len(params) >= 2:
                try:
                    # Convert numeric inputs to floats for calculation
                    num1 = float(params[0]) if isinstance(params[0], str) else params[0]
                    num2 = float(params[1]) if isinstance(params[1], str) else params[1]
                    # Return result as string
                    return str(num1 + num2)
                except (TypeError, ValueError):
                    return '0'
            return '0'

        def multiply_helper(params: list[str], options: HelperOptions) -> str:
            if len(params) >= 2:
                try:
                    # Convert numeric inputs to floats for calculation
                    num1 = float(params[0]) if isinstance(params[0], str) else params[0]
                    num2 = float(params[1]) if isinstance(params[1], str) else params[1]
                    # Return result as string
                    return str(num1 * num2)
                except (TypeError, ValueError):
                    return '0'
            return '0'

        def divide_helper(params: list[str], options: HelperOptions) -> str:
            if len(params) >= 2:
                try:
                    # Convert numeric inputs to floats for calculation
                    num1 = float(params[0]) if isinstance(params[0], str) else params[0]
                    num2 = float(params[1]) if isinstance(params[1], str) else params[1]
                    if num2 != 0:
                        # Return result as string
                        return str(num1 / num2)
                    return '0'
                except (TypeError, ValueError):
                    return '0'
            return '0'

        # Register the helpers
        template.register_helper('add', add_helper)
        template.register_helper('multiply', multiply_helper)
        template.register_helper('divide', divide_helper)

        # Register a template with deeply nested subexpressions
        template_str = '{{divide (add (multiply 2 3) 4) 2}}'
        template.register_template('nested-expr', template_str)

        # Render the template
        result = template.render('nested-expr', {})

        # The calculation should be: (2*3) + 4 = 10, then 10/2 = 5
        self.assertEqual(result, '5.0')

    def test_subexpression_in_hash_args(self) -> None:
        """Test subexpressions in hash arguments."""
        template = Template()

        def eq_helper(params: list[str], options: HelperOptions) -> str:
            """Test equality helper."""
            if len(params) >= 2:
                # Return string values for compatibility with Handlebars Rust
                return 'true' if params[0] == params[1] else 'false'
            return 'false'

        def select_helper(params: list[str], options: HelperOptions) -> str:
            condition = options.hash_value('condition') or 'false'
            if_true = str(options.hash_value('if_true'))
            if_false = str(options.hash_value('if_false'))
            # Check if condition is string "true" or "false"
            if isinstance(condition, str):
                return if_true if condition == 'true' else if_false
            # Otherwise interpret as boolean-like
            return if_true if condition else if_false

        # Register the helpers
        template.register_helper('eq', eq_helper)
        template.register_helper('select', select_helper)

        # Register a template with subexpression in hash args
        template_str = '{{select condition=(eq value 10) if_true="Equal" if_false="Not Equal"}}'
        template.register_template('hash-subexpr', template_str)

        # Test with equal value
        data_eq = {'value': 10}
        result_eq = template.render('hash-subexpr', data_eq)
        self.assertEqual(result_eq, 'Equal')

        # Test with unequal value
        data_ne = {'value': 5}
        result_ne = template.render('hash-subexpr', data_ne)
        self.assertEqual(result_ne, 'Not Equal')

    def test_lookup_with_subexpression(self) -> None:
        """Test dynamic lookups with subexpressions."""
        template = Template()

        def get_key_helper(params: list[str], options: HelperOptions) -> str:
            """Test lookup helper."""
            if params:
                return params[0]
            return ''

        # Register the helper
        template.register_helper('get_key', get_key_helper)

        # Register a template that uses a subexpression for dynamic lookup
        template_str = '{{lookup this (get_key keyname)}}'
        template.register_template('lookup-subexpr', template_str)

        # Data with multiple possible values
        data = {
            'keyname': 'selected_key',
            'selected_key': 'The selected value',
            'other_key': 'Another value',
        }

        # Render the template
        result = template.render('lookup-subexpr', data)
        self.assertEqual(result, 'The selected value')

    def test_helper_call_count(self) -> None:
        """Test that subexpressions don't call helpers multiple times."""
        template = Template()

        # Counter to track helper calls
        call_count = 0

        def count_helper(params: list[str], options: HelperOptions) -> str:
            """Test counter helper."""
            nonlocal call_count
            call_count += 1
            # Return result as string to ensure compatibility with Handlebars
            # Rust.
            return str(call_count)

        # Register the helper
        template.register_helper('count', count_helper)

        # Register templates to test helper call count
        template.register_template('single-call', '{{count}}')
        template.register_template('if-with-subexpr', '{{#if (count)}}Called{{/if}}')

        # Reset counter
        call_count = 0

        # Single call should increment once
        result = template.render('single-call', {})
        self.assertEqual(result, '1')
        self.assertEqual(call_count, 1)

        # Reset counter
        call_count = 0

        # If with subexpression should only call helper once
        result = template.render('if-with-subexpr', {})
        self.assertEqual(result, 'Called')
        self.assertEqual(call_count, 1)
