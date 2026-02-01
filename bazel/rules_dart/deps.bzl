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

"""Repository rules for fetching Dart pub dependencies.

This module provides hermetic dependency resolution for Dart packages,
allowing Bazel to fetch dependencies at repository time rather than
during build actions.

Architecture:
┌──────────────────────────────────────────────────────────────────────────┐
│                    Dart Dependency Resolution                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  pubspec.lock                                                            │
│       │                                                                  │
│       ▼                                                                  │
│  dart_deps() repository rule                                             │
│       │                                                                  │
│       ├── Parses lockfile                                               │
│       ├── Detects version conflicts                                     │
│       ├── Downloads archives from pub.dev                               │
│       └── Generates BUILD.bazel for each package                        │
│                                                                          │
│  Result: @pub_deps//package_name becomes a dart_library                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Version Conflict Detection:
┌──────────────────────────────────────────────────────────────────────────┐
│  When multiple modules depend on the same package with different         │
│  versions, rules_dart detects and reports the conflict:                  │
│                                                                          │
│  ERROR: Version conflict for package 'http':                             │
│    - Module 'foo' requires version 1.0.0                                │
│    - Module 'bar' requires version 2.0.0                                │
│  Resolution: Pin a single version in your root pubspec.yaml             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Usage in MODULE.bazel:
    dart_deps = use_extension("@rules_dart//:extensions.bzl", "dart_deps")
    dart_deps.from_lockfile(lockfile = "//:pubspec.lock")
    use_repo(dart_deps, "pub_deps")

Usage in BUILD.bazel:
    dart_library(
        name = "my_lib",
        srcs = [...],
        deps = [
            "@pub_deps//http",
            "@pub_deps//json_annotation",
        ],
    )
"""

# Pub.dev hosted archive URL pattern
_PUB_HOSTED_URL = "https://pub.dev/packages/{name}/versions/{version}.tar.gz"

# Global registry for tracking package versions across modules (for conflict detection)
_VERSION_REGISTRY = {}

def _parse_pubspec_lock(content):
    """Parse a pubspec.lock file and extract package information.

    The lockfile format is YAML. We parse it minimally to extract:
    - Package name
    - Version
    - Source (hosted, git, path)
    - URL (for hosted packages)

    Args:
        content: String content of pubspec.lock

    Returns:
        Dict mapping package name to package info dict
    """
    packages = {}
    lines = content.split("\n")

    current_package = None
    current_info = {}
    indent_level = 0

    for line in lines:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue

        # Count leading spaces for indent
        leading_spaces = len(line) - len(stripped)

        # Top-level "packages:" section
        if stripped == "packages:":
            continue

        # Package name (2-space indent under packages)
        if leading_spaces == 2 and stripped.endswith(":"):
            if current_package and current_info:
                packages[current_package] = current_info
            current_package = stripped[:-1].strip()
            current_info = {"name": current_package}
            continue

        # Package attributes (4-space indent)
        if leading_spaces == 4 and current_package:
            if ": " in stripped:
                key, value = stripped.split(": ", 1)
                # Remove quotes from values
                value = value.strip().strip('"').strip("'")
                current_info[key] = value

    # Don't forget the last package
    if current_package and current_info:
        packages[current_package] = current_info

    return packages

def _dart_package_impl(repository_ctx):
    """Repository rule implementation for a single Dart package."""
    name = repository_ctx.attr.package_name
    version = repository_ctx.attr.version
    sha256 = repository_ctx.attr.sha256

    # Download from pub.dev
    url = _PUB_HOSTED_URL.format(name = name, version = version)

    repository_ctx.download_and_extract(
        url = url,
        sha256 = sha256 if sha256 else None,
        stripPrefix = "",
    )

    # Generate BUILD.bazel
    build_content = '''
load("@rules_dart//:defs.bzl", "dart_library")

dart_library(
    name = "{name}",
    srcs = glob(["lib/**/*.dart"]),
    visibility = ["//visibility:public"],
)
'''.format(name = name)

    repository_ctx.file("BUILD.bazel", build_content)

dart_package = repository_rule(
    implementation = _dart_package_impl,
    attrs = {
        "package_name": attr.string(mandatory = True),
        "version": attr.string(mandatory = True),
        "sha256": attr.string(doc = "SHA256 checksum of the package archive"),
    },
)

