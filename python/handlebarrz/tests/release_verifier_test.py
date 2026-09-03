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

import base64
import csv
import hashlib
import importlib.util
import itertools
import json
import shutil
import sys
import zipfile
from collections.abc import Iterable
from pathlib import Path

import pytest
from packaging.version import Version

MODULE_PATH = Path(__file__).parents[1] / 'release_verifier.py'
SPEC = importlib.util.spec_from_file_location('release_verifier', MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
release_verifier = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release_verifier
SPEC.loader.exec_module(release_verifier)

PACKAGE_NAME = release_verifier.PACKAGE_NAME
TARGETS = release_verifier.TARGETS
TARGET_KEYS = tuple(target.key for target in TARGETS)
VERSION = Version('1.2.3')
PROPER_SUBSETS = [
    combination for size in range(1, len(TARGET_KEYS)) for combination in itertools.combinations(TARGET_KEYS, size)
]
RESULT_COMBINATIONS = list(itertools.product(('success', 'failure', 'skipped', 'cancelled'), repeat=6))


def _digest(data: bytes) -> str:
    return 'sha256=' + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()


def _write_wheel(
    path: Path,
    target: object,
    *,
    metadata_name: str = PACKAGE_NAME,
    metadata_version: str = str(VERSION),
    wheel_tag: str | None = None,
    record_change: str | None = None,
    extra_member: str | None = None,
    duplicate_member: bool = False,
) -> None:
    dist_info = f'dotpromptz_handlebars-{VERSION}.dist-info'
    files = {
        'handlebarrz/__init__.py': b'from ._native import *\n',
        f'{dist_info}/METADATA': (
            f'Metadata-Version: 2.4\nName: {metadata_name}\nVersion: {metadata_version}\n'
        ).encode(),
        f'{dist_info}/WHEEL': (
            f'Wheel-Version: 1.0\nRoot-Is-Purelib: false\nTag: {wheel_tag or target.tag}\n'
        ).encode(),
    }
    if extra_member is not None:
        files[extra_member] = b'extra'
    record_path = f'{dist_info}/RECORD'
    rows = [[name, _digest(data), str(len(data))] for name, data in files.items()]
    rows.append([record_path, '', ''])
    if record_change == 'hash':
        rows[0][1] = 'sha256=wrong'
    elif record_change == 'size':
        rows[0][2] = '999'
    elif record_change == 'missing':
        rows.pop(0)
    elif record_change == 'extra':
        rows.append(['not/in/archive', 'sha256=wrong', '1'])
    elif record_change == 'duplicate':
        rows.append(rows[0])
    record = '\n'.join(','.join(row) for row in rows).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in (*files.items(), (record_path, record)):
            archive.writestr(zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0)), data)
        if duplicate_member:
            archive.writestr(
                zipfile.ZipInfo('handlebarrz/__init__.py', date_time=(2020, 1, 1, 0, 0, 0)),
                files['handlebarrz/__init__.py'],
            )


def _wheel_name(target: object, version: Version = VERSION) -> str:
    return f'dotpromptz_handlebars-{version}-cp310-abi3-{target.platform}.whl'


def _artifacts(root: Path, enabled: Iterable[str] = TARGET_KEYS) -> None:
    enabled_set = set(enabled)
    for target in TARGETS:
        if target.key in enabled_set:
            _write_wheel(root / target.artifact / _wheel_name(target), target)


def _stage(tmp_path: Path) -> tuple[Path, Path]:
    artifacts = tmp_path / 'artifacts'
    candidate = tmp_path / 'release-candidate'
    _artifacts(artifacts)
    release_verifier.stage_wheels(artifacts, candidate, VERSION)
    return artifacts, candidate


@pytest.mark.parametrize('subset', PROPER_SUBSETS)
def test_all_62_nonempty_proper_subsets_are_rejected(subset: tuple[str, ...]) -> None:
    with pytest.raises(release_verifier.VerificationError, match='all six'):
        release_verifier.require_all_targets(subset)


