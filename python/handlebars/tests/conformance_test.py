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

"""The supported subset, checked against Handlebars 4.7.8.

Real prompts are mostly a variable, an if, an each, an else, a dotted path,
or a partial. Those cases are the ``reality`` layer. The other layers walk
the edges of that same subset: paths, blocks, partials, and whitespace.
Decorators, raw blocks, and ``.5`` are refused on purpose and are not here.

``text`` is what Handlebars 4.7.8 renders. ``raises`` means both sides
reject the template. The wording of the error is not compared.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from handlebars import Handlebars, StrictModeError

_CASES = json.loads(Path(__file__).with_name('conformance_cases.json').read_text())
_REFERENCE = '4.7.8'


def _upper(args, options):
    value = args[0] if args else ''
    return '' if value is None else str(value).upper()


def _add(args, options):
    def num(value):
        if value is None or value is False:
            return 0
        if value is True:
            return 1
        if isinstance(value, int | float):
            return value
        return float(value)

    left = num(args[0]) if args else 0
    right = num(args[1]) if len(args) > 1 else 0
    return left + right


def _ident(args, options):
    return args[0] if args else None


def _wrap(args, options):
    if options.is_block and not args:
        return options.fn()
    prefix = options.hash.get('prefix') or ''
    value = '' if not args or args[0] is None else args[0]
    return f'{prefix}[{value}]'


def _eq(args, options):
    same = len(args) >= 2 and args[0] == args[1]
    if options.is_block:
        return options.fn() if same else options.inverse()
    return same


_HELPERS = {'upper': _upper, 'add': _add, 'ident': _ident, 'wrap': _wrap, 'eq': _eq}


def _render(case):
    hb = Handlebars(strict=bool(case['strict']))
    for name in case['helpers']:
        hb.register_helper(name, _HELPERS[name])
    for name, source in case['partials'].items():
        hb.register_partial(name, source)
    return hb.compile(case['template'])(case['context'], data=case['data'])


@pytest.mark.parametrize('case', _CASES, ids=[case['name'] for case in _CASES])
def test_conformance(case):
    if case.get('raises'):
        with pytest.raises((ValueError, StrictModeError)):
            _render(case)
        return
    assert _render(case) == case['text']


def _reference_engine():
    candidates = [
        os.environ.get('HANDLEBARS_JS'),
        '/tmp/hbjs/node_modules/handlebars',
    ]
    for candidate in candidates:
        if not candidate:
            continue
        package = Path(candidate, 'package.json')
        if not package.is_file():
            continue
        version = json.loads(package.read_text()).get('version')
        if version == _REFERENCE:
            return candidate
    return None


def test_recorded_output_still_matches_handlebars_4_7_8():
    root = _reference_engine()
    if root is None or shutil.which('node') is None:
        pytest.skip('Handlebars 4.7.8 is not installed')
    script = Path(__file__).with_name('conformance_oracle.js')
    cases = Path(__file__).with_name('conformance_cases.json')
    result = subprocess.run(
        ['node', str(script), root, str(cases)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
