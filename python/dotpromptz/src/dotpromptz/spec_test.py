from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any

import pytest
import yaml

from dotpromptz.dotprompt import Dotprompt, DotpromptOptions, ToolDefinition

SPEC_DIR = Path('..') / 'spec'


class SpecTest:
    """A test case for a YAML spec."""

    def __init__(
        self,
        desc: str | None = None,
        data: dict[str, Any] | None = None,
        expect: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> None:
        self.desc = desc
        self.data = data
        self.expect = expect
        self.options = options


class SpecSuite:
    """A suite of test cases for a YAML spec."""

    def __init__(
        self,
        name: str,
        template: str,
        data: dict[str, Any] | None = None,
        schemas: dict[str, dict[str, Any]] | None = None,
        tools: dict[str, dict[str, Any]] | None = None,
        partials: dict[str, str] | None = None,
        resolverPartials: dict[str, str] | None = None,
        tests: list[SpecTest] | None = None,
    ) -> None:
        self.name = name
        self.template = template
        self.data = data
        self.schemas = schemas
        self.tools = tools
        self.partials = partials
        self.resolverPartials = resolverPartials
        self.tests = tests


def make_test_function(
    s: SpecSuite,
    tc: SpecTest,
    dotprompt_factory: Callable[[SpecSuite], Any],
) -> Callable[[], Coroutine[Any, Any, None]]:
    @pytest.mark.asyncio
    async def test_function() -> None:
        env = dotprompt_factory(s)

        # Register partials if specified in the suite
        if s.partials:
            for name, template in s.partials.items():
                env.definePartial(name, template)

        # Execute the render with combined data
        result = env.render(
            s.template,
            {**(s.data or {}), **(tc.data or {})},
        )

        # Validate expectations
        if tc.expect:
            # Compare messages
            expected_messages = tc.expect.get('messages', [])
            assert result.get('messages') == expected_messages

            # Compare metadata
            expected_metadata = tc.expect.get('metadata', {})
            assert result.get('metadata') == expected_metadata

            # Compare raw output if specified
            if 'raw' in tc.expect:
                assert result.get('raw') == tc.expect['raw']

    test_function.__name__ = tc.desc or f'test_{s.name}'
    return test_function


def process_spec_file(
    file: Path,
    dotprompt_factory: Callable[[SpecSuite], Any],
) -> None:
    """Processes a single spec file."""
    suite_name = str(file.relative_to(SPEC_DIR)).replace('.yaml', '')
    raw_data = yaml.safe_load(file.read_text(encoding='utf-8'))

    # Convert raw YAML data to SpecSuite objects
    suites = []
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
            resolverPartials=raw_suite.get('resolverPartials'),
            tests=tests,
        )

        suites.append(suite)

    # Dynamically register tests with pytest
    for s in suites:
        for idx, tc in enumerate(s.tests or []):
            test_name = f'test_{suite_name}_{s.name}_{idx}'
            globals()[test_name] = make_test_function(s, tc, dotprompt_factory)


def process_spec_files() -> None:
    """Top level processing, orchestrates the other functions."""
    files = [
        f
        for f in SPEC_DIR.rglob('*')
        if f.is_file() and f.name.endswith('.yaml')
    ]
    for file in files:
        process_spec_file(
            file,
            lambda s: Dotprompt(
                options=DotpromptOptions(
                    schemas=s.schemas,
                    tools=(
                        {
                            name: ToolDefinition(name=name, **data)
                            for name, data in s.tools.items()
                        }
                        if s.tools
                        else None
                    ),
                    partialResolver=(
                        lambda name: s.resolverPartials.get(name)
                        if s.resolverPartials
                        else None
                    ),
                )
            ),
        )


# Entry point for pytest test discovery
process_spec_files()


# Add new test here
@pytest.mark.asyncio
async def test_basic_variable() -> None:
    dp = Dotprompt(
        options=DotpromptOptions()  # Add options if needed
    )

    result = dp.render(
        'Hello {{name}}!',
        {'name': 'World'},
    )

    assert result.get('messages') == [
        {'role': 'user', 'content': [{'text': 'Hello World!'}]}
    ]
