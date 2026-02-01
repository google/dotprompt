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

"""Repository rules for downloading the Dart SDK.

This module provides repository rules similar to rules_go and rules_rust that
automatically download and configure the Dart SDK for hermetic builds.

The Dart SDK is downloaded from the official Google storage:
https://storage.googleapis.com/dart-archive/channels/stable/release/{version}/sdk/

Supported platforms:
- linux-x64, linux-arm64
- macos-x64, macos-arm64
- windows-x64
"""

# Dart SDK version to download
DART_VERSION = "3.7.0"

# Dart SDK download URLs by platform
_DART_SDK_URLS = {
    "linux-x64": "https://storage.googleapis.com/dart-archive/channels/stable/release/{version}/sdk/dartsdk-linux-x64-release.zip",
    "linux-arm64": "https://storage.googleapis.com/dart-archive/channels/stable/release/{version}/sdk/dartsdk-linux-arm64-release.zip",
    "macos-x64": "https://storage.googleapis.com/dart-archive/channels/stable/release/{version}/sdk/dartsdk-macos-x64-release.zip",
    "macos-arm64": "https://storage.googleapis.com/dart-archive/channels/stable/release/{version}/sdk/dartsdk-macos-arm64-release.zip",
    "windows-x64": "https://storage.googleapis.com/dart-archive/channels/stable/release/{version}/sdk/dartsdk-windows-x64-release.zip",
}

# SHA256 checksums for Dart SDK versions
_DART_SDK_SHA256 = {
    "3.7.0": {
        "linux-x64": "367b5a6f1364a1697dc597775e5cd7333c332363902683a0970158cbb978b80d",
        "linux-arm64": "7c849abc0d06a130d26d71490d5f2b4b2fe1ca477b1a9cee6b6d870e6f9d626f",
        "macos-x64": "d601c9da420552dc6deba1992d07aad9637b970077d58c5cda895baebc83d7f5",
        "macos-arm64": "9bfd7c74ebc5f30b5832dfcf4f47e5a3260f2e9b98743506c67ad02b3b6964bb",
        "windows-x64": "cd9b96be7ab7d81fd719391c4ee0771af6b6db3309d00d33a0a71d56214e5bb3",
    },
    "3.6.0": {
        "linux-x64": "8e14ff436e1eec72618dabc94f421a97251f2068c9cc9ad2d3bb9d232d6155a3",
        "linux-arm64": "0f82f10f808c7003d0d03294ae9220b5e0824ab3d2d19b4929d4fa735254e7bf",
        "macos-x64": "b859b1abd92997b389061be6b301e598a3edcbf7e092cfe5b8d6ce2acdf0732b",
        "macos-arm64": "1bdbc6544aaa53673e7cbbf66ad7cde914cb7598936ebbd6a4245e1945a702a0",
        "windows-x64": "be7e6bec6ee131a2fc55612d98af61793f3944457fc6825e72bb2d5abb7dd8ad",
    },
    "3.5.0": {
        "linux-x64": "011a1dd6ff4e0bb4a168f7b4e13063514fbc255dc52d1ad660bf5a28773e9773",
        "linux-arm64": "ee2cbcc36a190a883254ddc28ef772c15735022bfc5cfc11a56dbaebd5353903",
        "macos-x64": "68e6746c44eb4bf359e5b57f140b555f3c022536c58d3951ccf5fe8dc4011c32",
        "macos-arm64": "730978a02a6d72b8a2e05ff7a6ef3dc34aa214ed7a1e79e06913ea7bf7227d94",
        "windows-x64": "c6cd95d9f12e8a9d947f8d4693502c2a9e3918b3816ef06bca3fc426cdcea2c0",
    },
    "3.4.0": {
        "linux-x64": "631acea14a87a3c5d34f4fbd67ec8670cfe1345cbaa8fb8a3c45095880858620",
        "linux-arm64": "227562fab85cd9e7e842d282af376af0b4a717010b568016e0dd3b8524e7ac10",
        "macos-x64": "fc7c7c151c4bd2ec30d8d468d12c839c2be13c7569355ea60e0914dd1f7c2ff4",
        "macos-arm64": "e7b6b78febbe2f6ed8795af03a90f19331ce97115107199119a113800d441c86",
        "windows-x64": "7b69171ff9db80e03acb43ca6f745d223c9e431f71b933c27e29608c87154333",
    },
    "3.3.0": {
        "linux-x64": "3ebf6ba4065ec941bb3b2e82118ae06fce34125ce6f8289e633c4b67a56cbcad",
        "linux-arm64": "19684c1615b2070a6933972809ed61f3f236fc42829c77fa19737dd2e8b7b202",
        "macos-x64": "304ecad745b2e558be5951e6dd54b42a8ab84a8f3b6c7667258404318edd9db3",
        "macos-arm64": "b254b3f2987bdf7ea2b982855642cbea9b96e8973307cabf369ef312d0b38ab2",
        "windows-x64": "1071fca75573a35abe5aadf621b30dccad5dab87b6ae5afb18f3b82191cd58f0",
    },
}

