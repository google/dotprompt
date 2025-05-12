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

"""Runs specification tests defined in YAML files located in the `spec` directory.

These YAML files define test suites for Dotprompt templates.
The general structure of each YAML file is a list of test suites.

- Each YAML file is a set of test suites.
- Each test suite is a set of tests.
- Each test is a set of expectations.

Each test suite object in the list typically contains the following keys:

| Key                | Type   | Description                                                                          |
|--------------------|--------|--------------------------------------------------------------------------------------|
| `name`             | string | An identifier for this group of tests.                                               |
| `template`         | string | The Dotprompt template content (often multi-line, and may include YAML frontmatter). |
| `tests`            | list   | A list of individual test scenarios. Each scenario object has keys: `desc` (string), |
|                    |        | `data` (object, optional), `expect` (object).                                        |
| `partials`         | object | (Optional) A mapping where keys are partial names and values are the string content  |
|                    |        | of those partials. (e.g., see `partials.yaml`)                                       |
| `resolverPartials` | object | (Optional) Similar to `partials`, but for partials                                   |
|                    |        | that are expected to be provided by a resolver function. (e.g., see `partials.yaml`) |

Each test scenario object (i.e., an item in the `tests` list) has the following keys:

| Key      | Type   | Description                                                         |
|----------|--------|---------------------------------------------------------------------|
| `desc`   | string | A description of the specific test case.                            |
| `data`   | object | (Optional) Input data for the template. This can include `context`, |
|          |        | `input`, or other variables relevant to the template.               |
| `expect` | object | Defines the expected outcome. Common keys include                   |
|          |        | (list), and others corresponding to parsed frontmatter (`config`,   |
|          |        | `model`, `output.schema`, `input.schema`, `ext`, `raw`).            |

The YAML files located in the `spec/helpers` subdirectory also follow this
general structure, but are specifically focused on testing individual helper
functions available within the Dotprompt templating environment.

The structure of the YAML files is as follows:

```
spec/
├── *.yaml (e.g., metadata.yaml, partials.yaml, picoschema.yaml, etc.)
│   └── List of Test Suites
│       └── Test Suite 1
│           ├── name: "suite_name_1"
│           ├── template: "..."
│           ├── partials: { ... } (optional)
│           ├── resolverPartials: { ... } (optional)
│           └── tests:
│               ├── Test Case 1.1
│               │   ├── desc: "description_1.1"
│               │   ├── data: { ... } (optional)
│               │   └── expect: { ... }
│               ├── Test Case 1.2
│               │   ├── desc: "description_1.2"
│               │   ├── data: { ... } (optional)
│               │   └── expect: { ... }
│               └── ... (more test cases)
│       └── Test Suite 2
│           ├── name: "suite_name_2"
│           ├── template: "..."
│           └── tests:
│               ├── Test Case 2.1
│               │   ├── desc: "description_2.1"
│               │   └── expect: { ... }
│               └── ... (more test cases)
│       └── ... (more test suites)
│
└── helpers/
    ├── *.yaml (e.g., history.yaml, json.yaml, ifEquals.yaml, etc.)
    │   └── List of Test Suites (same structure as above)
    │       └── Test Suite H1
    │           ├── name: "helper_suite_name_1"
    │           ├── template: "..."
    │           └── tests:
    │               ├── Test Case H1.1
    │               │   ├── desc: "description_H1.1"
    │               │   └── expect: { ... }
    │               └── ...
    └── ... (more helper spec files)
```
"""

from __future__ import annotations

import logging
import re
import sys
import unittest
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, TypedDict

import structlog
import yaml

from dotpromptz.dotprompt import Dotprompt
from dotpromptz.typing import DataArgument, JsonSchema, PromptMetadata, ToolDefinition

# Configure basic logging to ensure output visibility during tests
logging.basicConfig(
    format='%(levelname)-8s [%(name)s] %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout,
)
# Configure structlog to use stdlib for simplicity in test output
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class Expect(TypedDict, total=False):
    """An expectation for the spec."""

    render: str
    compile: str
    error: str
    raw: bool


class SpecTest(TypedDict, total=False):
    """A test case for a YAML spec."""

    desc: str
    data: Any
    expect: Expect
    options: dict[str, Any]
    # template can also be at the test case level, overriding suite template
    template: str


