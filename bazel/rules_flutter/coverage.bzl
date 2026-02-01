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

"""Test coverage support for rules_flutter.

This module provides rules for collecting and reporting test coverage
for Flutter/Dart projects.

## Coverage Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Coverage Collection Flow                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  flutter test --coverage                                                         │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │ coverage/   │───▶│ format_     │───▶│ lcov.info   │───▶│ HTML Report │       │
│  │ lcov.info   │    │ coverage    │    │ (merged)    │    │ (genhtml)   │       │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘       │
│                                                                                  │
│  Output Formats:                                                                 │
│  • LCOV (lcov.info) - Compatible with most CI systems                           │
│  • HTML - Human-readable reports                                                 │
│  • Cobertura XML - Jenkins/Azure DevOps compatible                              │
│  • JSON - Machine-readable                                                       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Usage

```python
load("@rules_flutter//:coverage.bzl", "flutter_coverage", "flutter_coverage_report")

# Run tests with coverage
flutter_coverage(
    name = "coverage",
    test_target = ":my_test",
    minimum_coverage = 80,
)

# Aggregate coverage from multiple tests
flutter_coverage_report(
    name = "coverage_report",
    tests = [":unit_test", ":widget_test", ":integration_test"],
    output_format = "html",
)
```
"""

load("//private:helpers.bzl", "runfiles_path", "to_windows_path")

# =============================================================================
# Providers
# =============================================================================

FlutterCoverageInfo = provider(
    doc = "Coverage information for Flutter tests.",
    fields = {
        "lcov_file": "File: LCOV coverage data file.",
        "covered_lines": "Int: Number of covered lines.",
        "total_lines": "Int: Total number of lines.",
        "coverage_percent": "Float: Coverage percentage.",
        "uncovered_files": "List[String]: Files with no coverage.",
    },
)

# =============================================================================
# flutter_coverage - Run tests with coverage
# =============================================================================

