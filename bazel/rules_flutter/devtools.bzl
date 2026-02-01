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

"""Flutter DevTools integration rules.

# ELI5 (Explain Like I'm 5)

## What is DevTools?

Imagine you have a magnifying glass that lets you see inside your app:
- How fast it runs (performance)
- How much memory it uses
- What's happening on the network
- What your widget tree looks like

This module creates rules that launch DevTools alongside your app!

## Key Features

| Feature | Description |
|---------|-------------|
| **Inspector** | Widget tree visualization and editing |
| **Performance** | Frame-by-frame rendering analysis |
| **Memory** | Heap snapshots and allocation tracking |
| **Network** | HTTP request/response inspection |
| **Logging** | Structured log viewing |
| **CPU Profiler** | Method-level performance analysis |

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Flutter DevTools Integration                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  bazel run //:devtools                                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  1. Start Flutter app with --observatory-port                       │   │
│  │       ↓                                                             │   │
│  │  2. Wait for VM service URL                                         │   │
│  │       ↓                                                             │   │
│  │  3. Launch DevTools connected to VM service                         │   │
│  │       ↓                                                             │   │
│  │  4. Open browser to DevTools UI                                     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
"""

load("//private:helpers.bzl", "runfiles_path")

# =============================================================================
# Provider
# =============================================================================

FlutterDevToolsInfo = provider(
    doc = "Information about DevTools configuration for a Flutter app.",
    fields = {
        "app_target": "Label of the Flutter application",
        "features": "List of enabled DevTools features",
        "vm_service_port": "Port for VM service connection",
        "devtools_port": "Port for DevTools web UI",
    },
)

# =============================================================================
# Rule Implementation
# =============================================================================

def _flutter_devtools_impl(ctx):
    """Implementation of flutter_devtools rule."""
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo],
    )

    flutter_bin = ctx.executable.flutter_sdk
    dart_bin = ctx.executable.dart_sdk
    app_target = ctx.attr.app
    features = ctx.attr.features
    vm_service_port = ctx.attr.vm_service_port
    devtools_port = ctx.attr.devtools_port

    # Create runner script
    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)

    # Get paths
    flutter_path = runfiles_path(flutter_bin)
    dart_path = runfiles_path(dart_bin)

    # Feature flags for DevTools
    feature_args = []
    if "inspector" in features:
        feature_args.append("--inspector")
    if "performance" in features:
        feature_args.append("--performance")
    if "memory" in features:
        feature_args.append("--memory")
    if "network" in features:
        feature_args.append("--network")
    if "logging" in features:
        feature_args.append("--logging")
    if "cpu_profiler" in features:
        feature_args.append("--cpu-profiler")

    if is_windows:
        content = '''@echo off
setlocal enabledelayedexpansion

REM Flutter DevTools Launcher
REM Generated by rules_flutter

set "RUNFILES=%~dp0"
set "FLUTTER_BIN=%RUNFILES%{flutter_path}"
set "DART_BIN=%RUNFILES%{dart_path}"
set "VM_PORT={vm_port}"
set "DEVTOOLS_PORT={devtools_port}"

echo Starting Flutter DevTools...
echo.
echo Features: {features}
echo VM Service Port: %VM_PORT%
echo DevTools Port: %DEVTOOLS_PORT%
echo.

REM Activate DevTools if not installed
call "%DART_BIN%" pub global activate devtools 2>nul

REM Start DevTools
echo Launching DevTools at http://localhost:%DEVTOOLS_PORT%
call "%DART_BIN%" pub global run devtools --port=%DEVTOOLS_PORT% --machine

exit /b %errorlevel%
'''.format(
            flutter_path = flutter_path.replace("/", "\\"),
            dart_path = dart_path.replace("/", "\\"),
            vm_port = vm_service_port,
            devtools_port = devtools_port,
            features = " ".join(features),
        )
    else:
        content = '''#!/bin/bash
set -e

# Flutter DevTools Launcher
# Generated by rules_flutter

RUNFILES="${{BASH_SOURCE[0]%/*}}"
FLUTTER_BIN="$RUNFILES/{flutter_path}"
DART_BIN="$RUNFILES/{dart_path}"
VM_PORT="{vm_port}"
DEVTOOLS_PORT="{devtools_port}"

echo "Starting Flutter DevTools..."
echo
echo "Features: {features}"
echo "VM Service Port: $VM_PORT"
echo "DevTools Port: $DEVTOOLS_PORT"
echo

# Activate DevTools if not installed
"$DART_BIN" pub global activate devtools 2>/dev/null || true

# Start DevTools
echo "Launching DevTools at http://localhost:$DEVTOOLS_PORT"

# If app target is specified, run app first
if [ -n "{app_label}" ]; then
    echo "Starting app with VM service on port $VM_PORT..."
    # Run app in background with observatory port
    "$FLUTTER_BIN" run --observatory-port=$VM_PORT &
    APP_PID=$!
    
    # Wait for VM service to be ready
    sleep 3
    
    # Connect DevTools to running app
    "$DART_BIN" pub global run devtools \\
        --port=$DEVTOOLS_PORT \\
        --vm-uri=http://localhost:$VM_PORT
    
    # Kill app when DevTools exits
    kill $APP_PID 2>/dev/null || true
else
    # Just launch DevTools standalone
    "$DART_BIN" pub global run devtools --port=$DEVTOOLS_PORT --machine
fi

echo "DevTools exited."
'''.format(
            flutter_path = flutter_path,
            dart_path = dart_path,
            vm_port = vm_service_port,
            devtools_port = devtools_port,
            features = " ".join(features),
            app_label = str(app_target.label) if app_target else "",
        )

    ctx.actions.write(
        output = runner_script,
        content = content,
        is_executable = True,
    )

    # Collect runfiles
    runfiles = ctx.runfiles(files = [flutter_bin, dart_bin])
    if app_target:
        runfiles = runfiles.merge(app_target[DefaultInfo].default_runfiles)

    return [
        DefaultInfo(
            executable = runner_script,
            runfiles = runfiles,
        ),
        FlutterDevToolsInfo(
            app_target = app_target.label if app_target else None,
            features = features,
            vm_service_port = vm_service_port,
            devtools_port = devtools_port,
        ),
    ]

