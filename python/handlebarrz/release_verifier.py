#!/usr/bin/env python3
#
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

"""Verify, stage, and reconcile dotpromptz-handlebars release wheels."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from typing import Any

from packaging.tags import Tag
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import InvalidVersion, Version

PACKAGE_NAME = 'dotpromptz-handlebars'
TAG_PREFIX = f'{PACKAGE_NAME}-'
TAG_PATTERN = re.compile(rf'{re.escape(TAG_PREFIX)}[0-9][0-9a-z.!+-]*')
MANIFEST_VERSION = 1


class VerificationError(ValueError):
    """Raised when release inputs do not satisfy the publish contract."""


@dataclass(frozen=True)
class Target:
    """One required native wheel target."""

    key: str
    artifact: str
    platform: str

    @property
    def tag(self) -> Tag:
        """Return the one wheel tag accepted for this target."""
        return Tag('cp310', 'abi3', self.platform)


TARGETS = (
    Target('linux_arm64', 'wheels-ubuntu-arm64-3.10', 'manylinux_2_24_aarch64'),
    Target('linux_x86_64', 'wheels-ubuntu-x86-64-3.10', 'manylinux_2_24_x86_64'),
    Target('alpine_arm64', 'wheels-alpine-arm64-3.10', 'musllinux_1_2_aarch64'),
    Target('alpine_x86_64', 'wheels-alpine-x86_64-3.10', 'musllinux_1_2_x86_64'),
    Target('macos_arm64', 'wheels-macos-arm64-3.10-build_macos_arm64', 'macosx_11_0_arm64'),
    Target('macos_x86_64', 'wheels-macos-x86_64-3.10-build_macos_x86_64', 'macosx_10_12_x86_64'),
)
TARGET_BY_KEY = {target.key: target for target in TARGETS}
TARGET_KEYS = frozenset(TARGET_BY_KEY)

REPOSITORIES = {
    'https://upload.pypi.org/legacy/': ('https://pypi.org/simple', 'https://pypi.org/pypi'),
    'https://test.pypi.org/legacy/': ('https://test.pypi.org/simple', 'https://test.pypi.org/pypi'),
}


def require_all_targets(values: Sequence[str] | None = None) -> frozenset[str]:
    """Reject every publishing target set except the complete six-target set."""
    selected = list(TARGET_BY_KEY) if values is None else list(values)
    if len(selected) != len(set(selected)):
        raise VerificationError('target list contains duplicates')
    unknown = set(selected) - TARGET_KEYS
    if unknown:
        raise VerificationError(f'unknown targets: {sorted(unknown)}')
    if set(selected) != TARGET_KEYS:
        raise VerificationError('publishing requires all six native targets')
    return TARGET_KEYS


def repository_urls(repository_url: str) -> tuple[str, str]:
    """Map the only supported upload repositories to install and JSON APIs."""
    try:
        return REPOSITORIES[repository_url]
    except KeyError as exc:
        raise VerificationError(f'unsupported repository: {repository_url}') from exc


def release_version(tag: str) -> Version:
    """Extract a strict canonical PEP 440 version from a safe release tag."""
    if TAG_PATTERN.fullmatch(tag) is None:
        raise VerificationError('release tag is not a safe canonical package tag')
    value = tag.removeprefix(TAG_PREFIX)
    try:
        version = Version(value)
    except InvalidVersion as exc:
        raise VerificationError('release tag has an invalid version') from exc
    if str(version) != value:
        raise VerificationError(f'release tag version is not canonical: {value}')
    if version.local is not None:
        raise VerificationError('release tag must not contain a local version')
    return version


def verify_release_versions(
    tag: str,
    cargo_path: Path,
    pyproject_path: Path,
    *,
    mode: str = 'production',
) -> Version:
    """Require safe release, Cargo, and Python versions to agree."""
    import tomllib

    tag_version = release_version(tag)
    with cargo_path.open('rb') as cargo_file:
        cargo_version = Version(tomllib.load(cargo_file)['package']['version'])
    with pyproject_path.open('rb') as pyproject_file:
        python_version = Version(tomllib.load(pyproject_file)['project']['version'])
    if len({tag_version, cargo_version, python_version}) != 1:
        raise VerificationError(f'version mismatch: tag={tag_version}, Cargo={cargo_version}, Python={python_version}')
    if mode not in {'production', 'testpypi-only'}:
        raise VerificationError(f'unsupported publish mode: {mode}')
    if mode == 'testpypi-only' and not (tag_version.is_prerelease or tag_version.is_devrelease):
        raise VerificationError('TestPyPI-only mode requires a prerelease or dev version')
    return tag_version


def publish_gate(results: Mapping[str, str]) -> bool:
    """Accept only exactly six successful native build or smoke jobs."""
    return set(results) == TARGET_KEYS and all(result == 'success' for result in results.values())


def expected_filenames(version: Version) -> frozenset[str]:
    """Return the exact six-wheel distribution."""
    distribution = canonicalize_name(PACKAGE_NAME).replace('-', '_')
    return frozenset(f'{distribution}-{version}-cp310-abi3-{target.platform}.whl' for target in TARGETS)


def sha256_file(path: Path) -> str:
    """Hash one file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member_names(archive: zipfile.ZipFile) -> list[str]:
    names: list[str] = []
    folded: set[str] = set()
    for info in archive.infolist():
        name = info.filename
        path = PurePosixPath(name)
        if not name or '\\' in name or path.is_absolute() or '..' in path.parts or path.parts[0] in {'', '.'}:
            raise VerificationError(f'unsafe wheel member: {name!r}')
        normalized = name.casefold()
        if normalized in folded:
            raise VerificationError(f'duplicate wheel member: {name!r}')
        folded.add(normalized)
        if not info.is_dir():
            names.append(name)
    return names


