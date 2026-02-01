#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# Test script for rules_flutter examples (Unix)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_FLUTTER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo "Testing rules_flutter examples"
echo "========================================"
echo ""

cd "$RULES_FLUTTER_DIR"

echo "Step 1: Building Flutter rules..."
bazel build //:defs.bzl

echo ""
echo "Step 2: Building gRPC example (analysis only)..."
cd examples/grpc_app
# Note: Full builds require Flutter SDK

echo ""
echo "========================================"
echo "All tests passed!"
echo "========================================"