def test_exact_six_target_set_is_required() -> None:
    assert release_verifier.require_all_targets(TARGET_KEYS) == frozenset(TARGET_KEYS)
    with pytest.raises(release_verifier.VerificationError, match='all six'):
        release_verifier.require_all_targets(())
    with pytest.raises(release_verifier.VerificationError, match='duplicates'):
        release_verifier.require_all_targets((*TARGET_KEYS, TARGET_KEYS[0]))
    with pytest.raises(release_verifier.VerificationError, match='unknown'):
        release_verifier.require_all_targets((*TARGET_KEYS[:-1], 'windows_x86_64'))


@pytest.mark.parametrize('statuses', RESULT_COMBINATIONS)
def test_complete_result_status_truth_table(statuses: tuple[str, ...]) -> None:
    results = dict(zip(TARGET_KEYS, statuses, strict=True))
    assert release_verifier.publish_gate(results) is all(status == 'success' for status in statuses)


def test_status_gate_rejects_missing_and_extra_jobs() -> None:
    results = dict.fromkeys(TARGET_KEYS, 'success')
    results.pop(TARGET_KEYS[0])
    assert not release_verifier.publish_gate(results)
    results['windows_x86_64'] = 'success'
    assert not release_verifier.publish_gate(results)


def test_collect_requires_all_six_artifact_directories(tmp_path: Path) -> None:
    artifacts = tmp_path / 'artifacts'
    _artifacts(artifacts, TARGET_KEYS[:-1])
    with pytest.raises(release_verifier.VerificationError, match='all six'):
        release_verifier.collect_wheels(artifacts, VERSION)


@pytest.mark.parametrize('mutation', ['extra', 'empty', 'multiple', 'root_file'])
def test_artifact_layout_must_be_exact(tmp_path: Path, mutation: str) -> None:
    artifacts = tmp_path / 'artifacts'
    _artifacts(artifacts)
    target = TARGETS[0]
    if mutation == 'extra':
        (artifacts / 'unexpected').mkdir()
    elif mutation == 'empty':
        next((artifacts / target.artifact).iterdir()).unlink()
    elif mutation == 'multiple':
        (artifacts / target.artifact / 'extra.whl').write_bytes(b'extra')
    else:
        (artifacts / 'unexpected.whl').write_bytes(b'extra')
    with pytest.raises(release_verifier.VerificationError):
        release_verifier.collect_wheels(artifacts, VERSION)


@pytest.mark.parametrize(
    ('filename', 'message'),
    [
        ('other-1.2.3-cp310-abi3-manylinux_2_24_aarch64.whl', 'distribution'),
        ('dotpromptz_handlebars-1.2.4-cp310-abi3-manylinux_2_24_aarch64.whl', 'version'),
        ('dotpromptz_handlebars-1.2.3-1-cp310-abi3-manylinux_2_24_aarch64.whl', 'build'),
        ('dotpromptz_handlebars-1.2.3-cp311-abi3-manylinux_2_24_aarch64.whl', 'tags'),
        ('dotpromptz_handlebars-1.2.3-cp310-cp310-manylinux_2_24_aarch64.whl', 'tags'),
        ('dotpromptz_handlebars-1.2.3-cp310-abi3-manylinux_2_24_x86_64.whl', 'tags'),
        ('dotpromptz_handlebars-1.2.3-cp310-abi3-manylinux_2_28_aarch64.whl', 'tags'),
        ('dotpromptz_handlebars-1.2.3-cp310-abi3-musllinux_1_2_aarch64.whl', 'tags'),
    ],
)
def test_wheel_filename_fields_are_exact(tmp_path: Path, filename: str, message: str) -> None:
    target = TARGETS[0]
    wheel = tmp_path / filename
    _write_wheel(wheel, target)
    with pytest.raises(release_verifier.VerificationError, match=message):
        release_verifier.verify_wheel(wheel, target, VERSION)


