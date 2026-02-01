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

"""Starlark-native pubspec.yaml and pubspec.lock parser.

# ELI5 (Explain Like I'm 5)

## What is this?

Imagine you have a recipe book (pubspec.yaml) that lists ingredients you need.
Instead of going to the store yourself (running `pub get`), this module reads
the recipe and fetches ingredients directly from the pantry (pub.dev).

## Why is it important?

Using pure Starlark (no shell scripts) makes builds:
- Faster (no subprocess overhead)
- More hermetic (no environment dependencies)
- Cacheable (Bazel can cache the parsing)

## Key Terms

| Term | Description |
|------|-------------|
| **pubspec.yaml** | Package manifest listing dependencies |
| **pubspec.lock** | Locked versions of all transitive dependencies |
| **pub.dev** | The official Dart package registry |
| **Hosted dependency** | A package from pub.dev |
| **Path dependency** | A local package in the workspace |
| **Git dependency** | A package from a git repository |

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Starlark Dependency Resolution                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  pubspec.lock  ──┬──▶  parse_pubspec_lock()  ──▶  PubDependency structs    │
│                  │                                                          │
│  pubspec.yaml  ──┴──▶  parse_pubspec_yaml()  ──▶  Package metadata         │
│                                                                             │
│                           │                                                 │
│                           ▼                                                 │
│              ┌─────────────────────────────────┐                           │
│              │   dart_deps.from_pubspec_lock() │                           │
│              │   (Module extension)            │                           │
│              └─────────────────────────────────┘                           │
│                           │                                                 │
│                           ▼                                                 │
│              ┌─────────────────────────────────┐                           │
│              │   @dart_deps//:package_name     │                           │
│              │   (External repository)         │                           │
│              └─────────────────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
"""

# =============================================================================
# YAML Mini-Parser
# =============================================================================
#
# Starlark doesn't have a built-in YAML parser, so we implement a minimal one
# that handles the subset of YAML used in pubspec files.

def _strip_comment(line):
    """Remove trailing comments from a line."""

    # Handle comments not inside quotes
    in_quotes = False
    quote_char = None
    for i, c in enumerate(line):
        if c in ["'", '"'] and (i == 0 or line[i - 1] != "\\"):
            if not in_quotes:
                in_quotes = True
                quote_char = c
            elif c == quote_char:
                in_quotes = False
        elif c == "#" and not in_quotes:
            return line[:i].rstrip()
    return line

def _get_indent(line):
    """Get the indentation level of a line."""
    count = 0
    for c in line:
        if c == " ":
            count += 1
        elif c == "\t":
            count += 2
        else:
            break
    return count

def _parse_yaml_value(value):
    """Parse a YAML value string into a Starlark value."""
    value = value.strip()

    # Empty
    if not value:
        return None

    # Boolean
    if value.lower() in ["true", "yes", "on"]:
        return True
    if value.lower() in ["false", "no", "off"]:
        return False

    # Null
    if value.lower() in ["null", "~"]:
        return None

    # Quoted string
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    # Number (integer)
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)

    # Number (float) - basic check
    if "." in value:
        parts = value.split(".")
        if len(parts) == 2 and parts[0].lstrip("-").isdigit() and parts[1].isdigit():
            return float(value)

    # Plain string
    return value

def parse_yaml_simple(content):
    """Parse a simple YAML document into a dict.

    This is a minimal YAML parser that handles:
    - Key-value pairs
    - Nested mappings (indentation-based)
    - Simple values (strings, numbers, booleans)

    Args:
        content: YAML content as a string.

    Returns:
        A dict representing the YAML structure.

    Note:
        This parser does NOT handle:
        - Flow styles ({}, [])
        - Multi-line strings (|, >)
        - Anchors and aliases
        - Complex keys
    """
    result = {}
    stack = [(result, -1)]  # (dict, indent_level)
    lines = content.split("\n")

    for line in lines:
        # Skip empty lines and comments
        stripped = _strip_comment(line).strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = _get_indent(line)

        # Pop stack until we find a parent with lower indentation
        # Use for loop since Starlark doesn't support while
        for _ in range(len(stack)):
            if len(stack) <= 1 or stack[-1][1] < indent:
                break
            stack.pop()

        current_dict = stack[-1][0]

        # Parse key-value
        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value_str = stripped[colon_idx + 1:].strip()

            if value_str:
                # Simple key-value pair
                current_dict[key] = _parse_yaml_value(value_str)
            else:
                # Nested mapping
                new_dict = {}
                current_dict[key] = new_dict
                stack.append((new_dict, indent))

    return result

