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

"""Coverage support for Dart tests.

This module provides integration with Bazel's coverage system,
allowing `bazel coverage` to work with Dart tests.

Usage:
    bazel coverage //my:dart_test

Output:
    bazel-out/.../coverage.dat (LCOV format)

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Dart Coverage Integration                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  bazel coverage //my:test                                                    │
│           │                                                                  │
│           ▼                                                                  │
│  dart_test rule (with coverage instrumentation)                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  dart run --enable-vm-service --pause-isolates-on-exit                 │ │
│  │  coverage:collect_coverage ...                                         │ │
│  │  coverage:format_coverage --lcov                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│           │                                                                  │
│           ▼                                                                  │
│  coverage.dat (LCOV format)                                                  │
│           │                                                                  │
│           ▼                                                                  │
│  genhtml coverage.dat -o coverage_report/  (optional)                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

The `dart test --coverage` flag outputs coverage data in JSON format.
We convert this to LCOV for Bazel compatibility.
"""

def generate_coverage_script_unix(dart_path, main_path, pkg_dir, coverage_output):
    """Generate a Unix coverage collection script.

    Args:
        dart_path: Path to the dart executable
        main_path: Path to the test file
        pkg_dir: Package directory
        coverage_output: Output path for coverage.dat

    Returns:
        String containing the shell script
    """
    return """#!/bin/bash
set -e

DART="{dart_path}"
MAIN="{main_path}"
PKG_DIR="{pkg_dir}"
COVERAGE_OUTPUT="{coverage_output}"

# Create temp directory for coverage data
COVERAGE_DIR=$(mktemp -d)
trap "rm -rf $COVERAGE_DIR" EXIT

cd "$PKG_DIR"

# Run dart pub get if needed
if [ ! -d ".dart_tool" ]; then
    "$DART" pub get --offline 2>/dev/null || "$DART" pub get
fi

# Run tests with coverage enabled
# dart test --coverage outputs JSON coverage data
"$DART" test --coverage="$COVERAGE_DIR" "$MAIN"

# Convert coverage JSON to LCOV format
# The coverage package provides format_coverage for this
if [ -f "$COVERAGE_DIR/coverage.json" ]; then
    "$DART" run coverage:format_coverage \\
        --lcov \\
        --in="$COVERAGE_DIR" \\
        --out="$COVERAGE_OUTPUT" \\
        --report-on=lib
fi

echo "Coverage written to $COVERAGE_OUTPUT"
""".format(
        dart_path = dart_path,
        main_path = main_path,
        pkg_dir = pkg_dir,
        coverage_output = coverage_output,
    )

def generate_coverage_script_windows(dart_path, main_path, pkg_dir, coverage_output):
    """Generate a Windows coverage collection script.

    Args:
        dart_path: Path to the dart executable
        main_path: Path to the test file
        pkg_dir: Package directory
        coverage_output: Output path for coverage.dat

    Returns:
        String containing the batch script
    """
    return """@echo off
setlocal enabledelayedexpansion

set "DART={dart_path}"
set "MAIN={main_path}"
set "PKG_DIR={pkg_dir}"
set "COVERAGE_OUTPUT={coverage_output}"

REM Create temp directory
set "COVERAGE_DIR=%TEMP%\\dart_coverage_%RANDOM%"
mkdir "%COVERAGE_DIR%"

cd /d "%PKG_DIR%"

REM Run dart pub get if needed
if not exist ".dart_tool" (
    call "%DART%" pub get --offline 2>nul || call "%DART%" pub get
)

REM Run tests with coverage
call "%DART%" test --coverage="%COVERAGE_DIR%" "%MAIN%"

REM Convert to LCOV
if exist "%COVERAGE_DIR%\\coverage.json" (
    call "%DART%" run coverage:format_coverage ^
        --lcov ^
        --in="%COVERAGE_DIR%" ^
        --out="%COVERAGE_OUTPUT%" ^
        --report-on=lib
)

echo Coverage written to %COVERAGE_OUTPUT%

REM Cleanup
rmdir /s /q "%COVERAGE_DIR%" 2>nul
exit /b 0
""".format(
        dart_path = dart_path.replace("/", "\\"),
        main_path = main_path.replace("/", "\\"),
        pkg_dir = pkg_dir.replace("/", "\\"),
        coverage_output = coverage_output.replace("/", "\\"),
    )

# Coverage output group for Bazel's coverage system
COVERAGE_OUTPUT_GROUP = "coverage"