class SpecSuite(TypedDict, total=False):
    """A suite of test cases for a YAML spec."""

    name: str  # Name of the suite, used for logging and test naming
    suite: str  # Often same as name, or a more specific identifier
    template: str  # Default template for tests in this suite
    data: Any  # Default data for tests in this suite
    schemas: dict[str, JsonSchema]
    tools: dict[str, ToolDefinition]
    partials: dict[str, str]  # Partials directly defined in the suite
    resolver_partials: dict[str, str]  # Partials to be provided by the resolver
    tests: list[SpecTest]


CURRENT_FILE = Path(__file__)
ROOT_DIR = CURRENT_FILE.parent.parent.parent.parent.parent
SPECS_DIR = ROOT_DIR / 'spec'

ALLOWLISTED_FILES = [
    'spec/helpers/history.yaml',
    'spec/helpers/ifEquals.yaml',
    'spec/helpers/json.yaml',
    'spec/helpers/media.yaml',
    'spec/helpers/role.yaml',
    'spec/helpers/section.yaml',
    'spec/helpers/unlessEquals.yaml',
    'spec/metadata.yaml',
    'spec/partials.yaml',
    'spec/picoschema.yaml',
    'spec/variables.yaml',
]


def is_allowed_spec_file(file: Path) -> bool:
    """Check if a spec file is allowed.

    Args:
        file: The file to check.

    Returns:
        True if the file is allowed, False otherwise.
    """
    fname = file.absolute().as_posix()
    for allowed_file in ALLOWLISTED_FILES:
        if fname.endswith(allowed_file):
            return True
    return False


def sanitize_name_component(name: str | None) -> str:
    """Sanitizes a name component for use in a Python identifier."""
    name_str = str(name) if name is not None else 'None'
    name_str = re.sub(r'[^a-zA-Z0-9_]', '_', name_str)
    if name_str and name_str[0].isdigit():
        name_str = '_' + name_str
    return name_str or 'unnamed_component'


def make_test_method_name(yaml_file_name: str, suite_name: str | None, test_desc: str | None) -> str:
    """Creates a sanitized test method name."""
    file_part = sanitize_name_component(yaml_file_name.replace('.yaml', ''))
    suite_part = sanitize_name_component(suite_name)
    desc_part = sanitize_name_component(test_desc)
    return f'test_{file_part}_{suite_part}_{desc_part}_'


def make_test_class_name(yaml_file_name: str, suite_name: str | None) -> str:
    """Creates a sanitized test class name for a suite."""
    file_part = sanitize_name_component(yaml_file_name.replace('.yaml', ''))
    suite_part = sanitize_name_component(suite_name)
    return f'Test_{file_part}_{suite_part}Suite'


def make_dotprompt_for_suite(suite: SpecSuite) -> Dotprompt:
    """Constructs and sets up a Dotprompt instance for the given suite."""
    # Use 'suite' if available, fallback to 'name', then a default
    resolver_partials_from_suite: dict[str, str] = suite.get('resolver_partials', {})

    def partial_resolver_fn(name: str) -> str | None:
        return resolver_partials_from_suite.get(name)

    dotprompt = Dotprompt(
        schemas=suite.get('schemas'),
        tools=suite.get('tools'),
        partial_resolver=partial_resolver_fn if resolver_partials_from_suite else None,
    )

    # Register partials directly defined in the suite
    defined_partials: dict[str, str] = suite.get('partials', {})
    for name, template_content in defined_partials.items():
        dotprompt.define_partial(name, template_content)

    return dotprompt


