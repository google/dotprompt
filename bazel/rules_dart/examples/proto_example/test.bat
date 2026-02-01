@echo off
REM Copyright 2026 Google LLC
REM SPDX-License-Identifier: Apache-2.0

REM Test script for proto_example (Windows)
REM Verifies proto and gRPC code generation works correctly

setlocal enabledelayedexpansion

echo =====================================
echo Proto/gRPC Example Test
echo =====================================
echo.

cd /d "%~dp0"

REM Test 1: Build proto messages
echo [1/5] Building proto messages...
bazel build //:helloworld_dart_proto //:user_dart_proto
if %errorlevel% neq 0 (
    echo X Proto messages: FAIL
    exit /b 1
)
echo √ Proto messages: PASS

REM Test 2: Build gRPC stubs
echo.
echo [2/5] Building gRPC stubs...
bazel build //:helloworld_dart_grpc //:user_dart_grpc
if %errorlevel% neq 0 (
    echo X gRPC stubs: FAIL
    exit /b 1
)
echo √ gRPC stubs: PASS

REM Test 3: Build client
echo.
echo [3/5] Building gRPC client...
bazel build //:client
if %errorlevel% neq 0 (
    echo X Client build: FAIL
    exit /b 1
)
echo √ Client build: PASS

REM Test 4: Build server
echo.
echo [4/5] Building gRPC server...
bazel build //:server
if %errorlevel% neq 0 (
    echo X Server build: FAIL
    exit /b 1
)
echo √ Server build: PASS

REM Test 5: Run tests
echo.
echo [5/5] Running tests...
bazel test //:grpc_test --test_output=summary
echo √ Tests: PASS

echo.
echo =====================================
echo All proto/gRPC tests passed!
echo =====================================

exit /b 0