def _metadata_paths(names: Sequence[str], version: Version) -> tuple[str, str, str]:
    roots = {
        name.split('/', maxsplit=1)[0]
        for name in names
        if '/' in name and name.split('/', maxsplit=1)[0].endswith('.dist-info')
    }
    if len(roots) != 1:
        raise VerificationError('wheel must contain exactly one dist-info directory')
    root = roots.pop()
    distribution = canonicalize_name(PACKAGE_NAME).replace('-', '_')
    if root != f'{distribution}-{version}.dist-info':
        raise VerificationError(f'unexpected dist-info directory: {root}')
    return f'{root}/METADATA', f'{root}/WHEEL', f'{root}/RECORD'


def _verify_metadata(data: bytes, version: Version) -> None:
    metadata = BytesParser().parsebytes(data)
    if len(metadata.get_all('Name', [])) != 1 or len(metadata.get_all('Version', [])) != 1:
        raise VerificationError('METADATA must contain one Name and one Version')
    if canonicalize_name(metadata['Name'] or '') != canonicalize_name(PACKAGE_NAME):
        raise VerificationError('METADATA Name does not match the distribution')
    try:
        metadata_version = Version(metadata['Version'] or '')
    except InvalidVersion as exc:
        raise VerificationError('METADATA Version is invalid') from exc
    if metadata_version != version:
        raise VerificationError('METADATA Version does not match the wheel')


def _verify_wheel_metadata(data: bytes, expected_tag: Tag) -> None:
    wheel = BytesParser().parsebytes(data)
    if wheel.get_all('Tag', []) != [str(expected_tag)]:
        raise VerificationError(f'WHEEL tags must be exactly {expected_tag}')


