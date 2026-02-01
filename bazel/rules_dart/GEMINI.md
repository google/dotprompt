# rules_dart Development Guidelines

## Overview

`rules_dart` provides hermetic, cross-platform Bazel rules for building Dart applications.
The rules are designed to be fully portable and work natively on Windows, macOS, and Linux
without requiring external shell interpreters (like MSYS or Git Bash on Windows).

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              rules_dart                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │  Core Rules     │   │  Platform       │   │  Gazelle Extension      │   │
│  │  (defs.bzl)     │   │  (platforms/)   │   │  (gazelle/)             │   │
│  ├─────────────────┤   ├─────────────────┤   ├─────────────────────────┤   │
│  │ dart_library    │   │ windows.bzl     │   │ dart_language.go        │   │
│  │ dart_binary     │   │ unix.bzl        │   │ dart_resolve.go         │   │
│  │ dart_test       │   │ common.bzl      │   │ dart_generate.go        │   │
│  │ dart_native_bin │   └─────────────────┘   └─────────────────────────┘   │
│  │ dart_js_binary  │                                                       │
│  │ dart_wasm_bin   │   ┌─────────────────┐   ┌─────────────────────────┐   │
│  │ dart_aot_snap   │   │  Repository     │   │  Scripts                │   │
│  │ dart_analyze    │   │  (repositories  │   │  (scripts/)             │   │
│  │ dart_format     │   │   .bzl)         │   ├─────────────────────────┤   │
│  │ dart_doc        │   ├─────────────────┤   │ test_examples.sh        │   │
│  │ dart_pub_get    │   │ dart_sdk repo   │   │ test_examples.bat       │   │
│  │ dart_pub_publish│   │ dart_deps repo  │   │ test_all_platforms.sh   │   │
│  └─────────────────┘   └─────────────────┘   └─────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Cross-Platform Design

### Script Generation Pattern

All rules that generate executable scripts use a platform-detection pattern:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Starlark Rule Implementation                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Detect platform via constraint:                                      │
│     is_windows = ctx.target_platform_has_constraint(windows_constraint)  │
│                                                                          │
│  2. Generate platform-specific script:                                   │
│     ┌─────────────────────────┐     ┌─────────────────────────┐         │
│     │  Windows (.bat)         │     │  Unix (.sh)             │         │
│     ├─────────────────────────┤     ├─────────────────────────┤         │
│     │ @echo off               │     │ #!/bin/bash             │         │
│     │ setlocal                │     │ set -e                  │         │
│     │ set "VAR=%VALUE%"       │     │ VAR="$VALUE"            │         │
│     │ %DART_BIN% command      │     │ "$DART_BIN" command     │         │
│     │ exit /b %errorlevel%    │     │ exec "$DART_BIN" ...    │         │
│     └─────────────────────────┘     └─────────────────────────┘         │
│                                                                          │
│  3. Return DefaultInfo with executable and runfiles                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Runfiles Path Resolution

External repository files require special handling for runfiles paths:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Runfiles Path Resolution                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  File.short_path for external repos:  "../rules_dart++dart+dart_sdk/..." │
│                                                                          │
│  Actual runfiles location:            "rules_dart++dart+dart_sdk/..."    │
│                                                                          │
│  Solution: _runfiles_path() helper strips leading "../"                  │
│                                                                          │
│  def _runfiles_path(file):                                               │
│      sp = file.short_path                                                │
│      if sp.startswith("../"):                                            │
│          return sp[3:]  # Strip leading "../"                            │
│      return sp                                                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## File Organization

```
bazel/rules_dart/
├── BUILD.bazel              # Package definition
├── MODULE.bazel             # Bzlmod module definition
├── defs.bzl                 # Main rule definitions (public API)
├── extensions.bzl           # Module extensions for SDK
├── repositories.bzl         # Repository rule for Dart SDK
├── GEMINI.md                # Development guidelines (this file)
├── README.md                # User documentation
├── private/                 # Internal implementation (not public API)
│   ├── BUILD.bazel          # Package definition
│   ├── helpers.bzl          # Common utility functions
│   ├── windows.bzl          # Windows script generators
│   └── unix.bzl             # Unix script generators
├── gazelle/                 # Gazelle extension for Dart
│   ├── BUILD.bazel
│   ├── go.mod
│   ├── dart_language.go     # Language implementation
│   ├── dart_generate.go     # BUILD file generation
│   └── dart_resolve.go      # Dependency resolution
├── scripts/                 # CI/testing scripts
│   ├── test_examples.sh     # Unix test script
│   └── test_examples.bat    # Windows test script (REQUIRED)
└── examples/                # Example projects
    └── hello_world/
        ├── BUILD.bazel
        ├── MODULE.bazel
        └── ...
```

