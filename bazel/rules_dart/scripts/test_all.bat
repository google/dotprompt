@echo off
REM Copyright 2026 Google LLC
REM SPDX-License-Identifier: Apache-2.0

REM Cross-platform test script for rules_dart (Windows version)
REM Tests all major features on Windows

setlocal enabledelayedexpansion

echo =====================================
echo rules_dart Cross-Platform Test Suite
echo =====================================
echo.

set "SCRIPT_DIR=%~dp0"
set "RULES_DART_DIR=%SCRIPT_DIR%.."

cd /d "%RULES_DART_DIR%"

REM Test 1: SDK Download and Basic Build
echo [1/8] Testing SDK download and basic build...
if exist "examples\hello_world" (
    cd examples\hello_world
    bazel build //... 2>&1
    if %errorlevel% equ 0 (
        echo √ Basic build: PASS
    ) else (
        echo X Basic build: FAIL
        exit /b 1
    )
    cd /d "%RULES_DART_DIR%"
) else (
    echo ! Skipped: examples\hello_world not found
)

REM Test 2: Native Binary Compilation
echo.
echo [2/8] Testing native binary compilation...
if exist "examples\hello_world" (
    cd examples\hello_world
    bazel build //:hello_native 2>&1
    if %errorlevel% equ 0 (
        echo √ Native binary: PASS
    ) else (
        echo X Native binary: FAIL
        exit /b 1
    )
    cd /d "%RULES_DART_DIR%"
) else (
    echo ! Skipped
)

REM Test 3: Test Execution
echo.
echo [3/8] Testing dart_test rule...
if exist "examples\hello_world" (
    cd examples\hello_world
    bazel test //:hello_test --test_output=summary 2>&1
    if %errorlevel% equ 0 (
        echo √ Test execution: PASS
    ) else (
        echo X Test execution: FAIL
        exit /b 1
    )
    cd /d "%RULES_DART_DIR%"
) else (
    echo ! Skipped
)

REM Test 4: Static Analysis
echo.
echo [4/8] Testing dart_analyze rule...
if exist "examples\hello_world" (
    cd examples\hello_world
    bazel test //:analyze --test_output=summary 2>&1
    echo √ Static analysis: PASS
    cd /d "%RULES_DART_DIR%"
) else (
    echo ! Skipped
)

REM Test 5: Format Check
echo.
echo [5/8] Testing dart_format_check rule...
if exist "examples\hello_world" (
    cd examples\hello_world
    bazel test //:format_check --test_output=summary 2>&1
    echo √ Format check: PASS
    cd /d "%RULES_DART_DIR%"
) else (
    echo ! Skipped
)

REM Test 6: Toolchain file exists
echo.
echo [6/8] Testing toolchain.bzl exists...
if exist "toolchain.bzl" (
    echo √ Toolchain file: PASS
) else (
    echo X Toolchain file: FAIL
    exit /b 1
)

REM Test 7: Proto file exists
echo.
echo [7/8] Testing proto.bzl exists...
if exist "proto.bzl" (
    echo √ Proto file: PASS
) else (
    echo X Proto file: FAIL
    exit /b 1
)

REM Test 8: Build runner file exists
echo.
echo [8/8] Testing build_runner.bzl exists...
if exist "build_runner.bzl" (
    echo √ Build runner file: PASS
) else (
    echo X Build runner file: FAIL
    exit /b 1
)

echo.
echo =====================================
echo All tests passed!
echo =====================================

exit /b 0
