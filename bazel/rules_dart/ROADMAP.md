# rules_dart Roadmap

This document tracks the feature parity between `rules_dart` and mature Bazel rulesets
like `rules_go` and `rules_rust`.

## Current Status: Production Ready (v1.0.0)

All core features are implemented and tested. The ruleset is ready for BCR publication.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         rules_dart Status                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ Complete                       │  Implementation Files                  │
│  ─────────────────────────────────┼──────────────────────────────────────  │
│  • dart_library                   │  defs.bzl                              │
│  • dart_binary                    │  defs.bzl                              │
│  • dart_test (with sharding)      │  defs.bzl                              │
│  • dart_native_binary             │  defs.bzl                              │
│  • dart_js_binary                 │  defs.bzl                              │
│  • dart_wasm_binary               │  defs.bzl                              │
│  • dart_aot_snapshot              │  defs.bzl                              │
│  • dart_analyze                   │  defs.bzl                              │
│  • dart_format_check              │  defs.bzl                              │
│  • dart_doc                       │  defs.bzl                              │
│  • dart_pub_get/upgrade           │  defs.bzl                              │
│  • dart_pub_publish               │  defs.bzl                              │
│  • dart_proto_library             │  proto.bzl                             │
│  • dart_grpc_library              │  proto.bzl                             │
│  • dart_build_runner              │  build_runner.bzl                      │
│  • Toolchain model                │  toolchain.bzl                         │
│  • Gazelle extension              │  gazelle/                              │
│  • IDE aspects                    │  aspects.bzl                           │
│  • Hermetic SDK management        │  repositories.bzl, extensions.bzl     │
│  • Dependency resolution          │  deps.bzl                              │
│  • Coverage support               │  private/coverage.bzl                  │
│  • Test sharding                  │  private/sharding.bzl                  │
│  • Persistent workers             │  private/workers.bzl, worker/          │
│  • Incremental compilation        │  private/incremental.bzl               │
│  • BEP integration                │  private/bep.bzl                       │
│  • RBE support                    │  private/rbe.bzl, rbe.bazelrc          │
│  • Sandbox hermeticity            │  private/sandbox.bzl                   │
│  • Platform transitions           │  transitions.bzl                       │
│  • Cross-platform (100% MSYS-free)│  private/windows.bzl, unix.bzl         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Feature Parity Matrix

| Feature | rules_go | rules_rust | rules_dart | Status |
|---------|:--------:|:----------:|:----------:|--------|
| **Dependency Management** |||||
| Lockfile-based deps | ✅ | ✅ | ✅ | Done (deps.bzl) |
| Transitive resolution | ✅ | ✅ | ✅ | Done |
| Package registry fetching | ✅ | ✅ | ✅ | Done |
| Version conflict resolution | ✅ | ✅ | ✅ | Done (deps.bzl) |
| **Toolchain** |||||
| Proper toolchain abstraction | ✅ | ✅ | ✅ | Done (toolchain.bzl) |
| Multiple SDK versions | ✅ | ✅ | ✅ | Done |
| Cross-compilation targets | ✅ | ✅ | ✅ | Done (transitions.bzl) |
| Platform transitions | ✅ | ✅ | ✅ | Done |
| **Build Features** |||||
| Persistent workers | ✅ | ✅ | ✅ | Done (private/workers.bzl) |
| Incremental compilation | ✅ | ✅ | ✅ | Done (private/incremental.bzl) |
| Remote caching | ✅ | ✅ | ✅ | Works |
| Remote execution (RBE) | ✅ | ✅ | ✅ | Done (rbe.bazelrc) |
| Action caching | ✅ | ✅ | ✅ | Done |
| Sandbox hermeticity | ✅ | ✅ | ✅ | Done (sandbox.bzl) |
| Build Event Protocol | ✅ | ✅ | ✅ | Done (bep.bzl) |
| **Code Generation** |||||
| Gazelle extension | ✅ | ❌ | ✅ | Done |
| Proto/gRPC integration | ✅ | ✅ | ✅ | Done (proto.bzl) |
| Freezed/JSON codegen | N/A | N/A | ✅ | Done (build_runner.bzl) |
| **Testing** |||||
| Coverage integration | ✅ | ✅ | ✅ | Done (coverage.bzl) |
| Test sharding | ✅ | ✅ | ✅ | Done (sharding.bzl) |
| **IDE Support** |||||
| IDE aspects (IntelliJ/VSCode) | ✅ | ✅ | ✅ | Done (aspects.bzl) |
| **Flutter** |||||
| flutter_library | ❌ | ❌ | ✅ | In rules_flutter |
| flutter_test | ❌ | ❌ | ✅ | In rules_flutter |
| flutter_application | ❌ | ❌ | ✅ | In rules_flutter |
| flutter_coverage | ❌ | ❌ | ✅ | In rules_flutter |
| Desktop apps | ❌ | ❌ | ✅ | In rules_flutter |

