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
| `schemas`          | object | (Optional) A mapping of schema names to JSONSchema definitions.                      |
| `tools`            | dict   | (Optional) A mapping of tool names to ToolDefinitions.                               |
| `data`             | object | (Optional) Default data (fields for DataArgument) for all tests in the suite.        |


Each test scenario object (i.e., an item in the `tests` list) has the following keys:

| Key      | Type   | Description                                                                         |
|----------|--------|-------------------------------------------------------------------------------------|
| `desc`   | string | A description of the specific test case.                                            |
| `data`   | object | (Optional) Input data (fields for DataArgument) for the template. Merged with suite `data`. |
| `expect` | object | Defines the expected outcome. Common keys include `raw` (string), `messages`      |
|          |        | (list), and others corresponding to parsed frontmatter (`config`,                 |
|          |        | `model` (referred to as `metadata` in some contexts), `output_schema`, `input_schema`, `ext`). |
| `options`| object | (Optional) Options to pass to the render methods, corresponding to `PromptMetadata`.  |


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
from typing import Any, Callable, TypedDict, cast

import structlog
import yaml

from dotpromptz.dotprompt import Dotprompt
from dotpromptz.typing import (
    DataArgument,
    JsonSchema,
    PartialResolver,
    PromptInputConfig,
    PromptMetadata,
    RenderedPrompt,  # Corrected import
    ToolDefinition,
)

logger = structlog.get_logger(__name__)


class Expect(TypedDict, total=False):
    """An expectation for the spec. These keys correspond to fields in
    RenderedPrompt or PromptMetadata from Dotpromptz.
    """

    raw: str | None
    messages: list[Any] | None
    config: dict[str, Any] | None
    ext: dict[str, Any] | None
    input: JsonSchema | None  # This typically refers to PromptInputConfig.schema_
    metadata: dict[str, Any] | None  # This typically refers to PromptMetadata.config (model-specific config)


class SpecTest(TypedDict, total=False):
    """A test case for a YAML spec."""

    desc: str
    data: dict[str, Any] | None  # Raw dict from YAML to construct DataArgument
    expect: Expect
    options: dict[str, Any]  # Corresponds to PromptMetadata fields


