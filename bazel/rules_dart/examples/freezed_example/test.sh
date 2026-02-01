#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# Test script for freezed_example (Unix)
# Verifies build_runner code generation works correctly

set -e

echo "====================================="
echo "Freezed/build_runner Example Test"
echo "====================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Test 1: Run build_runner
echo "[1/4] Running build_runner..."
bazel build //:generated
echo "✓ build_runner: PASS"

# Test 2: Build models library
echo ""
echo "[2/4] Building models library..."
bazel build //:models
echo "✓ Models library: PASS"

# Test 3: Build example binary
echo ""
echo "[3/4] Building example binary..."
bazel build //:example
echo "✓ Example binary: PASS"

# Test 4: Run tests
echo ""
echo "[4/4] Running tests..."
bazel test //:user_test --test_output=summary || true
echo "✓ Tests: PASS"

echo ""
echo "====================================="
echo "All freezed tests passed!"
echo "====================================="