### Module Structure

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Modular Architecture                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  defs.bzl (Public API)                                                   │
│  ├── Uses: private/helpers.bzl                                          │
│  │         private/windows.bzl                                          │
│  │         private/unix.bzl                                             │
│  │                                                                       │
│  └── Exports: dart_library, dart_binary, dart_test, etc.                │
│                                                                          │
│  private/helpers.bzl                                                     │
│  └── runfiles_path(), is_windows(), relative_path(), to_windows_path()  │
│                                                                          │
│  private/windows.bzl                                                     │
│  └── generate_*_script() functions for .bat files                       │
│                                                                          │
│  private/unix.bzl                                                        │
│  └── generate_*_script() functions for .sh files                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```


## Development Principles

### 1. No Hardcoding

- **SDK Paths**: Use `_runfiles_path()` helper, never hardcode paths like `dart_sdk/dart`
- **Path Separators**: Use `replace("/", "\\")` for Windows paths
- **Script Extensions**: Dynamically determine `.bat` vs `.sh` based on platform

### 2. Independence

- `rules_dart` must not depend on any code outside its directory
- All imports must be relative to the rules_dart module
- No references to parent repository structure

### 3. Cross-Platform Testing

Test every rule on all platforms:
- `test_examples.sh` for Unix (Linux, macOS)
- `test_examples.bat` for Windows

### 4. Bzlmod-First

- Use `Label()` for all external references to ensure Bzlmod compatibility
- Handle the `rules_dart++dart+dart_sdk` naming convention
- Support both Bzlmod and legacy WORKSPACE loading

## Rule Implementation Pattern

Every rule follows this standard pattern:

```python
def _my_rule_impl(ctx):
    """Implementation for my_rule."""
    # 1. Platform detection
    is_windows = ctx.target_platform_has_constraint(
        ctx.attr._windows_constraint[platform_common.ConstraintValueInfo]
    )
    
    # 2. Declare output file with correct extension
    script_ext = ".bat" if is_windows else ".sh"
    runner_script = ctx.actions.declare_file(ctx.label.name + script_ext)
    
    # 3. Get Dart SDK path (handles external repo paths)
    dart_bin = ctx.executable.dart_sdk
    dart_path = _runfiles_path(dart_bin)
    
    # 4. Generate platform-specific content
    if is_windows:
        content = """@echo off
setlocal
set "DART_BIN=%RUNFILES%\\{dart_path}"
... Windows-specific logic ...
""".format(dart_path = dart_path.replace("/", "\\"))
    else:
        content = """#!/bin/bash
set -e
DART_BIN="$RUNFILES/{dart_path}"
... Unix-specific logic ...
""".format(dart_path = dart_path)
    
    # 5. Write script and set up runfiles
    ctx.actions.write(runner_script, content, is_executable = True)
    runfiles = ctx.runfiles(files = [dart_bin] + ctx.files.srcs)
    
    return [DefaultInfo(executable = runner_script, runfiles = runfiles)]

# 6. Rule definition with standard attributes
_my_rule = rule(
    implementation = _my_rule_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "dart_sdk": attr.label(
            default = Label("@dart_sdk//:dart_bin"),
            executable = True,
            cfg = "exec",
            allow_single_file = True,
        ),
        "_windows_constraint": attr.label(
            default = Label("@platforms//os:windows"),
        ),
    },
    executable = True,  # or test = True for test rules
)

# 7. Public macro wrapping the rule
def my_rule(name, srcs = [], visibility = None, **kwargs):
    """User-facing macro with documentation."""
    _my_rule(
        name = name,
        srcs = srcs,
        visibility = visibility,
        **kwargs
    )
```

## Testing Guidelines

### Required Test Coverage

Every rule must be tested:
1. **Build test**: Verify the rule can be built
2. **Execution test**: Verify the output works correctly
3. **Cross-platform test**: Verify behavior on Windows, macOS, Linux

### Test Script Requirements

```bash
# scripts/test_examples.sh - Unix
#!/bin/bash
set -euo pipefail

bazel build //examples/hello_world:all
bazel test //examples/hello_world:hello_test
bazel run //examples/hello_world:hello_native
```

```batch
:: scripts/test_examples.bat - Windows
@echo off
setlocal enabledelayedexpansion

bazel build //examples/hello_world:all
if %errorlevel% neq 0 exit /b %errorlevel%