class TestSpecFiles(unittest.IsolatedAsyncioTestCase):
    """Runs meta-tests for specification files (e.g., existence, validity)."""

    def test_spec_path(self) -> None:
        """Test that the spec directory exists."""
        self.assertTrue(SPECS_DIR.exists())
        self.assertTrue(SPECS_DIR.is_dir())

    def test_spec_path_contains_yaml_files(self) -> None:
        """Test that the spec directory contains YAML files."""
        self.assertTrue(list(SPECS_DIR.glob('**/*.yaml')))

    def test_spec_files_are_valid(self) -> None:
        """Test that all spec files contain valid YAML."""
        for file in SPECS_DIR.glob('**/*.yaml'):
            with open(file, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.assertIsNotNone(data, f'File {file} is not valid YAML or is empty.')


class YamlSpecTestBase(unittest.IsolatedAsyncioTestCase):
    """Base class for dynamically generated YAML spec test suites."""

    yaml_file_path: Path
    current_suite_info: SpecSuite
    current_test_case_info: SpecTest

    async def run_yaml_test(
        self,
        yaml_file: Path,
        suite: SpecSuite,
        test_case: SpecTest,
    ) -> None:
        """Runs a single specification test."""
        dotprompt = make_dotprompt_for_suite(suite)

        suite_name = suite.get('name', 'UnnamedSuite')
        test_desc = test_case.get('desc', 'UnnamedTest')
        template_content = suite.get('template')

        if template_content is None:
            self.fail(f"Suite '{suite_name}' in {yaml_file.name} is missing 'template' content.")
            return

        render_data_dict = {**suite.get('data', {}), **test_case.get('data', {})}
        render_options_dict = test_case.get('options', {})

        try:
            data_arg: DataArgument[Any] = DataArgument(**render_data_dict)
            prompt_meta: PromptMetadata[Any] = PromptMetadata(**render_options_dict)
        except TypeError as e:
            self.fail(
                f'Failed to create DataArgument/PromptMetadata for {yaml_file.name} > {suite_name} > {test_desc}: {e}'
            )
            return

        expectations = test_case.get('expect', {})
        expected_error = expectations.get('error')

        log_details = {
            'yaml_file': yaml_file.name,
            'suite_name': suite_name,
            'test_name': test_desc,
        }
        logger.info(f'[TEST] {yaml_file.name}: {suite_name} > {test_desc}', **log_details)

        # actual_render: str | None = None
        # actual_compile_error: str | None = None
        # actual_metadata: PromptMetadata[Any] | None = None

        if expected_error:
            with self.assertRaises(Exception) as cm:
                await dotprompt.render(
                    template_content,
                    data_arg,
                    prompt_meta,
                )
            self.assertIn(
                expected_error,
                str(cm.exception),
                f"Expected error '{expected_error}' not in '{str(cm.exception)}' for "
                f'{yaml_file.name} > {suite_name} > {test_desc}',
            )
        else:
            # return  # TODO: implement

            try:
                result = await dotprompt.render(
                    template_content,
                    data_arg,
                    prompt_meta,
                )
            except Exception as e:
                self.fail(
                    f'Test {yaml_file.name} > {suite_name} > {test_desc} failed during render (expected no error): {e}'
                )
                return

            expected_content = expectations.get('content')
            if expected_content is not None:
                actual_content = result
                if hasattr(result, 'content'):
                    actual_content = result.content
                elif not isinstance(result, str | list):
                    self.fail(
                        f'Render result type unhandled: {type(result)}. Expected str, list, '
                        f'or obj with .content for {yaml_file.name} > {suite_name} > {test_desc}'
                    )
                    return

                self.assertEqual(
                    actual_content,
                    expected_content,
                    f'Content mismatch for {yaml_file.name} > {suite_name} > {test_desc}',
                )

            expected_pruned_content = expectations.get('pruned_content')
            if expected_pruned_content is not None:
                logger.warn("Assertion for 'pruned_content' is not yet implemented.", **log_details)
                # self.assertEqual(actual_pruned_content, expected_pruned_content)

            expected_metadata_raw = expectations.get('metadata_raw')
            if expected_metadata_raw is not None:
                logger.warn("Assertion for 'metadata_raw' is not yet implemented.", **log_details)
                # self.assertEqual(actual_metadata_raw, expected_metadata_raw)

            expected_pruned_metadata = expectations.get('pruned_metadata')
            if expected_pruned_metadata is not None:
                logger.warn("Assertion for 'pruned_metadata' is not yet implemented.", **log_details)
                # self.assertEqual(actual_pruned_metadata, expected_pruned_metadata)

            expected_metadata_json_schema = expectations.get('metadata_json_schema')
            if expected_metadata_json_schema is not None:
                logger.warn("Assertion for 'metadata_json_schema' is not yet implemented.", **log_details)
                # validate_json_schema(actual_metadata, expected_metadata_json_schema)


def _create_failing_test_method(
    class_name: str, method_name: str, error_message: str
) -> Callable[[YamlSpecTestBase], Coroutine[Any, Any, None]]:
    async def _failing_test(self: YamlSpecTestBase) -> None:
        self.fail(f'Test generation failed for {class_name}.{method_name}: {error_message}')

    return _failing_test


def _create_async_test_method_for_case(
    yaml_file_path_for_case: Path,
    suite_info_for_case: SpecSuite,
    test_case_info_for_case: SpecTest,
) -> Callable[[YamlSpecTestBase], Coroutine[Any, Any, None]]:
    """Creates an async test method for a single test case."""

    async def dynamic_test_method(self_of_dynamic_class: YamlSpecTestBase) -> None:
        """Runs a single test case."""
        await self_of_dynamic_class.run_yaml_test(yaml_file_path_for_case, suite_info_for_case, test_case_info_for_case)

    return dynamic_test_method


def generate_dynamic_test_classes_for_suites() -> None:
    """Dynamically generates test classes and methods from YAML spec files."""
    module_globals = globals()
    generated_class_names: set[str] = set()

    for yaml_file in SPECS_DIR.glob('**/*.yaml'):
        if not is_allowed_spec_file(yaml_file):
            logger.warn('Skipping non-allowlisted spec file for class generation', file=str(yaml_file))
            continue

        try:
            with open(yaml_file, encoding='utf-8') as f:
                suites_data = yaml.safe_load(f)
            if not suites_data:
                logger.warn('Skipping empty spec file for class generation', file=str(yaml_file))
                continue
        except yaml.YAMLError as e:
            method_name = f'test_yaml_parsing_error_{sanitize_name_component(yaml_file.stem)}'
            error_msg = f'Failed to parse YAML file {yaml_file}: {e}'
            test_fn = _create_failing_test_method('TestSpecFiles', method_name, error_msg)
            setattr(TestSpecFiles, method_name, test_fn)
            logger.error(error_msg)
            continue

        for suite_data_raw in suites_data:
            suite: SpecSuite = suite_data_raw
            raw_suite_name = suite.get('name', f'UnnamedSuite_in_{yaml_file.stem}')
            suite['name'] = raw_suite_name

            sanitized_file_prefix = sanitize_name_component(yaml_file.stem)
            sanitized_suite_name = sanitize_name_component(raw_suite_name)
            class_name_base = f'Test_{sanitized_file_prefix}_{sanitized_suite_name}Suite'
            class_name = class_name_base
            counter = 1
            while class_name in generated_class_names:
                class_name = f'{class_name_base}_{counter}'
                counter += 1
            generated_class_names.add(class_name)

            dynamic_class = type(class_name, (YamlSpecTestBase,), {})

            if not suite.get('tests'):

                def create_skip_test_for_suite(
                    s_name: str = raw_suite_name, yf_name: str = yaml_file.name
                ) -> Callable[[YamlSpecTestBase], Coroutine[Any, Any, None]]:
                    async def _skip_empty_suite_test(self_of_dynamic_class: YamlSpecTestBase) -> None:
                        self_of_dynamic_class.skipTest(f"Suite '{s_name}' in {yf_name} has no tests.")

                    return _skip_empty_suite_test

                dynamic_class.test_empty_suite = create_skip_test_for_suite()  # type: ignore[attr-defined]

            for tc_raw in suite.get('tests', []):
                tc: SpecTest = tc_raw
                raw_tc_name = tc.get('desc', f'UnnamedTest_in_{raw_suite_name}')
                tc['desc'] = raw_tc_name

                sanitized_tc_name = sanitize_name_component(raw_tc_name)
                method_name_base = f'test_{sanitized_tc_name}'
                method_name = method_name_base
                m_counter = 1
                while hasattr(dynamic_class, method_name):
                    method_name = f'{method_name_base}_{m_counter}'
                    m_counter += 1

                test_method_fn = _create_async_test_method_for_case(yaml_file, suite, tc)
                setattr(dynamic_class, method_name, test_method_fn)

            module_globals[class_name] = dynamic_class


generate_dynamic_test_classes_for_suites()

if __name__ == '__main__':
    unittest.main()