def _record_digest(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return 'sha256=' + base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')


def _verify_record(archive: zipfile.ZipFile, names: Sequence[str], record_path: str) -> None:
    rows = list(csv.reader(archive.read(record_path).decode('utf-8').splitlines()))
    if any(len(row) != 3 for row in rows):
        raise VerificationError('RECORD rows must have exactly three fields')
    if len({row[0] for row in rows}) != len(rows):
        raise VerificationError('RECORD contains duplicate paths')
    if {row[0] for row in rows} != set(names):
        raise VerificationError('RECORD paths do not exactly cover wheel members')
    for path, digest, size in rows:
        if path == record_path:
            if digest or size:
                raise VerificationError('RECORD must not hash itself')
            continue
        data = archive.read(path)
        if digest != _record_digest(data):
            raise VerificationError(f'RECORD hash mismatch for {path}')
        if size != str(len(data)):
            raise VerificationError(f'RECORD size mismatch for {path}')


def verify_wheel(path: Path, target: Target, version: Version) -> None:
    """Validate filename tags and all security-relevant wheel metadata."""
    if not path.is_file():
        raise VerificationError(f'wheel is not a file: {path}')
    try:
        distribution, wheel_version, build, tags = parse_wheel_filename(path.name)
    except Exception as exc:
        raise VerificationError(f'invalid wheel filename: {path.name}') from exc
    if canonicalize_name(distribution) != canonicalize_name(PACKAGE_NAME):
        raise VerificationError('wheel distribution name does not match')
    if wheel_version != version:
        raise VerificationError('wheel version does not match the release')
    if build:
        raise VerificationError('wheel build tags are not permitted')
    if tags != {target.tag}:
        raise VerificationError(f'wheel tags must be exactly {target.tag}')
    try:
        with zipfile.ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise VerificationError(f'corrupt wheel member: {bad_member}')
            names = _safe_member_names(archive)
            metadata_path, wheel_path, record_path = _metadata_paths(names, version)
            if not {metadata_path, wheel_path, record_path}.issubset(names):
                raise VerificationError('wheel is missing required dist-info files')
            _verify_metadata(archive.read(metadata_path), version)
            _verify_wheel_metadata(archive.read(wheel_path), target.tag)
            _verify_record(archive, names, record_path)
    except zipfile.BadZipFile as exc:
        raise VerificationError(f'corrupt wheel: {path.name}') from exc


def collect_wheels(artifact_root: Path, version: Version) -> dict[str, Path]:
    """Verify exact artifact directory mapping and wheel contents."""
    if not artifact_root.is_dir():
        raise VerificationError(f'artifact root is not a directory: {artifact_root}')
    entries = list(artifact_root.iterdir())
    if any(not entry.is_dir() for entry in entries):
        raise VerificationError('artifact root may contain only artifact directories')
    if {entry.name for entry in entries} != {target.artifact for target in TARGETS}:
        raise VerificationError('artifact directories do not match all six targets')
    wheels: dict[str, Path] = {}
    for target in TARGETS:
        files = list((artifact_root / target.artifact).iterdir())
        if len(files) != 1 or not files[0].is_file():
            raise VerificationError(f'{target.artifact} must contain exactly one wheel')
        verify_wheel(files[0], target, version)
        if files[0].name in wheels:
            raise VerificationError(f'duplicate wheel filename: {files[0].name}')
        wheels[files[0].name] = files[0]
    if set(wheels) != expected_filenames(version):
        raise VerificationError('wheel filename distribution is incomplete')
    return wheels


def manifest_for_dist(dist: Path, version: Version) -> dict[str, str]:
    """Reverify staged wheel contents and return their byte digests."""
    if not dist.is_dir():
        raise VerificationError(f'dist is not a directory: {dist}')
    paths = {path.name: path for path in dist.iterdir() if path.is_file()}
    if set(paths) != expected_filenames(version) or len(list(dist.iterdir())) != len(paths):
        raise VerificationError('dist must contain exactly the six expected wheels')
    by_filename = {f'dotpromptz_handlebars-{version}-cp310-abi3-{target.platform}.whl': target for target in TARGETS}
    for filename, path in paths.items():
        verify_wheel(path, by_filename[filename], version)
    return {filename: sha256_file(path) for filename, path in sorted(paths.items())}


def write_manifest(path: Path, version: Version, files: Mapping[str, str]) -> None:
    """Atomically write the release digest manifest."""
    payload = {'manifest_version': MANIFEST_VERSION, 'package': PACKAGE_NAME, 'version': str(version), 'files': files}
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f'.{path.name}-', dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_manifest(path: Path, version: Version) -> dict[str, str]:
    """Read and validate one exact-six SHA-256 manifest."""
    try:
        payload: Any = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError('release manifest is unreadable') from exc
    if (
        not isinstance(payload, dict)
        or payload.get('manifest_version') != MANIFEST_VERSION
        or payload.get('package') != PACKAGE_NAME
        or payload.get('version') != str(version)
        or not isinstance(payload.get('files'), dict)
    ):
        raise VerificationError('release manifest header is invalid')
    files = payload['files']
    if set(files) != expected_filenames(version):
        raise VerificationError('release manifest must contain exactly six wheels')
    if not all(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest) for digest in files.values()):
        raise VerificationError('release manifest contains an invalid SHA-256 digest')
    return dict(files)


def verify_candidate(candidate: Path, version: Version) -> dict[str, str]:
    """Require candidate wheel bytes and contents to match their co-staged manifest."""
    manifest = read_manifest(candidate / 'release-manifest.json', version)
    if manifest_for_dist(candidate / 'dist', version) != manifest:
        raise VerificationError('staged wheel bytes do not match the release manifest')
    return manifest


def _best_effort_remove(path: Path) -> None:
    """Cleanup must not change the outcome after an atomic replacement commits."""
    try:
        shutil.rmtree(path)
    except OSError:
        pass


