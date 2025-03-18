# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

import asyncio
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, cast

import pytest
import yaml

from .dotprompt import Dotprompt, DotpromptOptions
from .typing import DataArgument, RenderedPrompt, ToolDefinition

# In spec_test.py
SPEC_DIR = Path(__file__).parent.parent.parent.parent / "spec"


class SpecTest:
    """Individual test case specification"""

    def __init__(
        self,
        desc: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        expect: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.desc = desc
        self.data = data
        self.expect = expect
        self.options = options


class SpecSuite:
    """Collection of test cases for a template"""

    def __init__(
        self,
        name: str,
        template: str,
        data: Optional[Dict[str, Any]] = None,
        schemas: Optional[Dict[str, Dict[str, Any]]] = None,
        tools: Optional[Dict[str, Dict[str, Any]]] = None,
        partials: Optional[Dict[str, str]] = None,
        resolver_partials: Optional[Dict[str, str]] = None,
        tests: Optional[List[SpecTest]] = None,
    ) -> None:
        self.name = name
        self.template = template
        self.data = data
        self.schemas = schemas
        self.tools = tools
        self.partials = partials
        self.resolver_partials = resolver_partials
        self.tests = tests


def process_spec_file(
    file: Path,
    dotprompt_factory: Callable[[SpecSuite], Dotprompt],
) -> None:
    """Process individual YAML spec file"""
    try:
        print(f"\nProcessing spec file: {file}")
        raw_data = yaml.safe_load(file.read_text(encoding='utf-8'))
        print(f"Found {len(raw_data)} test suites in {file.name}")
        suite_name = file.relative_to(SPEC_DIR).stem

        suites: List[SpecSuite] = []
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
                globals()[test_name] = make_test_function(s, tc, dotprompt_factory)
    except yaml.YAMLError as ye:
        pytest.fail(f"YAML error in {file.name}: {str(ye)}")

    except Exception as e:
        pytest.fail(f"Error processing {file.name}: {str(e)}")


def make_test_function(
    s: SpecSuite,
    tc: SpecTest,
    dotprompt_factory: Callable[[SpecSuite], Dotprompt],
) -> Callable[[], Coroutine[Any, Any, None]]:
    """Generate pytest test function from spec"""

    @pytest.mark.asyncio
    async def test_function() -> None:
        env = dotprompt_factory(s)
        # Handle async resolution with type hint
        await env.resolve_partials(s.template)  # type: ignore[func-returns-value]

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

        # Type-annotate the awaitable render result
        result: Dict[str, Any] = cast(
            Dict[str, Any],
            await env.render(s.template, render_data),  # type: ignore[misc]
        )

        if tc.expect:
            # Direct dictionary access
            assert result.get('messages') == tc.expect.get('messages', []), \
                f'Messages mismatch in {tc.desc}'
            assert result.get('metadata') == tc.expect.get('metadata', {}), \
                f'Metadata mismatch in {tc.desc}'
            if 'raw' in tc.expect:
                assert result.get('raw') == tc.expect['raw'], \
                    f'Raw output mismatch in {tc.desc}'

    test_function.__name__ = tc.desc or f'test_{s.name}'
    return test_function


def sync_partial_resolver(
    resolver_partials: Optional[Dict[str, str]],
) -> Optional[Callable[[str], Optional[str]]]:
    """Create synchronous partial resolver"""
    if not resolver_partials:
        return None
    return lambda name: resolver_partials.get(name)


def process_spec_files() -> None:
    """Process all spec files in the spec directory"""
    try:
        # Get absolute path to spec directory
        print(f"SPEC_DIR absolute path: {SPEC_DIR.resolve()}")
        print(f"SPEC_DIR exists: {SPEC_DIR.exists()}")
        spec_path = SPEC_DIR.resolve()
        print(f"Looking for spec files in: {spec_path}")  # Debugging

        files = [
            f for f in spec_path.rglob('*.yaml')
            if f.is_file()
        ]

        print(f"Found {len(files)} spec files")  # Debugging

        for file in files:
            print(f"Processing: {file}")  # Debugging
            process_spec_file(
                file,
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
                            s.resolver_partials),
                    ),
                ),
            )

    except Exception as e:
        pytest.fail(f"Failed to load spec tests: {str(e)}")


# Initialize tests during module import
process_spec_files()


