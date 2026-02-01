# Bazel Rules for Dart

Hermetic, cross-platform Bazel rules for building and testing Dart applications.
Designed for the [Bazel Central Registry (BCR)](https://registry.bazel.build/).

## Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           rules_dart Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │   Compilation      │  │   Development      │  │   Publishing       │   │
│  ├────────────────────┤  ├────────────────────┤  ├────────────────────┤   │
│  │ dart_native_binary │  │ dart_binary        │  │ dart_pub_get       │   │
│  │ dart_js_binary     │  │ dart_test          │  │ dart_pub_publish   │   │
│  │ dart_wasm_binary   │  │ dart_analyze       │  │                    │   │
│  │ dart_aot_snapshot  │  │ dart_format_check  │  │                    │   │
│  │                    │  │ dart_doc           │  │                    │   │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    Hermetic Dart SDK                                │   │
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │  • Auto-downloaded for Windows/macOS/Linux (x64/arm64)             │   │
│  │  • Local SDK override via DART_HOME environment variable           │   │
│  │  • FreeBSD support through local toolchain                         │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Platform Support Matrix

| Feature | Windows | macOS | Linux | Notes |
|---------|:-------:|:-----:|:-----:|-------|
| dart_library | ✅ | ✅ | ✅ | Filegroup wrapper |
| dart_binary | ✅ | ✅ | ✅ | VM execution |
| dart_test | ✅ | ✅ | ✅ | Hermetic test runner |
| dart_native_binary | ✅ | ✅ | ✅ | `.exe` on Windows |
| dart_js_binary | ✅ | ✅ | ✅ | JavaScript output |
| dart_wasm_binary | ✅ | ✅ | ✅ | WebAssembly (Preview) |
| dart_aot_snapshot | ✅ | ✅ | ✅ | AOT compilation |
| dart_analyze | ✅ | ✅ | ✅ | Static analysis |
| dart_format_check | ✅ | ✅ | ✅ | Format validation |
| dart_doc | ✅ | ✅ | ✅ | Documentation gen |
| dart_pub_get | ✅ | ✅ | ✅ | Dependency fetch |
| dart_pub_publish | ✅ | ✅ | ✅ | Package publish |
| dart_proto_library | ✅ | ✅ | ✅ | Proto codegen |
| dart_grpc_library | ✅ | ✅ | ✅ | gRPC codegen |
| dart_build_runner | ✅ | ✅ | ✅ | freezed/json_serializable |
| Coverage | ✅ | ✅ | ✅ | LCOV output |
| Persistent Workers | ✅ | ✅ | ✅ | JSON protocol |
| Toolchain | ✅ | ✅ | ✅ | Multi-version SDK |
| Version Conflict Detection | ✅ | ✅ | ✅ | Cross-module |
| Remote Execution (RBE) | ✅ | ✅ | ✅ | rbe.bazelrc |
| IDE Aspects | ✅ | ✅ | ✅ | IntelliJ/VSCode |
| Gazelle extension | ✅ | ✅ | ✅ | BUILD generation |

**Windows**: Native Batch (`.bat`) scripts - no MSYS/Git Bash required.

## Quick Start

### 1. Add to MODULE.bazel

```python
bazel_dep(name = "rules_dart", version = "0.1.0")

dart = use_extension("@rules_dart//:extensions.bzl", "dart")
dart.configure(version = "3.7.0")
use_repo(dart, "dart_sdk")
```

### 2. Create BUILD.bazel

```python
load("@rules_dart//:defs.bzl", "dart_library", "dart_native_binary", "dart_test")

dart_library(
    name = "mylib",
    srcs = glob(["lib/**/*.dart"]),
    pubspec = "pubspec.yaml",
)

dart_native_binary(
    name = "app",
    main = "bin/main.dart",
    deps = [":mylib"],
)

dart_test(
    name = "test",
    main = "test/mylib_test.dart",
    deps = [":mylib"],
)
```

### 3. Build and Run

```bash
# Build native executable
bazel build //:app

# Run tests
bazel test //:test

# Run the app
bazel run //:app
```

## Rules Reference

### dart_library

Creates a Dart library target (filegroup wrapper).

```python
dart_library(
    name = "mylib",
    srcs = glob(["lib/**/*.dart"]),
    deps = ["//other:lib"],
    pubspec = "pubspec.yaml",
)
```

### dart_binary

Runs Dart code using the VM (for development).

```python
dart_binary(
    name = "dev_server",
    main = "bin/server.dart",
    deps = [":mylib"],
)
```

### dart_native_binary

Compiles Dart to a native executable using `dart compile exe`.

```python
dart_native_binary(
    name = "app",
    main = "bin/main.dart",
    deps = [":mylib"],
)
```

**Output**: `app.exe` (Windows) or `app` (Unix)

### dart_js_binary

Compiles Dart to JavaScript using `dart compile js`.

```python
dart_js_binary(
    name = "web_app",
    main = "web/main.dart",
    deps = [":mylib"],
)
```

**Output**: `web_app.js`

### dart_wasm_binary

Compiles Dart to WebAssembly using `dart compile wasm`.

```python
dart_wasm_binary(
    name = "wasm_app",
    main = "lib/main.dart",
    deps = [":mylib"],
)
```

**Output**: `wasm_app.wasm`, `wasm_app.mjs`

> **Note**: WebAssembly compilation is a preview feature.

### dart_aot_snapshot

Creates an AOT snapshot using `dart compile aot-snapshot`.

```python
dart_aot_snapshot(
    name = "app_aot",
    main = "bin/main.dart",
    deps = [":mylib"],
)
```

**Output**: `app_aot.aot`

### dart_test

Runs Dart tests using `dart test`.

```python
dart_test(
    name = "unit_tests",
    main = "test/mylib_test.dart",
    deps = [":mylib"],
)
```

### dart_analyze

Runs static analysis with `dart analyze --fatal-infos --fatal-warnings`.

```python
dart_analyze(
    name = "analyze",
    srcs = glob(["lib/**/*.dart", "test/**/*.dart"]),
)
```

### dart_format_check

Validates code formatting (fails if not formatted).

```python
dart_format_check(
    name = "format_check",
    srcs = glob(["lib/**/*.dart", "test/**/*.dart"]),
)
```

### dart_doc

Generates API documentation using `dart doc`.

```python
dart_doc(
    name = "docs",
    srcs = glob(["lib/**/*.dart"]),
)
```

### dart_pub_get

Runs `dart pub get` to fetch dependencies.

```python
dart_pub_get(name = "pub_get")
```

### dart_pub_publish

Runs `dart pub publish` to publish to pub.dev.

```python
dart_pub_publish(name = "publish")
```

## Code Generation

### dart_proto_library

Generates Dart code from `.proto` files.

```python
load("@rules_dart//:proto.bzl", "dart_proto_library")

proto_library(
    name = "user_proto",
    srcs = ["user.proto"],
)

dart_proto_library(
    name = "user_dart_proto",
    deps = [":user_proto"],
)
```

**Output**: `user.pb.dart`, `user.pbenum.dart`, `user.pbjson.dart`

### dart_grpc_library

Generates Dart gRPC service stubs from `.proto` files.

```python
load("@rules_dart//:proto.bzl", "dart_grpc_library")

dart_grpc_library(
    name = "user_dart_grpc",
    deps = [":user_proto"],
)
```

**Output**: `user.pbgrpc.dart` (service stubs)

### dart_build_runner

Runs Dart `build_runner` for code generation (freezed, json_serializable, etc.).

```python
load("@rules_dart//:build_runner.bzl", "dart_build_runner")

dart_build_runner(
    name = "generated",
    srcs = glob(["lib/**/*.dart"]),
)

dart_library(
    name = "models",
    srcs = glob(["lib/**/*.dart"]) + [":generated"],
)
```

## Toolchain

### Using the Toolchain

The Dart toolchain provides proper abstraction for multi-version support:

```python
load("@rules_dart//:toolchain.bzl", "dart_toolchain", "DartToolchainInfo")

# Access toolchain in a rule
def _my_rule_impl(ctx):
    tc = ctx.toolchains["@rules_dart//:toolchain_type"].dart
    dart_bin = tc.dart_bin
    version = tc.version
```

### Multiple SDK Versions

```python
# MODULE.bazel
dart = use_extension("@rules_dart//:extensions.bzl", "dart")
dart.toolchain(version = "3.7.0", name = "dart_3_7")
dart.toolchain(version = "3.6.0", name = "dart_3_6")
```

## Coverage

### Running Tests with Coverage

```bash
# Run with coverage collection
bazel coverage //my:test

# Output: bazel-out/.../coverage.dat (LCOV format)
```

### Generating HTML Report

```bash
# After running coverage
genhtml bazel-out/.../coverage.dat -o coverage_report/
open coverage_report/index.html
```

## Remote Build Execution (RBE)

### Configuration

Include the RBE configuration in your `.bazelrc`:

```bash
try-import %workspace%/bazel/rules_dart/rbe.bazelrc
```

### Running with Remote Cache

```bash
# Read-only cache
bazel build --config=remote-cache //...

# Read-write cache
bazel build --config=remote-cache-rw //...
```

### Full Remote Execution

```bash
# Run builds on remote workers
bazel build --config=remote //...
```

### Supported RBE Providers

- **BuildBuddy**: `--config=buildbuddy`
- **Google Cloud Build**: `--config=google`

## IDE Integration

### Generating IDE Metadata

```bash
# Generate IDE info for all Dart targets
bazel build //... --aspects=@rules_dart//:aspects.bzl%dart_ide_info \
    --output_groups=dart_ide_info
```

### Output

Each target generates a `.dart-info.json` file:

```json
{
  "label": "//my:lib",
  "kind": "dart_library",
  "package_root": "my",
  "sources": ["lib/main.dart"],
  "dependencies": [],
  "is_test": false
}
```

### IDE-specific Settings

```python
# Use in custom rules to generate IDE settings
load("@rules_dart//:aspects.bzl", "generate_vscode_settings", "generate_intellij_facet")
```

## Version Conflict Detection

When multiple modules depend on the same package with different versions, 
`rules_dart` automatically detects and reports the conflict:

```
======================================================================
VERSION CONFLICT DETECTED
======================================================================

Package 'http':
  - Module 'foo' requires version 1.0.0 (from //:pubspec.lock)
  - Module 'bar' requires version 2.0.0 (from //sub:pubspec.lock)

Resolution:
  1. Pin a single version in your root pubspec.yaml
  2. Run 'dart pub get' to update pubspec.lock
  3. Ensure all modules use compatible versions

======================================================================
```

## Advanced Configuration

### Local Dart SDK

For custom Dart installations or unsupported platforms (e.g., FreeBSD):

**Option 1: Environment Variable**
```bash
export DART_HOME=/usr/local/lib/dart
bazel build //...
```

**Option 2: MODULE.bazel**
```python
dart.configure(
    sdk_home = "/usr/local/lib/dart",
)
```

### Disabling Analytics

By default, Dart analytics are disabled for hermetic builds. You can control this:

```python
dart.configure(
    version = "3.7.0",
    disable_analytics = True,   # Default: analytics disabled
)
```

To enable analytics (not recommended for CI/hermetic builds):

```python
dart.configure(
    version = "3.7.0",
    disable_analytics = False,
)
```

**Note**: Disabling analytics creates `disable_analytics.sh` and `disable_analytics.bat` 
scripts in the SDK repository that you can run to permanently disable analytics.

### Gazelle Integration

Generate BUILD files from `pubspec.yaml`:

```python
# MODULE.bazel
dart_deps = use_extension("@rules_dart//:extensions.bzl", "dart_deps")
dart_deps.from_file(lock_file = "//:pubspec.lock")
use_repo(dart_deps, "dart_deps_path", "dart_deps_yaml", ...)
```

```bash
# Generate/update BUILD files
bazel run //:gazelle
```

### .bazelrc Configuration

Recommended settings for Dart projects:

```bash
# .bazelrc

# Enable Bzlmod (Bazel 7+)
common --enable_bzlmod

# Dart SDK version (can be overridden)
build --@rules_dart//config:dart_version=3.7.0

# Increase test timeout for large projects
test --test_timeout=300

# Enable verbose test output
test --test_output=errors
```

## Cross-Platform Script Generation

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     How Cross-Platform Works                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Platform Detection (at analysis time):                               │
│     ┌─────────────────────────────────────────────────────────────────┐ │
│     │ is_windows = ctx.target_platform_has_constraint(windows)        │ │
│     └─────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  2. Script Generation:                                                   │
│     ┌─────────────────────────┐     ┌─────────────────────────┐         │
│     │  Windows (.bat)         │     │  Unix (.sh)             │         │
│     ├─────────────────────────┤     ├─────────────────────────┤         │
│     │ @echo off               │     │ #!/bin/bash             │         │
│     │ set "VAR=%VALUE%"       │     │ VAR="$VALUE"            │         │
│     │ %DART_BIN% compile      │     │ "$DART_BIN" compile     │         │
│     │ exit /b %errorlevel%    │     │ exit $?                 │         │
│     └─────────────────────────┘     └─────────────────────────┘         │
│                                                                          │
│  3. No external dependencies:                                            │
│     • Windows: Pure CMD/Batch - no MSYS, Git Bash, or Cygwin required   │
│     • Unix: Standard /bin/bash                                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Examples

See the [examples/hello_world](examples/hello_world) directory for a complete working example.

```bash
cd examples/hello_world

# Build everything
bazel build //...

# Run tests
bazel test //...

# Run the native binary
bazel run //:hello_native
```

## Performance

### Persistent Workers

`rules_dart` supports Bazel's persistent worker mode for faster incremental builds.
Workers keep a Dart VM process alive across multiple build actions, reducing startup overhead.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Worker-Enabled Compilation                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Without Workers:                                                           │
│  Bazel → Spawn → Script → dart compile → Exit (repeat for each action)    │
│                                                                             │
│  With Workers:                                                              │
│  Bazel → Worker (stays alive)                                               │
│         ├── Request 1 → compile → Response                                 │
│         ├── Request 2 → compile → Response                                 │
│         └── Request N → compile → Response                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Enable Workers

**Option 1: Via config flag**
```bash
bazel build --config=dart_worker //...
```

**Option 2: In `.bazelrc` (always enabled)**
```bash
# Enable persistent workers for Dart compilation
build --strategy=DartCompile=worker
build --worker_sandboxing
```

#### Worker Protocol

The worker uses JSON protocol for communication:
- Request: `{"arguments": ["dart", "compile", "exe", ...]}`
- Response: `{"exitCode": 0, "output": "..."}`

### Sandboxing

For hermetic builds with fallback support:

```bash
# In .bazelrc - sandbox with fallback
build --spawn_strategy=sandboxed,standalone
```

For maximum hermeticity (may break some third-party rules):
```bash
bazel build --config=strict //...
```

## Updating Dart SDK Version

When a new Dart SDK version is released, update the following files:

| File | What to Update |
|------|----------------|
| `repositories.bzl` | Add new version checksums in `DART_SDK_VERSIONS` |
| `extensions.bzl` | Update default version if needed |
| `examples/*/MODULE.bazel` | Update example version references |
| `README.md` | Update version in Quick Start examples |
| `CHANGELOG.md` | Document the new SDK support |

### Adding New SDK Version

Edit `repositories.bzl` and add the new version to `DART_SDK_VERSIONS`:

```python
DART_SDK_VERSIONS = {
    "3.7.0": {
        "linux-x64": "sha256-...",
        "linux-arm64": "sha256-...",
        "macos-x64": "sha256-...",
        "macos-arm64": "sha256-...",
        "windows-x64": "sha256-...",
    },
    # Add new version here:
    "3.8.0": {
        "linux-x64": "sha256-...",
        # ...
    },
}
```

### Getting SHA256 Checksums

Download the SDK and compute checksums:

```bash
# Example for Linux x64
curl -L https://storage.googleapis.com/dart-archive/channels/stable/release/3.8.0/sdk/dartsdk-linux-x64-release.zip -o dart.zip
shasum -a 256 dart.zip
```

Or use the official checksums from https://dart.dev/get-dart/archive.

## File Structure

```
rules_dart/
├── defs.bzl           # Core rules (dart_library, dart_binary, etc.)
├── deps.bzl           # Hermetic dependency resolution
├── extensions.bzl     # Bzlmod extensions
├── repositories.bzl   # SDK download rules
├── toolchain.bzl      # Toolchain abstraction
├── proto.bzl          # Proto/gRPC code generation
├── build_runner.bzl   # build_runner integration
├── ROADMAP.md         # Feature parity tracking
├── private/           # Internal implementation
│   ├── coverage.bzl   # Coverage support
│   ├── helpers.bzl    # Common utilities
│   ├── windows.bzl    # Windows script generation
│   └── unix.bzl       # Unix script generation
├── worker/            # Persistent worker
│   ├── bin/worker.dart    # JSON protocol implementation
│   ├── worker_wrapper.sh  # Unix wrapper
│   └── worker_wrapper.bat # Windows wrapper
├── scripts/           # Test scripts (Unix + Windows)
│   ├── test_all.sh / .bat
│   └── test_examples.sh / .bat
├── gazelle/           # Gazelle extension (Go)
└── examples/          # Working examples
    ├── hello_world/       # Basic rules
    ├── proto_example/     # Proto/gRPC
    └── freezed_example/   # build_runner
```

## Contributing

See [GEMINI.md](GEMINI.md) for development guidelines.

## License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.

