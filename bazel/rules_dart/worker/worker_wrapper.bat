@echo off
REM Copyright 2026 Google LLC
REM SPDX-License-Identifier: Apache-2.0

REM Worker wrapper script for Windows
REM Locates the Dart SDK and runs the worker

setlocal enabledelayedexpansion

REM Find runfiles directory
set "RUNFILES=%~dp0.runfiles"
if not exist "%RUNFILES%" (
    set "RUNFILES=%~dp0..\.runfiles"
)

REM Find Dart SDK
set "DART_BIN=%RUNFILES%\_main\external\dart_sdk\bin\dart.exe"
if not exist "%DART_BIN%" (
    REM Try Bzlmod path
    set "DART_BIN=%RUNFILES%\rules_dart++dart+dart_sdk\bin\dart.exe"
)
if not exist "%DART_BIN%" (
    REM Fallback to system dart
    set "DART_BIN=dart"
)

REM Find worker script
set "WORKER_SCRIPT=%RUNFILES%\_main\bazel\rules_dart\worker\bin\worker.dart"
if not exist "%WORKER_SCRIPT%" (
    set "WORKER_SCRIPT=%RUNFILES%\rules_dart\worker\bin\worker.dart"
)

"%DART_BIN%" run "%WORKER_SCRIPT%" %*
exit /b %errorlevel%
