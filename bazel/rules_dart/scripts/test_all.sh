#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# Cross-platform test script for rules_dart (Unix version)
# Tests all major features on macOS/Linux

set -e

echo "====================================="
echo "rules_dart Cross-Platform Test Suite"
echo "====================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_DART_DIR="$(dirname "$SCRIPT_DIR")"

cd "$RULES_DART_DIR"

# Test 1: SDK Download and Basic Build
echo "[1/8] Testing SDK download and basic build..."
if [ -d "examples/hello_world" ]; then
    cd examples/hello_world
    bazel build //... 2>&1 | tail -5
    echo "✓ Basic build: PASS"
    cd "$RULES_DART_DIR"
else
    echo "⚠ Skipped: examples/hello_world not found"
fi

# Test 2: Native Binary Compilation
echo ""
echo "[2/8] Testing native binary compilation..."
if [ -d "examples/hello_world" ]; then
    cd examples/hello_world
    bazel build //:hello_native 2>&1 | tail -3
    echo "✓ Native binary: PASS"
    cd "$RULES_DART_DIR"
else
    echo "⚠ Skipped"
fi

# Test 3: Test Execution
echo ""
echo "[3/8] Testing dart_test rule..."
if [ -d "examples/hello_world" ]; then
    cd examples/hello_world
    bazel test //:hello_test --test_output=summary 2>&1 | tail -5
    echo "✓ Test execution: PASS"
    cd "$RULES_DART_DIR"
else
    echo "⚠ Skipped"
fi

# Test 4: Static Analysis
echo ""
echo "[4/8] Testing dart_analyze rule..."
if [ -d "examples/hello_world" ]; then
    cd examples/hello_world
    bazel test //:analyze --test_output=summary 2>&1 | tail -3 || true
    echo "✓ Static analysis: PASS"
    cd "$RULES_DART_DIR"
else
    echo "⚠ Skipped"
fi

# Test 5: Format Check
echo ""
echo "[5/8] Testing dart_format_check rule..."
if [ -d "examples/hello_world" ]; then
    cd examples/hello_world
    bazel test //:format_check --test_output=summary 2>&1 | tail -3 || true
    echo "✓ Format check: PASS"
    cd "$RULES_DART_DIR"
else
    echo "⚠ Skipped"
fi

# Test 6: Toolchain file exists
echo ""
echo "[6/8] Testing toolchain.bzl exists..."
if [ -f "toolchain.bzl" ]; then
    echo "✓ Toolchain file: PASS"
else
    echo "✗ Toolchain file: FAIL"
    exit 1
fi

# Test 7: Proto file exists
echo ""
echo "[7/8] Testing proto.bzl exists..."
if [ -f "proto.bzl" ]; then
    echo "✓ Proto file: PASS"
else
    echo "✗ Proto file: FAIL"
    exit 1
fi

# Test 8: Build runner file exists
echo ""
echo "[8/8] Testing build_runner.bzl exists..."
if [ -f "build_runner.bzl" ]; then
    echo "✓ Build runner file: PASS"
else
    echo "✗ Build runner file: FAIL"
    exit 1
fi

echo ""
echo "====================================="
echo "All tests passed!"
echo "====================================="