def _get_platform(repository_ctx):
    """Determines the current platform string."""
    os_name = repository_ctx.os.name.lower()
    arch = repository_ctx.os.arch

    if "mac" in os_name or "darwin" in os_name:
        os_key = "macos"
    elif "linux" in os_name:
        os_key = "linux"
    elif "win" in os_name:
        os_key = "windows"
    else:
        fail("Unsupported operating system: " + os_name)

    if arch == "aarch64" or arch == "arm64":
        arch_key = "arm64"
    elif arch == "amd64" or arch == "x86_64" or arch == "x64":
        arch_key = "x64"
    else:
        fail("Unsupported architecture: " + arch)

    return os_key + "-" + arch_key

def _dart_sdk_impl(repository_ctx):
    """Implementation of the dart_sdk repository rule."""
    version = repository_ctx.attr.version
    platform = _get_platform(repository_ctx)

    # Check for local SDK override
    dart_home = repository_ctx.os.environ.get("DART_HOME")
    if dart_home:
        repository_ctx.report_progress("Using local Dart SDK at {}".format(dart_home))
        sdk_path = repository_ctx.path(dart_home)
        if not sdk_path.exists:
            fail("DART_HOME points to non-existent path: {}".format(dart_home))

        # Symlink essential directories
        repository_ctx.symlink(sdk_path.get_child("bin"), "bin")
        repository_ctx.symlink(sdk_path.get_child("lib"), "lib")

        if sdk_path.get_child("include").exists:
            repository_ctx.symlink(sdk_path.get_child("include"), "include")

        if sdk_path.get_child("version").exists:
            repository_ctx.symlink(sdk_path.get_child("version"), "version")
            version = repository_ctx.read(sdk_path.get_child("version")).strip()
        else:
            version = "local"

        platform = "local"

    else:
        if platform not in _DART_SDK_URLS:
            fail("No Dart SDK available for platform: " + platform)

        url = _DART_SDK_URLS[platform].format(version = version)

        # Look up checksum for the specific version
        sha256 = ""
        if version in _DART_SDK_SHA256:
            sha256 = _DART_SDK_SHA256[version].get(platform, "")

        # Download and extract the SDK
        repository_ctx.report_progress("Downloading Dart SDK {} for {}...".format(version, platform))

        # Download the SDK zip file
        if sha256:
            repository_ctx.download_and_extract(
                url = url,
                sha256 = sha256,
                stripPrefix = "dart-sdk",
            )
        else:
            # No checksum verification (for development/initial setup)
            repository_ctx.download_and_extract(
                url = url,
                stripPrefix = "dart-sdk",
            )

    # Create the BUILD.bazel file (Common logic)
    _generate_build_file(repository_ctx, version, platform)

    # Disable analytics if requested
    disable_analytics = repository_ctx.attr.disable_analytics
    if disable_analytics:
        # Create a script to disable analytics on first use
        analytics_script = '''#!/bin/bash
# Disable Dart analytics
"$1/bin/dart" --disable-analytics 2>/dev/null || true
'''
        repository_ctx.file("disable_analytics.sh", content = analytics_script, executable = True)

        analytics_script_bat = '''@echo off
REM Disable Dart analytics
"%~1\\bin\\dart.exe" --disable-analytics 2>nul
'''
        repository_ctx.file("disable_analytics.bat", content = analytics_script_bat, executable = True)

    # Create a wrapper script that sets up the environment
    dart_ext = ".exe" if "windows" in platform else ""
    repository_ctx.file("dart_wrapper.sh", content = """#!/bin/bash
# Dart SDK wrapper script
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
exec "$SCRIPT_DIR/bin/dart{ext}" "$@"
""".format(ext = dart_ext), executable = True)

def _generate_build_file(repository_ctx, version, platform):
    is_windows = "windows" in platform
    if platform == "local":
        is_windows = "win" in repository_ctx.os.name.lower()

    dart_ext = ".exe" if is_windows else ""

    repository_ctx.file("BUILD.bazel", content = """
# Auto-generated by dart_sdk/dart_local_sdk repository rule.
# Dart SDK version: {version}
# Platform: {platform}

package(default_visibility = ["//visibility:public"])

filegroup(
    name = "sdk",
    srcs = glob(["**"]),
)

# Dart executable
exports_files(["bin/dart{ext}"])

# Toolchain targets
filegroup(
    name = "dart_bin",
    srcs = ["bin/dart{ext}"],
)

filegroup(
    name = "dart_libs",
    srcs = glob(["lib/**"]),
)
""".format(version = version, platform = platform, ext = dart_ext))

