# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import Path

import tomllib

REPOSITORY_ROOT = Path(__file__).parents[3]
PYTHON_ROOT = REPOSITORY_ROOT / 'python'
WORKFLOW_PATH = REPOSITORY_ROOT / '.github/workflows/publish_python_handlebarrz_package.yml'
WORKFLOW = WORKFLOW_PATH.read_text()
HANDLEBARRZ_PROJECT = tomllib.loads((PYTHON_ROOT / 'handlebarrz/pyproject.toml').read_text())
DOTPROMPTZ_PROJECT = tomllib.loads((PYTHON_ROOT / 'dotpromptz/pyproject.toml').read_text())


def _job(name: str) -> str:
    match = re.search(rf'^  {name}:\n(?P<body>.*?)(?=^  [a-z][a-z0-9_]+:\n|\Z)', WORKFLOW, re.M | re.S)
    assert match is not None
    return match.group('body')


BUILD_JOBS = (
    'build_ubuntu_arm64',
    'build_ubuntu_x86_64',
    'build_alpine_arm64',
    'build_alpine_x86_64',
    'build_macos_arm64',
    'build_macos_x86_64',
)
SMOKE_JOBS = (
    'smoke_test_linux_arm64',
    'smoke_test_linux_x86_64',
    'smoke_test_alpine_arm64',
    'smoke_test_alpine_x86_64',
    'smoke_test_macos_arm64',
    'smoke_test_macos_x86_64',
)


def test_publish_workflow_has_no_subset_or_windows_controls() -> None:
    dispatch = WORKFLOW.split('jobs:', maxsplit=1)[0]
    assert 'enable_' not in dispatch
    assert '#   - Windows:       UNSUPPORTED' in WORKFLOW
    assert 'windows-latest' not in WORKFLOW
    assert 'build_windows' not in WORKFLOW
    for job_name in BUILD_JOBS:
        assert 'if: needs.setup.outputs.enable_' not in _job(job_name)


def test_setup_peels_tag_once_and_later_checkouts_use_source_sha() -> None:
    setup = _job('setup')
    assert 'RELEASE_TAG: ${{' in setup
    assert "re.fullmatch(r'dotpromptz-handlebars-[0-9][0-9a-z.!+-]*', tag)" in setup
    assert "output.write(f'release_ref=refs/tags/{tag}\\n')" in setup
    assert '${{ inputs.tag_name }}' not in setup
    assert "git rev-parse 'HEAD^{commit}'" in setup
    assert 'source_sha=$SOURCE_SHA' in setup
    checkout_blocks = re.findall(
        r'- uses: actions/checkout@v6\n(?P<with>        with:\n          ref: [^\n]+)', WORKFLOW
    )
    assert len(checkout_blocks) == WORKFLOW.count('- uses: actions/checkout@v6')
    assert 'steps.mode.outputs.release_ref' in checkout_blocks[0]
    assert all('source_sha' in block for block in checkout_blocks[1:])
    assert all('release_ref' not in block for block in checkout_blocks[1:])


def test_builds_are_exactly_one_cp310_abi3_wheel_per_target() -> None:
    for name in BUILD_JOBS:
        job = _job(name)
        assert job.count('- "3.10"') == 1
        assert '- "3.11"' not in job
        assert 'if-no-files-found: error' in job
    assert '--compatibility manylinux_2_24' in _job('build_ubuntu_arm64')
    assert '--compatibility manylinux_2_24' in _job('build_ubuntu_x86_64')
    assert '--compatibility musllinux_1_2' in _job('build_alpine_arm64')
    assert '--compatibility musllinux_1_2' in _job('build_alpine_x86_64')
    assert 'MACOSX_DEPLOYMENT_TARGET: "11.0"' in _job('build_macos_arm64')
    assert 'MACOSX_DEPLOYMENT_TARGET: "10.12"' in _job('build_macos_x86_64')
    assert 'maturin sdist' not in WORKFLOW


def test_one_run_graph_is_testpypi_then_smoke_then_production() -> None:
    prepare = _job('prepare_candidate')
    testpypi = _job('testpypi_publish')
    production = _job('production_publish')
    assert 'release-candidate' in prepare
    assert '--candidate release-candidate' in prepare
    assert 'path: release-candidate/' in prepare
    assert 'needs: [setup, prepare_candidate]' in testpypi
    for smoke in SMOKE_JOBS:
        assert 'needs: [setup, testpypi_publish]' in _job(smoke)
        assert f'- {smoke}' in production
    assert '- prepare_candidate' in production
    assert '- testpypi_publish' in production
    assert "needs.setup.outputs.publish_mode == 'production'" in production
    assert 'actions/download-artifact@v7' in testpypi
    assert 'actions/download-artifact@v7' in production
    assert 'pattern: wheels-*' not in production
    assert production.index('Reconfirm TestPyPI still matches current-run bytes') < production.index(
        'Reconcile PyPI and stage only missing wheels'
    )


def test_registry_paths_are_hash_reconciled_and_missing_only() -> None:
    for name, repository in (
        ('testpypi_publish', 'https://test.pypi.org/legacy/'),
        ('production_publish', 'https://upload.pypi.org/legacy/'),
    ):
        job = _job(name)
        assert 'release_verifier.py reconcile' in job
        assert '--candidate candidate' in job
        assert '--upload-dir upload' in job
        assert '--require-complete' in job
        assert 'packages-dir: upload/' in job
        assert f'repository-url: {repository}' in job
        assert 'missing_count' in job
    assert 'skip-existing' not in WORKFLOW
    assert 'continue-on-error' not in WORKFLOW


