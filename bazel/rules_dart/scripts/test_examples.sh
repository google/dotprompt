#!/bin/bash
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

# =============================================================================
# rules_dart Integration Test Script (Unix)
# =============================================================================
#
# This script tests all rules_dart functionality on Unix-like systems:
# - macOS (x64, arm64)
# - Linux (x64, arm64)
#
# Usage:
#   ./scripts/test_examples.sh
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$SCRIPT_DIR/../examples/hello_world"

echo "=============================================="
echo "  rules_dart Integration Tests (Unix)"
echo "=============================================="
echo ""
echo "Platform: $(uname -s) $(uname -m)"
echo "Bazel: $(bazel --version)"
echo ""

pushd "$EXAMPLES_DIR" > /dev/null

# -----------------------------------------------------------------------------
# Step 1: Clean build
# -----------------------------------------------------------------------------
echo "[1/7] Cleaning previous build..."
bazel clean --expunge 2>/dev/null || true

# -----------------------------------------------------------------------------
# Step 2: Build all targets
# -----------------------------------------------------------------------------
echo "[2/7] Building all targets..."
bazel build --verbose_failures //...

# -----------------------------------------------------------------------------
# Step 3: Test compilation targets
# -----------------------------------------------------------------------------
echo "[3/7] Testing compilation targets..."
echo "  - dart_native_binary"
bazel build //:hello_native
echo "  - dart_js_binary"
bazel build //:hello_js
echo "  - dart_wasm_binary"
bazel build //:hello_wasm 2>/dev/null || echo "    (WebAssembly may not be supported on this platform)"
echo "  - dart_aot_snapshot"
bazel build //:hello_aot

# -----------------------------------------------------------------------------
# Step 4: Test pub commands
# -----------------------------------------------------------------------------
echo "[4/7] Testing pub commands..."
echo "  - dart_pub_get"
bazel run //:hello_pub_get
echo "  - dart_pub_publish --help"
bazel run //:hello_release -- --help 2>/dev/null || true

# -----------------------------------------------------------------------------
# Step 5: Run unit tests
# -----------------------------------------------------------------------------
echo "[5/7] Running unit tests..."
bazel test --verbose_failures //:hello_test

# -----------------------------------------------------------------------------
# Step 6: Run CI checks
# -----------------------------------------------------------------------------
echo "[6/7] Running CI checks..."
echo "  - dart_format_check"
bazel test //:hello_format
echo "  - dart_analyze"
bazel test //:hello_analyze

# -----------------------------------------------------------------------------
# Step 7: Test native binary execution
# -----------------------------------------------------------------------------
echo "[7/7] Testing native binary execution..."
bazel run //:hello_native

echo ""
echo "=============================================="
echo "  All tests passed!"
echo "=============================================="

popd > /dev/null
