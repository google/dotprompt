# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Smoke tests for package structure."""

# TODO: Replace this with proper imports once we have a proper implementation.
from dotpromptz import package_name as dotpromptz_package_name
from handlebarz import package_name as handlebarz_package_name


def square(n: int | float) -> int | float:
    return n * n


def test_package_names() -> None:
    assert handlebarz_package_name() == 'handlebarz'
    assert dotpromptz_package_name() == 'dotpromptz'


def test_square() -> None:
    assert square(2) == 4
    assert square(3) == 9
    assert square(4) == 16
