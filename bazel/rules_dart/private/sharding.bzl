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

"""Test sharding support for rules_dart.

This module provides utilities for running Dart tests in parallel shards,
significantly reducing test execution time for large test suites.

## Test Sharding Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Test Sharding Architecture                               │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Test Suite (100 tests)                                                          │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────┐                                                                 │
│  │  Sharding   │─── shard_count = 4                                             │
│  │  Logic      │                                                                 │
│  └─────────────┘                                                                 │
│       │                                                                          │
│       ├─────────────┬─────────────┬─────────────┐                               │
│       ▼             ▼             ▼             ▼                               │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐                          │
│  │ Shard 0 │   │ Shard 1 │   │ Shard 2 │   │ Shard 3 │                          │
│  │ 25 tests│   │ 25 tests│   │ 25 tests│   │ 25 tests│                          │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘                          │
│       │             │             │             │                               │
│       └─────────────┴─────────────┴─────────────┘                               │
│                          │                                                       │
│                          ▼                                                       │
│                    All tests pass                                                │
│                                                                                  │
│  Environment Variables (set by Bazel):                                           │
│  • TEST_SHARD_INDEX: Current shard (0-3)                                        │
│  • TEST_TOTAL_SHARDS: Total shards (4)                                          │
│  • TEST_SHARD_STATUS_FILE: Status file for shard                                │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```python
dart_sharded_test(
    name = "large_test",
    main = "test/all_test.dart",
    shard_count = 4,  # Run 4 shards in parallel
)
```
"""

load("@rules_dart//private:helpers.bzl", "runfiles_path")

# =============================================================================
# Sharding Provider
# =============================================================================

DartTestShardInfo = provider(
    doc = "Information about test sharding configuration.",
    fields = {
        "shard_count": "Int: Number of shards.",
        "shard_index": "Int: Current shard index (if known).",
        "test_files": "List[File]: All test files.",
        "uses_sharding": "Bool: Whether sharding is enabled.",
    },
)

# =============================================================================
# Sharded Test Implementation
# =============================================================================

def _dart_sharded_test_impl(ctx):
    """Implementation of dart_sharded_test rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    dart_bin = ctx.executable.dart_sdk
    dart_path = runfiles_path(dart_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package
    main_file = ctx.file.main.short_path if ctx.file.main else "test/"

    # Sharding configuration
    shard_count = ctx.attr.shard_count

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"
if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
)

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

REM Sharding support
set "SHARD_INDEX=%TEST_SHARD_INDEX%"
set "TOTAL_SHARDS=%TEST_TOTAL_SHARDS%"

if defined TOTAL_SHARDS (
    echo Running shard %SHARD_INDEX% of %TOTAL_SHARDS%
)

REM Run pub get for dependencies
call "%DART_BIN%" pub get --offline 2>nul || call "%DART_BIN%" pub get

REM Run tests with sharding
if defined TOTAL_SHARDS (
    call "%DART_BIN%" test --shard-index=%SHARD_INDEX% --total-shards=%TOTAL_SHARDS% {main_file} {test_args}
) else (
    call "%DART_BIN%" test {main_file} {test_args}
)

set "RESULT=%errorlevel%"

REM Touch shard status file if present
if defined TEST_SHARD_STATUS_FILE (
    if %RESULT% equ 0 (
        echo PASSED > "%TEST_SHARD_STATUS_FILE%"
    ) else (
        echo FAILED > "%TEST_SHARD_STATUS_FILE%"
    )
)

exit /b %RESULT%
""".format(
            dart_path = dart_path.replace("/", "\\"),
            pkg_dir = pkg_dir.replace("/", "\\"),
            main_file = main_file.replace("/", "\\"),
            test_args = " ".join(ctx.attr.test_args),
        )
    else:
        content = """#!/bin/bash
set -e

if [[ -n "${{BUILD_WORKSPACE_DIRECTORY:-}}" ]]; then
    WORKSPACE_ROOT="$BUILD_WORKSPACE_DIRECTORY"
elif [[ -d "$0.runfiles/_main" ]]; then
    WORKSPACE_ROOT="$0.runfiles/_main"
else
    WORKSPACE_ROOT="$(pwd)"
fi

DART_BIN="$WORKSPACE_ROOT/{dart_path}"
if [ ! -f "$DART_BIN" ]; then
    DART_BIN="dart"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

# Sharding support
SHARD_INDEX="${{TEST_SHARD_INDEX:-}}"
TOTAL_SHARDS="${{TEST_TOTAL_SHARDS:-}}"

if [[ -n "$TOTAL_SHARDS" ]]; then
    echo "Running shard $SHARD_INDEX of $TOTAL_SHARDS"
fi

# Run pub get for dependencies
"$DART_BIN" pub get --offline 2>/dev/null || "$DART_BIN" pub get

# Run tests with sharding
RESULT=0
if [[ -n "$TOTAL_SHARDS" ]]; then
    "$DART_BIN" test --shard-index="$SHARD_INDEX" --total-shards="$TOTAL_SHARDS" {main_file} {test_args} || RESULT=$?
else
    "$DART_BIN" test {main_file} {test_args} || RESULT=$?
fi

# Touch shard status file if present
if [[ -n "${{TEST_SHARD_STATUS_FILE:-}}" ]]; then
    if [[ $RESULT -eq 0 ]]; then
        echo "PASSED" > "$TEST_SHARD_STATUS_FILE"
    else
        echo "FAILED" > "$TEST_SHARD_STATUS_FILE"
    fi
fi

exit $RESULT
""".format(
            dart_path = dart_path,
            pkg_dir = pkg_dir,
            main_file = main_file,
            test_args = " ".join(ctx.attr.test_args),
        )

    ctx.actions.write(runner_script, content, is_executable = True)

    all_files = [dart_bin]
    if ctx.file.main:
        all_files.append(ctx.file.main)
    all_files.extend(ctx.files.srcs)
    all_files.extend(ctx.files.deps)
    all_files.extend(ctx.files.data)

    runfiles = ctx.runfiles(files = all_files)

    return [
        DefaultInfo(
            executable = runner_script,
            runfiles = runfiles,
        ),
        DartTestShardInfo(
            shard_count = shard_count,
            shard_index = -1,  # Determined at runtime
            test_files = ctx.files.srcs,
            uses_sharding = shard_count > 1,
        ),
    ]

