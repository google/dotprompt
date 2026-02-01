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

"""Unix script generation for rules_dart.

This module provides functions to generate Unix shell (.sh) scripts
for Dart compilation and execution. Scripts are designed for standard
/bin/bash and work on macOS and Linux (x64, arm64).

Script Structure:
┌──────────────────────────────────────────────────────────────────────────┐
│                      Unix Shell Script Pattern                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  #!/bin/bash                         # Standard bash interpreter         │
│  set -e                              # Exit on first error               │
│                                                                          │
│  # Locate runfiles directory                                             │
│  if [[ -n "${TEST_SRCDIR:-}" ]]; then                                   │
│      RUNFILES="$TEST_SRCDIR"         # Bazel test mode                   │
│  elif [[ -d "$0.runfiles" ]]; then                                      │
│      RUNFILES="$0.runfiles"          # Direct execution                  │
│  fi                                                                      │
│                                                                          │
│  DART_BIN="$RUNFILES/path/to/dart"   # Set Dart SDK path                 │
│                                                                          │
│  "$DART_BIN" compile exe ...         # Execute Dart command              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Key Patterns:
- Use `set -e` for fail-fast behavior
- Check TEST_SRCDIR for Bazel test environment
- Quote all variable expansions
- Use `exec` for final command when possible
"""

# Note: runfiles_path is available from helpers.bzl if needed
# load("@rules_dart//private:helpers.bzl", "runfiles_path")  # @unused

def generate_binary_script(dart_path, main_path):
    """Generate a Unix script to run a Dart binary.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        main_path: Path to main Dart file

    Returns:
        String content of the shell script
    """
    return """#!/bin/bash
set -e
cd "$BUILD_WORKSPACE_DIRECTORY"

RUNFILES="${{RUNFILES:-$0.runfiles}}"
DART_BIN="$RUNFILES/{dart_path}"

if [ ! -f "$DART_BIN" ]; then
    DART_BIN="dart"
fi

exec "$DART_BIN" run {main} "$@"
""".format(
        dart_path = dart_path,
        main = main_path,
    )

def generate_test_script(dart_path, pkg_dir, test_file):
    """Generate a Unix script to run Dart tests.

    Creates a hermetic test environment by copying the workspace
    to a temporary directory and running pub get before tests.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        test_file: Path to test file (relative to package)

    Returns:
        String content of the shell script
    """
    return """#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$TEST_SRCDIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$RUNFILES/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $DART_BIN" >&2
    exit 1
fi

WORKSPACE_ROOT="$RUNFILES/_main"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

export HOME="$TEMP_DIR"
export PUB_CACHE="$TEMP_DIR/.pub-cache"
mkdir -p "$PUB_CACHE"

cp -R "$WORKSPACE_ROOT"/. "$TEMP_DIR/"
cd "$TEMP_DIR/{pkg_dir}"

"$DART_BIN" pub get --offline 2>/dev/null || "$DART_BIN" pub get
"$DART_BIN" test {main}
""".format(
        dart_path = dart_path,
        pkg_dir = pkg_dir,
        main = test_file,
    )

def generate_format_check_script(dart_path, pkg_dir):
    """Generate a Unix script to check Dart formatting.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path

    Returns:
        String content of the shell script
    """
    return """#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$TEST_SRCDIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$RUNFILES/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $DART_BIN" >&2
    exit 1
fi

WORKSPACE_ROOT="$RUNFILES/_main"
cd "$WORKSPACE_ROOT/{pkg_dir}"

"$DART_BIN" format --set-exit-if-changed --output=none lib/ test/ 2>/dev/null || {{
    echo "ERROR: Code is not properly formatted. Run 'dart format .' to fix." >&2
    exit 1
}}
""".format(
        dart_path = dart_path,
        pkg_dir = pkg_dir,
    )