# =============================================================================
# Pubspec Lock Parser
# =============================================================================

# Dependency source types
_SOURCE_HOSTED = "hosted"
_SOURCE_PATH = "path"

# TODO(#123): Implement git dependency support
# _SOURCE_GIT = "git"
_SOURCE_SDK = "sdk"

def _parse_packages_section(lock_content):
    """Parse the packages section of pubspec.lock.

    The pubspec.lock format is:
    ```
    packages:
      package_name:
        dependency: "direct main"
        description:
          name: package_name
          sha256: "..."
          url: "https://pub.dev"
        source: hosted
        version: "1.2.3"
    ```

    Args:
        lock_content: The content of pubspec.lock as a string.

    Returns:
        A list of PubDependency structs.
    """
    dependencies = []
    lines = lock_content.split("\n")

    in_packages = False
    current_package = None
    current_data = {}
    current_indent = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = _get_indent(line)

        # Detect packages section
        if stripped == "packages:":
            in_packages = True
            current_indent = indent
            continue

        if not in_packages:
            continue

        # Detect end of packages section (new top-level key)
        if indent <= current_indent and ":" in stripped and not stripped.startswith(" "):
            break

        # Package name (indent = 2)
        if indent == 2 and stripped.endswith(":"):
            # Save previous package
            if current_package and current_data:
                dep = _create_pub_dependency(current_package, current_data)
                if dep:
                    dependencies.append(dep)

            current_package = stripped[:-1]
            current_data = {}
            continue

        # Package attributes
        if current_package and ":" in stripped:
            key = stripped.split(":")[0].strip()
            value = ":".join(stripped.split(":")[1:]).strip().strip('"')

            if key == "version":
                current_data["version"] = value
            elif key == "source":
                current_data["source"] = value
            elif key == "dependency":
                current_data["dependency"] = value
            elif key == "url":
                current_data["url"] = value
            elif key == "name":
                current_data["name"] = value
            elif key == "sha256":
                current_data["sha256"] = value
            elif key == "path":
                current_data["path"] = value
            elif key == "ref":
                current_data["ref"] = value

    # Save last package
    if current_package and current_data:
        dep = _create_pub_dependency(current_package, current_data)
        if dep:
            dependencies.append(dep)

    return dependencies

def _create_pub_dependency(name, data):
    """Create a PubDependency struct from parsed data."""
    source = data.get("source", "hosted")
    version = data.get("version", "0.0.0")
    sha256 = data.get("sha256", "")
    url = data.get("url", "https://pub.dev")
    dependency_type = data.get("dependency", "transitive")
    path = data.get("path", "")
    git_ref = data.get("ref", "")

    return struct(
        name = name,
        version = version,
        source = source,
        sha256 = sha256,
        url = url,
        dependency_type = dependency_type,
        path = path,
        git_ref = git_ref,
        is_direct = "direct" in dependency_type,
        is_dev = "dev" in dependency_type,
    )

def parse_pubspec_lock(content):
    """Parse pubspec.lock content into a list of dependencies.

    Args:
        content: The content of pubspec.lock as a string.

    Returns:
        A list of PubDependency structs with fields:
        - name: Package name
        - version: Package version
        - source: "hosted", "path", "git", or "sdk"
        - sha256: SHA256 hash for verification
        - url: Package registry URL
        - dependency_type: "direct main", "direct dev", or "transitive"
        - path: For path dependencies, the local path
        - git_ref: For git dependencies, the ref/branch/tag
        - is_direct: True if this is a direct dependency
        - is_dev: True if this is a dev dependency
    """
    return _parse_packages_section(content)

# =============================================================================
# Pubspec YAML Parser
# =============================================================================

def parse_pubspec_yaml(content):
    """Parse pubspec.yaml content into package metadata.

    Args:
        content: The content of pubspec.yaml as a string.

    Returns:
        A struct with fields:
        - name: Package name
        - version: Package version
        - description: Package description
        - dependencies: Dict of direct dependencies
        - dev_dependencies: Dict of dev dependencies
        - environment: Environment constraints (sdk, flutter)
    """
    data = parse_yaml_simple(content)

    return struct(
        name = data.get("name", ""),
        version = data.get("version", "0.0.0"),
        description = data.get("description", ""),
        dependencies = data.get("dependencies", {}),
        dev_dependencies = data.get("dev_dependencies", {}),
        environment = data.get("environment", {}),
    )