dart_sharded_test = rule(
    implementation = _dart_sharded_test_impl,
    doc = """Run Dart tests with sharding support.

    This rule enables running large test suites in parallel by splitting
    tests across multiple shards. Bazel handles shard orchestration.

    Example:
        ```python
        dart_sharded_test(
            name = "all_tests",
            main = "test/all_test.dart",
            shard_count = 4,
        )
        ```

        Run with: `bazel test :all_tests --test_sharding_strategy=explicit`

    Sharding works by:
    1. Bazel spawns N parallel test processes (one per shard)
    2. Each process receives TEST_SHARD_INDEX and TEST_TOTAL_SHARDS
    3. Dart's test runner uses these to select which tests to run
    4. Results are aggregated by Bazel
    """,
    attrs = {
        "main": attr.label(
            doc = "Main test file or directory.",
            allow_single_file = [".dart"],
        ),
        "srcs": attr.label_list(
            doc = "Source files.",
            allow_files = [".dart"],
        ),
        "deps": attr.label_list(
            doc = "Dependencies.",
        ),
        "data": attr.label_list(
            doc = "Runtime data files.",
            allow_files = True,
        ),
        "package_dir": attr.string(
            doc = "Package directory containing pubspec.yaml.",
        ),
        "shard_count": attr.int(
            doc = "Number of shards to split tests into.",
            default = 1,
        ),
        "test_args": attr.string_list(
            doc = "Additional arguments to pass to dart test.",
            default = [],
        ),
        "dart_sdk": attr.label(
            default = Label("@dart_sdk//:dart_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(
            default = Label("@platforms//os:windows"),
        ),
    },
    test = True,
)

# =============================================================================
# Helper Macro
# =============================================================================

def dart_test_suite(
        name,
        srcs = [],
        deps = [],
        data = [],
        package_dir = None,
        shard_count = 1,
        size = "medium",
        timeout = None,
        visibility = None,
        **kwargs):
    """Create a sharded test suite from multiple test files.

    This is a convenience macro that creates a dart_sharded_test with
    proper sharding configuration.

    Args:
        name: Target name.
        srcs: Test source files.
        deps: Dependencies.
        data: Runtime data files.
        package_dir: Package directory.
        shard_count: Number of shards (default 1).
        size: Test size (small, medium, large, enormous).
        timeout: Test timeout.
        visibility: Target visibility.
        **kwargs: Additional arguments.

    Example:
        ```python
        dart_test_suite(
            name = "unit_tests",
            srcs = glob(["test/**/*_test.dart"]),
            shard_count = 4,
            size = "medium",
        )
        ```
    """
    dart_sharded_test(
        name = name,
        srcs = srcs,
        deps = deps,
        data = data,
        package_dir = package_dir,
        shard_count = shard_count,
        size = size,
        timeout = timeout,
        visibility = visibility,
        **kwargs
    )