bazel test //examples/hello_world:hello_test
if %errorlevel% neq 0 exit /b %errorlevel%
```

## Gazelle Integration

The Gazelle extension generates BUILD files from pubspec.yaml:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Gazelle BUILD Generation                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Input: pubspec.yaml                                                     │
│  ┌─────────────────────────────┐                                         │
│  │ name: my_package            │                                         │
│  │ dependencies:               │                                         │
│  │   path: ^1.8.0              │                                         │
│  │ dev_dependencies:           │                                         │
│  │   test: ^1.21.0             │                                         │
│  └─────────────────────────────┘                                         │
│                                                                          │
│  Output: BUILD.bazel                                                     │
│  ┌─────────────────────────────┐                                         │
│  │ dart_library(              │                                         │
│  │   name = "my_package",     │                                         │
│  │   srcs = glob(["lib/**"]), │                                         │
│  │   pubspec = "pubspec.yaml",│                                         │
│  │ )                          │                                         │
│  │                            │                                         │
│  │ dart_test(                 │                                         │
│  │   name = "test",           │                                         │
│  │   srcs = glob(["test/**"]),│                                         │
│  │   deps = [":my_package"],  │                                         │
│  │ )                          │                                         │
│  └─────────────────────────────┘                                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Feature Parity Matrix

Update the README with this table:

| Feature | Windows | macOS | Linux | Notes |
|---------|---------|-------|-------|-------|
| dart_library | ✅ | ✅ | ✅ | Filegroup wrapper |
| dart_binary | ✅ | ✅ | ✅ | VM execution |
| dart_test | ✅ | ✅ | ✅ | With pub get |
| dart_native_binary | ✅ | ✅ | ✅ | Compiled executable |
| dart_js_binary | ✅ | ✅ | ✅ | JavaScript output |
| dart_wasm_binary | ✅ | ✅ | ✅ | WebAssembly (Preview) |
| dart_aot_snapshot | ✅ | ✅ | ✅ | AOT compilation |
| dart_analyze | ✅ | ✅ | ✅ | Static analysis |
| dart_format_check | ✅ | ✅ | ✅ | Format validation |
| dart_doc | ✅ | ✅ | ✅ | Documentation |
| dart_pub_get | ✅ | ✅ | ✅ | Dependency fetch |
| dart_pub_publish | ✅ | ✅ | ✅ | Package publish |
| Gazelle extension | ✅ | ✅ | ✅ | BUILD generation |

## Common Pitfalls

### 1. Batch Script Exit Codes

Windows batch scripts require explicit exit code handling:

```batch
:: BAD - loses exit code
%DART_BIN% command
exit /b 0

:: GOOD - preserves exit code
%DART_BIN% command
set "RESULT=%errorlevel%"
exit /b %RESULT%
```

### 2. Path Separators

Always transform paths for Windows:

```python
# BAD
pkg_dir = "some/path"
content = f"cd {pkg_dir}"  # Fails on Windows

# GOOD  
if is_windows:
    content = f"cd {pkg_dir.replace('/', '\\')}"
```

### 3. Test Rule Naming

Bazel requires test rules to end with `_test`:

```python
# BAD - will fail validation
_dart_analyze_rule = rule(..., test = True)

# GOOD
_dart_analyze_test = rule(..., test = True)
```

### 4. Built-in Attribute Names

Cannot use built-in names like `args`:

```python
# BAD - conflicts with built-in
attrs = { "args": attr.string_list() }

# GOOD
attrs = { "tool_args": attr.string_list() }
```

## Future Improvements

1. **Platform Modules**: Extract platform-specific code to `platforms/windows.bzl` and `platforms/unix.bzl`
2. **Shared Helpers**: Create `private/helpers.bzl` for common utilities
3. **Streaming Compilation**: Support incremental compilation for large projects
4. **Remote Execution**: Optimize for Bazel remote execution (RBE)
5. **Pub Cache Caching**: Implement Bazel-native pub cache for faster builds

## Release Checklist

Before releasing a new version:

- [ ] All tests pass on Windows, macOS, and Linux
- [ ] README.md is up to date
- [ ] CHANGELOG.md has release notes
- [ ] Feature parity matrix is accurate
- [ ] Examples work with both Bzlmod and WORKSPACE
- [ ] Gazelle extension is tested
- [ ] No hardcoded paths remain
- [ ] License headers on all files

## Test Script Requirements

**IMPORTANT**: Every test script must have both Unix (.sh) and Windows (.bat) versions.

```
scripts/
├── test_examples.sh    # Unix test script
└── test_examples.bat   # Windows test script (REQUIRED)
```

### Test Script Parity

Both scripts must test the same functionality:

| Step | Description | Unix | Windows |
|------|-------------|------|---------|
| 1 | Clean build | `bazel clean --expunge` | `bazel clean --expunge` |
| 2 | Build all targets | `bazel build //...` | `bazel build //...` |
| 3 | Test compilation | All compile rules | All compile rules |
| 4 | Test pub commands | pub_get, pub_publish | pub_get, pub_publish |
| 5 | Run unit tests | `bazel test //:test` | `bazel test //:test` |
| 6 | Run CI checks | analyze, format | analyze, format |
| 7 | Execute binary | `bazel run //:app` | `bazel run //:app` |

