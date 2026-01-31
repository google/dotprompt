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

"""Generic Dart Bazel rules.

This module provides reusable Bazel rules for building and testing Dart code.
The Dart SDK is automatically downloaded via the dart_sdk repository rule
in repositories.bzl, similar to how rules_go and rules_rust work.

Key Rules:
    - dart_library: Creates a Dart library target
    - dart_binary: Creates an executable Dart binary
    - dart_test: Runs Dart tests

Usage in BUILD files:
    load("@rules_dart//:defs.bzl", "dart_library", "dart_test")

    dart_library(
        name = "my_lib",
        srcs = glob(["lib/**/*.dart"]),
    )

    dart_test(
        name = "my_test",
        main = "test/my_test.dart",
        deps = [":my_lib"],
    )

Note: Dart tests require the package dependencies to be resolved first.
Run `dart pub get` in the package directory before running Bazel tests.
"""

# Path to the downloaded Dart SDK binary
DART_SDK = "@dart_sdk//:dart_bin"

# Runfiles path to the Dart SDK binary (works in sandboxed tests)
_DART_SDK_RUNFILES_PATH = "+dart+dart_sdk/bin/dart"

def dart_library(name, srcs = [], deps = [], visibility = None, **kwargs):
    """Creates a Dart library target.

    This is a lightweight wrapper that creates a filegroup for Dart sources.
    Dart's module system handles the actual compilation.

    Args:
        name: Name of the library target.
        srcs: List of Dart source files.
        deps: List of dependencies (other dart_library targets).
        visibility: Visibility declaration.
        **kwargs: Additional arguments passed to native.filegroup.
    """
    native.filegroup(
        name = name,
        srcs = srcs,
        visibility = visibility,
        **kwargs
    )

def dart_binary(name, main, srcs = [], deps = [], visibility = None, **kwargs):
    """Creates a Dart binary target.

    Args:
        name: Name of the binary target.
        main: Main Dart file to execute.
        srcs: Additional Dart source files.
        deps: List of dependencies.
        visibility: Visibility declaration.
        **kwargs: Additional arguments passed to native.sh_binary.
    """
    script_name = name + "_runner"

    native.genrule(
        name = script_name,
        srcs = [main] + srcs,
        outs = [name + ".sh"],
        tools = [DART_SDK],
        cmd = """
cat > $@ << 'EOF'
#!/bin/bash
set -e
cd "$$BUILD_WORKSPACE_DIRECTORY"

# Use the hermetic Dart SDK from runfiles or fallback
RUNFILES="$${{RUNFILES:-$$0.runfiles}}"
DART_BIN="$$RUNFILES/{dart_sdk_path}"
if [ ! -f "$$DART_BIN" ]; then
    DART_BIN="dart"
fi

exec "$$DART_BIN" run $(location {main}) "$$@"
EOF
chmod +x $@
""".format(main = main, dart_sdk_path = _DART_SDK_RUNFILES_PATH),
        executable = True,
    )

    native.sh_binary(
        name = name,
        srcs = [":" + script_name],
        data = [main, DART_SDK] + srcs + deps,
        visibility = visibility,
        **kwargs
    )

def dart_test(name, main, srcs = [], deps = [], data = [], visibility = None, package_dir = None, **kwargs):
    """Creates a Dart test target.

    The test uses the hermetic Dart SDK downloaded by the dart_sdk repository
    rule.

    Args:
        name: Name of the test target.
        main: Main test file to execute (relative to package_dir/test/).
        srcs: Additional Dart source files.
        deps: List of dependencies.
        data: Data files needed by the test.
        visibility: Visibility declaration.
        package_dir: The Dart package directory (defaults to dart/dotprompt).
        **kwargs: Additional arguments passed to native.sh_test.
    """
    script_name = name + "_runner"
    pkg_dir = package_dir or "dart/dotprompt"

    native.genrule(
        name = script_name,
        srcs = [main] + srcs,
        outs = [name + "_test.sh"],
        tools = [DART_SDK],
        cmd = """
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
DART_BIN="$$RUNFILES/{dart_sdk_path}"
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

# Change to the package directory
cd "$$TEMP_DIR/{pkg_dir}"

# Get dependencies (required for dart test)
"$$DART_BIN" pub get --offline 2>/dev/null || "$$DART_BIN" pub get

# Run the specific test file (test files are in test/ subdirectory)
"$$DART_BIN" test test/{main}
EOF
chmod +x $@
""".format(
            main = main,
            dart_sdk_path = _DART_SDK_RUNFILES_PATH,
            pkg_dir = pkg_dir,
            pkg_name = pkg_dir.split("/")[-1],
        ),
        executable = True,
    )

    # Build the data dependencies, avoiding duplicates for handlebarrz
    data_deps = [
        main,
        DART_SDK,
        "//" + pkg_dir + ":" + pkg_dir.split("/")[-1],
        "//" + pkg_dir + ":pubspec.yaml",
    ]
    # Include handlebarrz as a dependency only if we're not testing handlebarrz itself
    if pkg_dir != "dart/handlebarrz":
        data_deps.append("//dart/handlebarrz:handlebarrz")
        data_deps.append("//dart/handlebarrz:pubspec.yaml")

    native.sh_test(
        name = name,
        srcs = [":" + script_name],
        data = data_deps + srcs + deps + data,
        visibility = visibility,
        tags = kwargs.pop("tags", []) + ["requires-network"],
        **kwargs
    )
