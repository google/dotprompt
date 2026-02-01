# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Windows script generation for rules_dart.

This module provides functions to generate Windows Batch (.bat) scripts
for Dart compilation and execution. All scripts are designed to run in
standard cmd.exe without requiring MSYS, Git Bash, or Cygwin.

Script Structure:
┌──────────────────────────────────────────────────────────────────────────┐
│                    Windows Batch Script Pattern                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  @echo off                           # Disable command echo              │
│  setlocal enabledelayedexpansion     # Enable delayed var expansion      │
│                                                                          │
│  set "RUNFILES=%~dp0.runfiles"       # Locate runfiles directory         │
│  set "DART_BIN=%RUNFILES%\\path"     # Set Dart SDK path                 │
│                                                                          │
│  if not exist "%DART_BIN%" (         # Validate SDK exists               │
│      echo ERROR: ...                                                     │
│      exit /b 1                                                           │
│  )                                                                       │
│                                                                          │
│  %DART_BIN% compile exe ...          # Execute Dart command              │
│  set "RESULT=%errorlevel%"           # Capture exit code                 │
│  exit /b %RESULT%                    # Preserve exit code                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Key Patterns:
- Always use `setlocal` to avoid polluting environment
- Use `%~dp0` for script directory (trailing backslash included)
- Capture `%errorlevel%` before any other command
- Use `exit /b` (not `exit`) to preserve parent shell
"""

load("@rules_dart//private:helpers.bzl", "to_windows_path")  # runfiles_path available if needed

def generate_binary_script(dart_path, main_path):
    """Generate a Windows script to run a Dart binary.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        main_path: Path to main Dart file

    Returns:
        String content of the batch script
    """
    return """@echo off
setlocal
if defined BUILD_WORKSPACE_DIRECTORY (
    cd /d "%BUILD_WORKSPACE_DIRECTORY%"
)

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
)

"%DART_BIN%" run {main} %*
""".format(
        dart_path = to_windows_path(dart_path),
        main = to_windows_path(main_path),
    )

def generate_test_script(dart_path, pkg_dir, test_file):
    """Generate a Windows script to run Dart tests.

    Creates a hermetic test environment by copying the workspace
    to a temporary directory and running pub get before tests.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        test_file: Path to test file (relative to package)

    Returns:
        String content of the batch script
    """
    return """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    echo ERROR: Dart SDK not found at %DART_BIN%
    exit /b 1
)

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
set "TEMP_DIR=%TEMP%\\dart_test_%RANDOM%"
mkdir "%TEMP_DIR%"

set "HOME=%TEMP_DIR%"
set "PUB_CACHE=%TEMP_DIR%\\.pub-cache"
mkdir "%PUB_CACHE%"

xcopy "%WORKSPACE_ROOT%" "%TEMP_DIR%" /E /I /Q >nul
cd /d "%TEMP_DIR%\\{pkg_dir}"

call "%DART_BIN%" pub get --offline 2>nul || call "%DART_BIN%" pub get
"%DART_BIN%" test {main}
set "RESULT=%errorlevel%"

cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" 2>nul
exit /b %RESULT%
""".format(
        dart_path = to_windows_path(dart_path),
        pkg_dir = to_windows_path(pkg_dir),
        main = to_windows_path(test_file),
    )

def generate_format_check_script(dart_path, pkg_dir):
    """Generate a Windows script to check Dart formatting.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path

    Returns:
        String content of the batch script
    """
    return """@echo off
setlocal

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    echo ERROR: Dart SDK not found at %DART_BIN%
    exit /b 1
)

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
cd /d "%WORKSPACE_ROOT%\\{pkg_dir}"

"%DART_BIN%" format --set-exit-if-changed --output=none lib\\ test\\ 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Code is not properly formatted. Run 'dart format .' to fix.
    exit /b 1
)
""".format(
        dart_path = to_windows_path(dart_path),
        pkg_dir = to_windows_path(pkg_dir),
    )

def generate_analyze_script(dart_path, pkg_dir):
    """Generate a Windows script to run Dart static analysis.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path

    Returns:
        String content of the batch script
    """
    return """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    echo ERROR: Dart SDK not found at %DART_BIN%
    exit /b 1
)

set "TEMP_DIR=%TEMP%\\dart_analyze_%RANDOM%"
mkdir "%TEMP_DIR%"

