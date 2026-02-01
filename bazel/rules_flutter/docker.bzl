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

"""Docker/OCI container rules for rules_flutter.

This module provides rules for building and running containers for:
- gRPC-Web proxy (Envoy)
- Flutter web builds (nginx)
- Dart gRPC servers

CURRENTLY DISABLED: These rules require rules_oci which has a
toolchain resolution issue with aspect_bazel_lib on Bazel 9.x.

TODO(#125): Re-enable when aspect_bazel_lib toolchain resolution issue is fixed.

To enable OCI support, uncomment the following in MODULE.bazel:
    bazel_dep(name = "aspect_bazel_lib", version = "2.16.0")
    bazel_dep(name = "rules_oci", version = "2.2.0")
    bazel_dep(name = "rules_pkg", version = "1.0.1")

And uncomment the load statements and implementations below.

Usage in BUILD.bazel (when enabled):
    load("@rules_flutter//:docker.bzl", "envoy_grpc_web_proxy")

    envoy_grpc_web_proxy(
        name = "grpc_web_proxy",
        envoy_config = "envoy.yaml",
    )
"""

# TODO(#125): Uncomment when rules_oci is re-enabled
# load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")
# load("@rules_pkg//pkg:tar.bzl", "pkg_tar")

# buildifier: disable=unused-variable
def envoy_grpc_web_proxy(
        name,
        envoy_config,
        base_image = "@envoy",
        proxy_port = 8080,
        admin_port = 9901,
        visibility = None,
        **kwargs):
    """Creates an Envoy gRPC-Web proxy container.

    NOTE: This rule is currently disabled. See module docstring for details.

    This rule builds an OCI image with your Envoy configuration baked in.

    Args:
        name: Target name
        envoy_config: Label to envoy.yaml configuration file
        base_image: Base Envoy image (default: @envoy from oci.pull)
        proxy_port: Port to expose the gRPC-Web proxy (default: 8080)
        admin_port: Port for Envoy admin interface (default: 9901)
        visibility: Visibility
        **kwargs: Additional arguments

    Example:
        envoy_grpc_web_proxy(
            name = "grpc_web_proxy",
            envoy_config = "envoy.yaml",
        )

        # Then run:
        # bazel run //:grpc_web_proxy_tarball
        # docker load -i bazel-bin/.../grpc_web_proxy.tar
        # docker run -p 8080:8080 -p 9901:9901 grpc_web_proxy:latest
    """
    fail("envoy_grpc_web_proxy is currently disabled. See rules_flutter/docker.bzl for details.")

# buildifier: disable=unused-variable
def dart_grpc_server_image(
        name,
        main,
        srcs = [],
        deps = [],
        pubspec = None,
        base_image = "@dart_runtime",
        port = 50051,
        visibility = None,
        **kwargs):
    """Creates a container image for a Dart gRPC server.

    NOTE: This rule is currently disabled. See module docstring for details.

    This rule compiles your Dart server to a native binary and packages it
    in a minimal container.

    Args:
        name: Target name
        main: Main Dart file for the server (e.g., "bin/server.dart")
        srcs: Source files
        deps: Dependencies
        pubspec: pubspec.yaml file
        base_image: Base image with Dart runtime
        port: Port to expose (default: 50051)
        visibility: Visibility
        **kwargs: Additional arguments

    Example:
        dart_grpc_server_image(
            name = "server_image",
            main = "bin/server.dart",
            srcs = glob(["lib/**/*.dart", "bin/**/*.dart"]),
            pubspec = "pubspec.yaml",
        )
    """
    fail("dart_grpc_server_image is currently disabled. See rules_flutter/docker.bzl for details.")

# buildifier: disable=unused-variable
def flutter_web_server(
        name,
        web_bundle,
        base_image = "@nginx",
        port = 80,
        visibility = None,
        **kwargs):
    """Creates a container to serve a Flutter web build with nginx.

    NOTE: This rule is currently disabled. See module docstring for details.

    Args:
        name: Target name
        web_bundle: Label to the Flutter web build output directory
        base_image: Base nginx image
        port: Port to expose (default: 80)
        visibility: Visibility
        **kwargs: Additional arguments

    Example:
        flutter_web_server(
            name = "web_server",
            web_bundle = ":client_web",
        )
    """
    fail("flutter_web_server is currently disabled. See rules_flutter/docker.bzl for details.")
