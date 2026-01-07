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

"""Rust-specific Bazel build definitions for dotprompt."""

load("@rules_rust//rust:defs.bzl", "rust_test")

def rust_spec_test(name, spec_file, deps = [], **kwargs):
    """Macro to create a Rust spec test that runs against a YAML spec file.

    This macro creates a rust_test target that passes the spec file path
    via an environment variable, following the pattern from java_spec_test.

    Args:
        name: Name of the test target
        spec_file: Label of the YAML spec file to test against
        deps: Additional dependencies for the test
        **kwargs: Additional arguments to pass to rust_test
    """

    # specific spec file path (assuming //spec:file.yaml format)
    spec_path = spec_file.replace("//", "").replace(":", "/")

    rust_test(
        name = name,
        srcs = ["tests/spec_test.rs"],
        deps = deps + [
            "@crates//:serde",
            "@crates//:serde_json",
            "@crates//:serde_yaml",
        ],
        data = [spec_file],
        env = {
            "SPEC_FILE": spec_path,
        },
        **kwargs
    )