@pytest.mark.parametrize(
    ('target_index', 'wrong_platform'),
    [
        (2, 'musllinux_1_1_aarch64'),
        (3, 'musllinux_1_2_i686'),
        (4, 'macosx_10_15_arm64'),
        (4, 'macosx_11_0_x86_64'),
        (5, 'macosx_11_0_x86_64'),
        (5, 'macosx_10_12_arm64'),
    ],
)
def test_arches_and_platform_baselines_are_exact(tmp_path: Path, target_index: int, wrong_platform: str) -> None:
    target = TARGETS[target_index]
    wheel = tmp_path / f'dotpromptz_handlebars-{VERSION}-cp310-abi3-{wrong_platform}.whl'
    _write_wheel(wheel, target, wheel_tag=f'cp310-abi3-{wrong_platform}')
    with pytest.raises(release_verifier.VerificationError, match='tags'):
        release_verifier.verify_wheel(wheel, target, VERSION)


def test_corrupt_zip_is_rejected(tmp_path: Path) -> None:
    target = TARGETS[0]
    wheel = tmp_path / _wheel_name(target)
    wheel.write_bytes(b'not a zip')
    with pytest.raises(release_verifier.VerificationError, match='corrupt wheel'):
        release_verifier.verify_wheel(wheel, target, VERSION)


@pytest.mark.parametrize('member', ['/absolute', '../escape', 'dir/../../escape', r'dir\escape'])
def test_unsafe_zip_members_are_rejected(tmp_path: Path, member: str) -> None:
    target = TARGETS[0]
    wheel = tmp_path / _wheel_name(target)
    _write_wheel(wheel, target, extra_member=member)
    with pytest.raises(release_verifier.VerificationError, match='unsafe wheel member'):
        release_verifier.verify_wheel(wheel, target, VERSION)


def test_duplicate_zip_member_is_rejected(tmp_path: Path) -> None:
    target = TARGETS[0]
    wheel = tmp_path / _wheel_name(target)
    with pytest.warns(UserWarning, match='Duplicate name'):
        _write_wheel(wheel, target, duplicate_member=True)
    with pytest.raises(release_verifier.VerificationError, match='duplicate wheel member'):
        release_verifier.verify_wheel(wheel, target, VERSION)


@pytest.mark.parametrize(
    ('kwargs', 'message'),
    [
        ({'metadata_name': 'other'}, 'METADATA Name'),
        ({'metadata_version': '1.2.4'}, 'METADATA Version'),
        ({'wheel_tag': 'cp311-abi3-manylinux_2_24_aarch64'}, 'WHEEL tags'),
        ({'record_change': 'hash'}, 'hash mismatch'),
        ({'record_change': 'size'}, 'size mismatch'),
        ({'record_change': 'missing'}, 'exactly cover'),
        ({'record_change': 'extra'}, 'exactly cover'),
        ({'record_change': 'duplicate'}, 'duplicate paths'),
    ],
)
def test_internal_wheel_metadata_is_verified(tmp_path: Path, kwargs: dict[str, str], message: str) -> None:
    target = TARGETS[0]
    wheel = tmp_path / _wheel_name(target)
    _write_wheel(wheel, target, **kwargs)
    with pytest.raises(release_verifier.VerificationError, match=message):
        release_verifier.verify_wheel(wheel, target, VERSION)


def test_stage_verifies_copied_bytes_not_only_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = tmp_path / 'artifacts'
    _artifacts(artifacts)
    candidate = tmp_path / 'release-candidate'
    candidate.mkdir()
    sentinel = candidate / 'existing'
    sentinel.write_bytes(b'original')
    real_copy = shutil.copyfile

    def corrupt_copy(source: Path, destination: Path) -> str:
        result = real_copy(source, destination)
        Path(destination).write_bytes(b'changed after source verification')
        return result

    monkeypatch.setattr(release_verifier.shutil, 'copyfile', corrupt_copy)
    with pytest.raises(release_verifier.VerificationError):
        release_verifier.stage_wheels(artifacts, candidate, VERSION)
    assert sentinel.read_bytes() == b'original'