## Action Caching Details

Bazel's action caching works automatically when actions are hermetic. Here's the status
for `rules_dart`:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         Action Caching Status                                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Rule              │ Local Cache │ Remote Cache │ Notes                         │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  dart_library      │     ✅      │      ✅      │ Pure file collection          │
│  dart_binary       │     ✅      │      ✅      │ Script generation only        │
│  dart_test         │     ✅      │      ✅      │ Hermetic with copy-to-temp    │
│  dart_native_binary│     ✅      │      ✅      │ AOT compilation is hermetic   │
│  dart_proto_library│     ✅      │      ✅      │ Proto codegen is hermetic     │
│  dart_analyze      │     ✅      │      ✅      │ Hermetic with copy-to-temp    │
│  dart_format_check │     ✅      │      ✅      │ Pure analysis                 │
│                                                                                  │
│  Cache Location: ~/.cache/bazel/ (local) or --remote_cache=URL (remote)         │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Enabling Remote Caching

```bash
# Use remote cache with Google Cloud Storage
bazel build //... --remote_cache=grpcs://remotebuildexecution.googleapis.com

# Use remote cache with BuildBuddy (popular free option)
bazel build //... --remote_cache=grpcs://remote.buildbuddy.io

# Configuration in .bazelrc
build --remote_cache=grpcs://your-cache-server.com
build --remote_upload_local_results=true
```

### Cache Key Components

For Dart rules, the cache key is computed from:
1. **Input files** - All source files and dependencies
2. **Tool versions** - Dart SDK version
3. **Command line** - Build flags and options
4. **Environment variables** - Only those explicitly declared

---

## Implementation Phases

### Phase 1: Foundation ✅ Complete
- [x] Cross-platform script generation (100% Windows native)
- [x] Hermetic SDK download
- [x] Persistent workers (JSON protocol)
- [x] Basic Gazelle extension
- [x] Open source governance files
- [x] Cross-platform test scripts (.sh + .bat)

### Phase 2: Toolchain Abstraction ✅ Complete
- [x] `dart_toolchain` rule definition
- [x] `DartToolchainInfo` provider
- [x] `toolchain_type` registration
- [x] `current_dart_toolchain` helper

### Phase 3: Dependency Management ✅ Complete
- [x] `pubspec.lock` parsing
- [x] `dart_package` repository rule
- [x] `dart_deps` module extension
- [x] Version conflict detection

### Phase 4: Testing & Coverage ✅ Complete
- [x] Coverage script generation (Unix/Windows)
- [x] LCOV output format support
- [x] Test sharding (`shard_count` attribute)
- [x] `dart_sharded_test` rule
- [x] `dart_test_suite` macro
- [x] Integration with `bazel coverage`

### Phase 5: Code Generation ✅ Complete
- [x] `dart_proto_library`
- [x] `dart_grpc_library`
- [x] `dart_build_runner` (for freezed, json_serializable)
- [x] Working examples (proto_example, freezed_example)
- [x] Test scripts for examples

### Phase 6: Advanced Features ✅ Complete
- [x] Test sharding (`shard_count` attribute)
- [x] Version conflict detection in deps.bzl
- [x] Remote execution (RBE) configuration (rbe.bazelrc)
- [x] Coverage infrastructure (private/coverage.bzl)
- [x] BEP integration (private/bep.bzl)
- [x] Incremental compilation infrastructure (private/incremental.bzl)
- [x] Platform transitions (transitions.bzl)
- [x] Sandbox hermeticity (private/sandbox.bzl)
- [x] Persistent workers (private/workers.bzl)

### Phase 7: Flutter Support ✅ Complete (in rules_flutter)
- [x] `flutter_library` rule (in rules_flutter)
- [x] `flutter_test` rule (in rules_flutter)
- [x] `flutter_application` rule (in rules_flutter)
- [x] Flutter SDK repository rule (in rules_flutter)
- [x] Platform-specific builds (iOS, Android, Web, Desktop)
- [x] Coverage support (in rules_flutter)
- [x] Desktop platform rules (macOS, Linux, Windows)
- [x] Dev server with hot reload

### Phase 8: IDE Integration ✅ Complete
- [x] `dart_ide_info` aspect
- [x] `DartIdeInfo` provider
- [x] VSCode settings generator
- [x] IntelliJ facet generator

### Phase 9: BCR Publication ✅ Ready
- [x] Full documentation
- [x] Compatibility testing
- [x] Release automation
- [x] BCR submission ready

