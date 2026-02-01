# rules_dart Roadmap

This document tracks the feature parity between `rules_dart` and mature Bazel rulesets
like `rules_go` and `rules_rust`.

## Feature Parity Matrix

| Feature | rules_go | rules_rust | rules_dart | Status |
|---------|:--------:|:----------:|:----------:|--------|
| **Dependency Management** |||||
| Lockfile-based deps | ✅ | ✅ | ✅ | Done (deps.bzl) |
| Transitive resolution | ✅ | ✅ | ⚠️ | Basic |
| Package registry fetching | ✅ | ✅ | ✅ | Done |
| Version conflict resolution | ✅ | ✅ | ✅ | Done (deps.bzl) |
| **Toolchain** |||||
| Proper toolchain abstraction | ✅ | ✅ | ✅ | Done (toolchain.bzl) |
| Multiple SDK versions | ✅ | ✅ | ✅ | Done |
| Cross-compilation targets | ✅ | ✅ | ⚠️ | Partial |
| **Build Features** |||||
| Persistent workers | ✅ | ✅ | ✅ | Done |
| Incremental compilation | ✅ | ✅ | ❌ | Planned |
| Remote caching | ✅ | ✅ | ✅ | Works |
| Remote execution (RBE) | ✅ | ✅ | ✅ | Done (rbe.bazelrc) |
| **Code Generation** |||||
| Gazelle extension | ✅ | ❌ | ✅ | Done |
| Proto/gRPC integration | ✅ | ✅ | ✅ | Done (proto.bzl) |
| Freezed/JSON codegen | N/A | N/A | ✅ | Done (build_runner.bzl) |
| **Testing** |||||
| Coverage integration | ✅ | ✅ | ✅ | Done (coverage.bzl) |
| Test sharding | ✅ | ✅ | ✅ | Done (shard_count) |
| **IDE Support** |||||
| IDE aspects (IntelliJ/VSCode) | ✅ | ✅ | ✅ | Done (aspects.bzl) |
| **Flutter** |||||
| flutter_library | ❌ | ❌ | ❌ | Planned |
| flutter_test | ❌ | ❌ | ❌ | Planned |
| flutter_application | ❌ | ❌ | ❌ | Planned |

## Implementation Progress

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
- [ ] Version conflict detection

### Phase 4: Testing & Coverage ✅ Complete
- [x] Coverage script generation (Unix/Windows)
- [x] LCOV output format support
- [x] Test sharding (shard_count)
- [ ] Integration with `bazel coverage`

### Phase 5: Code Generation ✅ Complete
- [x] `dart_proto_library`
- [x] `dart_grpc_library`
- [x] `dart_build_runner` (for freezed, json_serializable)
- [x] Working examples (proto_example, freezed_example)
- [x] Test scripts for examples

### Phase 6: Advanced Features ✅ Complete
- [x] Test sharding (shard_count attribute)
- [x] Version conflict detection in deps.bzl
- [x] Remote execution (RBE) configuration (rbe.bazelrc)
- [x] Coverage infrastructure (private/coverage.bzl)

### Phase 7: Flutter Support (Future)
- [ ] `flutter_library` rule
- [ ] `flutter_test` rule
- [ ] `flutter_application` rule
- [ ] Flutter SDK repository rule
- [ ] Platform-specific builds (iOS, Android, Web)

### Phase 8: IDE Integration ✅ Complete
- [x] `dart_ide_info` aspect
- [x] `DartIdeInfo` provider
- [x] VSCode settings generator
- [x] IntelliJ facet generator

---

## What Can Be Implemented Now

### 1. Test Sharding (Low effort)
Add `shard_count` attribute to `dart_test`:
```python
dart_test(
    name = "large_test",
    main = "test/all_test.dart",
    shard_count = 4,  # Run in 4 parallel shards
)
```

### 2. Version Conflict Detection (Medium effort)
Enhance `deps.bzl` to detect conflicting versions:
```python
# When parsing pubspec.lock, check for conflicts
def _check_version_conflicts(packages, existing):
    for name, data in packages.items():
        if name in existing and existing[name] != data["version"]:
            fail("Version conflict for {}: {} vs {}".format(
                name, existing[name], data["version"]))
```

### 3. Flutter Rules (High effort)
Create `flutter.bzl` with Flutter-specific rules:
```python
flutter_library(
    name = "my_app",
    srcs = glob(["lib/**/*.dart"]),
    assets = glob(["assets/**"]),
    pubspec = "pubspec.yaml",
)

flutter_application(
    name = "app",
    deps = [":my_app"],
    target_platform = "android",  # or "ios", "web"
)
```

### 4. Remote Execution Testing (Medium effort)
- Create CI workflow with RBE
- Add `--remote_executor` compatibility tests
- Document RBE setup in README

---

## File Reference

| File | Purpose |
|------|---------|
| `defs.bzl` | Core rules (dart_library, dart_binary, dart_test, etc.) |
| `toolchain.bzl` | Toolchain abstraction and provider |
| `deps.bzl` | Hermetic dependency resolution |
| `proto.bzl` | Proto and gRPC code generation |
| `build_runner.bzl` | build_runner integration |
| `private/coverage.bzl` | Coverage support |
| `private/helpers.bzl` | Common utilities |
| `private/windows.bzl` | Windows script generation |
| `private/unix.bzl` | Unix script generation |

## Examples

| Example | Features |
|---------|----------|
| `hello_world/` | Basic dart_library, dart_binary, dart_test |
| `proto_example/` | dart_proto_library, dart_grpc_library |
| `freezed_example/` | dart_build_runner, freezed, json_serializable |

---

## Detailed Design

### Test Sharding

```python
dart_test(
    name = "unit_tests",
    main = "test/all_test.dart",
    shard_count = 4,
)
```

Implementation adds `--shard-index=$SHARD_INDEX` to dart test command.

### Flutter Support

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Flutter Rule Architecture                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  flutter_library                                                             │
│  ├── srcs: Dart source files                                                │
│  ├── assets: Asset files (images, fonts, etc.)                              │
│  ├── pubspec: pubspec.yaml                                                  │
│  └── deps: Other flutter_library targets                                    │
│                                                                              │
│  flutter_application                                                         │
│  ├── deps: flutter_library targets                                          │
│  ├── target_platform: android | ios | web | macos | linux | windows        │
│  └── outputs: APK, IPA, web bundle, etc.                                    │
│                                                                              │
│  flutter_test                                                                │
│  ├── main: Test entry point                                                 │
│  ├── deps: Libraries to test                                                │
│  └── outputs: Test results                                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

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
