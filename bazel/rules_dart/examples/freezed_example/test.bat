@echo off
REM Copyright 2026 Google LLC
REM SPDX-License-Identifier: Apache-2.0

REM Test script for freezed_example (Windows)
REM Verifies build_runner code generation works correctly

setlocal enabledelayedexpansion

echo =====================================
echo Freezed/build_runner Example Test
echo =====================================
echo.

cd /d "%~dp0"

REM Test 1: Run build_runner
echo [1/4] Running build_runner...
bazel build //:generated
if %errorlevel% neq 0 (
    echo X build_runner: FAIL
    exit /b 1
)
echo √ build_runner: PASS

REM Test 2: Build models library
echo.
echo [2/4] Building models library...
bazel build //:models
if %errorlevel% neq 0 (
    echo X Models library: FAIL
    exit /b 1
)
echo √ Models library: PASS

REM Test 3: Build example binary
echo.
echo [3/4] Building example binary...
bazel build //:example
if %errorlevel% neq 0 (
    echo X Example binary: FAIL
    exit /b 1
)
echo √ Example binary: PASS

REM Test 4: Run tests
echo.
echo [4/4] Running tests...
bazel test //:user_test --test_output=summary
echo √ Tests: PASS

echo.
echo =====================================
echo All freezed tests passed!
echo =====================================

exit /b 0
