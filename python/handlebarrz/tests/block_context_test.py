# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

import unittest

from handlebarrz import Template


class BlockContextTest(unittest.TestCase):
    def test_partial_with_blocks(self) -> None:
        """Test partial templates with inline blocks."""
        template = Template()

        # Using inline partials.
        template_str = (
            """{{#*inline "test"}}{{b}};{{/inline}}"""
            """{{#each a as |z|}}{{> test z}}{{/each}}"""
        )
        template.register_template('partial-blocks', template_str)

        data = {'a': [{'b': 1}, {'b': 2}]}

        result = template.render('partial-blocks', data)
        self.assertEqual(result, '1;2;')

    def test_root_with_blocks(self) -> None:
        """Test accessing root context from within blocks."""
        template = Template()

        template_str = (
            """{{#*inline "test"}}{{b}}:{{@root.b}};{{/inline}}"""
            """{{#each a}}{{> test}}{{/each}}"""
        )
        template.register_template('root-blocks', template_str)

        data = {'a': [{'b': 1}, {'b': 2}], 'b': 3}

        result = template.render('root-blocks', data)
        self.assertEqual(result, '1:3;2:3;')

    def test_singular_and_pair_block_params(self) -> None:
        """Test block parameters in different formats."""
        template = Template()

        template_str = (
            """{{#each items as |b index|}}{{b.value}}"""
            """{{#each this as |value key|}}:{{key}},{{/each}}"""
            """{{/each}}"""
        )
        template.register_template('block-params', template_str)

        data = {'items': [{'value': 11}, {'value': 22}]}

        result = template.render('block-params', data)
        self.assertEqual(result, '11:value,22:value,')

    def test_nested_each(self) -> None:
        """Test nested each blocks with complex data."""
        template = Template()

        template_str = (
            """{{#each classes as |class|}}"""
            """{{#each class.methods as |method|}}"""
            """{{method.id}};{{/each}}{{/each}}"""
        )
        template.register_template('nested-each', template_str)

        data = {
            'classes': [
                {'methods': [{'id': 1}, {'id': 2}]},
                {'methods': [{'id': 3}, {'id': 4}]},
            ]
        }

        result = template.render('nested-each', data)
        self.assertEqual(result, '1;2;3;4;')

    def test_referencing_block_param_from_upper_scope(self) -> None:
        """Test accessing parameters from parent scopes."""
        template = Template()

        template_str = (
            """{{#each classes as |class|}}"""
            """{{#each class.methods as |method|}}"""
            """{{class.private}}|{{method.id}};{{/each}}{{/each}}"""
        )
        template.register_template('param-scope', template_str)

        data = {
            'classes': [
                {'methods': [{'id': 1}, {'id': 2}], 'private': False},
                {'methods': [{'id': 3}, {'id': 4}], 'private': True},
            ]
        }

        result = template.render('param-scope', data)
        self.assertEqual(result, 'false|1;false|2;true|3;true|4;')

    def test_nested_path_lookup(self) -> None:
        """Test looking up nested paths in block parameters."""
        template = Template()

        template_str = (
            """{{#each classes as |class|}}{{#with class as |cls|}}"""
            """{{#each cls.methods}}{{../private}}:{{id}},{{/each}}"""
            """{{/with}}{{/each}}"""
        )
        template.register_template('nested-path', template_str)

        data = {
            'classes': [
                {'methods': [{'id': 1}, {'id': 2}], 'private': False},
                {'methods': [{'id': 3}, {'id': 4}], 'private': True},
            ]
        }

        result = template.render('nested-path', data)
        self.assertEqual(result, 'false:1,false:2,true:3,true:4,')
