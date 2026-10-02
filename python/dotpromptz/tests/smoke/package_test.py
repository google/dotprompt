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

"""Smoke tests for package structure."""

from dotpromptz import Dotprompt


def square(n: int | float) -> int | float:
    return n * n


def test_package_import() -> None:
    dp = Dotprompt()
    assert dp is not None


def test_square() -> None:
    assert square(2) == 4
    assert square(3) == 9
    assert square(4) == 16
