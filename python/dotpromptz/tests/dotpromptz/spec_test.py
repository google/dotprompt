# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Spec test runner."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict
from unicodedata import normalize

import pytest
import structlog
import yaml

from dotpromptz.typing import DataArgument, JsonSchema, ToolDefinition

logger = structlog.get_logger(__name__)


class Expect(TypedDict, total=False):
    """Expected output from a spec test."""

    config: bool
    ext: bool
    input: bool
    messages: bool
    metadata: bool
    raw: bool


class SpecTest(TypedDict, total=False):
    """Specification test definition."""

    desc: str
    data: DataArgument[Any]
    expect: Expect
    options: dict[str, Any]


class SpecSuite(TypedDict, total=False):
    """Specification test suite definition."""

    # These fields are not defined in other spec tests but are here for our
    # convenience.
    module_id: str
    suite_id: str
    location: Path

    # Common fields.
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


def file_digest(filepath: Path, length: int = -1) -> str:
    """Generate a hex-encoded SHA256 hash of a file.

    Args:
        filepath: The file to hash.
        length: The length of the hash to return.

    Returns:
        A hex-encoded SHA256 hash of the file.
    """
    digest = hashlib.sha256(filepath.read_bytes()).hexdigest()
    if length < 0:
        return digest
    if length > len(digest):
        raise ValueError(
            f'Length {length} is greater than the digest length {len(digest)}'
        )
    return digest[:length]


def slugify(text: str, chars: str = r' /\\:;,.?!@#$%^&*()[]{}|<>+="\'') -> str:
    """Slugify a path component.

    Replaces special characters found in a path component with an underscore,
    handles Unicode characters, and removes consecutive underscores.

    Args:
        text: The string to slugify.
        chars: The characters to replace.

    Returns:
        A slugified string.
    """
    text = normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    pattern = f'[{re.escape(chars)}]+'
    text = re.sub(pattern, '_', text)
    text = text.strip('_')
    text = re.sub('_+', '_', text)
    return text.lower()


def generate_module_id(root_dir: Path, filepath: Path) -> str:
    """Generate a unique ID for a spec module.

    Args:
        root_dir: The root directory of the project.
        filepath: The file to generate an ID for.

    Returns:
        A unique ID for the spec module.
    """
    if not filepath.exists():
        raise FileNotFoundError(f'File {filepath} does not exist')
    digest = file_digest(filepath, 8)
    fname = filepath.relative_to(root_dir).name
    slug = slugify(fname)
    return f'{slug}_{digest}'


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


def create_spec_suites_for(filepath: Path, module_id: str) -> list[SpecSuite]:
    """Create a list of spec suites from a spec file.

    Args:
        filepath: The file to process.
        module_id: The ID of the module.

    Returns:
        A list of spec suites.
    """
    with open(filepath) as f:
        data = yaml.safe_load(f)
    suites = []
    for suite in data:
        suite['module_id'] = module_id
        suite['location'] = filepath
        name_slug = slugify(suite['name'])
        suite['suite_id'] = f'{module_id}_{name_slug}'
        suites.append(SpecSuite(**suite))  # type: ignore[typeddict-item]
    return suites


def create_spec_suites(
    directory: Path,
    glob: str = '**/*.yaml',
    filter: Callable[[Path], bool] = lambda p: True,
) -> list[SpecSuite]:
    """Create test suites from spec files in the given directory.

    The test suites are grouped by the spec file name.

    Args:
        directory: The directory to process.
        glob: The glob pattern to use to find spec files.
        filter: A filter function to apply to each spec file.

    Returns:
        A list of spec suites.
    """
    suites: list[SpecSuite] = []
    for file in enlist_spec_files(directory, glob, filter):
        module_id = generate_module_id(directory, file)
        spec_suites = create_spec_suites_for(file, module_id=module_id)
        suites.extend(spec_suites)
    return suites


def test_spec_path() -> None:
    """Test that the spec directory exists."""
    assert SPECS_DIR.exists()
    assert SPECS_DIR.is_dir()


def test_spec_path_contains_yaml_files() -> None:
    """Test that the spec directory contains YAML files."""
    assert list(SPECS_DIR.glob('**/*.yaml'))


def test_spec_files_are_valid() -> None:
    """Test that all spec files contain valid YAML."""
    for file in SPECS_DIR.glob('**/*.yaml'):
        with open(file) as f:
            data = yaml.safe_load(f)
            assert data is not None


def test_spec_files_set() -> None:
    """Test that the expected set of spec files exists."""
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

    assert len(files) == 11
    assert names == expected


@pytest.fixture(scope='session')
def all_spec_suites() -> list[SpecSuite]:
    """Create test suites from spec files in the given directory."""
    return create_spec_suites(SPECS_DIR, filter=is_allowed_spec_file)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate tests dynamically from spec files."""
    if (
        'spec_suite' in metafunc.fixturenames
        and 'spec_test' in metafunc.fixturenames
    ):
        suites = create_spec_suites(SPECS_DIR, filter=is_allowed_spec_file)
        tests = [(suite, test) for suite in suites for test in suite['tests']]
        metafunc.parametrize('spec_suite, spec_test', tests)


@pytest.mark.asyncio
async def test_spec_test_case(
    spec_suite: SpecSuite, spec_test: SpecTest
) -> None:
    """Dynamically generated test case."""
    module_id = spec_suite.get('module_id', 'unknown_module')
    suite_id = spec_suite.get('suite_id', 'unknown_suite')

    await logger.ainfo(
        'Running spec test',
        module_id=module_id,
        suite_id=suite_id,
        test_desc=spec_test.get('desc', 'Unnamed test'),
        suite_name=spec_suite['name'],
        test_data=spec_test.get('data'),
        expected=spec_test.get('expect'),
    )

    # TODO: Implement the core testing logic in a follow up PR.
    # message = (
    #    f'Test not implemented. MODULE_ID={module_id}, SUITE_ID={suite_id}'
    # )
    # raise AssertionError(message)
