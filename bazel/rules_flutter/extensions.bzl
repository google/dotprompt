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

"""Module extensions for rules_flutter.

Usage in MODULE.bazel:
    flutter = use_extension("@rules_flutter//:extensions.bzl", "flutter")
    flutter.configure(version = "3.27.0", channel = "stable")
    use_repo(flutter, "flutter_sdk")
"""

load("//:repositories.bzl", "flutter_sdk")

def _flutter_extension_impl(module_ctx):
    """Module extension for Flutter SDK."""

    # Ensure default SDK is always registered if not explicitly configured
    sdk_registered = False

    for mod in module_ctx.modules:
        for config in mod.tags.configure:
            flutter_sdk(
                name = config.name or "flutter_sdk",
                version = config.version,
                channel = config.channel,
                sdk_home = config.sdk_home,
                disable_analytics = config.disable_analytics,
            )
            sdk_registered = True

    if not sdk_registered:
        flutter_sdk(
            name = "flutter_sdk",
            version = "3.27.0",
            channel = "stable",
            disable_analytics = True,
        )

_configure = tag_class(
    attrs = {
        "name": attr.string(default = "flutter_sdk"),
        "version": attr.string(default = "3.27.0"),
        "channel": attr.string(default = "stable"),
        "sdk_home": attr.string(),
        "disable_analytics": attr.bool(default = True),
    },
)

flutter = module_extension(
    implementation = _flutter_extension_impl,
    tag_classes = {"configure": _configure},
)
