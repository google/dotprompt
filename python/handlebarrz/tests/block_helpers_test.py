# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

import unittest

from handlebarrz import Template


class BlockHelpersTest(unittest.TestCase):
    def test_block_helper_basic(self) -> None:
        """Test basic block helper functionality."""
        template = Template()

        # Register a template with a block helper
        template_str = """{{#with person}}{{firstname}} {{lastname}}{{/with}}"""
        template.register_template('with-test', template_str)

        # Data to render
        data = {'person': {'firstname': 'John', 'lastname': 'Doe'}}

        # Render the template
        result = template.render('with-test', data)
        self.assertEqual(result, 'John Doe')

    def test_block_helper_nested(self) -> None:
        """Test nested block helper functionality."""
        template = Template()

        # Register a template with nested block helpers
        template_str = (
            """{{#with person}}{{firstname}} """
            """{{#with address}}{{city}}, {{state}}{{/with}}{{/with}}"""
        )
        template.register_template('nested-with-test', template_str)

        # Data to render
        data = {
            'person': {
                'firstname': 'John',
                'address': {'city': 'San Francisco', 'state': 'CA'},
            }
        }

        # Render the template
        result = template.render('nested-with-test', data)
        self.assertEqual(result, 'John San Francisco, CA')

    def test_block_helper_with_else(self) -> None:
        """Test block helper with else clause."""
        template = Template()

        # Register a template with an if block helper that has an else
        template_str = (
            """{{#if condition}}True condition{{else}}False condition{{/if}}"""
        )
        template.register_template('if-else-test', template_str)

        # Test true condition
        data_true = {'condition': True}
        result_true = template.render('if-else-test', data_true)
        self.assertEqual(result_true, 'True condition')

        # Test false condition
        data_false = {'condition': False}
        result_false = template.render('if-else-test', data_false)
        self.assertEqual(result_false, 'False condition')
