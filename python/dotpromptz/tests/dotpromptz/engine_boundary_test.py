# Copyright 2026 Google LLC
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

"""Verify dotpromptz only imports from the public API of dotpromptz-handlebars."""

from __future__ import annotations

import ast
from pathlib import Path

import dotpromptz_handlebars


def _find_import_violations(source: str, filename: str = '<test>') -> list[str]:
    public_api = set(dotpromptz_handlebars.__all__)
    violations: list[str] = []
    tree = ast.parse(source, filename=filename)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith('dotpromptz_handlebars.'):
                    violations.append(f'{filename}:{node.lineno} imports private submodule {alias.name!r}')
                if alias.name == 'handlebarrz' or alias.name.startswith('handlebarrz.'):
                    violations.append(f'{filename}:{node.lineno} imports deleted package {alias.name!r}')
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            if mod == 'dotpromptz_handlebars':
                for alias in node.names:
                    if alias.name not in public_api:
                        violations.append(
                            f'{filename}:{node.lineno} imports private symbol {alias.name!r} from dotpromptz_handlebars'
                        )
            elif mod.startswith('dotpromptz_handlebars.'):
                violations.append(f'{filename}:{node.lineno} imports from private submodule {mod!r}')
            elif mod == 'handlebarrz' or mod.startswith('handlebarrz.'):
                violations.append(f'{filename}:{node.lineno} imports from deleted package {mod!r}')

    return violations


def test_dotpromptz_only_imports_from_public_handlebars_api() -> None:
    """Ensure all dotpromptz source files only import from dotpromptz_handlebars.__all__."""
    pkg_dir = Path(__file__).resolve().parent.parent.parent / 'src' / 'dotpromptz'
    source_files = sorted(pkg_dir.rglob('*.py'))
    assert source_files, f'No source files found in {pkg_dir}'

    all_violations: list[str] = []
    for src_file in source_files:
        rel_path = str(src_file.relative_to(pkg_dir))
        all_violations.extend(_find_import_violations(src_file.read_text(encoding='utf-8'), filename=rel_path))

    assert not all_violations, 'Found prohibited private imports from dotpromptz_handlebars:\n' + '\n'.join(
        all_violations
    )


def test_boundary_scanner_catches_private_and_deleted_imports() -> None:
    """Verify that _find_import_violations catches private submodule imports and non-exported symbols."""
    snippet = """
from dotpromptz_handlebars._render import compile_template, Mustache
from dotpromptz_handlebars import Handlebars, _compiler
import dotpromptz_handlebars._render
import handlebarrz
from handlebarrz import Context
"""
    violations = _find_import_violations(snippet, filename='test_sample.py')
    assert any('imports from private submodule' in v for v in violations)
    assert any('imports private symbol' in v for v in violations)
    assert any('imports private submodule' in v for v in violations)
    assert any('imports deleted package' in v for v in violations)
    assert len(violations) == 5
