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

import nox

# See: https://github.com/astral-sh/uv/issues/6579
nox.options.default_venv_backend = 'uv|virtualenv'

PYTHON_VERSIONS = [
    '3.10',
    '3.11',
    '3.12',
    '3.13',
    #'3.14', # This still fails.
]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Runs the test suite.

    Args:
        session: The nox session object.

    Returns:
        None
    """
    session.run(
        'uv',
        'run',
        '--active',
        '--directory',
        'handlebarrz',
        'maturin',
        'develop',
    )

    session.run(
        'uv',
        'run',
        '--active',
        'pytest',
        '-v',
        '.',
        *session.posargs,
        external=True,
    )


@nox.session
def lint(session: nox.Session) -> None:
    """Run linters.

    Args:
        session: The nox session object.

    Returns:
        None
    """
    session.log('Running linters')
    session.log('Running ruff format check')
    session.run('uv', 'run', 'ruff', 'format', '--check', '.', external=True)
    session.log('Running ruff checks')
    session.run('uv', 'run', 'ruff', 'check', '--preview', '--unsafe-fixes', '--fix', '.', external=True)
    # session.log("Running mypy checks") # mypy has many errors currently
    # session.run("mypy", external=True)
