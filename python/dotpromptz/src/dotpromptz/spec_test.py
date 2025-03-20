# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""
This module provides utilities for processing specification files, managing test
cases (`SpecTest`), and test suites (`SpecSuite`), as well as synchronization of
partial resolvers.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
import structlog
import yaml

from .dotprompt import Dotprompt, DotpromptOptions
from .typing import DataArgument, ToolDefinition

logger = structlog.get_logger()

SPEC_DIR = Path('..') / 'spec'

SPEC_DIR = SPEC_DIR.resolve()


@dataclass
class SpecTest:
    """
    Dataclass representing a specification test.

    Attributes:
        desc: An optional string providing a description of the test.
        data: An optional dictionary containing input data for the test.
        expect: An optional dictionary specifying expected output or results of the test.
        options: An optional dictionary specifying additional options or configurations for the test.
    """

    desc: str | None = None
    data: dict[str, Any] | None = None
    expect: dict[str, Any] | None = None
    options: dict[str, Any] | None = None


@dataclass
class SpecSuite:
    """Collection of test cases for a template."""

    name: str
    template: str
    data: dict[str, Any] | None = None
    schemas: dict[str, dict[str, Any]] | None = None
    tools: dict[str, dict[str, Any]] | None = None
    partials: dict[str, str] | None = None
    resolver_partials: dict[str, str] | None = None
    tests: list[SpecTest] | None = None


def process_spec_file(
    filepath: Path,
    dotprompt_factory: Callable[[SpecSuite], Dotprompt],
) -> None:
    """Process individual YAML spec filepath.

    Args:
        filepath: Path to the YAML spec filepath.
        dotprompt_factory: Factory function to create Dotprompt instances.
    """
    try:
        logger.info('Processing spec filepath', filepath=str(filepath))
        raw_data = yaml.safe_load(filepath.read_text(encoding='utf-8'))
        logger.info(
            'Found test suites', count=len(raw_data), file_name=filepath.name
        )
        suite_name = filepath.relative_to(SPEC_DIR).stem
        suites: list[SpecSuite] = []

        for raw_suite in raw_data:
            tests = [
                SpecTest(
                    desc=test.get('desc'),
                    data=test.get('data'),
                    expect=test.get('expect'),
                    options=test.get('options'),
                )
                for test in raw_suite.get('tests', [])
            ]

            suite = SpecSuite(
                name=raw_suite['name'],
                template=raw_suite['template'],
                data=raw_suite.get('data'),
                schemas=raw_suite.get('schemas'),
                tools=raw_suite.get('tools'),
                partials=raw_suite.get('partials'),
                resolver_partials=raw_suite.get('resolver_partials'),
                tests=tests,
            )

            suites.append(suite)

        for s in suites:
            for idx, tc in enumerate(s.tests or []):
                test_name = f'test_{suite_name}_{s.name}_{idx}'
                globals()[test_name] = make_test_function(
                    s, tc, dotprompt_factory
                )
    except yaml.YAMLError as ye:
        pytest.fail(f'YAML error in {filepath.name}: {str(ye)}')
    except Exception as e:
        pytest.fail(f'Error processing {filepath.name}: {str(e)}')


def make_test_function(
    s: SpecSuite,
    tc: SpecTest,
    dotprompt_factory: Callable[[SpecSuite], Dotprompt],
) -> Callable[[], None]:
    """Generate pytest test function from spec

    Args:
        s: Test suite specification
        tc: Individual test case
        dotprompt_factory: Factory function to create Dotprompt instances

    Returns:
        Async test function for pytest
    """

    def test_function() -> None:
        env = dotprompt_factory(s)
        env.resolve_partials(s.template)

        if s.partials:
            for name, template in s.partials.items():
                env.define_partial(name, template)

        # Type-safe data construction
        render_data: DataArgument[Any] = cast(
            DataArgument[Any],
            {
                **(s.data or {}),
                **(tc.data or {}),
            },
        )

        # render result
        result = env.render(s.template, render_data)

        if tc.expect:
            # Convert Message objects to dictionaries for comparison
            result_dict = [
                {
                    'role': msg.role.value
                    if hasattr(msg, 'role')
                    else msg.role,
                    'content': [
                        {'text': part.text}
                        if hasattr(part, 'text')
                        else {'media': part.metadata}
                        if hasattr(part, 'metadata')
                        and part.metadata
                        and 'contentType' in part.metadata
                        else part
                        for part in (
                            msg.content
                            if hasattr(msg, 'content')
                            else msg.content
                        )
                    ],
                }
                for msg in result.messages
            ]

            assert result_dict == tc.expect.get('messages', []), (
                f'Messages mismatch in {tc.desc}'
            )
            assert result.metadata == tc.expect.get('metadata', {}), (
                f'Metadata mismatch in {tc.desc}'
            )
            if 'raw' in tc.expect:
                assert result.raw == tc.expect['raw'], (
                    f'Raw output mismatch in {tc.desc}'
                )

    test_function.__name__ = tc.desc or f'test_{s.name}'
    return test_function


def sync_partial_resolver(
    resolver_partials: dict[str, str] | None,
) -> Callable[[str], str | None] | None:
    """Create synchronous partial resolver

    Args:
        resolver_partials: Dictionary mapping partial names to content

    Returns:
        Resolver function or None if no partials provided
    """
    if not resolver_partials:
        return None

    return lambda name: resolver_partials.get(name)


def process_spec_files() -> None:
    """Process all spec files in the spec directory"""
    try:
        # Get absolute path to spec directory
        logger.info('SPEC_DIR absolute path', path=str(SPEC_DIR.resolve()))
        logger.info('SPEC_DIR exists', exists=SPEC_DIR.exists())
        spec_path = SPEC_DIR.resolve()
        logger.info('Looking for spec files', path=str(spec_path))

        filepaths = [f for f in spec_path.rglob('*.yaml') if f.is_file()]

        logger.info('Found spec files', count=len(filepaths))
        for filepath in filepaths:
            logger.info('Processing filepath', filepath=str(filepath))
            process_spec_file(
                filepath,
                lambda s: Dotprompt(
                    options=DotpromptOptions(
                        schemas=s.schemas,
                        tools=(
                            {
                                name: ToolDefinition(name=name, **data)
                                for name, data in (s.tools or {}).items()
                            }
                            if s.tools
                            else None
                        ),
                        partial_resolver=sync_partial_resolver(
                            s.resolver_partials
                        ),
                    ),
                ),
            )
    except Exception as e:
        pytest.fail(f'Failed to load spec tests: {str(e)}')


process_spec_files()