def generate_analyze_script(dart_path, pkg_dir):
    """Generate a Unix script to run Dart static analysis.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path

    Returns:
        String content of the shell script
    """
    return """#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$TEST_SRCDIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$RUNFILES/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $DART_BIN" >&2
    exit 1
fi

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT
export HOME="$TEMP_DIR"
export PUB_CACHE="$TEMP_DIR/.pub-cache"
mkdir -p "$PUB_CACHE"

WORKSPACE_ROOT="$RUNFILES/_main"
cp -R "$WORKSPACE_ROOT"/. "$TEMP_DIR/"
cd "$TEMP_DIR/{pkg_dir}"

"$DART_BIN" pub get --offline 2>/dev/null || "$DART_BIN" pub get
"$DART_BIN" analyze --fatal-infos --fatal-warnings
""".format(
        dart_path = dart_path,
        pkg_dir = pkg_dir,
    )

def generate_doc_script(dart_path, pkg_dir, out_dir):
    """Generate a Unix script to build Dart documentation.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        out_dir: Output directory for generated docs

    Returns:
        String content of the shell script
    """
    return """#!/bin/bash
set -e
cd "$BUILD_WORKSPACE_DIRECTORY/{pkg_dir}"

RUNFILES="${{RUNFILES:-$0.runfiles}}"
DART_BIN="$RUNFILES/{dart_path}"

if [ ! -f "$DART_BIN" ]; then
    DART_BIN="dart"
fi

"$DART_BIN" pub get
"$DART_BIN" doc --output={out_dir}
echo "Documentation generated at {pkg_dir}/{out_dir}"
""".format(
        dart_path = dart_path,
        pkg_dir = pkg_dir,
        out_dir = out_dir,
    )

def generate_tool_script(dart_path, pkg_dir, command, args_str):
    """Generate a Unix script to run a Dart tool command.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        command: Dart command to run (e.g., "pub", "compile")
        args_str: Additional arguments as a string

    Returns:
        String content of the shell script
    """
    return """#!/bin/bash
set -e
cd "${{BUILD_WORKSPACE_DIRECTORY}}/{pkg_dir}"

RUNFILES="${{RUNFILES:-$0.runfiles}}"
DART_BIN="$RUNFILES/{dart_path}"

if [ ! -f "$DART_BIN" ]; then
    echo "Warning: Hermetic Dart SDK not found, falling back to system dart" >&2
    DART_BIN="dart"
fi

echo "Executing: $DART_BIN {command} {args} $@"
exec "$DART_BIN" {command} {args} "$@"
""".format(
        dart_path = dart_path,
        pkg_dir = pkg_dir,
        command = command,
        args = args_str,
    )

def generate_compile_script(dart_path, pkg_dir, main_path, _output_path, compile_cmd, extra_args = ""):
    """Generate a Unix script for Dart compilation.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        main_path: Path to main Dart file
        _output_path: Path for compiled output (managed internally)
        compile_cmd: Compile target (exe, js, wasm, aot-snapshot)
        extra_args: Additional compile arguments

    Returns:
        String content of the shell script
    """
    return """#!/bin/bash
set -e

if [[ -n "${{TEST_SRCDIR:-}}" ]]; then
    RUNFILES="$TEST_SRCDIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

DART_BIN="$RUNFILES/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    echo "ERROR: Dart SDK not found at $DART_BIN" >&2
    exit 1
fi

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

export HOME="$TEMP_DIR"
export PUB_CACHE="$TEMP_DIR/.pub-cache"
mkdir -p "$PUB_CACHE"

WORKSPACE_ROOT="$RUNFILES/_main"
cp -R "$WORKSPACE_ROOT"/. "$TEMP_DIR/"
cd "$TEMP_DIR/{pkg_dir}"

"$DART_BIN" pub get --offline 2>/dev/null || "$DART_BIN" pub get

echo "Compiling to {compile_cmd}..."
"$DART_BIN" compile {compile_cmd} {extra_args} -o "$TEMP_DIR/output" {main}

cp "$TEMP_DIR"/output* "$BUILD_WORKING_DIRECTORY/" 2>/dev/null || true
""".format(
        dart_path = dart_path,
        pkg_dir = pkg_dir,
        main = main_path,
        compile_cmd = compile_cmd,
        extra_args = extra_args,
    )
