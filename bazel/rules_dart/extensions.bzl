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

"""Bzlmod extension for Dart SDK configuration and dependencies.

This extension allows the Dart SDK to be configured via Bzlmod.
It downloads the SDK from Google's official CDN.
It also manages Dart package dependencies from pubspec.lock files.
"""

load(":repositories.bzl", "DART_VERSION", "dart_package", "dart_sdk")

def _dart_impl(module_ctx):
    """Implementation of the dart module extension."""

    # Get the version from the first module that uses this extension
    version = DART_VERSION

    for mod in module_ctx.modules:
        for config in mod.tags.configure:
            if config.version:
                version = config.version
                break

    # Create the dart_sdk repository
    dart_sdk(
        name = "dart_sdk",
        version = version,
    )

_configure = tag_class(
    attrs = {
        "version": attr.string(
            default = "",
            doc = "The Dart SDK version to use. Defaults to the version in repositories.bzl.",
        ),
    },
)

dart = module_extension(
    implementation = _dart_impl,
    tag_classes = {
        "configure": _configure,
    },
)

# dependency management

def _parse_pubspec_lock(content):
    packages = {}
    lines = content.split("\n")
    current_pkg = None
    pkg_data = {}
    
    for line in lines:
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
            
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        if stripped == "packages:":
            continue
            
        if indent == 2 and stripped.endswith(":"):
            # New package
            if current_pkg and pkg_data.get("source") == "hosted" and "sha256" in pkg_data:
                packages[current_pkg] = pkg_data
            
            current_pkg = stripped[:-1]
            pkg_data = {}
            
        elif current_pkg:
            parts = stripped.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip().strip('"\'')
                if key == "version":
                    pkg_data["version"] = val
                elif key == "sha256":
                    pkg_data["sha256"] = val
                elif key == "source":
                    pkg_data["source"] = val

    # Add last package
    if current_pkg and pkg_data.get("source") == "hosted" and "sha256" in pkg_data:
        packages[current_pkg] = pkg_data
        
    return packages

def _dart_deps_impl(ctx):
    all_packages = {}
    rules_label = "@rules_dart//:defs.bzl"
    
    for mod in ctx.modules:
        for config in mod.tags.from_file:
            if config.rules_dart_label != "@rules_dart//:defs.bzl":
                 rules_label = config.rules_dart_label
            
            content = ctx.read(config.lock_file)
            pkgs = _parse_pubspec_lock(content)
            all_packages.update(pkgs)
            
    for name, data in all_packages.items():
        dart_package(
            name = "dart_deps_" + name,
            package_name = name,
            version = data["version"],
            sha256 = data["sha256"],
            rules_dart_label = rules_label,
        )

_deps_configure = tag_class(
    attrs = {
        "lock_file": attr.label(allow_single_file = True, mandatory = True),
        "rules_dart_label": attr.string(default = "@rules_dart//:defs.bzl"),
    },
)

dart_deps = module_extension(
    implementation = _dart_deps_impl,
    tag_classes = {
        "from_file": _deps_configure,
    },
)
