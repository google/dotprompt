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

"""Named errors are available from dotpromptz.errors, not the package root."""

from __future__ import annotations

import importlib

import pytest

from dotpromptz.errors import (
    DotpromptError,
    FrontmatterError,
    PartialCycleError,
    ResolverFailedError,
)


def test_package_root_exports_dotprompt_only() -> None:
    package = importlib.import_module('dotpromptz')

    assert package.__all__ == ['Dotprompt']
    assert package.Dotprompt.__name__ == 'Dotprompt'


def test_named_errors_import_from_errors_module() -> None:
    errors = importlib.import_module('dotpromptz.errors')

    assert errors.PartialCycleError is PartialCycleError
    assert errors.ResolverFailedError is ResolverFailedError
    assert errors.FrontmatterError is FrontmatterError
    assert errors.DotpromptError is DotpromptError


def test_named_errors_are_not_on_the_package_root() -> None:
    package = importlib.import_module('dotpromptz')

    with pytest.raises(ImportError):
        exec('from dotpromptz import PartialCycleError', {})
    with pytest.raises(ImportError):
        exec('from dotpromptz import ResolverFailedError', {})
    with pytest.raises(ImportError):
        exec('from dotpromptz import FrontmatterError', {})
    with pytest.raises(ImportError):
        exec('from dotpromptz import DotpromptError', {})

    assert not hasattr(package, 'PartialCycleError')
    assert not hasattr(package, 'ResolverFailedError')
    assert not hasattr(package, 'FrontmatterError')
    assert not hasattr(package, 'DotpromptError')
