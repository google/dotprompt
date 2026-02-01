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

"""Protocol Buffers and gRPC support for Dart.

This module provides rules for generating Dart code from .proto files
using the protoc-gen-dart plugin.

Architecture:
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Dart Proto Generation                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  user.proto                                                                  │
│       │                                                                      │
│       ▼                                                                      │
│  protoc --dart_out=...                                                       │
│       │                                                                      │
│       ├── user.pb.dart        (messages)                                    │
│       ├── user.pbenum.dart    (enums)                                       │
│       ├── user.pbjson.dart    (JSON serialization)                          │
│       └── user.pbgrpc.dart    (gRPC service stubs, if --grpc_out used)     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Usage:
    load("@rules_dart//:proto.bzl", "dart_proto_library", "dart_grpc_library")

    proto_library(
        name = "user_proto",
        srcs = ["user.proto"],
    )

    dart_proto_library(
        name = "user_dart_proto",
        deps = [":user_proto"],
    )

    dart_grpc_library(
        name = "user_dart_grpc",
        deps = [":user_proto"],
    )

Requirements:
    - protoc (Protocol Buffer compiler)
    - protoc-gen-dart plugin (from package:protoc_plugin)
    - For gRPC: protoc-gen-dart with grpc option
"""

load("@com_google_protobuf//bazel/common:proto_info.bzl", "ProtoInfo")

# Proto info provider
DartProtoInfo = provider(
    doc = "Information about generated Dart proto files.",
    fields = {
        "dart_srcs": "Depset of generated .dart files",
        "direct_srcs": "List of direct .dart files from this target",
        "transitive_srcs": "Depset of all transitive .dart files",
    },
)

def _dart_proto_library_impl(ctx):
    """Implementation of dart_proto_library."""

    # Collect proto sources from deps
    proto_infos = [dep[ProtoInfo] for dep in ctx.attr.deps if ProtoInfo in dep]

    if not proto_infos:
        fail("dart_proto_library requires at least one proto_library dep")

    proto_info = proto_infos[0]  # Use first for now
    proto_srcs = proto_info.direct_sources

    # Output directory for generated files
    out_dir = ctx.actions.declare_directory(ctx.label.name + "_dart_proto")

    # Get protoc and plugin
    protoc = ctx.executable._protoc
    plugin = ctx.executable._protoc_gen_dart

    # Build protoc command
    args = ctx.actions.args()
    args.add("--plugin=protoc-gen-dart=" + plugin.path)
    args.add("--dart_out=" + out_dir.path)

    # Add proto paths
    for proto_src in proto_srcs:
        args.add("-I" + proto_src.dirname)
        args.add(proto_src.path)

    ctx.actions.run(
        executable = protoc,
        arguments = [args],
        inputs = depset(proto_srcs, transitive = [proto_info.transitive_sources]),
        outputs = [out_dir],
        tools = [plugin],
        mnemonic = "DartProtoGen",
        progress_message = "Generating Dart protos for %s" % ctx.label,
    )

    return [
        DefaultInfo(files = depset([out_dir])),
        DartProtoInfo(
            dart_srcs = depset([out_dir]),
            direct_srcs = [out_dir],
            transitive_srcs = depset([out_dir]),
        ),
    ]

dart_proto_library = rule(
    implementation = _dart_proto_library_impl,
    doc = "Generates Dart code from proto_library targets.",
    attrs = {
        "deps": attr.label_list(
            doc = "proto_library targets to generate Dart code for.",
            providers = [ProtoInfo],
            mandatory = True,
        ),
        "_protoc": attr.label(
            doc = "The protoc compiler.",
            default = Label("@com_google_protobuf//:protoc"),
            executable = True,
            cfg = "exec",
        ),
        "_protoc_gen_dart": attr.label(
            doc = "The protoc-gen-dart plugin.",
            default = Label("@protoc_gen_dart//:protoc_gen_dart"),
            executable = True,
            cfg = "exec",
        ),
    },
    provides = [DartProtoInfo],
)

def _dart_grpc_library_impl(ctx):
    """Implementation of dart_grpc_library."""

    # Similar to proto but with grpc flag
    proto_infos = [dep[ProtoInfo] for dep in ctx.attr.deps if ProtoInfo in dep]

    if not proto_infos:
        fail("dart_grpc_library requires at least one proto_library dep")

    proto_info = proto_infos[0]
    proto_srcs = proto_info.direct_sources

    out_dir = ctx.actions.declare_directory(ctx.label.name + "_dart_grpc")

    protoc = ctx.executable._protoc
    plugin = ctx.executable._protoc_gen_dart

    args = ctx.actions.args()
    args.add("--plugin=protoc-gen-dart=" + plugin.path)

    # Enable gRPC generation
    args.add("--dart_out=grpc:" + out_dir.path)

    for proto_src in proto_srcs:
        args.add("-I" + proto_src.dirname)
        args.add(proto_src.path)

    ctx.actions.run(
        executable = protoc,
        arguments = [args],
        inputs = depset(proto_srcs, transitive = [proto_info.transitive_sources]),
        outputs = [out_dir],
        tools = [plugin],
        mnemonic = "DartGrpcGen",
        progress_message = "Generating Dart gRPC for %s" % ctx.label,
    )

    return [
        DefaultInfo(files = depset([out_dir])),
        DartProtoInfo(
            dart_srcs = depset([out_dir]),
            direct_srcs = [out_dir],
            transitive_srcs = depset([out_dir]),
        ),
    ]

dart_grpc_library = rule(
    implementation = _dart_grpc_library_impl,
    doc = "Generates Dart gRPC code from proto_library targets.",
    attrs = {
        "deps": attr.label_list(
            doc = "proto_library targets to generate Dart gRPC code for.",
            providers = [ProtoInfo],
            mandatory = True,
        ),
        "_protoc": attr.label(
            doc = "The protoc compiler.",
            default = Label("@com_google_protobuf//:protoc"),
            executable = True,
            cfg = "exec",
        ),
        "_protoc_gen_dart": attr.label(
            doc = "The protoc-gen-dart plugin with gRPC support.",
            default = Label("@protoc_gen_dart//:protoc_gen_dart"),
            executable = True,
            cfg = "exec",
        ),
    },
    provides = [DartProtoInfo],
)