dart_sdk = repository_rule(
    implementation = _dart_sdk_impl,
    attrs = {
        "version": attr.string(
            default = DART_VERSION,
            doc = "The Dart SDK version to download.",
        ),
        "disable_analytics": attr.bool(
            default = True,
            doc = "Disable Dart analytics for hermetic builds.",
        ),
    },
    environ = ["DART_HOME"],
    doc = """Downloads and configures the Dart SDK automatically.""",
)

def _dart_local_sdk_impl(repository_ctx):
    path_str = repository_ctx.attr.path
    sdk_path = repository_ctx.path(path_str)

    if not sdk_path.exists:
        fail("Path specified in dart_local_sdk does not exist: {}".format(path_str))

    repository_ctx.report_progress("Configuring local Dart SDK at {}".format(path_str))

    # Symlink essential directories
    repository_ctx.symlink(sdk_path.get_child("bin"), "bin")
    repository_ctx.symlink(sdk_path.get_child("lib"), "lib")

    if sdk_path.get_child("include").exists:
        repository_ctx.symlink(sdk_path.get_child("include"), "include")

    version = "local"
    if sdk_path.get_child("version").exists:
        repository_ctx.symlink(sdk_path.get_child("version"), "version")
        version = repository_ctx.read(sdk_path.get_child("version")).strip()

    _generate_build_file(repository_ctx, version, "local")

    # Wrapper
    # Determine extension?
    # We can check if bin/dart.exe exists
    dart_ext = ".exe" if sdk_path.get_child("bin").get_child("dart.exe").exists else ""
    repository_ctx.file("dart_wrapper.sh", content = """#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
exec "$SCRIPT_DIR/bin/dart{ext}" "$@"
""".format(ext = dart_ext), executable = True)

dart_local_sdk = repository_rule(
    implementation = _dart_local_sdk_impl,
    attrs = {
        "path": attr.string(mandatory = True, doc = "Absolute path to the Dart SDK Directory"),
    },
    doc = """Configures a local Dart SDK.""",
)

def dart_rules_dependencies():
    """Declares external dependencies for Dart rules."""
    if not native.existing_rule("dart_sdk"):
        dart_sdk(name = "dart_sdk")

def dart_register_toolchains(version = DART_VERSION):
    """Registers Dart toolchains."""

    # Register the SDK repository if not already registered
    if not native.existing_rule("dart_sdk"):
        dart_sdk(
            name = "dart_sdk",
            version = version,
        )

# Helper to extract dependencies from pubspec.yaml
def _extract_pubspec_deps(content):
    deps = []
    in_dependencies = False
    for line in content.split("\n"):
        line = line.strip()
        if line == "dependencies:":
            in_dependencies = True
            continue
        if in_dependencies:
            if not line or line.startswith("#"):
                continue
            if line.endswith(":") or line == "dev_dependencies:" or line == "dependency_overrides:" or line == "environment:":
                in_dependencies = False
                break

            # Parse "name:" or "name: version"
            parts = line.split(":")
            if len(parts) >= 1:
                name = parts[0].strip()
                if name and name != "flutter" and name != "sdk":  # Skip SDK deps
                    deps.append(name)
    return deps

def _dart_package_impl(ctx):
    url = "https://pub.dev/api/archives/{}-{}.tar.gz".format(ctx.attr.package_name, ctx.attr.version)

    # Use manual download and extraction to avoid Java GZIP issues with some packages
    archive = "package.tar.gz"
    ctx.download(
        url = url,
        sha256 = ctx.attr.sha256,
        output = archive,
    )

    # Extract using system tar (standard in Bazel environment)
    res = ctx.execute(["tar", "-xf", archive])
    if res.return_code != 0:
        fail("Failed to extract {}: {}".format(url, res.stderr))

    ctx.delete(archive)

    # Read pubspec to find dependencies
    content = ctx.read("pubspec.yaml")
    deps = _extract_pubspec_deps(content)

    # Format deps labels
    dep_labels = ["@dart_deps_%s//:%s" % (d, d) for d in deps]

    rules_label = ctx.attr.rules_dart_label

    ctx.file("BUILD.bazel", """
load("{}", "dart_library")

package(default_visibility = ["//visibility:public"])

dart_library(
    name = "{name}",
    srcs = glob(["lib/**/*.dart"]),
    pubspec = "pubspec.yaml",
    deps = {deps},
)
""".format(
        rules_label,
        name = ctx.attr.package_name,
        deps = str(dep_labels),
    ))

dart_package = repository_rule(
    implementation = _dart_package_impl,
    attrs = {
        "package_name": attr.string(mandatory = True),
        "version": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "rules_dart_label": attr.string(default = "@rules_dart//:defs.bzl"),
    },
)