def test_manifest_write_failure_cannot_commit_dist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts = tmp_path / 'artifacts'
    _artifacts(artifacts)
    candidate = tmp_path / 'release-candidate'
    candidate.mkdir()
    sentinel = candidate / 'existing'
    sentinel.write_bytes(b'original')

    def fail_manifest(*_args: object, **_kwargs: object) -> None:
        raise OSError('manifest write failed')

    monkeypatch.setattr(release_verifier, 'write_manifest', fail_manifest)
    with pytest.raises(OSError, match='manifest write failed'):
        release_verifier.stage_wheels(artifacts, candidate, VERSION)
    assert list(candidate.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b'original'


def test_backup_cleanup_failure_does_not_reverse_committed_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts = tmp_path / 'artifacts'
    _artifacts(artifacts)
    candidate = tmp_path / 'release-candidate'
    candidate.mkdir()
    (candidate / 'old').write_text('old')
    real_rmtree = shutil.rmtree

    def fail_backup(path: Path) -> None:
        if '-backup-' in str(path):
            raise OSError('cleanup failed')
        real_rmtree(path)

    monkeypatch.setattr(release_verifier.shutil, 'rmtree', fail_backup)
    release_verifier.stage_wheels(artifacts, candidate, VERSION)
    assert {path.name for path in (candidate / 'dist').iterdir()} == release_verifier.expected_filenames(VERSION)


def test_manifest_rejects_changed_staged_bytes(tmp_path: Path) -> None:
    _, candidate = _stage(tmp_path)
    next((candidate / 'dist').iterdir()).write_bytes(b'changed')
    with pytest.raises(release_verifier.VerificationError):
        release_verifier.verify_candidate(candidate, VERSION)


@pytest.mark.parametrize('remote_state', ['absent', 'partial', 'exact'])
def test_registry_reconciliation_accepts_resumable_matching_states(tmp_path: Path, remote_state: str) -> None:
    _, candidate = _stage(tmp_path)
    local = release_verifier.read_manifest(candidate / 'release-manifest.json', VERSION)
    if remote_state == 'absent':
        remote = None
    elif remote_state == 'partial':
        remote = dict(list(local.items())[:2])
    else:
        remote = local
    missing = release_verifier.reconcile_index(remote, local)
    assert missing == frozenset(set(local) - set(remote or {}))


@pytest.mark.parametrize('bad_state', ['wrong_hash', 'extra', 'duplicate_equivalent'])
def test_registry_reconciliation_rejects_poisoned_states(tmp_path: Path, bad_state: str) -> None:
    _, candidate = _stage(tmp_path)
    local = release_verifier.read_manifest(candidate / 'release-manifest.json', VERSION)
    remote = dict(local)
    if bad_state == 'wrong_hash':
        remote[next(iter(remote))] = '0' * 64
    elif bad_state == 'extra':
        remote['dotpromptz_handlebars-1.2.3.tar.gz'] = '1' * 64
    else:
        remote[next(iter(remote)).upper()] = next(iter(remote.values()))
    with pytest.raises(release_verifier.VerificationError):
        release_verifier.reconcile_index(remote, local)


def test_partial_registry_state_stages_only_missing_files(tmp_path: Path) -> None:
    _, candidate = _stage(tmp_path)
    local = release_verifier.read_manifest(candidate / 'release-manifest.json', VERSION)
    existing = dict(list(local.items())[:3])
    upload = tmp_path / 'upload'
    missing = release_verifier.stage_missing(candidate, upload, VERSION, existing)
    assert {path.name for path in upload.iterdir()} == missing
    assert {path.name for path in upload.iterdir()} == set(local) - set(existing)
    assert all(path.stat().st_mode & 0o222 == 0 for path in upload.iterdir())


def test_exact_registry_state_stages_empty_noop(tmp_path: Path) -> None:
    _, candidate = _stage(tmp_path)
    local = release_verifier.read_manifest(candidate / 'release-manifest.json', VERSION)
    upload = tmp_path / 'upload'
    assert not release_verifier.stage_missing(candidate, upload, VERSION, local)
    assert not list(upload.iterdir())


def test_upload_reverification_rejects_changed_missing_bytes(tmp_path: Path) -> None:
    _, candidate = _stage(tmp_path)
    upload = tmp_path / 'upload'
    release_verifier.stage_missing(candidate, upload, VERSION, None)
    release_verifier.verify_upload(candidate, upload, VERSION)
    changed = next(upload.iterdir())
    changed.chmod(0o644)
    changed.write_bytes(b'changed')
    with pytest.raises(release_verifier.VerificationError, match='read-only|upload bytes'):
        release_verifier.verify_upload(candidate, upload, VERSION)


def test_smoke_wheel_must_equal_retained_candidate_digest(tmp_path: Path) -> None:
    _, candidate = _stage(tmp_path)
    target = TARGETS[0]
    source = candidate / 'dist' / _wheel_name(target)
    downloaded = tmp_path / _wheel_name(target)
    shutil.copyfile(source, downloaded)
    release_verifier.verify_smoke_wheel(candidate, downloaded, target.key, VERSION)
    downloaded.write_bytes(b'not the candidate')
    with pytest.raises(release_verifier.VerificationError, match='retained candidate'):
        release_verifier.verify_smoke_wheel(candidate, downloaded, target.key, VERSION)


def test_registry_json_requires_sha256_for_every_filename(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        'urls': [
            {'filename': 'one.whl', 'digests': {'sha256': 'a' * 64}},
            {'filename': 'two.whl', 'digests': {'sha256': 'b' * 64}},
        ]
    }

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(payload).encode()

    monkeypatch.setattr(release_verifier.urllib.request, 'urlopen', lambda *_args, **_kwargs: Response())
    assert release_verifier.fetch_index_files('https://index.invalid', VERSION) == {
        'one.whl': 'a' * 64,
        'two.whl': 'b' * 64,
    }
    del payload['urls'][0]['digests']
    with pytest.raises(release_verifier.VerificationError, match='invalid file metadata'):
        release_verifier.fetch_index_files('https://index.invalid', VERSION)


@pytest.mark.parametrize(
    'tag',
    [
        'dotpromptz-handlebars-1.2.3\nmalicious=1',
        'dotpromptz-handlebars-1.2.3$(id)',
        'dotpromptz-handlebars-refs/heads/main',
        'dotpromptz-handlebars-01.2.3',
        'dotpromptz-handlebars-1.2.3RC1',
        'dotpromptz-handlebars-1.2.3+local',
        'other-1.2.3',
    ],
)
def test_release_tag_rejects_output_and_ref_injection(tag: str) -> None:
    with pytest.raises(release_verifier.VerificationError):
        release_verifier.release_version(tag)


def test_release_versions_and_test_only_mode(tmp_path: Path) -> None:
    cargo = tmp_path / 'Cargo.toml'
    pyproject = tmp_path / 'pyproject.toml'
    cargo.write_text('[package]\nversion = "1.2.3rc1"\n')
    pyproject.write_text('[project]\nversion = "1.2.3rc1"\n')
    assert release_verifier.verify_release_versions(
        'dotpromptz-handlebars-1.2.3rc1', cargo, pyproject, mode='testpypi-only'
    ) == Version('1.2.3rc1')
    cargo.write_text('[package]\nversion = "1.2.3"\n')
    pyproject.write_text('[project]\nversion = "1.2.3"\n')
    with pytest.raises(release_verifier.VerificationError, match='prerelease or dev'):
        release_verifier.verify_release_versions('dotpromptz-handlebars-1.2.3', cargo, pyproject, mode='testpypi-only')


def test_repository_mapping_is_closed() -> None:
    assert release_verifier.repository_urls('https://upload.pypi.org/legacy/')[1] == 'https://pypi.org/pypi'
    assert release_verifier.repository_urls('https://test.pypi.org/legacy/')[1] == 'https://test.pypi.org/pypi'
    with pytest.raises(release_verifier.VerificationError, match='unsupported repository'):
        release_verifier.repository_urls('https://example.com/')


def test_target_contract_has_no_windows_and_exact_six_wheels() -> None:
    assert len(TARGETS) == 6
    assert not any('win' in target.key or 'win' in target.platform for target in TARGETS)
    assert len(release_verifier.expected_filenames(VERSION)) == 6


def test_record_fixture_is_well_formed(tmp_path: Path) -> None:
    target = TARGETS[0]
    wheel = tmp_path / _wheel_name(target)
    _write_wheel(wheel, target)
    with zipfile.ZipFile(wheel) as archive:
        record_path = next(name for name in archive.namelist() if name.endswith('/RECORD'))
        rows = list(csv.reader(archive.read(record_path).decode().splitlines()))
    assert rows[-1] == [record_path, '', '']
