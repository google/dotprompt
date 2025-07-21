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

import asyncio
import re
import unittest
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, Generic, TypedDict

import structlog
import yaml
from pydantic import BaseModel, Field

from dotpromptz.dotprompt import Dotprompt
from dotpromptz.typing import (
    DataArgument,
    JsonSchema,
    Message,
    ModelConfigT,
    PromptInputConfig,
    PromptMetadata,
    PromptOutputConfig,
    ToolDefinition,
)

logger = structlog.get_logger(__name__)


CURRENT_FILE = Path(__file__)
ROOT_DIR = CURRENT_FILE.parent.parent.parent.parent.parent
SPECS_DIR = ROOT_DIR / 'spec'

# List of files that are allowed to be used as spec files.
# Useful for debugging and testing.
ALLOWLISTED_FILES = [
    'spec/helpers/history.yaml',
    'spec/helpers/ifEquals.yaml',
    'spec/helpers/json.yaml',
    'spec/helpers/media.yaml',
    'spec/helpers/role.yaml',
    'spec/helpers/unlessEquals.yaml',
    'spec/helpers/section.yaml',
    'spec/variables.yaml',
    'spec/partials.yaml',
    'spec/picoschema.yaml',
    'spec/metadata.yaml',
]

# Counters for test class and test method names.
suite_counter = 0
test_case_counter = 0


class Expect(BaseModel):
    """An expectation for the spec."""

    config: dict[Any, Any] = Field(default_factory=dict)
    ext: dict[str, dict[str, Any]] = Field(default_factory=dict)
    input: PromptInputConfig | None = None
    output: PromptOutputConfig | None = None
    messages: list[Message] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] | None = None


class SpecTest(BaseModel, Generic[ModelConfigT]):
    """A test case for a YAML spec."""

    desc: str = Field(default='UnnamedTest')
    data: DataArgument[Any] | None = None
    expect: Expect
    options: PromptMetadata[ModelConfigT] | None = None


class SpecSuite(BaseModel, Generic[ModelConfigT]):
    """A suite of test cases for a YAML spec."""

    name: str = Field(default='UnnamedSuite')
    template: str
    data: DataArgument[Any] | None = None
    schemas: dict[str, JsonSchema] | None = None
    tools: dict[str, ToolDefinition] | None = None
    partials: dict[str, str] = Field(default_factory=dict)
    resolver_partials: dict[str, str] = Field(default_factory=dict, alias='resolverPartials')
    tests: list[SpecTest[ModelConfigT]] = Field(default_factory=list)


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
    """Sanitizes a name component for use in a Python identifier.

    Args:
        name: The name to sanitize.

    Returns:
        A sanitized name.
    """
    name_str = str(name) if name is not None else 'None'
    name_str = re.sub(r'[^a-zA-Z0-9_]', '_', name_str)
    if name_str and name_str[0].isdigit():
        name_str = '_' + name_str
    return name_str or 'unnamed_component'


def make_test_method_name(yaml_file_name: str, suite_name: str | None, test_desc: str | None) -> str:
    """Creates a sanitized test method name.

    Args:
        yaml_file_name: The name of the YAML file.
        suite_name: The name of the suite.
        test_desc: The description of the test.

    Returns:
        A sanitized test method name.
    """
    file_part = sanitize_name_component(yaml_file_name.replace('.yaml', ''))
    suite_part = sanitize_name_component(suite_name)
    desc_part = sanitize_name_component(test_desc)
    return f'test_{file_part}_{suite_part}_{desc_part}_'


def make_test_class_name(yaml_file_name: str, suite_name: str | None) -> str:
    """Creates a sanitized test class name for a suite.

    Args:
        yaml_file_name: The name of the YAML file.
        suite_name: The name of the suite.

    Returns:
        A sanitized test class name.
    """
    file_part = sanitize_name_component(yaml_file_name.replace('.yaml', ''))
    suite_part = sanitize_name_component(suite_name)
    return f'Test_{file_part}_{suite_part}Suite'


def make_dotprompt_for_suite(suite: SpecSuite[ModelConfigT]) -> Dotprompt:
    """Constructs and sets up a Dotprompt instance for the given suite.

    Args:
        suite: The suite to construct a Dotprompt for.

    Returns:
        A Dotprompt instance.
    """
    resolver_partials_from_suite: dict[str, str] = suite.resolver_partials

    def partial_resolver_fn(name: str) -> str | None:
        return resolver_partials_from_suite.get(name)

    dotprompt = Dotprompt(
        schemas=suite.schemas,
        tools=suite.tools,
        partial_resolver=partial_resolver_fn if suite.resolver_partials else None,
    )

    # Register partials directly defined in the suite
    defined_partials: dict[str, str] = suite.partials
    for name, template_content in defined_partials.items():
        dotprompt.define_partial(name, template_content)

    return dotprompt


class TestSpecFiles(unittest.IsolatedAsyncioTestCase):
    """Runs essential checks to ensure the spec directory is valid."""

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
            with open(file) as f:
                data = yaml.safe_load(f)
                self.assertIsNotNone(data)


