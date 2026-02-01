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

"""Dotprompt-specific Bazel macros for Dart.

This module provides macros specific to the Dotprompt project, such as
spec test runners. These are NOT part of the generic rules_dart package.
"""

load("@rules_dart//:defs.bzl", "DART_SDK")

# Runfiles path to the Dart SDK binary
# Removed: _DART_SDK_RUNFILES_PATH (using dynamic resolution now)

def dart_spec_test(name, spec_file, deps = [], **kwargs):
    """Creates a Dart spec test target that runs against a YAML spec file.

    This is a Dotprompt-specific macro that creates a Dart test target
    that passes the spec file path via the SPEC_FILE environment variable,
    following the pattern from rust_spec_test and java_spec_test.

    The test runs the spec_test.dart file which reads the YAML spec and
    validates the Dart implementation against the expected behavior.

    NOTE: This macro is specific to dotprompt and should NOT be included
    in the generic rules_dart package.

    For generic Dart rules, use @rules_dart//:defs.bzl instead.

    Args:
        name: Name of the test target.
        spec_file: Label of the YAML spec file to test against.
        deps: Additional dependencies for the test (unused, kept for API compat).
        **kwargs: Additional arguments to pass to the test.
    """

    # Extract spec path from label (assuming //spec:file.yaml format)
    spec_path = spec_file.replace("//", "").replace(":", "/")

    script_name = name + "_runner"

    # We use explicit double-dollar signs for Bazel Make variable escaping in the shell script
    # and double-braces for Python format string escaping.
    cmd_template = """
cat > $@ << 'EOF'
#!/bin/bash
set -e

# Find the runfiles directory
if [[ -n "$${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$$TEST_SRCDIR"
elif [[ -d "$$0.runfiles" ]]; then
    RUNFILES="$$0.runfiles"
elif [[ -d "$${{BASH_SOURCE[0]}}.runfiles" ]]; then
    RUNFILES="$${{BASH_SOURCE[0]}}.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

# Find the Dart SDK
DART_BIN="$$RUNFILES/$(rlocationpath {dart_sdk})"
if [ ! -f "$$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $$DART_BIN" >&2
    exit 1
fi

# Get the workspace root from runfiles
WORKSPACE_ROOT="$$RUNFILES/_main"

# Copy the package to a temp directory so we can run dart test
TEMP_DIR=$$(mktemp -d)
trap "rm -rf $$TEMP_DIR" EXIT

# Set up environment for Dart pub (sandbox doesn't have HOME)
export HOME="$$TEMP_DIR"
export PUB_CACHE="$$TEMP_DIR/.pub-cache"
mkdir -p "$$PUB_CACHE"

# Copy the entire dart directory to preserve path dependencies
cp -r "$$WORKSPACE_ROOT/dart" "$$TEMP_DIR/"

# Copy the spec file to the temp dir preserving directory structure
mkdir -p "$$TEMP_DIR/{spec_dir}"
cp "$$WORKSPACE_ROOT/{spec_path}" "$$TEMP_DIR/{spec_path}"

# Change to the package directory
cd "$$TEMP_DIR/dart/dotprompt"

# Get dependencies (required for dart test)
"$$DART_BIN" pub get --offline 2>/dev/null || "$$DART_BIN" pub get

# Set the spec file path (relative to dart/dotprompt in temp dir)
export SPEC_FILE="../../{spec_path}"

# Run the spec test
"$$DART_BIN" test test/spec_test.dart
EOF
chmod +x $@
"""

    native.genrule(
        name = script_name,
        srcs = [],
        outs = [name + "_spec.sh"],
        tools = [DART_SDK],
        cmd = cmd_template.format(
            spec_path = spec_path,
            spec_dir = "/".join(spec_path.split("/")[:-1]),
            dart_sdk = DART_SDK,
        ),
        executable = True,
    )

    native.sh_test(
        name = name,
        srcs = [":" + script_name],
        data = [
            spec_file,
            DART_SDK,
            "//dart/dotprompt:dotprompt",
            "//dart/dotprompt:pubspec.yaml",
            "//dart/dotprompt:test/spec_test.dart",
            # Include handlebarrz as it's a path dependency
            "//dart/handlebarrz:handlebarrz",
            "//dart/handlebarrz:pubspec.yaml",
        ],
        tags = kwargs.pop("tags", []) + ["requires-network"],
        **kwargs
    )