_flutter_devtools = rule(
    implementation = _flutter_devtools_impl,
    attrs = {
        "app": attr.label(
            doc = "Flutter application to connect to DevTools.",
            providers = [DefaultInfo],
        ),
        "features": attr.string_list(
            doc = "DevTools features to enable.",
            default = ["inspector", "performance", "memory", "network", "logging"],
        ),
        "vm_service_port": attr.int(
            doc = "Port for VM service connection.",
            default = 8181,
        ),
        "devtools_port": attr.int(
            doc = "Port for DevTools web UI.",
            default = 9100,
        ),
        "flutter_sdk": attr.label(
            doc = "Flutter SDK executable.",
            default = Label("@flutter_sdk//:flutter_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "dart_sdk": attr.label(
            doc = "Dart SDK executable.",
            default = Label("@flutter_sdk//:dart_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(
            default = Label("@platforms//os:windows"),
        ),
    },
    executable = True,
    doc = "Launches Flutter DevTools for debugging and profiling.",
)

# =============================================================================
# Public Macro
# =============================================================================

def flutter_devtools(
        name,
        app = None,
        features = None,
        vm_service_port = 8181,
        devtools_port = 9100,
        visibility = None,
        **kwargs):
    """Launch Flutter DevTools for debugging and profiling.

    DevTools provides a suite of debugging and profiling tools:
    - Widget Inspector: Visualize and edit the widget tree
    - Performance: Analyze rendering performance
    - Memory: Track memory usage and find leaks
    - Network: Inspect HTTP requests and responses
    - Logging: View structured logs
    - CPU Profiler: Analyze method-level performance

    Args:
        name: Name of the DevTools target.
        app: Optional Flutter application to connect to.
        features: List of DevTools features to enable.
            Options: "inspector", "performance", "memory", "network",
                     "logging", "cpu_profiler"
            Default: All features enabled.
        vm_service_port: Port for VM service connection (default: 8181).
        devtools_port: Port for DevTools web UI (default: 9100).
        visibility: Target visibility.
        **kwargs: Additional arguments passed to the rule.

    Example:
        ```python
        flutter_application(
            name = "my_app",
            srcs = glob(["lib/**/*.dart"]),
        )

        flutter_devtools(
            name = "devtools",
            app = ":my_app",
            features = ["inspector", "performance", "memory"],
        )
        ```

        Then run: `bazel run //:devtools`
    """
    if features == None:
        features = ["inspector", "performance", "memory", "network", "logging"]

    _flutter_devtools(
        name = name,
        app = app,
        features = features,
        vm_service_port = vm_service_port,
        devtools_port = devtools_port,
        visibility = visibility,
        **kwargs
    )

# =============================================================================
# DevTools Configuration Rule
# =============================================================================

def _flutter_devtools_config_impl(ctx):
    """Generate DevTools configuration file."""
    config_file = ctx.actions.declare_file("devtools_options.yaml")

    content = """# Flutter DevTools Configuration
# Generated by rules_flutter

# Performance view settings
performance:
  showFlameChart: true
  showTimelineEvents: true
  recordCpuProfile: {record_cpu}

# Memory view settings
memory:
  showHeapSnapshots: true
  trackAllocations: {track_allocs}
  autoSnapshot: false

# Inspector settings
inspector:
  selectWidgetOnHover: true
  highlightRepaintedWidgets: {highlight_repaints}

# Network settings
network:
  recordOnStart: true

# Logging settings
logging:
  showTimestamps: true
  wrapLongLines: true
""".format(
        record_cpu = "true" if "cpu_profiler" in ctx.attr.features else "false",
        track_allocs = "true" if "memory" in ctx.attr.features else "false",
        highlight_repaints = "true" if "performance" in ctx.attr.features else "false",
    )

    ctx.actions.write(
        output = config_file,
        content = content,
    )

    return [DefaultInfo(files = depset([config_file]))]

flutter_devtools_config = rule(
    implementation = _flutter_devtools_config_impl,
    attrs = {
        "features": attr.string_list(
            doc = "DevTools features to configure.",
            default = ["inspector", "performance", "memory", "network", "logging"],
        ),
    },
    doc = "Generates a DevTools configuration file.",
)
