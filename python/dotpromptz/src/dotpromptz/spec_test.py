# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Tests for dotprompt spec files."""

import os
from os import path
from typing import Any, TypedDict

import pytest
import yaml

from dotpromptz import Dotprompt
from dotpromptz.interfaces import DataArgument, JSONSchema, ToolDefinition


class TestCase(TypedDict):
    """Type definition for a test case."""

    desc: str | None
    data: DataArgument
    expect: Any
    options: dict[str, Any]


class SpecSuite(TypedDict):
    """Type definition for a spec suite."""

    name: str
    template: str
    data: DataArgument | None
    schemas: dict[str, JSONSchema] | None
    tools: dict[str, ToolDefinition] | None
    partials: dict[str, str] | None
    resolverPartials: dict[str, str] | None
    tests: list[TestCase]


def load_spec_files() -> list[tuple[str, list[SpecSuite]]]:
    """Load all YAML spec files.

    Returns:
        List of tuples containing (suite_name, list of suites).
    """
    spec_dir = path.join(path.dirname(__file__), '..', '..', '..', '..', 'spec')
    spec_files = []

    for root, _, files in os.walk(spec_dir):
        for file in files:
            if file.endswith('.yaml'):
                file_path = path.join(root, file)
                suite_name = path.join(
                    path.relpath(root, spec_dir), file.replace('.yaml', '')
                )
                with open(file_path, encoding='utf-8') as f:
                    suites: list[SpecSuite] = yaml.safe_load(f)
                spec_files.append((suite_name, suites))

    return spec_files


@pytest.mark.parametrize('suite_name,suites', load_spec_files())
def test_spec_file(suite_name: str, suites: list[SpecSuite]) -> None:
    """Test a spec file.

    Args:
        suite_name: Name of the suite being tested.
        suites: List of suites to test.
    """
    for suite in suites:
        for test_case in suite['tests']:
            # Create test description
            desc = test_case.get('desc', 'should match expected output')
            test_id = f'{suite_name}/{suite["name"]}: {desc}'

            # Create dotprompt environment
            env = Dotprompt(
                options={
                    'schemas': suite.get('schemas'),
                    'tools': suite.get('tools'),
                    'partial_resolver': lambda name: suite.get(
                        'resolverPartials', {}
                    ).get(name),
                }
            )

            # Register partials
            if suite.get('partials'):
                for name, template in suite['partials'].items():
                    env.define_partial(name, template)

            # Run render test
            result = env.render(
                suite['template'],
                (suite.get('data') or {}) | test_case.get('data', {}),
                test_case.get('options', {}),
            )
            raw = result.pop('raw', None)
            expect_raw = test_case['expect'].pop('raw', None)
            test_case['expect'].pop('input', None)  # Discard input

            # Check render result
            expected = test_case['expect'] | {
                'ext': test_case['expect'].get('ext', {}),
                'config': test_case['expect'].get('config', {}),
                'metadata': test_case['expect'].get('metadata', {}),
            }
            assert result == expected, (
                f'{test_id}: render should produce the expected result'
            )

            # Check raw output if specified
            if expect_raw is not None:
                assert raw == expect_raw, f'{test_id}: raw output should match'

            # Run metadata test
            metadata_result = env.render_metadata(
                suite['template'], test_case.get('options', {})
            )
            metadata_raw = metadata_result.pop('raw', None)
            metadata_expect_raw = test_case['expect'].pop('raw', None)
            messages = test_case['expect'].pop('messages', None)

            # Check metadata result
            expected_metadata = test_case['expect'] | {
                'ext': test_case['expect'].get('ext', {}),
                'config': test_case['expect'].get('config', {}),
                'metadata': test_case['expect'].get('metadata', {}),
            }
            assert metadata_result == expected_metadata, (
                f'{test_id}: renderMetadata should produce the expected result'
            )
