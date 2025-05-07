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

import unittest
from pathlib import Path
from typing import Any, TypedDict, cast

import structlog
import yaml

from dotpromptz.dotprompt import Dotprompt
from dotpromptz.typing import DataArgument, JsonSchema, PromptMetadata, ToolDefinition

logger = structlog.get_logger(__name__)


class Expect(TypedDict, total=False):
    """An expectation for the spec."""

    config: bool
    ext: bool
    input: bool
    messages: bool
    metadata: bool
    raw: bool


class SpecTest(TypedDict, total=False):
    """A test case for a YAML spec."""

    desc: str
    data: DataArgument[Any]
    expect: Expect
    options: dict[str, Any]


class SpecSuite(TypedDict, total=False):
    """A suite of test cases for a YAML spec."""

    name: str
    template: str
    data: DataArgument[Any]
    schemas: dict[str, JsonSchema]
    tools: dict[str, ToolDefinition]
    partials: dict[str, str]
    resolver_partials: dict[str, str]
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
    #'spec/partials.yaml',
    #'spec/picoschema.yaml',
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


class TestSpecFiles(unittest.IsolatedAsyncioTestCase):
    """Runs specification tests defined in YAML files."""

    def test_spec_path(self) -> None:
        """Test that the spec directory exists."""
        assert SPECS_DIR.exists()
        assert SPECS_DIR.is_dir()

    def test_spec_path_contains_yaml_files(self) -> None:
        """Test that the spec directory contains YAML files."""
        assert list(SPECS_DIR.glob('**/*.yaml'))

    def test_spec_files_are_valid(self) -> None:
        """Test that all spec files contain valid YAML."""
        for file in SPECS_DIR.glob('**/*.yaml'):
            with open(file) as f:
                data = yaml.safe_load(f)
                assert data is not None

    async def test_specs(self) -> None:
        """Discovers and runs all YAML specification tests."""
        for yaml_file in SPECS_DIR.glob('**/*.yaml'):
            if not is_allowed_spec_file(yaml_file):
                logger.debug(
                    'Skipping spec file',
                    file=yaml_file,
                )
                continue
            with self.subTest(file=yaml_file):
                with open(yaml_file) as f:
                    suites_data = yaml.safe_load(f)

                for suite_data_raw in suites_data:
                    suite: SpecSuite = cast(SpecSuite, suite_data_raw)

                    with self.subTest(suite=suite.get('name', 'UnnamedSuite')):
                        for test_case_data_raw in suite.get('tests', []):
                            test_case: SpecTest = test_case_data_raw

                            with self.subTest(test=test_case.get('desc', 'UnnamedTest')):
                                dotprompt = Dotprompt()
                                await self.run_yaml_test(yaml_file, dotprompt, suite, test_case)

    async def run_yaml_test(
        self,
        yaml_file: Path,
        dotprompt: Dotprompt,
        suite: SpecSuite,
        test_case: SpecTest,
    ) -> None:
        """Runs a single specification test.

        Args:
            yaml_file: The YAML file containing the specification.
            dotprompt: The Dotprompt instance to use.
            suite: The suite to run the test on.
            test_case: The test case to run.

        Returns:
            None
        """
        logger.debug(
            'Running spec test',
            yaml_file=yaml_file,
            suite=suite,
            test=test_case,
        )

        # Define partials if they exist.
        partials: dict[str, str] = suite.get('partials', {})
        for name, template in partials.items():
            dotprompt.define_partial(name, template)

        # TODO: Render the template.
        # data = {**suite.get('data', {}), **test_case.get('data', {})}
        # result = await dotprompt.render(
        #    suite.get('template'),
        #    DataArgument(**data),
        #    PromptMetadata(**test_case.get('options', {})),
        # )

        # TODO: Prune the result and compare to the expected output.
        # TODO: Compare pruned result to the expected output.
        # TODO: Only compare raw if the spec demands it.
        # TODO: Render the metadata.
        # TODO: Compare pruned metadata to the expected output.

        logger.debug(
            'Finished running spec test',
            yaml_file=yaml_file,
            suite=suite,
            test=test_case,
            # result=result,
        )


if __name__ == '__main__':
    unittest.main()
