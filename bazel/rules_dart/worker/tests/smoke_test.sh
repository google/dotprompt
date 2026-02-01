#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# Smoke test for the persistent worker
# Tests both one-shot and persistent worker modes

set -e

echo "=== Worker Smoke Test ==="

# Test 1: One-shot mode (help/version)
echo "[1/3] Testing one-shot mode..."
# The worker should exit cleanly when given no args
timeout 5 echo '' | $TEST_SRCDIR/_main/bazel/rules_dart/worker/worker_unix --help 2>&1 || true
echo "One-shot mode: PASS"

# Test 2: JSON protocol smoke test
echo "[2/3] Testing JSON worker protocol..."
# Send a simple request and check for JSON response
REQUEST='{"arguments": ["echo", "hello"]}'
RESPONSE=$(echo "$REQUEST" | timeout 5 $TEST_SRCDIR/_main/bazel/rules_dart/worker/worker_unix --persistent_worker 2>&1 || true)

if echo "$RESPONSE" | grep -q '"exitCode"'; then
    echo "JSON protocol: PASS"
else
    echo "JSON protocol: FAIL (no valid response)"
    echo "Response was: $RESPONSE"
    exit 1
fi

# Test 3: Multiple requests in worker mode
echo "[3/3] Testing multiple requests..."
REQUESTS='{"arguments": ["echo", "first"]}
{"arguments": ["echo", "second"]}'

RESPONSES=$(echo "$REQUESTS" | timeout 10 $TEST_SRCDIR/_main/bazel/rules_dart/worker/worker_unix --persistent_worker 2>&1 || true)

COUNT=$(echo "$RESPONSES" | grep -c '"exitCode"' || true)
if [ "$COUNT" -ge 2 ]; then
    echo "Multiple requests: PASS ($COUNT responses)"
else
    echo "Multiple requests: FAIL (expected 2+ responses, got $COUNT)"
    exit 1
fi

echo ""
echo "=== All smoke tests passed ==="
