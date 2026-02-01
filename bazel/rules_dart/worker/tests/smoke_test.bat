@echo off
REM Copyright 2026 Google LLC
REM SPDX-License-Identifier: Apache-2.0

REM Smoke test for the persistent worker on Windows

setlocal enabledelayedexpansion

echo === Worker Smoke Test (Windows) ===

REM Test 1: One-shot mode (help)
echo [1/2] Testing one-shot mode...
call "%TEST_SRCDIR%\_main\bazel\rules_dart\worker\worker_wrapper.bat" --help
if %errorlevel% neq 0 (
    echo One-shot mode: FAIL
    exit /b 1
)
echo One-shot mode: PASS

REM Test 2: Verify worker script exists
echo [2/2] Verifying worker script...
if exist "%TEST_SRCDIR%\_main\bazel\rules_dart\worker\bin\worker.dart" (
    echo Worker script exists: PASS
) else (
    echo Worker script exists: FAIL
    exit /b 1
)

echo.
echo === All smoke tests passed ===
exit /b 0