class YamlSpecTestBase(unittest.IsolatedAsyncioTestCase, Generic[ModelConfigT]):
    """A base class that is used as a template for all YAML spec test suites."""

    async def run_yaml_test(
        self, yaml_file: Path, suite: SpecSuite[ModelConfigT], test_case: SpecTest[ModelConfigT]
    ) -> None:
        """Runs a YAML test.

        Args:
            yaml_file: The path to the YAML file.
            suite: The suite to run the test on.
            test_case: The test case to run.

        Returns:
            None.
        """
        logger.info(f'[TEST] {yaml_file.stem} > {suite.name} > {test_case.desc}')

        # Create test-specific dotprompt instance.
        dotprompt = make_dotprompt_for_suite(suite)
        self.assertIsNotNone(dotprompt)

        data = self._merge_data(suite.data or DataArgument[Any](), test_case.data or DataArgument[Any]())
        result = await dotprompt.render(suite.template, data, test_case.options)
        pruned_res: Expect = Expect(**result.model_dump())

        # Only compare raw if the spec demands it.
        if test_case.expect.raw is None:
            pruned_res.raw = None

        self.assertEqual(pruned_res, test_case.expect)

    def _merge_data(self, data1: DataArgument[Any], data2: DataArgument[Any]) -> DataArgument[Any]:
        merged = DataArgument[Any]()
        merged.input = data1.input or data2.input
        merged.docs = (data1.docs or []) + (data2.docs or [])
        merged.messages = (data1.messages or []) + (data2.messages or [])
        merged.context = {**(data1.context or {}), **(data2.context or {})}
        return merged


def make_suite_class_name(yaml_file: Path, suite_name: str | None) -> str:
    """Creates a class name for a suite.

    Args:
        yaml_file: The path to the YAML file.
        suite_name: The name of the suite.

    Returns:
        A class name for the suite.
    """
    global suite_counter
    suite_counter += 1
    file_part = sanitize_name_component(yaml_file.stem)
    suite_part = sanitize_name_component(suite_name)
    return f'Test_{file_part}_{suite_part}Suite_{suite_counter}'


def make_test_case_name(yaml_file: Path, suite_name: str, test_desc: str) -> str:
    """Creates a test case name.

    Args:
        yaml_file: The path to the YAML file.
        suite_name: The name of the suite.
        test_desc: The description of the test.

    Returns:
        A test case name.
    """
    global test_case_counter
    test_case_counter += 1
    file_part = sanitize_name_component(yaml_file.stem)
    suite_part = sanitize_name_component(suite_name)
    test_method_part = sanitize_name_component(test_desc)
    return f'test_{file_part}_{suite_part}_{test_method_part}_{test_case_counter}'


def make_async_test_case_method(
    yaml_file: Path,
    suite: SpecSuite[ModelConfigT],
    test_case: SpecTest[ModelConfigT],
) -> Callable[[YamlSpecTestBase[ModelConfigT]], Coroutine[Any, Any, None]]:
    """Creates an async test method for a test case.

    Args:
        yaml_file: The path to the YAML file.
        suite: The suite to create the test method for.
        test_case: The test case to create the test method for.

    Returns:
        An async test method.
    """

    async def test_method(self_dynamic: YamlSpecTestBase[ModelConfigT]) -> None:
        """An async test method."""
        await self_dynamic.run_yaml_test(yaml_file, suite, test_case)

    return test_method


def make_async_skip_test_method(
    yaml_file: Path, suite_name: str
) -> Callable[[YamlSpecTestBase[ModelConfigT]], Coroutine[Any, Any, None]]:
    """Creates a skip test for a suite.

    Args:
        yaml_file: The path to the YAML file.
        suite_name: The name of the suite.

    Returns:
        A skip test.
    """

    async def skip_method(self_dynamic: YamlSpecTestBase[ModelConfigT]) -> None:
        self_dynamic.skipTest(f"Suite '{suite_name}' in {yaml_file.stem} has no tests.")

    return skip_method


def generate_test_suites(files: list[Path]) -> None:
    """Dynamically generates test suite classes and methods from YAML spec files.

    Args:
        files: A list of YAML spec files to generate test suites from.

    Returns:
        None.
    """
    module_globals = globals()

    for yaml_file in files:
        if not is_allowed_spec_file(yaml_file):
            logger.warn('Skipping non-allowlisted spec file for class generation', file=str(yaml_file))
            continue

        # Load the YAML file and ensure it's valid.
        try:
            with open(yaml_file, encoding='utf-8') as f:
                suites_data = yaml.safe_load(f)
            if not suites_data:
                logger.warn('Skipping spec file with no data', file=str(yaml_file))
                continue
        except yaml.YAMLError as e:
            logger.error('Error loading spec file', file=str(yaml_file), error=e)
            raise

        # Iterate over the suites in the YAML file and ensure it has a name.
        for suite_data in suites_data:
            # Normalize the suite data to ensure it has a name.
            suite = SpecSuite(**suite_data)
            suite.name = suite.name or f'UnnamedSuite_{yaml_file.stem}'

            # Create the dynamic test class for the suite.
            class_name = make_suite_class_name(yaml_file, suite.name)
            klass = type(class_name, (YamlSpecTestBase,), {})

            # Skip the suite if it has no tests.
            if not suite.tests:
                klass.test_empty_suite = make_async_skip_test_method(yaml_file, suite.name)  # type: ignore[attr-defined]

            # Iterate over the tests in the suite and add them to the class.
            for tc in suite.tests:
                # Create the test case method and add it to the class.
                test_case_name = make_test_case_name(yaml_file, suite.name, tc.desc)
                test_method = make_async_test_case_method(yaml_file, suite, tc)
                setattr(klass, test_case_name, test_method)

            # Add the test suite class to the module globals.
            module_globals[class_name] = klass


generate_test_suites(list(SPECS_DIR.glob('**/*.yaml')))

if __name__ == '__main__':
    unittest.main()
