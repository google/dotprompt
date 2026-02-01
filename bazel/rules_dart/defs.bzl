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
# Path to the downloaded Dart SDK binary
# We use Label() to ensure it resolves relative to the rules_dart module,
# making it portable regardless of how the consuming workspace names the repo.
DART_SDK = Label("@dart_sdk//:dart_bin")

def dart_library(name, srcs = [], deps = [], pubspec = None, visibility = None, **kwargs):
    """Creates a Dart library target.

    This is a lightweight wrapper that creates a filegroup for Dart sources.
    Dart's module system handles the actual compilation.

    Args:
        name: Name of the library target.
        srcs: List of Dart source files.
        deps: List of dependencies (other dart_library targets).
        pubspec: The pubspec.yaml file (optional).
        visibility: Visibility declaration.
        **kwargs: Additional arguments passed to native.filegroup.
    """
    all_srcs = srcs + deps
    if pubspec and pubspec not in all_srcs:
        all_srcs.append(pubspec)

    native.filegroup(
        name = name,
        srcs = all_srcs,
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
DART_BIN="$$RUNFILES/$(rlocationpath {dart_sdk})"
if [ ! -f "$$DART_BIN" ]; then
    DART_BIN="dart"
fi

exec "$$DART_BIN" run $(location {main}) "$$@"
EOF
chmod +x $@
""".format(main = main, dart_sdk = DART_SDK),
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
        package_dir: The Dart package directory (defaults to current package).
        **kwargs: Additional arguments passed to native.sh_test.
    """
    script_name = name + "_runner"
    pkg_dir = package_dir or native.package_name()

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

# Copy the entire workspace to preserve path dependencies
cp -R "$$WORKSPACE_ROOT"/. "$$TEMP_DIR/"

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
            dart_sdk = DART_SDK,
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



    native.sh_test(
        name = name,
        srcs = [":" + script_name],
        data = data_deps + srcs + deps + data,
        visibility = visibility,
        tags = kwargs.pop("tags", []) + ["requires-network"],
        **kwargs
    )

def dart_format_check(name, srcs = [], package_dir = None, visibility = None, **kwargs):
    """Creates a Dart format check target for CI.

    Verifies that Dart source files are properly formatted.

    Args:
        name: Name of the format check target.
        srcs: Dart source files to check (defaults to lib/**/*.dart).
        package_dir: The Dart package directory.
        visibility: Visibility declaration.
        **kwargs: Additional arguments passed to native.sh_test.
    """
    script_name = name + "_runner"
    pkg_dir = package_dir or native.package_name()

    native.genrule(
        name = script_name,
        srcs = srcs,
        outs = [name + "_format.sh"],
        tools = [DART_SDK],
        cmd = """
cat > $@ << 'EOF'
#!/bin/bash
set -e

# Find the runfiles directory
if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$$TEST_SRCDIR"
elif [[ -d "$$0.runfiles" ]]; then
    RUNFILES="$$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$$RUNFILES/$(rlocationpath {dart_sdk})"
if [ ! -f "$$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $$DART_BIN" >&2
    exit 1
fi

WORKSPACE_ROOT="$$RUNFILES/_main"
cd "$$WORKSPACE_ROOT/{pkg_dir}"

# Run dart format --set-exit-if-changed
"$$DART_BIN" format --set-exit-if-changed --output=none lib/ test/ 2>/dev/null || {{
    echo "ERROR: Code is not properly formatted. Run 'dart format .' to fix." >&2
    exit 1
}}
EOF
chmod +x $@
""".format(
            dart_sdk = DART_SDK,
            pkg_dir = pkg_dir,
        ),
        executable = True,
    )

    native.sh_test(
        name = name,
        srcs = [":" + script_name],
        data = [
            DART_SDK,
            "//" + pkg_dir + ":" + pkg_dir.split("/")[-1],
        ] + srcs,
        visibility = visibility,
        **kwargs
    )

def dart_analyze(name, srcs = [], package_dir = None, visibility = None, **kwargs):
    """Creates a Dart static analysis target.

    Runs dart analyze with fatal-infos and fatal-warnings.

    Args:
        name: Name of the analyze target.
        srcs: Dart source files to analyze.
        package_dir: The Dart package directory.
        visibility: Visibility declaration.
        **kwargs: Additional arguments passed to native.sh_test.
    """
    script_name = name + "_runner"
    pkg_dir = package_dir or native.package_name()

    native.genrule(
        name = script_name,
        srcs = srcs,
        outs = [name + "_analyze.sh"],
        tools = [DART_SDK],
        cmd = """
cat > $@ << 'EOF'
#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$$TEST_SRCDIR"
elif [[ -d "$$0.runfiles" ]]; then
    RUNFILES="$$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$$RUNFILES/$(rlocationpath {dart_sdk})"
if [ ! -f "$$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $$DART_BIN" >&2
    exit 1
fi

TEMP_DIR=$$(mktemp -d)
trap "rm -rf $$TEMP_DIR" EXIT
export HOME="$$TEMP_DIR"
export PUB_CACHE="$$TEMP_DIR/.pub-cache"
mkdir -p "$$PUB_CACHE"

WORKSPACE_ROOT="$$RUNFILES/_main"
cp -R "$$WORKSPACE_ROOT"/. "$$TEMP_DIR/"
cd "$$TEMP_DIR/{pkg_dir}"

"$$DART_BIN" pub get --offline 2>/dev/null || "$$DART_BIN" pub get
"$$DART_BIN" analyze --fatal-infos --fatal-warnings
EOF
chmod +x $@
""".format(
            dart_sdk = DART_SDK,
            pkg_dir = pkg_dir,
        ),
        executable = True,
    )

    data_deps = [
        DART_SDK,
        "//" + pkg_dir + ":" + pkg_dir.split("/")[-1],
        "//" + pkg_dir + ":pubspec.yaml",
    ]


    native.sh_test(
        name = name,
        srcs = [":" + script_name],
        data = data_deps + srcs,
        visibility = visibility,
        tags = kwargs.pop("tags", []) + ["requires-network"],
        **kwargs
    )

def dart_doc(name, srcs = [], package_dir = None, output_dir = None, visibility = None, **kwargs):
    """Creates a Dart documentation generation target.

    Generates API documentation using dart doc.

    Args:
        name: Name of the doc target.
        srcs: Dart source files.
        package_dir: The Dart package directory.
        output_dir: Output directory for docs (defaults to doc/api).
        visibility: Visibility declaration.
        **kwargs: Additional arguments passed to native.genrule.
    """
    script_name = name + "_runner"
    pkg_dir = package_dir or native.package_name()
    out_dir = output_dir or "doc/api"

    native.genrule(
        name = script_name,
        srcs = srcs,
        outs = [name + "_doc.sh"],
        tools = [DART_SDK],
        cmd = """
cat > $@ << 'EOF'
#!/bin/bash
set -e
cd "$$BUILD_WORKSPACE_DIRECTORY/{pkg_dir}"

RUNFILES="${{RUNFILES:-$$0.runfiles}}"
DART_BIN="$$RUNFILES/$(rlocationpath {dart_sdk})"
if [ ! -f "$$DART_BIN" ]; then
    DART_BIN="dart"
fi

"$$DART_BIN" pub get
"$$DART_BIN" doc --output={out_dir}
echo "Documentation generated at {pkg_dir}/{out_dir}"
EOF
chmod +x $@
""".format(
            dart_sdk = DART_SDK,
            pkg_dir = pkg_dir,
            out_dir = out_dir,
        ),
        executable = True,
    )

    native.sh_binary(
        name = name,
        srcs = [":" + script_name],
        data = [DART_SDK] + srcs,
        visibility = visibility,
        **kwargs
    )

def _dart_tool_target(name, command, args = [], package_dir = None, **kwargs):
    script_name = name + "_runner"
    pkg_dir = package_dir or native.package_name()
    
    native.genrule(
        name = script_name,
        outs = [name + ".sh"],
        tools = [DART_SDK],
        cmd = """
cat > $@ << 'EOF'
#!/bin/bash
set -e
# Run in the original workspace directory
cd "$${BUILD_WORKSPACE_DIRECTORY}/{pkg_dir}"

RUNFILES="$${{RUNFILES:-$$0.runfiles}}"
DART_BIN="$$RUNFILES/$(rlocationpath {dart_sdk})"

if [ ! -f "$$DART_BIN" ]; then
     if [[ -f "$$0.runfiles/$(rlocationpath {dart_sdk})" ]]; then
         DART_BIN="$$0.runfiles/$(rlocationpath {dart_sdk})"
     else
         echo "Warning: Hermetic Dart SDK not found in runfiles, falling back to system dart" >&2
         DART_BIN="dart"
     fi
fi

exec "$$DART_BIN" {command} {args} "$@"
EOF
chmod +x $@
""".format(
            pkg_dir = pkg_dir,
            dart_sdk = DART_SDK,
            command = command,
            args = " ".join(args),
        ),
        executable = True,
    )
    
    native.sh_binary(
        name = name,
        srcs = [":" + script_name],
        data = [DART_SDK],
        tags = kwargs.pop("tags", []) + ["local"],
        **kwargs
    )

def dart_format(name, package_dir = None, **kwargs):
    """Creates a target to format Dart code."""
    _dart_tool_target(name, "format", args = ["."], package_dir = package_dir, **kwargs)

def dart_pub_get(name, package_dir = None, **kwargs):
    """Creates a target to run 'dart pub get'."""
    _dart_tool_target(name, "pub", args = ["get"], package_dir = package_dir, **kwargs)

def dart_pub_publish(name, package_dir = None, dry_run = True, **kwargs):
    """Creates a target to publish to pub.dev."""
    args = ["publish"]
    if dry_run:
        args.append("--dry-run")
    _dart_tool_target(name, "pub", args = args, package_dir = package_dir, **kwargs)
