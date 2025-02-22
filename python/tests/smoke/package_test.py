# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Smoke tests for package structure."""

from dotpromptz import package_name as dotpromptz_package_name


def square(n: int | float) -> int | float:
    """Calculates the square of a number.

    Args:
        n: The number to square.

    Returns:
       The square of n.
    """
    return n * n


def test_package_names() -> None:
    """Smoke test to ensure that package imports work."""
    assert dotpromptz_package_name() == 'dotpromptz'


# TODO: Failing test on purpose to be removed after we complete
# this runtime and stop skipping all failures.
def test_skip_failures() -> None:
    """Purposeful failing test.

    To be removed after we complete the runtime implementation and stop skipping
    all failures.
    """
    assert dotpromptz_package_name() == 'skip.failures'


def test_square() -> None:
    """Tests whether the square function calculates the square of n."""
    assert square(2) == 4
    assert square(3) == 9
    assert square(4) == 16