set "HOME=%TEMP_DIR%"
set "PUB_CACHE=%TEMP_DIR%\\.pub-cache"
mkdir "%PUB_CACHE%"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
xcopy "%WORKSPACE_ROOT%" "%TEMP_DIR%" /E /I /Q >nul
cd /d "%TEMP_DIR%\\{pkg_dir}"

call "%DART_BIN%" pub get --offline 2>nul || call "%DART_BIN%" pub get
"%DART_BIN%" analyze --fatal-infos --fatal-warnings
set "RESULT=%errorlevel%"

cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" 2>nul
exit /b %RESULT%
""".format(
        dart_path = to_windows_path(dart_path),
        pkg_dir = to_windows_path(pkg_dir),
    )

def generate_doc_script(dart_path, pkg_dir, out_dir):
    """Generate a Windows script to build Dart documentation.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        out_dir: Output directory for generated docs

    Returns:
        String content of the batch script
    """
    return """@echo off
setlocal

cd /d "%BUILD_WORKSPACE_DIRECTORY%\\{pkg_dir}"

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
)

call "%DART_BIN%" pub get
"%DART_BIN%" doc --output={out_dir}
echo Documentation generated at {pkg_dir}\\{out_dir}
""".format(
        dart_path = to_windows_path(dart_path),
        pkg_dir = to_windows_path(pkg_dir),
        out_dir = to_windows_path(out_dir),
    )

def generate_tool_script(dart_path, pkg_dir, command, args_str):
    """Generate a Windows script to run a Dart tool command.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        command: Dart command to run (e.g., "pub", "compile")
        args_str: Additional arguments as a string

    Returns:
        String content of the batch script
    """
    return """@echo off
setlocal
cd /d "%BUILD_WORKSPACE_DIRECTORY%\\{pkg_dir}"

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    set "DART_BIN=dart"
    echo Warning: Hermetic Dart SDK not found, falling back to system dart
)

echo Executing: %DART_BIN% {command} {args} %*
"%DART_BIN%" {command} {args} %*
""".format(
        dart_path = to_windows_path(dart_path),
        pkg_dir = to_windows_path(pkg_dir),
        command = command,
        args = args_str,
    )

def generate_compile_script(dart_path, pkg_dir, main_path, _output_path, compile_cmd, extra_args = ""):
    """Generate a Windows script for Dart compilation.

    Args:
        dart_path: Runfiles path to Dart SDK binary
        pkg_dir: Package directory path
        main_path: Path to main Dart file
        _output_path: Path for compiled output (managed internally)
        compile_cmd: Compile target (exe, js, wasm, aot-snapshot)
        extra_args: Additional compile arguments

    Returns:
        String content of the batch script
    """
    return """@echo off
setlocal enabledelayedexpansion

set "RUNFILES=%~dp0.runfiles"
set "DART_BIN=%RUNFILES%\\{dart_path}"

if not exist "%DART_BIN%" (
    echo ERROR: Dart SDK not found at %DART_BIN%
    exit /b 1
)

set "TEMP_DIR=%TEMP%\\dart_compile_%RANDOM%"
mkdir "%TEMP_DIR%"

set "HOME=%TEMP_DIR%"
set "PUB_CACHE=%TEMP_DIR%\\.pub-cache"
mkdir "%PUB_CACHE%"

set "WORKSPACE_ROOT=%RUNFILES%\\_main"
xcopy "%WORKSPACE_ROOT%" "%TEMP_DIR%" /E /I /Q >nul
cd /d "%TEMP_DIR%\\{pkg_dir}"

call "%DART_BIN%" pub get --offline 2>nul || call "%DART_BIN%" pub get

echo Compiling to {compile_cmd}...
"%DART_BIN%" compile {compile_cmd} {extra_args} -o "%TEMP_DIR%\\output" {main}
set "RESULT=%errorlevel%"

if %RESULT% equ 0 (
    copy "%TEMP_DIR%\\output*" "%BUILD_WORKING_DIRECTORY%\\" >nul
)

cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" 2>nul
exit /b %RESULT%
""".format(
        dart_path = to_windows_path(dart_path),
        pkg_dir = to_windows_path(pkg_dir),
        main = to_windows_path(main_path),
        compile_cmd = compile_cmd,
        extra_args = extra_args,
    )
