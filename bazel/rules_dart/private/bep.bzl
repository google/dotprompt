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

"""Build Event Protocol (BEP) integration for rules_dart.

This module provides utilities for integrating Dart builds with Bazel's
Build Event Protocol, enabling CI/CD systems to consume structured build data.

## Build Event Protocol Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Build Event Protocol Flow                                │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Bazel Build                                                                     │
│       │                                                                          │
│       ▼                                                                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────────┐      │
│  │ BEP Stream  │───▶│ BEP File    │───▶│ CI/CD System                    │      │
│  │ (protobuf)  │    │ (JSON/proto)│    │ • Build dashboards              │      │
│  └─────────────┘    └─────────────┘    │ • Failure analysis              │      │
│                                        │ • Performance tracking           │      │
│  Events Include:                       │ • Test result aggregation        │      │
│  • BuildStarted                        └─────────────────────────────────┘      │
│  • TargetConfigured                                                              │
│  • TargetCompleted                                                               │
│  • TestResult                                                                    │
│  • BuildFinished                                                                 │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Usage

Enable BEP output in your .bazelrc:

```
# .bazelrc
build --build_event_json_file=bazel-bep.json
build --build_event_binary_file=bazel-bep.proto

# For CI systems
build:ci --build_event_json_file=build_events.json
build:ci --build_event_publish_all_actions
```

Or pass flags directly:

```bash
bazel build //... --build_event_json_file=events.json
bazel test //... --build_event_json_file=test_events.json
```

## CI Integration Examples

### GitHub Actions
```yaml
- name: Build with BEP
  run: |
    bazel build //... --build_event_json_file=bep.json
    
- name: Parse build events
  run: |
    jq '.id.targetCompleted.label' bep.json
```

### BuildKite / BuildBuddy
```bash
bazel build //... \\
    --bes_backend=grpcs://remote.buildbuddy.io \\
    --bes_results_url=https://app.buildbuddy.io/invocation/
```
"""

# BEP-related providers for Dart targets
DartBuildEventInfo = provider(
    doc = "Build event information for Dart targets.",
    fields = {
        "target_label": "String: The target label.",
        "target_kind": "String: Type of target (library, binary, test).",
        "source_count": "Int: Number of source files.",
        "dependency_count": "Int: Number of direct dependencies.",
        "build_time_ms": "Int: Build time in milliseconds (if available).",
        "output_files": "List[File]: Output files produced.",
        "test_results": "Optional TestResultInfo: Test results if applicable.",
    },
)

DartTestResultInfo = provider(
    doc = "Test result information for BEP.",
    fields = {
        "status": "String: PASSED, FAILED, FLAKY, TIMEOUT, NO_STATUS.",
        "duration_ms": "Int: Test duration in milliseconds.",
        "cached": "Bool: Whether result was cached.",
        "shard_count": "Int: Number of shards.",
        "run_count": "Int: Number of test runs.",
        "failures": "List[String]: Failure messages if any.",
    },
)

def create_bep_aspect():
    """Create an aspect that collects BEP-compatible information.

    Returns:
        An aspect definition.
    """

    def _bep_aspect_impl(_target, ctx):
        source_count = 0
        if hasattr(ctx.rule.attr, "srcs"):
            source_count = len(ctx.rule.files.srcs)

        dep_count = 0
        if hasattr(ctx.rule.attr, "deps"):
            dep_count = len(ctx.rule.attr.deps)

        # Determine target kind
        target_kind = "unknown"
        if ctx.rule.kind.startswith("dart_library"):
            target_kind = "library"
        elif ctx.rule.kind.startswith("dart_binary"):
            target_kind = "binary"
        elif ctx.rule.kind.startswith("dart_test"):
            target_kind = "test"

        return [
            DartBuildEventInfo(
                target_label = str(ctx.label),
                target_kind = target_kind,
                source_count = source_count,
                dependency_count = dep_count,
                build_time_ms = 0,
                output_files = [],
                test_results = None,
            ),
        ]

    return aspect(
        implementation = _bep_aspect_impl,
        doc = "Collects BEP-compatible build information.",
        attr_aspects = ["deps"],
    )

dart_bep_aspect = create_bep_aspect()

# =============================================================================
# BEP Configuration Helpers
# =============================================================================

def bep_flags(
        json_file = None,
        binary_file = None,
        publish_all_actions = False,
        bes_backend = None,
        bes_results_url = None):
    """Generate BEP-related bazel flags.

    Args:
        json_file: Path for JSON BEP output.
        binary_file: Path for binary (protobuf) BEP output.
        publish_all_actions: Include all actions in BEP stream.
        bes_backend: Build Event Service backend URL.
        bes_results_url: URL for viewing build results.

    Returns:
        List of bazel flags.
    """
    flags = []

    if json_file:
        flags.append("--build_event_json_file={}".format(json_file))

    if binary_file:
        flags.append("--build_event_binary_file={}".format(binary_file))

    if publish_all_actions:
        flags.append("--build_event_publish_all_actions")

    if bes_backend:
        flags.append("--bes_backend={}".format(bes_backend))

    if bes_results_url:
        flags.append("--bes_results_url={}".format(bes_results_url))

    return flags