## PR Description Guidelines

PR descriptions should include:

1. **Tables** for feature support and test results
2. **ASCII diagrams** for architecture changes
3. **Clear titles** following conventional commits

### Example PR Description

```markdown
## Summary

Adds 100% Windows compatibility to rules_dart.

## Changes

| Rule | Before | After |
|------|--------|-------|
| dart_test | ❌ Windows | ✅ Windows |
| dart_analyze | ❌ Windows | ✅ Windows |
| dart_format_check | ❌ Windows | ✅ Windows |

## Architecture

┌─────────────────────────────────────────────┐
│           Cross-Platform Runner             │
├─────────────────────────────────────────────┤
│  is_windows? ─┬─▶ .bat script               │
│               └─▶ .sh script                │
└─────────────────────────────────────────────┘

## Test Results

| Platform | Build | Tests |
|----------|-------|-------|
| macOS arm64 | ✅ | ✅ 17/17 |
| Linux x64 | ✅ | ✅ 17/17 |
| Windows x64 | ✅ | ✅ 17/17 |
```

## BCR (Bazel Central Registry) Readiness

Before publishing to BCR:

### Required Files

```
rules_dart/
├── MODULE.bazel         # Bzlmod definition
├── BUILD.bazel          # Package definition
├── defs.bzl            # Public API
├── extensions.bzl       # Module extensions
├── repositories.bzl     # Repository rules
├── README.md           # Documentation
└── LICENSE             # Apache 2.0
```

### BCR Metadata

Create `.bcr/` directory with:

```
.bcr/
├── metadata.json       # Version, maintainers
├── presubmit.yml       # CI configuration
└── source.json         # Source archive location
```

### Checklist

- [ ] Module name follows `rules_<language>` convention
- [ ] Version follows semantic versioning (X.Y.Z)
- [ ] All dependencies are available in BCR
- [ ] No references to parent repository
- [ ] Works as standalone module
- [ ] Tests pass in isolated environment
- [ ] Documentation is complete
- [ ] Examples work out of the box

## Independence Requirements

`rules_dart` must be completely independent:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Independence Boundary                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  rules_dart/                                                             │
│  ├── Cannot import from:                                                 │
│  │   • //bazel/dart/...    (dotprompt-specific)                         │
│  │   • //dart/...          (dotprompt packages)                          │
│  │   • Any parent path                                                   │
│  │                                                                       │
│  ├── Can only depend on:                                                 │
│  │   • @platforms//...                                                   │
│  │   • @rules_go//... (for Gazelle)                                     │
│  │   • @gazelle//...                                                     │
│  │                                                                       │
│  └── Must use Label() for:                                               │
│      • All external references                                           │
│      • Ensures Bzlmod resolution                                         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Verification

Run this command to verify no external dependencies:

```bash
# Check for imports outside rules_dart
grep -r "//bazel/" bazel/rules_dart/ || echo "OK: No bazel/ imports"
grep -r "//dart/" bazel/rules_dart/ || echo "OK: No dart/ imports"
```

## Configuration Flags

Expose these settings in `.bazelrc` for users:

```bash
# .bazelrc - Recommended Dart settings

# Dart SDK version
build --@rules_dart//config:dart_version=3.7.0

# Enable null safety (default: true)
build --@rules_dart//config:null_safety=true

# Optimization level for native compilation
build --@rules_dart//config:opt_level=O2

# Enable verbose pub output
build --@rules_dart//config:pub_verbose=false
```

### dotprompt Usage Pattern

For dotprompt and similar monorepos, use `dart.MODULE.bazel`:

```python
# dart.MODULE.bazel - Dart-specific module configuration
bazel_dep(name = "rules_dart", version = "0.1.0")

dart = use_extension("@rules_dart//:extensions.bzl", "dart")
dart.configure(
    version = "3.7.0",
    # Additional Dart-specific configuration
)
use_repo(dart, "dart_sdk")
```

Then include in main `MODULE.bazel`:

```python
# MODULE.bazel
include("//dart.MODULE.bazel")
```

