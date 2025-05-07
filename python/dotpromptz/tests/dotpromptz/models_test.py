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

"""Unit tests for the models module."""

import unittest

from pydantic import BaseModel

from dotpromptz.models import dump_models


class TestModel(BaseModel):
    """Test model."""

    name: str
    age: int


class TestDumpList(unittest.TestCase):
    """Unit tests for the dump_list function."""

    def test_dump_list(self) -> None:
        """Test that dump_list returns the correct output."""
        self.assertEqual(dump_models([]), [])
        self.assertEqual(dump_models([TestModel(name='test', age=1)]), [{'name': 'test', 'age': 1}])
        self.assertEqual(
            dump_models([TestModel(name='test', age=1), TestModel(name='test2', age=2)]),
            [{'name': 'test', 'age': 1}, {'name': 'test2', 'age': 2}],
        )