# =============================================================================
# Repository Rule for Hosted Dependencies
# =============================================================================

def _pub_package_impl(repository_ctx):
    """Repository rule that downloads a package from pub.dev."""
    name = repository_ctx.attr.package_name
    version = repository_ctx.attr.version
    sha256 = repository_ctx.attr.sha256
    url = repository_ctx.attr.url

    # Construct download URL
    # pub.dev URL format: https://pub.dev/packages/{name}/versions/{version}.tar.gz
    if url == "https://pub.dev" or not url:
        download_url = "https://pub.dev/packages/{name}/versions/{version}.tar.gz".format(
            name = name,
            version = version,
        )
    else:
        # Custom registry
        download_url = "{url}/packages/{name}/versions/{version}.tar.gz".format(
            url = url.rstrip("/"),
            name = name,
            version = version,
        )

    repository_ctx.report_progress("Downloading {name} {version}".format(
        name = name,
        version = version,
    ))

    # Download and extract
    repository_ctx.download_and_extract(
        url = download_url,
        sha256 = sha256 if sha256 else None,
    )

    # Generate BUILD.bazel
    build_content = '''# Generated by pub_package repository rule
# Package: {name}
# Version: {version}

load("@rules_dart//:defs.bzl", "dart_library")

package(default_visibility = ["//visibility:public"])

dart_library(
    name = "{name}",
    srcs = glob(["lib/**/*.dart"]),
    package_name = "{name}",
    pubspec = "pubspec.yaml",
)
'''.format(name = name, version = version)

    repository_ctx.file("BUILD.bazel", build_content)

pub_package = repository_rule(
    implementation = _pub_package_impl,
    attrs = {
        "package_name": attr.string(mandatory = True),
        "version": attr.string(mandatory = True),
        "sha256": attr.string(default = ""),
        "url": attr.string(default = "https://pub.dev"),
    },
    doc = "Downloads a Dart package from pub.dev or a custom registry.",
)

# =============================================================================
# Module Extension for Starlark-Native Dependencies
# =============================================================================

def _dart_deps_impl(module_ctx):
    """Module extension that resolves dependencies from pubspec.lock."""
    for mod in module_ctx.modules:
        for lock_file in mod.tags.from_pubspec_lock:
            lock_content = module_ctx.read(lock_file.lock_file)
            dependencies = parse_pubspec_lock(lock_content)

            for dep in dependencies:
                # Skip SDK and path dependencies
                if dep.source == _SOURCE_SDK:
                    continue
                if dep.source == _SOURCE_PATH:
                    continue

                # Create repository for hosted dependencies
                if dep.source == _SOURCE_HOSTED:
                    pub_package(
                        name = "dart_deps_" + dep.name.replace("-", "_"),
                        package_name = dep.name,
                        version = dep.version,
                        sha256 = dep.sha256,
                        url = dep.url,
                    )

_from_pubspec_lock = tag_class(
    attrs = {
        "lock_file": attr.label(
            mandatory = True,
            allow_single_file = [".lock"],
            doc = "Path to pubspec.lock file",
        ),
    },
    doc = "Resolve dependencies from a pubspec.lock file.",
)

dart_deps = module_extension(
    implementation = _dart_deps_impl,
    tag_classes = {
        "from_pubspec_lock": _from_pubspec_lock,
    },
    doc = """Starlark-native dependency resolution for Dart packages.

Usage in MODULE.bazel:
```python
dart_deps = use_extension("@rules_dart//:extensions.bzl", "dart_deps")
dart_deps.from_pubspec_lock(lock_file = "//:pubspec.lock")
use_repo(dart_deps, "dart_deps_http", "dart_deps_path", ...)
```
""",
)

# =============================================================================
# Exports
# =============================================================================

# Export for testing
exports = struct(
    parse_yaml_simple = parse_yaml_simple,
    parse_pubspec_lock = parse_pubspec_lock,
    parse_pubspec_yaml = parse_pubspec_yaml,
)