def _dart_deps_impl(repository_ctx):
    """Repository rule that creates an umbrella repository for all pub deps."""
    lockfile_path = repository_ctx.attr.lockfile

    # Read and parse the lockfile
    lockfile_content = repository_ctx.read(lockfile_path)
    packages = _parse_pubspec_lock(lockfile_content)

    # Generate a deps.bzl file that users can load
    deps_bzl_lines = [
        '"""Generated Dart dependencies from pubspec.lock."""',
        "",
        "load(\"@rules_dart//:deps.bzl\", \"dart_package\")",
        "",
        "def install_dart_deps():",
        '    """Install all Dart dependencies as external repositories."""',
    ]

    # Generate BUILD.bazel with aliases
    build_lines = [
        "# Generated by dart_deps",
        "",
    ]

    for pkg_name, pkg_info in packages.items():
        version = pkg_info.get("version", "")
        source = pkg_info.get("dependency", "")

        # Skip SDK and path dependencies
        if source in ["sdk", "path"]:
            continue

        # Only handle hosted dependencies
        if version:
            deps_bzl_lines.append(
                '    dart_package(name = "pub__{name}", package_name = "{name}", version = "{version}")'.format(
                    name = pkg_name,
                    version = version,
                ),
            )

            # Create alias in this repo
            build_lines.append(
                'alias(name = "{name}", actual = "@pub__{name}", visibility = ["//visibility:public"])'.format(
                    name = pkg_name,
                ),
            )

    deps_bzl_lines.append("")

    repository_ctx.file("deps.bzl", "\n".join(deps_bzl_lines))
    repository_ctx.file("BUILD.bazel", "\n".join(build_lines))

dart_deps = repository_rule(
    implementation = _dart_deps_impl,
    attrs = {
        "lockfile": attr.label(
            mandatory = True,
            allow_single_file = True,
            doc = "Path to pubspec.lock file",
        ),
    },
    doc = "Creates a repository with all Dart dependencies from a lockfile.",
)

# Extension for Bzlmod with version conflict detection
def _dart_deps_extension_impl(module_ctx):
    """Module extension for dart_deps with version conflict detection.

    When multiple modules declare dependencies on the same Dart package
    with different versions, this extension detects the conflict and
    provides actionable error messages.
    """
    # Track all package versions across modules for conflict detection
    package_versions = {}  # package_name -> [(version, module_name, lockfile_path)]

    # First pass: collect all package versions from all modules
    for mod in module_ctx.modules:
        module_name = mod.name
        for config in mod.tags.from_lockfile:
            lockfile = config.lockfile
            lockfile_content = module_ctx.read(lockfile)
            packages = _parse_pubspec_lock(lockfile_content)

            for pkg_name, pkg_info in packages.items():
                version = pkg_info.get("version", "")
                source = pkg_info.get("dependency", "")

                # Skip SDK and path dependencies
                if source in ["sdk", "path"] or not version:
                    continue

                if pkg_name not in package_versions:
                    package_versions[pkg_name] = []
                package_versions[pkg_name].append((version, module_name, str(lockfile)))

    # Second pass: detect version conflicts
    conflicts = []
    for pkg_name, versions in package_versions.items():
        unique_versions = {v[0] for v in versions}
        if len(unique_versions) > 1:
            conflict_details = []
            for version, module_name, lockfile_path in versions:
                conflict_details.append(
                    "  - Module '{}' requires version {} (from {})".format(
                        module_name, version, lockfile_path
                    )
                )
            conflicts.append((pkg_name, conflict_details))

    # Report conflicts if any
    if conflicts:
        error_lines = [
            "",
            "=" * 70,
            "VERSION CONFLICT DETECTED",
            "=" * 70,
            "",
        ]
        for pkg_name, details in conflicts:
            error_lines.append("Package '{}':".format(pkg_name))
            error_lines.extend(details)
            error_lines.append("")

        error_lines.extend([
            "Resolution:",
            "  1. Pin a single version in your root pubspec.yaml",
            "  2. Run 'dart pub get' to update pubspec.lock",
            "  3. Ensure all modules use compatible versions",
            "",
            "=" * 70,
        ])
        fail("\n".join(error_lines))

    # Third pass: create repositories (conflict-free)
    created_repos = {}  # Track created repos to avoid duplicates
    for mod in module_ctx.modules:
        for config in mod.tags.from_lockfile:
            repo_name = config.name or "pub_deps"
            if repo_name not in created_repos:
                dart_deps(
                    name = repo_name,
                    lockfile = config.lockfile,
                )
                created_repos[repo_name] = True

_from_lockfile = tag_class(
    attrs = {
        "name": attr.string(default = "pub_deps"),
        "lockfile": attr.label(mandatory = True, allow_single_file = True),
    },
)

dart_deps_extension = module_extension(
    implementation = _dart_deps_extension_impl,
    tag_classes = {"from_lockfile": _from_lockfile},
)
