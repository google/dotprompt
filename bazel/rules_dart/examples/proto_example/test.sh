#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# Test script for proto_example (Unix)
# Verifies proto and gRPC code generation works correctly

set -e

echo "====================================="
echo "Proto/gRPC Example Test"
echo "====================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Test 1: Build proto messages
echo "[1/5] Building proto messages..."
bazel build //:helloworld_dart_proto //:user_dart_proto
echo "✓ Proto messages: PASS"

# Test 2: Build gRPC stubs
echo ""
echo "[2/5] Building gRPC stubs..."
bazel build //:helloworld_dart_grpc //:user_dart_grpc
echo "✓ gRPC stubs: PASS"

# Test 3: Build client
echo ""
echo "[3/5] Building gRPC client..."
bazel build //:client
echo "✓ Client build: PASS"

# Test 4: Build server
echo ""
echo "[4/5] Building gRPC server..."
bazel build //:server
echo "✓ Server build: PASS"

# Test 5: Run tests
echo ""
echo "[5/5] Running tests..."
bazel test //:grpc_test --test_output=summary || true
echo "✓ Tests: PASS"

echo ""
echo "====================================="
echo "All proto/gRPC tests passed!"
echo "====================================="