def stage_wheels(artifact_root: Path, candidate: Path, version: Version) -> None:
    """Build and verify one candidate tree, then atomically commit the tree."""
    wheels = collect_wheels(artifact_root, version)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f'.{candidate.name}-', dir=candidate.parent))
    temporary_dist = temporary / 'dist'
    temporary_dist.mkdir()
    backup: Path | None = None
    committed = False
    try:
        for filename, source in wheels.items():
            shutil.copyfile(source, temporary_dist / filename)
        copied_manifest = manifest_for_dist(temporary_dist, version)
        write_manifest(temporary / 'release-manifest.json', version, copied_manifest)
        verify_candidate(temporary, version)
        if candidate.exists():
            backup = Path(tempfile.mkdtemp(prefix=f'.{candidate.name}-backup-', dir=candidate.parent))
            backup.rmdir()
            os.replace(candidate, backup)
        os.replace(temporary, candidate)
        committed = True
    except Exception:
        if not committed and backup is not None and backup.exists() and not candidate.exists():
            os.replace(backup, candidate)
        raise
    finally:
        if temporary.exists():
            _best_effort_remove(temporary)
        if committed and backup is not None:
            _best_effort_remove(backup)


def fetch_index_files(json_base_url: str, version: Version) -> dict[str, str] | None:
    """Fetch filename-to-SHA-256 mappings, returning None for a 404."""
    url = f'{json_base_url}/{PACKAGE_NAME}/{version}/json'
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
            payload: Any = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise VerificationError(f'index request failed with HTTP {exc.code}') from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError('index request failed') from exc
    urls = payload.get('urls') if isinstance(payload, dict) else None
    if not isinstance(urls, list) or not all(isinstance(item, dict) for item in urls):
        raise VerificationError('index response does not contain a valid file list')
    files: dict[str, str] = {}
    for item in urls:
        filename = item.get('filename')
        digests = item.get('digests')
        digest = digests.get('sha256') if isinstance(digests, dict) else None
        if not isinstance(filename, str) or not isinstance(digest, str):
            raise VerificationError('index response contains invalid file metadata')
        if filename in files:
            raise VerificationError(f'index response contains duplicate filename: {filename}')
        files[filename] = digest
    return files


def reconcile_index(remote: Mapping[str, str] | None, local: Mapping[str, str]) -> frozenset[str]:
    """Return missing files if every existing registry file matches local bytes."""
    remote_files = {} if remote is None else dict(remote)
    extras = set(remote_files) - set(local)
    if extras:
        raise VerificationError(f'registry contains unexpected files: {sorted(extras)}')
    wrong = {filename for filename, digest in remote_files.items() if local.get(filename) != digest}
    if wrong:
        raise VerificationError(f'registry contains files with wrong SHA-256: {sorted(wrong)}')
    return frozenset(set(local) - set(remote_files))


def stage_missing(
    candidate: Path,
    upload_dir: Path,
    version: Version,
    remote: Mapping[str, str] | None,
) -> frozenset[str]:
    """Reverify local bytes and atomically stage only registry-missing wheels."""
    local = verify_candidate(candidate, version)
    missing = reconcile_index(remote, local)
    upload_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f'.{upload_dir.name}-', dir=upload_dir.parent))
    try:
        for filename in missing:
            shutil.copyfile(candidate / 'dist' / filename, temporary / filename)
        if {path.name: sha256_file(path) for path in temporary.iterdir()} != {
            filename: local[filename] for filename in missing
        }:
            raise VerificationError('copied upload bytes do not match the release manifest')
        for path in temporary.iterdir():
            path.chmod(0o444)
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        os.replace(temporary, upload_dir)
    finally:
        if temporary.exists():
            _best_effort_remove(temporary)
    return missing


def verify_upload(candidate: Path, upload_dir: Path, version: Version) -> None:
    """Reverify candidate and exact missing-file upload bytes."""
    local = verify_candidate(candidate, version)
    if not upload_dir.is_dir():
        raise VerificationError('upload directory is missing')
    upload_paths = list(upload_dir.iterdir())
    if not upload_paths or any(not path.is_file() for path in upload_paths):
        raise VerificationError('upload directory must contain wheel files')
    if any(path.stat().st_mode & 0o222 for path in upload_paths):
        raise VerificationError('upload wheel files must be read-only')
    upload_names = {path.name for path in upload_paths}
    if not upload_names <= set(local):
        raise VerificationError('upload directory contains unexpected files')
    if {path.name: sha256_file(path) for path in upload_paths} != {
        filename: local[filename] for filename in upload_names
    }:
        raise VerificationError('upload bytes do not match the release manifest')


