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

"""Bazel macros for dotprompt Java spec tests."""

def java_spec_test(name, spec_file):
    """Creates a java_test target for a specific spec YAML file.

    This macro generates separate test targets for each spec YAML file,
    enabling granular pass/fail reporting in Bazel output.

    Args:
        name: The name of the test target.
        spec_file: The label of the spec YAML file to run.

    Example:
        java_spec_test(
            name = "SpecTest_metadata",
            spec_file = "//spec:metadata.yaml",
        )
    """
    native.java_test(
        name = name,
        srcs = ["SpecTest.java"],
        data = [spec_file],
        jvm_flags = ["-Dspec.file=$(location " + spec_file + ")"],
        test_class = "com.google.dotprompt.SpecTest",
        deps = [
            "//java/com/google/dotprompt:dotprompt",
            "//java/com/google/dotprompt/models",
            "//java/com/google/dotprompt/resolvers",
            "@maven//:com_fasterxml_jackson_core_jackson_databind",
            "@maven//:com_fasterxml_jackson_dataformat_jackson_dataformat_yaml",
            "@maven//:com_google_guava_guava",
            "@maven//:com_google_truth_truth",
            "@maven//:junit_junit",
        ],
    )
