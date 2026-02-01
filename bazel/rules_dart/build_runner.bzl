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

"""Build runner support for Dart code generation.

This module provides integration with Dart's build_runner package,
which powers code generation for popular packages like:
- freezed (immutable data classes)
- json_serializable (JSON serialization)
- built_value (immutable values)
- auto_route (routing)

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Dart Build Runner Integration                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Source Files          Generated Files                                      │
│  ┌──────────────┐      ┌──────────────────────┐                             │
│  │ user.dart    │  →   │ user.freezed.dart    │                             │
│  │ @freezed     │      │ user.g.dart          │                             │
│  └──────────────┘      └──────────────────────┘                             │
│         │                       │                                            │
│         └───────────┬───────────┘                                            │
│                     │                                                        │
│                     ▼                                                        │
│              dart_library                                                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Usage:
    load("@rules_dart//:build_runner.bzl", "dart_build_runner")

    dart_build_runner(
        name = "generated",
        srcs = glob(["lib/**/*.dart"]),
        generators = ["freezed", "json_serializable"],
    )

    dart_library(
        name = "models",
        srcs = glob(["lib/**/*.dart"]) + [":generated"],
        pubspec = "pubspec.yaml",
    )
"""

def _dart_build_runner_impl(ctx):
    """Implementation of dart_build_runner rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    # Output directory for generated files
    out_dir = ctx.actions.declare_directory(ctx.label.name)

    dart_bin = ctx.executable.dart_sdk
    pkg_dir = ctx.attr.package_dir or ctx.label.package

    # Create build runner script
    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + "_builder" + script_ext)

    if is_windows:
        content = """@echo off
setlocal
cd /d "%BUILD_WORKSPACE_DIRECTORY%\\{pkg_dir}"

set "DART={dart_path}"
set "OUT_DIR={out_dir}"

REM Run build_runner
call "%DART%" run build_runner build --delete-conflicting-outputs

REM Copy generated files to output
xcopy /E /Y lib\\*.g.dart "%OUT_DIR%\\" 2>nul
xcopy /E /Y lib\\*.freezed.dart "%OUT_DIR%\\" 2>nul

echo Build runner completed
""".format(
            dart_path = dart_bin.path.replace("/", "\\"),
            pkg_dir = pkg_dir.replace("/", "\\"),
            out_dir = out_dir.path.replace("/", "\\"),
        )
    else:
        content = """#!/bin/bash
set -e
cd "$BUILD_WORKSPACE_DIRECTORY/{pkg_dir}"

DART="{dart_path}"
OUT_DIR="{out_dir}"

# Run build_runner
"$DART" run build_runner build --delete-conflicting-outputs

# Copy generated files to output
find lib -name "*.g.dart" -o -name "*.freezed.dart" | while read f; do
    cp "$f" "$OUT_DIR/" 2>/dev/null || true
done

echo "Build runner completed"
""".format(
            dart_path = dart_bin.path,
            pkg_dir = pkg_dir,
            out_dir = out_dir.path,
        )

    ctx.actions.write(runner_script, content, is_executable = True)

    ctx.actions.run(
        executable = runner_script,
        outputs = [out_dir],
        inputs = ctx.files.srcs + [dart_bin],
        mnemonic = "DartBuildRunner",
        progress_message = "Running build_runner for %s" % ctx.label,
    )

    return [DefaultInfo(files = depset([out_dir]))]

dart_build_runner = rule(
    implementation = _dart_build_runner_impl,
    doc = "Runs Dart build_runner for code generation (freezed, json_serializable, etc.).",
    attrs = {
        "srcs": attr.label_list(
            doc = "Source files to process.",
            allow_files = [".dart"],
            mandatory = True,
        ),
        "generators": attr.string_list(
            doc = "List of generators to run (for documentation, actual generators determined by build.yaml).",
            default = [],
        ),
        "package_dir": attr.string(
            doc = "Package directory containing pubspec.yaml.",
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
)
