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

"""Bzlmod extension for Dart SDK configuration.

This extension allows the Dart SDK to be configured via Bzlmod.
It downloads the SDK from Google's official CDN.
"""

load(":repositories.bzl", "DART_VERSION", "dart_sdk")

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