def test_publish_jobs_have_oidc_and_checkout_permissions() -> None:
    for name in ('testpypi_publish', 'production_publish'):
        job = _job(name)
        assert 'contents: read' in job
        assert 'id-token: write' in job


def test_uploads_are_preceded_by_immediate_local_reverification() -> None:
    testpypi = _job('testpypi_publish')
    production = _job('production_publish')
    assert testpypi.index('Reverify read-only bytes immediately') < testpypi.index('Publish missing wheels')
    assert production.index('Reverify read-only bytes immediately') < production.index(
        'Publish missing distribution files'
    )
    assert 'upload wheel files must be read-only' in (PYTHON_ROOT / 'handlebarrz/release_verifier.py').read_text()


def test_smokes_use_two_explicit_indexes_without_source_fallback() -> None:
    shell = (PYTHON_ROOT / 'handlebarrz/smoke_tests/execute-test.sh').read_text()
    assert '--index-url "https://pypi.org/simple"' in shell
    assert '"structlog>=25.2.0"' in shell
    assert '--index-url "$candidate_index"' in shell
    assert '--isolated' in shell
    assert 'PIP_CONFIG_FILE=/dev/null' in shell
    assert 'UV_NO_CONFIG=1' in shell
    assert 'unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL PIP_FIND_LINKS' in shell
    assert 'UV_INDEX_URL UV_DEFAULT_INDEX UV_EXTRA_INDEX_URL UV_FIND_LINKS UV_NO_INDEX' in shell
    assert 'pip download' in shell
    assert 'verify-smoke-wheel' in shell
    assert '"$wheel"' in shell
    assert '--no-build' in shell
    assert '--only-binary=:all:' in shell
    assert '--no-deps' in shell
    assert '"dotpromptz-handlebars==$package_version"' in shell
    for name in ('smoke_test_macos_arm64', 'smoke_test_macos_x86_64'):
        job = _job(name)
        assert '--index-url "https://pypi.org/simple"' in job
        assert '--index-url "https://test.pypi.org/simple"' in job
        assert 'python -m pip download' in job
        assert '--isolated' in job
        assert 'PIP_CONFIG_FILE: /dev/null' in job
        assert 'verify-smoke-wheel' in job
        assert '"${wheels[0]}"' in job
        assert job.index('"structlog>=25.2.0"') < job.index('"dotpromptz-handlebars==')
        assert '--no-deps' in job


def test_tag_mutation_check_does_not_control_source_checkout() -> None:
    production = _job('production_publish')
    assert 'git ls-remote origin' in production
    assert 'needs.setup.outputs.release_tag' in production
    assert 'needs.setup.outputs.source_sha' in production
    assert production.index('Verify named tag still identifies pinned source') < production.index(
        'Publish missing distribution files'
    )


def test_partial_upload_recovery_is_retained_before_failure_point() -> None:
    for name, upload_name, completion_name in (
        ('testpypi_publish', 'Publish missing wheels', 'Require exact TestPyPI'),
        ('production_publish', 'Publish missing distribution files', 'Require exact PyPI'),
    ):
        job = _job(name)
        assert 'uploads are per-file' in job
        assert 'Re-run failed jobs' in job
        assert 'from **THIS run**' in job
        assert 'Never start a fresh production run' in job
        assert job.count('Re-run failed jobs') == 2
        assert job.count('Never start a fresh production run') == 2
        guidance = job.index('partial-upload recovery')
        upload = job.index(upload_name)
        success_summary = job.index('successful', upload)
        completeness = job.index(completion_name)
        assert guidance < upload < success_summary < completeness
        assert '&& success()' in job[success_summary:completeness]


def test_contract_is_poison_detecting_resumable_not_transactional() -> None:
    assert 'poison-detecting, resumable exact-six publication' in WORKFLOW
    assert 'transactional upload' not in WORKFLOW.lower()


def test_testpypi_only_mode_is_named_and_restricted() -> None:
    dispatch = WORKFLOW.split('jobs:', maxsplit=1)[0]
    setup = _job('setup')
    assert "'testpypi-only'" in dispatch
    assert 'for prerelease/dev versions' in dispatch
    assert "mode == 'testpypi-only'" in setup
    assert 'version.is_prerelease or version.is_devrelease' in setup


def test_publish_action_remains_commit_pinned() -> None:
    references = re.findall(r'pypa/gh-action-pypi-publish@([^\s]+)', WORKFLOW)
    assert len(references) == 2
    assert all(re.fullmatch(r'[0-9a-f]{40}', reference) for reference in references)


def test_platform_and_python_classifiers_are_truthful() -> None:
    expected_platforms = {'Operating System :: MacOS', 'Operating System :: POSIX :: Linux'}
    expected_pythons = {f'Programming Language :: Python :: 3.{minor}' for minor in range(10, 15)}
    for project in (HANDLEBARRZ_PROJECT, DOTPROMPTZ_PROJECT):
        classifiers = set(project['project']['classifiers'])
        assert expected_platforms <= classifiers
        assert 'Operating System :: OS Independent' not in classifiers
        assert not any('Windows' in classifier for classifier in classifiers)
        assert expected_pythons <= classifiers
