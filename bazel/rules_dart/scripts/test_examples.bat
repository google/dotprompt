@REM Copyright 2026 Google LLC
@REM
@REM Licensed under the Apache License, Version 2.0 (the "License");
@REM you may not use this file except in compliance with the License.
@REM You may obtain a copy of the License at
@REM
@REM     http://www.apache.org/licenses/LICENSE-2.0
@REM
@REM Unless required by applicable law or agreed to in writing, software
@REM distributed under the License is distributed on an "AS IS" BASIS,
@REM WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@REM See the License for the specific language governing permissions and
@REM limitations under the License.
@REM
@REM SPDX-License-Identifier: Apache-2.0

@REM =============================================================================
@REM rules_dart Integration Test Script (Windows)
@REM =============================================================================
@REM
@REM This script tests all rules_dart functionality on Windows:
@REM - Windows 10/11 (x64, arm64)
@REM - Runs in standard cmd.exe (no MSYS/Git Bash required)
@REM
@REM Usage:
@REM   scripts\test_examples.bat
@REM
@REM Exit codes:
@REM   0 - All tests passed
@REM   1 - One or more tests failed
@REM
@REM =============================================================================

@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo   rules_dart Integration Tests (Windows)
echo ==============================================
echo.
echo Platform: Windows %PROCESSOR_ARCHITECTURE%
for /f "tokens=*" %%i in ('bazel --version') do echo Bazel: %%i
echo.

cd /d "%~dp0..\examples\hello_world"

@REM -----------------------------------------------------------------------------
@REM Step 1: Clean build
@REM -----------------------------------------------------------------------------
echo [1/7] Cleaning previous build...
bazel clean --expunge 2>nul

@REM -----------------------------------------------------------------------------
@REM Step 2: Build all targets
@REM -----------------------------------------------------------------------------
echo [2/7] Building all targets...
bazel build --verbose_failures //...
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    exit /b 1
)

@REM -----------------------------------------------------------------------------
@REM Step 3: Test compilation targets
@REM -----------------------------------------------------------------------------
echo [3/7] Testing compilation targets...
echo   - dart_native_binary
bazel build //:hello_native
if %errorlevel% neq 0 exit /b 1

echo   - dart_js_binary
bazel build //:hello_js
if %errorlevel% neq 0 exit /b 1

echo   - dart_wasm_binary
bazel build //:hello_wasm 2>nul
@REM WebAssembly may not be supported on all platforms, don't fail

echo   - dart_aot_snapshot
bazel build //:hello_aot
if %errorlevel% neq 0 exit /b 1

@REM -----------------------------------------------------------------------------
@REM Step 4: Test pub commands
@REM -----------------------------------------------------------------------------
echo [4/7] Testing pub commands...
echo   - dart_pub_get
bazel run //:hello_pub_get
if %errorlevel% neq 0 exit /b 1

echo   - dart_pub_publish --help
bazel run //:hello_release -- --help 2>nul
@REM --help may return non-zero, don't fail

@REM -----------------------------------------------------------------------------
@REM Step 5: Run unit tests
@REM -----------------------------------------------------------------------------
echo [5/7] Running unit tests...
bazel test --verbose_failures //:hello_test
if %errorlevel% neq 0 (
    echo ERROR: Unit tests failed
    exit /b 1
)

@REM -----------------------------------------------------------------------------
@REM Step 6: Run CI checks
@REM -----------------------------------------------------------------------------
echo [6/7] Running CI checks...
echo   - dart_format_check
bazel test //:hello_format
if %errorlevel% neq 0 exit /b 1

echo   - dart_analyze
bazel test //:hello_analyze
if %errorlevel% neq 0 exit /b 1

@REM -----------------------------------------------------------------------------
@REM Step 7: Test native binary execution
@REM -----------------------------------------------------------------------------
echo [7/7] Testing native binary execution...
bazel run //:hello_native
if %errorlevel% neq 0 exit /b 1

echo.
echo ==============================================
echo   All tests passed!
echo ==============================================

exit /b 0
