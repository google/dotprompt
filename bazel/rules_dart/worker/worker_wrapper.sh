#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# Worker wrapper script for Unix systems
# Locates the Dart SDK and runs the worker

set -e

# Locate runfiles
if [[ -n "${RUNFILES_DIR:-}" ]]; then
    RUNFILES="$RUNFILES_DIR"
elif [[ -d "$0.runfiles" ]]; then
    RUNFILES="$0.runfiles"
elif [[ -d "${BASH_SOURCE[0]}.runfiles" ]]; then  
    RUNFILES="${BASH_SOURCE[0]}.runfiles"
else
    echo "ERROR: Cannot find runfiles directory" >&2
    exit 1
fi

# Find the Dart SDK
DART_BIN="$RUNFILES/_main/external/dart_sdk/bin/dart"
if [[ ! -f "$DART_BIN" ]]; then
    # Try Bzlmod path
    DART_BIN="$RUNFILES/rules_dart++dart+dart_sdk/bin/dart"
fi
if [[ ! -f "$DART_BIN" ]]; then
    # Fallback to system dart
    DART_BIN="dart"
fi

# Find the worker script
WORKER_SCRIPT="$RUNFILES/_main/bazel/rules_dart/worker/bin/worker.dart"
if [[ ! -f "$WORKER_SCRIPT" ]]; then
    WORKER_SCRIPT="$RUNFILES/rules_dart/worker/bin/worker.dart"
fi

exec "$DART_BIN" run "$WORKER_SCRIPT" "$@"
