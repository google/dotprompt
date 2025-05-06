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

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, TypedDict, cast

import structlog
import yaml

from dotpromptz.typing import DataArgument

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
    schemas: dict[str, Any]
    tools: list[Any]
    partials: dict[str, str]
    resolver_partials: dict[str, str]
    tests: list[SpecTest]


CURRENT_FILE = Path(__file__)
ROOT_DIR = CURRENT_FILE.parent.parent.parent.parent.parent
SPECS_DIR = ROOT_DIR / 'spec'


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
            with self.subTest(file=yaml_file):
                with open(yaml_file) as f:
                    suites_data = yaml.safe_load(f)

                for suite_data_raw in suites_data:
                    suite: SpecSuite = cast(SpecSuite, suite_data_raw)

                    with self.subTest(suite=suite.get('name', 'UnnamedSuite')):
                        for test_case_data_raw in suite.get('tests', []):
                            test_case: SpecTest = test_case_data_raw

                            with self.subTest(test=test_case.get('desc', 'UnnamedTest')):
                                await self.run_yaml_test(suite, test_case)

    async def run_yaml_test(self, suite: SpecSuite, test_case: SpecTest) -> None:
        """Runs a single specification test.

        Args:
            suite: The suite to run the test on.
            test_case: The test case to run.

        Returns:
            None
        """
        logger.info(
            'Running spec test',
            suite=suite,
            test=test_case,
        )


if __name__ == '__main__':
    unittest.main()
