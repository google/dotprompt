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

"""
This file contains custom rules.

- vitest_test: Runs tests with Vitest.
"""

load("@npm//:vitest/package_json.bzl", vitest_bin = "bin")

def vitest_test(name, srcs, deps = [], data = [], size = "small", run_args = [], visibility = ["//visibility:public"], config = None):
    """Runs Vitest tests.

    Args:
      name: The name of the test target.
      srcs: List of test source files.
      deps: List of dependencies.
      data: List of data files.
      size: Test size (e.g., "small", "medium").
      run_args: Additional arguments to pass to Vitest.
      visibility: Target visibility.
      config: Optional Vitest configuration file label.
    """
    data_deps = srcs + deps + data + [
        "//:node_modules",
    ]
    if config:
        data_deps.append(config)

    vitest_bin.vitest_test(
        name = name,
        size = size,
        args = ["run"] + run_args,
        chdir = native.package_name(),
        visibility = visibility,
        data = data_deps,
    )