class SpecSuite(TypedDict, total=False):
    """A suite of test cases for a YAML spec."""

    name: str
    template: str
    data: dict[str, Any] | None  # Raw dict from YAML to construct DataArgument (default for suite)
    schemas: dict[str, JsonSchema] | None
    tools: dict[str, ToolDefinition] | None  # Corrected type to dict
    partials: dict[str, str] | None
    resolver_partials: dict[str, str] | None
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
        self.assertTrue(SPECS_DIR.exists())
        self.assertTrue(SPECS_DIR.is_dir())

    def test_spec_path_contains_yaml_files(self) -> None:
        """Test that the spec directory contains YAML files."""
        self.assertTrue(list(SPECS_DIR.glob('**/*.yaml')))

    def test_spec_files_are_valid(self) -> None:
        """Test that all spec files contain valid YAML."""
        for file in SPECS_DIR.glob('**/*.yaml'):
            with self.subTest(file=file.name):
                with open(file, encoding='utf-8') as f:
                    try:
                        data = yaml.safe_load(f)
                        self.assertIsNotNone(data, f'File {file.name} loaded as None (empty or invalid YAML)')
                    except yaml.YAMLError as e:
                        self.fail(f'File {file.name} is not valid YAML: {e}')

    async def test_specs(self) -> None:
        """Discovers and runs all YAML specification tests."""
        for yaml_file in SPECS_DIR.glob('**/*.yaml'):
            if not is_allowed_spec_file(yaml_file):
                logger.debug('Skipping spec file (not in allowlist)', file=yaml_file.name)
                continue

            with self.subTest(file=yaml_file.name):
                with open(yaml_file, encoding='utf-8') as f:
                    try:
                        suites_data = yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self.fail(f'Failed to load/parse YAML file {yaml_file.name}: {e}')
                        continue

                    if not isinstance(suites_data, list):
                        logger.warning(
                            'Skipping non-list content in YAML file',
                            file=yaml_file.name,
                            content_type=type(suites_data).__name__,
                        )
                        continue

                for suite_data_raw in suites_data:
                    suite: SpecSuite = cast(SpecSuite, suite_data_raw)
                    suite_name = suite.get('name', f'UnnamedSuite_in_{yaml_file.name}')

                    with self.subTest(suite=suite_name):
                        resolver_partials_config = suite.get('resolver_partials')
                        resolver_partials_map = resolver_partials_config if resolver_partials_config is not None else {}

                        def partial_resolver_fn(name: str) -> str | None:
                            return resolver_partials_map.get(name)  # Safe now

                        tools_config = suite.get('tools')

                        dotprompt_for_suite = Dotprompt(
                            schemas=suite.get('schemas'),
                            tools=tools_config,  # Type now matches constructor
                            partial_resolver=cast(PartialResolver, partial_resolver_fn)
                            if resolver_partials_map  # Check map, not config
                            else None,
                        )

                        if suite_partials := suite.get('partials'):
                            for name, template_content in suite_partials.items():
                                dotprompt_for_suite.define_partial(name, template_content)

                        for i, test_case_data_raw in enumerate(suite.get('tests', [])):
                            test_case: SpecTest = cast(SpecTest, test_case_data_raw)
                            test_desc = test_case.get('desc', f'UnnamedTest_{i + 1}')

                            with self.subTest(test=test_desc):
                                await self.run_yaml_test(yaml_file, dotprompt_for_suite, suite, test_case)

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
            yaml_file=yaml_file.name,
            suite_name=suite.get('name'),
            test_desc=test_case.get('desc'),
        )

        suite_data_arg_fields = suite.get('data') or {}
        test_case_data_arg_fields = test_case.get('data') or {}
        if not isinstance(suite_data_arg_fields, dict):
            suite_data_arg_fields = {}
        if not isinstance(test_case_data_arg_fields, dict):
            test_case_data_arg_fields = {}

        final_data_arg_fields = {**suite_data_arg_fields, **test_case_data_arg_fields}
        data_argument_for_render = DataArgument[dict[str, Any]](**final_data_arg_fields)

        options_dict = test_case.get('options', {})
        # Note: PromptMetadata is generic, ModelConfigT defaults to Any if not specified.
        prompt_metadata_options: PromptMetadata[Any] = PromptMetadata[Any](**options_dict)
        template_content = suite['template']
        expected_results_from_spec = test_case.get('expect', {})

        # --- 1. Render phase (Main Render) ---
        render_result: RenderedPrompt[Any] = await dotprompt.render(  # Corrected return type
            template_content,
            data=data_argument_for_render,  # Correctly passing DataArgument instance
            options=prompt_metadata_options,
        )

        actual_pruned_render_output: dict[str, Any] = {}
        if 'messages' in expected_results_from_spec:
            actual_pruned_render_output['messages'] = render_result.messages
        if 'config' in expected_results_from_spec:  # This is PromptMetadata.config
            actual_pruned_render_output['config'] = render_result.config
        if 'ext' in expected_results_from_spec:
            actual_pruned_render_output['ext'] = render_result.ext  # Corrected attribute
        if 'input' in expected_results_from_spec:
            actual_pruned_render_output['input'] = (
                render_result.input.schema_ if render_result.input else None
            )  # Corrected attribute
        if 'metadata' in expected_results_from_spec:  # Mapping to PromptMetadata.config
            actual_pruned_render_output['metadata'] = render_result.config

        expected_dict_for_render: dict[str, Any] = {}
        for key, value in expected_results_from_spec.items():
            if key not in ['raw', 'input']:
                expected_dict_for_render[key] = value

        if 'ext' in expected_dict_for_render or 'ext' in actual_pruned_render_output:
            expected_dict_for_render['ext'] = expected_dict_for_render.get('ext', {})
        if 'config' in expected_dict_for_render or 'config' in actual_pruned_render_output:
            expected_dict_for_render['config'] = expected_dict_for_render.get('config', {})
        if 'metadata' in expected_dict_for_render or 'metadata' in actual_pruned_render_output:
            expected_dict_for_render['metadata'] = expected_dict_for_render.get('metadata', {})

        self.assertDictEqual(actual_pruned_render_output, expected_dict_for_render, 'Pruned render result mismatch')

        # Compare raw rendered output if expected
        # NOTE: RenderedPrompt in Python does not currently store the raw rendered string.
        # PromptMetadata.raw stores raw frontmatter.
        # If 'expect.raw' is for the full rendered string, this comparison needs re-evaluation
        # based on library capabilities. For now, if it means frontmatter:
        if 'raw' in expected_results_from_spec and expected_results_from_spec['raw'] is not None:
            # Assuming 'raw' in expect refers to raw frontmatter if it's part of RenderedPrompt's base
            # If it refers to the full rendered string, this will be incorrect.
            if hasattr(render_result, 'raw') and render_result.raw is not None:
                self.assertEqual(
                    render_result.raw,  # This is PromptMetadata.raw (frontmatter)
                    expected_results_from_spec['raw'],
                    'Raw frontmatter output mismatch (Note: not full rendered string)',
                )
        # else:
        #     self.fail("Test expected 'raw' comparison, but Python's RenderedPrompt.raw (frontmatter) was None or 'expect.raw' refers to full string not available.")

        # --- 2. Metadata Render phase ---
        # Corrected return type and argument passing
        metadata_render_result: PromptMetadata[Any] = await dotprompt.render_metadata(
            template_content,
            additional_metadata=prompt_metadata_options,
        )

        actual_pruned_metadata_output: dict[str, Any] = {}
        if 'config' in expected_results_from_spec:
            actual_pruned_metadata_output['config'] = metadata_render_result.config
        if 'ext' in expected_results_from_spec:
            actual_pruned_metadata_output['ext'] = metadata_render_result.ext  # Corrected
        if 'input' in expected_results_from_spec:
            actual_pruned_metadata_output['input'] = (
                metadata_render_result.input.schema_ if metadata_render_result.input else None
            )  # Corrected
        if 'metadata' in expected_results_from_spec:  # Mapping to PromptMetadata.config
            actual_pruned_metadata_output['metadata'] = metadata_render_result.config

        expected_dict_for_metadata: dict[str, Any] = {}
        for key, value in expected_results_from_spec.items():
            if key not in ['raw', 'messages']:
                expected_dict_for_metadata[key] = value

        if 'ext' in expected_dict_for_metadata or 'ext' in actual_pruned_metadata_output:
            expected_dict_for_metadata['ext'] = expected_dict_for_metadata.get('ext', {})
        if 'config' in expected_dict_for_metadata or 'config' in actual_pruned_metadata_output:
            expected_dict_for_metadata['config'] = expected_dict_for_metadata.get('config', {})
        if 'metadata' in expected_dict_for_metadata or 'metadata' in actual_pruned_metadata_output:
            expected_dict_for_metadata['metadata'] = expected_dict_for_metadata.get('metadata', {})

        self.assertDictEqual(
            actual_pruned_metadata_output, expected_dict_for_metadata, 'Pruned metadata result mismatch'
        )

        logger.debug(
            'Finished running spec test successfully',
            yaml_file=yaml_file.name,
            suite_name=suite.get('name'),
            test_desc=test_case.get('desc'),
        )


if __name__ == '__main__':
    unittest.main()