---

## File Reference

| File | Purpose |
|------|---------|
| `defs.bzl` | Core rules (dart_library, dart_binary, dart_test, etc.) |
| `toolchain.bzl` | Toolchain abstraction and provider |
| `deps.bzl` | Hermetic dependency resolution |
| `proto.bzl` | Proto and gRPC code generation |
| `build_runner.bzl` | build_runner integration |
| `aspects.bzl` | IDE integration aspects |
| `transitions.bzl` | Platform transitions for cross-compilation |
| `rbe.bazelrc` | Remote Build Execution configuration |
| `private/coverage.bzl` | Coverage support |
| `private/helpers.bzl` | Common utilities |
| `private/windows.bzl` | Windows script generation |
| `private/unix.bzl` | Unix script generation |
| `private/workers.bzl` | Persistent worker support |
| `private/incremental.bzl` | Incremental compilation |
| `private/bep.bzl` | Build Event Protocol integration |
| `private/rbe.bzl` | Remote Build Execution utilities |
| `private/sandbox.bzl` | Sandbox hermeticity |
| `private/sharding.bzl` | Test sharding |

## Examples

| Example | Features |
|---------|----------|
| `hello_world/` | Basic dart_library, dart_binary, dart_test |
| `proto_example/` | dart_proto_library, dart_grpc_library |
| `freezed_example/` | dart_build_runner, freezed, json_serializable |

---

## Detailed Design

### DartPackageInfo Provider

```python
DartPackageInfo = provider(
    fields = {
        "name": "Package name",
        "version": "Package version",
        "lib_root": "Path to lib directory",
        "srcs": "Depset of source files (direct)",
        "data": "Depset of data files (direct)",
        "transitive_srcs": "Depset of all transitive source files",
        "transitive_data": "Depset of all transitive data files",
        "transitive_packages": "Depset of transitive package infos",
    },
)
```

### Test Sharding

```python
dart_test(
    name = "unit_tests",
    main = "test/all_test.dart",
    shard_count = 4,
)
```

Implementation adds `--shard-index=$SHARD_INDEX` to dart test command.

### Toolchain Abstraction

```python
# In toolchain.bzl
DartToolchainInfo = provider(
    fields = {
        "dart_bin": "File: The dart executable.",
        "dart_sdk": "Depset: All SDK files.",
        "version": "String: The SDK version.",
    },
)

dart_toolchain = rule(
    implementation = _dart_toolchain_impl,
    attrs = {
        "dart_bin": attr.label(...),
        "version": attr.string(...),
    },
    provides = [platform_common.ToolchainInfo, DartToolchainInfo],
)
```

### Coverage Integration

```bash
# Run with coverage
bazel coverage //my:test

# Generated script uses:
dart test --coverage=<dir> test/my_test.dart
dart run coverage:format_coverage --lcov ...
```

### Proto Integration

```python
load("@rules_dart//:proto.bzl", "dart_proto_library", "dart_grpc_library")

proto_library(
    name = "user_proto",
    srcs = ["user.proto"],
)

dart_proto_library(
    name = "user_dart_proto",
    deps = [":user_proto"],
)

dart_grpc_library(
    name = "user_dart_grpc",
    deps = [":user_proto"],
)
```

### Build Runner Integration

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

---

## Recently Completed Enhancements

The following features were recently added:

### 1. ✅ Starlark-native Dependency Resolution
Replaces shell-based pub get with pure Starlark parsing.

**File**: `private/pubspec_parser.bzl`

```python
# In MODULE.bazel
dart_deps = use_extension("@rules_dart//:extensions.bzl", "dart_deps")
dart_deps.from_pubspec_lock(lock_file = "//:pubspec.lock")
use_repo(dart_deps, "dart_deps_http", "dart_deps_path", ...)
```

### 2. ✅ Enhanced Remote Execution Testing
CI workflow for RBE compatibility testing with:
- Remote caching validation
- Sandbox hermeticity checks
- Build metrics and profiling
- Action determinism verification

**File**: `.github/workflows/rules_dart_rbe.yml`

### 3. ✅ Additional IDE Integration
Support for modern AI-powered editors:

| IDE | File | Features |
|-----|------|----------|
| Cursor | `aspects/cursor.bzl` | Settings, AI rules, project context |
| Zed | `aspects/zed.bzl` | Settings, tasks, keymaps |
| Antigravity | `aspects/antigravity.bzl` | GEMINI.md, context.json |

Usage:
```bash
bazel build //my:target --aspects=@rules_dart//aspects:cursor.bzl%cursor_aspect \
    --output_groups=cursor_ide
```

