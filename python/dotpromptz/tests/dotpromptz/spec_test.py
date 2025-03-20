# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Spec test runner."""

from __future__ import annotations

import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

import structlog
import yaml

from dotpromptz.typing import DataArgument, JsonSchema, ToolDefinition

logger = structlog.get_logger(__name__)


class Expect(TypedDict, total=False):
    config: bool
    ext: bool
    input: bool
    messages: bool
    metadata: bool
    raw: bool


class SpecTest(TypedDict, total=False):
    desc: str
    data: DataArgument[Any]
    expect: Expect
    options: dict[str, Any]


class SpecSuite(TypedDict, total=False):
    """Specification test suite definition."""

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


def create_spec_suites(filepath: Path) -> list[SpecSuite]:
    """Create a list of spec suites from a spec file.

    Args:
        filepath: The file to process.

    Returns:
        A list of spec suites.
    """
    with open(filepath) as f:
        data = yaml.safe_load(f)
    return [SpecSuite(**suite) for suite in data]  # type: ignore[typeddict-item]


def is_allowed_spec_file(file: Path) -> bool:
    """Check if a spec file is allowed.

    Args:
        file: The file to check.

    Returns:
        True if the file is allowed, False otherwise.
    """
    allowed_files = {
        #'metadata.yaml',
        #'picoschema.yaml',
        #'partials.yaml',
        #'variables.yaml',
        'role.yaml',
        'unlessEquals.yaml',
        'history.yaml',
        'section.yaml',
        'json.yaml',
        'ifEquals.yaml',
        'media.yaml',
    }
    return file.name.endswith('.yaml') and file.name in allowed_files


def enlist_spec_files(
    directory: Path,
    glob: str = '**/*.yaml',
    filter: Callable[[Path], bool] = lambda p: True,
) -> list[Path]:
    """Filter spec files.

    Args:
        directory: The directory to process.
        glob: The glob pattern to use to find spec files.
        filter: A filter function to apply to each spec file.

    Returns:
        List of spec files that match the glob and filter.
    """
    return [file for file in directory.glob(glob) if filter(file)]


def create_test_suites(
    directory: Path,
    glob: str = '**/*.yaml',
    filter: Callable[[Path], bool] = lambda p: True,
) -> list[SpecSuite]:
    """Create test suites from spec files in the given directory.

    Args:
        directory: The directory to process.
        glob: The glob pattern to use to find spec files.
        filter: A filter function to apply to each spec file.

    Returns:
        A list of spec suites.
    """
    suites = []
    for file in enlist_spec_files(directory, glob, filter):
        suites.extend(create_spec_suites(file))
    return suites


class TestSpecLocation(unittest.TestCase):
    def test_spec_path(self) -> None:
        self.assertTrue(SPECS_DIR.exists())
        self.assertTrue(SPECS_DIR.is_dir())

    def test_spec_path_contains_yaml_files(self) -> None:
        self.assertTrue(list(SPECS_DIR.glob('**/*.yaml')))

    def test_spec_files_are_valid(self) -> None:
        for file in SPECS_DIR.glob('**/*.yaml'):
            with open(file) as f:
                data = yaml.safe_load(f)
                print(data)

    def test_spec_files_set(self) -> None:
        files = list(SPECS_DIR.glob('**/*.yaml'))
        names = [file.name for file in files]
        expected = [
            'history.yaml',
            'ifEquals.yaml',
            'json.yaml',
            'media.yaml',
            'metadata.yaml',
            'partials.yaml',
            'picoschema.yaml',
            'role.yaml',
            'section.yaml',
            'unlessEquals.yaml',
            'variables.yaml',
        ]

        names.sort()
        expected.sort()

        self.assertEqual(len(files), 11)
        self.assertEqual(names, expected)


if __name__ == '__main__':
    from pprint import pprint

    logger.info('Running spec tests')
    logger.info(
        'Locations:',
        current_file=CURRENT_FILE,
        root_dir=ROOT_DIR,
        specs_dir=SPECS_DIR,
    )
    pprint(enlist_spec_files(SPECS_DIR, filter=is_allowed_spec_file))
    pprint(create_test_suites(SPECS_DIR, filter=is_allowed_spec_file))
    unittest.main()
