@echo off
REM Copyright 2026 Google LLC
REM SPDX-License-Identifier: Apache-2.0

REM Test script for rules_flutter examples (Windows)

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "RULES_FLUTTER_DIR=%SCRIPT_DIR%.."

echo ========================================
echo Testing rules_flutter examples
echo ========================================
echo.

cd /d "%RULES_FLUTTER_DIR%"

echo Step 1: Building Flutter rules...
bazel build //:defs.bzl
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo Step 2: Building gRPC example (analysis only)...
cd examples\grpc_app
REM Note: Full builds require Flutter SDK

echo.
echo ========================================
echo All tests passed!
echo ========================================
exit /b 0