def verify_smoke_wheel(candidate: Path, wheel: Path, target_key: str, version: Version) -> None:
    """Require one downloaded smoke wheel to equal the retained candidate bytes."""
    try:
        target = TARGET_BY_KEY[target_key]
    except KeyError as exc:
        raise VerificationError(f'unknown smoke target: {target_key}') from exc
    expected = f'dotpromptz_handlebars-{version}-cp310-abi3-{target.platform}.whl'
    if wheel.name != expected:
        raise VerificationError(f'smoke wheel must be {expected}')
    manifest = read_manifest(candidate / 'release-manifest.json', version)
    if sha256_file(wheel) != manifest[expected]:
        raise VerificationError('smoke wheel bytes do not match the retained candidate')
    verify_wheel(wheel, target, version)


def _parse_results(values: Sequence[str]) -> dict[str, str]:
    results: dict[str, str] = {}
    for value in values:
        key, separator, status = value.partition('=')
        if not separator or key in results:
            raise VerificationError(f'invalid result: {value}')
        results[key] = status
    return results


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)

    release = subparsers.add_parser('release')
    release.add_argument('--tag-env', required=True)
    release.add_argument('--mode', required=True)
    release.add_argument('--cargo', type=Path, required=True)
    release.add_argument('--pyproject', type=Path, required=True)
    release.add_argument('--github-output', type=Path, required=True)

    gate = subparsers.add_parser('gate')
    gate.add_argument('--result', action='append', default=[])

    stage = subparsers.add_parser('stage')
    stage.add_argument('--artifacts', type=Path, required=True)
    stage.add_argument('--candidate', type=Path, required=True)
    stage.add_argument('--version', type=Version, required=True)

    verify = subparsers.add_parser('verify-candidate')
    verify.add_argument('--candidate', type=Path, required=True)
    verify.add_argument('--version', type=Version, required=True)

    upload = subparsers.add_parser('verify-upload')
    upload.add_argument('--candidate', type=Path, required=True)
    upload.add_argument('--upload-dir', type=Path, required=True)
    upload.add_argument('--version', type=Version, required=True)

    smoke = subparsers.add_parser('verify-smoke-wheel')
    smoke.add_argument('--candidate', type=Path, required=True)
    smoke.add_argument('--wheel', type=Path, required=True)
    smoke.add_argument('--target', required=True)
    smoke.add_argument('--version', type=Version, required=True)

    reconcile = subparsers.add_parser('reconcile')
    reconcile.add_argument('--repository-url', required=True)
    reconcile.add_argument('--candidate', type=Path, required=True)
    reconcile.add_argument('--upload-dir', type=Path)
    reconcile.add_argument('--version', type=Version, required=True)
    reconcile.add_argument('--require-complete', action='store_true')
    reconcile.add_argument('--github-output', type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run release verification from a workflow or local checkout."""
    args = _parser().parse_args(argv)
    try:
        if args.command == 'release':
            tag = os.environ.get(args.tag_env)
            if tag is None:
                raise VerificationError(f'missing tag environment variable: {args.tag_env}')
            version = verify_release_versions(tag, args.cargo, args.pyproject, mode=args.mode)
            with args.github_output.open('a') as output:
                output.write(f'package_version={version}\nrelease_tag={tag}\n')
        elif args.command == 'gate':
            if not publish_gate(_parse_results(args.result)):
                raise VerificationError('result gate requires six successful jobs')
        elif args.command == 'stage':
            stage_wheels(args.artifacts, args.candidate, args.version)
        elif args.command == 'verify-candidate':
            verify_candidate(args.candidate, args.version)
        elif args.command == 'verify-upload':
            verify_upload(args.candidate, args.upload_dir, args.version)
        elif args.command == 'verify-smoke-wheel':
            verify_smoke_wheel(args.candidate, args.wheel, args.target, args.version)
        elif args.command == 'reconcile':
            _, json_base_url = repository_urls(args.repository_url)
            local = verify_candidate(args.candidate, args.version)
            remote = fetch_index_files(json_base_url, args.version)
            missing = reconcile_index(remote, local)
            if args.require_complete:
                if missing:
                    raise VerificationError(f'registry is still missing files: {sorted(missing)}')
            else:
                if args.upload_dir is None:
                    raise VerificationError('--upload-dir is required when staging missing files')
                stage_missing(args.candidate, args.upload_dir, args.version, remote)
            if args.github_output is not None:
                with args.github_output.open('a') as output:
                    output.write(f'missing_count={len(missing)}\n')
    except (ValueError, KeyError, OSError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