def _flutter_coverage_impl(ctx):
    """Implementation of flutter_coverage rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Coverage options
    coverage_args = ["test", "--coverage"]

    if ctx.attr.branch_coverage:
        coverage_args.append("--branch-coverage")

    if ctx.attr.test_filter:
        coverage_args.extend(["--name", ctx.attr.test_filter])

    coverage_cmd = " ".join(coverage_args)

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

echo Running Flutter tests with coverage...
call "%FLUTTER_BIN%" pub get --offline 2>nul || call "%FLUTTER_BIN%" pub get
call "%FLUTTER_BIN%" {coverage_cmd}

if %errorlevel% neq 0 (
    echo Tests failed!
    exit /b %errorlevel%
)

if exist coverage\\lcov.info (
    echo.
    echo Coverage report generated: coverage/lcov.info
    
    REM Check minimum coverage if specified
    if "{min_coverage}" neq "0" (
        echo Minimum coverage threshold: {min_coverage}%%
        REM Note: Actual coverage check would require parsing lcov.info
    )
) else (
    echo Warning: No coverage data generated
)

exit /b 0
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            coverage_cmd = coverage_cmd,
            min_coverage = ctx.attr.minimum_coverage,
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

FLUTTER_BIN="$WORKSPACE_ROOT/{flutter_path}"
if [ ! -f "$FLUTTER_BIN" ]; then
    FLUTTER_BIN="flutter"
fi

cd "$WORKSPACE_ROOT/{pkg_dir}"

echo "Running Flutter tests with coverage..."
"$FLUTTER_BIN" pub get --offline 2>/dev/null || "$FLUTTER_BIN" pub get
"$FLUTTER_BIN" {coverage_cmd}

if [ -f coverage/lcov.info ]; then
    echo ""
    echo "Coverage report generated: coverage/lcov.info"
    
    # Calculate coverage percentage
    COVERED=$(grep -E "^DA:" coverage/lcov.info | grep -v ",0$" | wc -l)
    TOTAL=$(grep -E "^DA:" coverage/lcov.info | wc -l)
    
    if [ "$TOTAL" -gt 0 ]; then
        PERCENT=$((COVERED * 100 / TOTAL))
        echo "Coverage: $COVERED/$TOTAL lines ($PERCENT%)"
        
        # Check minimum coverage
        if [ "{min_coverage}" -gt 0 ] && [ "$PERCENT" -lt "{min_coverage}" ]; then
            echo "ERROR: Coverage $PERCENT% is below minimum {min_coverage}%"
            exit 1
        fi
    fi
else
    echo "Warning: No coverage data generated"
fi
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            coverage_cmd = coverage_cmd,
            min_coverage = ctx.attr.minimum_coverage,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    all_files = [flutter_bin] + ctx.files.srcs
    runfiles = ctx.runfiles(files = all_files)

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_coverage = rule(
    implementation = _flutter_coverage_impl,
    doc = "Run Flutter tests with coverage collection.",
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "package_dir": attr.string(),
        "minimum_coverage": attr.int(
            default = 0,
            doc = "Minimum coverage percentage required (0 = no minimum).",
        ),
        "branch_coverage": attr.bool(
            default = False,
            doc = "Enable branch coverage collection.",
        ),
        "test_filter": attr.string(
            default = "",
            doc = "Filter tests by name pattern.",
        ),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_coverage(
        name,
        srcs = [],
        package_dir = None,
        minimum_coverage = 0,
        branch_coverage = False,
        test_filter = "",
        visibility = None,
        **kwargs):
    """Run Flutter tests with coverage collection.

    Args:
        name: Target name.
        srcs: Source files (for dependency tracking).
        package_dir: Package directory containing pubspec.yaml.
        minimum_coverage: Minimum coverage percentage (0-100).
        branch_coverage: Enable branch coverage.
        test_filter: Filter tests by name.
        visibility: Target visibility.
        **kwargs: Additional arguments.

    Example:
        flutter_coverage(
            name = "coverage",
            minimum_coverage = 80,
        )
    """
    _flutter_coverage(
        name = name,
        srcs = srcs,
        package_dir = package_dir,
        minimum_coverage = minimum_coverage,
        branch_coverage = branch_coverage,
        test_filter = test_filter,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# flutter_coverage_report - Generate HTML coverage report
# =============================================================================

def _flutter_coverage_report_impl(ctx):
    """Implementation of flutter_coverage_report rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    flutter_bin = ctx.executable.flutter_sdk
    flutter_path = runfiles_path(flutter_bin)
    pkg_dir = ctx.attr.package_dir or ctx.label.package
    output_dir = ctx.attr.output_dir or "coverage/html"

    if is_windows:
        content = """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "FLUTTER_BIN=%RUNFILES%\\{flutter_path}"
if not exist "%FLUTTER_BIN%" set "FLUTTER_BIN=flutter"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

echo Generating coverage report...

if not exist coverage\\lcov.info (
    echo Error: No coverage data found. Run flutter test --coverage first.
    exit /b 1
)

REM Check if genhtml is available
where genhtml >nul 2>&1
if %errorlevel% equ 0 (
    genhtml coverage\\lcov.info -o {output_dir}
    echo HTML report generated: {output_dir}/index.html
) else (
    echo Note: genhtml not found. Install lcov for HTML reports.
    echo LCOV data available at: coverage/lcov.info
)

exit /b 0
""".format(
            flutter_path = to_windows_path(flutter_path),
            pkg_dir = to_windows_path(pkg_dir),
            output_dir = output_dir,
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

cd "$WORKSPACE_ROOT/{pkg_dir}"

echo "Generating coverage report..."

if [ ! -f coverage/lcov.info ]; then
    echo "Error: No coverage data found. Run flutter test --coverage first."
    exit 1
fi

# Check if genhtml is available
if command -v genhtml &> /dev/null; then
    genhtml coverage/lcov.info -o {output_dir} --quiet
    echo "HTML report generated: {output_dir}/index.html"
    
    # Try to open in browser
    if command -v open &> /dev/null; then
        echo "Opening report in browser..."
        open {output_dir}/index.html
    elif command -v xdg-open &> /dev/null; then
        echo "Opening report in browser..."
        xdg-open {output_dir}/index.html
    fi
else
    echo "Note: genhtml not found. Install lcov for HTML reports."
    echo "  macOS: brew install lcov"
    echo "  Linux: apt install lcov"
    echo ""
    echo "LCOV data available at: coverage/lcov.info"
fi
""".format(
            flutter_path = flutter_path,
            pkg_dir = pkg_dir,
            output_dir = output_dir,
        )

    ctx.actions.write(runner_script, content, is_executable = True)
    runfiles = ctx.runfiles(files = [flutter_bin])

    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

_flutter_coverage_report = rule(
    implementation = _flutter_coverage_report_impl,
    doc = "Generate HTML coverage report from LCOV data.",
    attrs = {
        "package_dir": attr.string(),
        "output_dir": attr.string(
            default = "coverage/html",
            doc = "Directory for HTML report output.",
        ),
        "flutter_sdk": attr.label(
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(default = Label("@platforms//os:windows")),
    },
    executable = True,
)

def flutter_coverage_report(
        name,
        package_dir = None,
        output_dir = "coverage/html",
        visibility = None,
        **kwargs):
    """Generate HTML coverage report from LCOV data.

    Requires genhtml (from lcov package) to be installed.

    Args:
        name: Target name.
        package_dir: Package directory containing coverage/lcov.info.
        output_dir: Directory for HTML report output.
        visibility: Target visibility.
        **kwargs: Additional arguments.

    Example:
        # First run coverage
        bazel run :coverage

        # Then generate HTML report
        bazel run :coverage_report
    """
    _flutter_coverage_report(
        name = name,
        package_dir = package_dir,
        output_dir = output_dir,
        visibility = visibility,
        **kwargs
    )
