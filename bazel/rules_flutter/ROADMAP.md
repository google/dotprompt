# rules_flutter Roadmap

This document tracks feature parity with mature Bazel rulesets and the development
roadmap for rules_flutter.

## Current Status: Production Ready (v1.0.0)

All core features are implemented and tested. The ruleset is ready for BCR publication.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         rules_flutter Status                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ✅ Complete                       │  Implementation Files                  │
│  ─────────────────────────────────┼──────────────────────────────────────  │
│  • flutter_library                │  defs.bzl                              │
│  • flutter_binary                 │  defs.bzl                              │
│  • flutter_test                   │  defs.bzl                              │
│  • flutter_application            │  defs.bzl                              │
│  • flutter_web_app (WASM)         │  flutter.bzl                           │
│  • flutter_android_apk            │  defs.bzl                              │
│  • flutter_android_bundle         │  defs.bzl                              │
│  • flutter_ios_app                │  defs.bzl                              │
│  • flutter_macos_app              │  defs.bzl                              │
│  • flutter_linux_app              │  defs.bzl                              │
│  • flutter_windows_app            │  defs.bzl                              │
│  • flutter_analyze                │  flutter.bzl                           │
│  • flutter_format_check           │  flutter.bzl                           │
│  • flutter_coverage               │  coverage.bzl                          │
│  • flutter_coverage_report        │  coverage.bzl                          │
│  • flutter_pub_get/upgrade        │  flutter.bzl                           │
│  • flutter_pub_outdated           │  flutter.bzl                           │
│  • flutter_pub_publish            │  flutter.bzl                           │
│  • flutter_build_runner           │  flutter.bzl                           │
│  • flutter_gen_l10n               │  flutter.bzl                           │
│  • flutter_clean                  │  flutter.bzl                           │
│  • flutter_doctor                 │  flutter.bzl                           │
│  • flutter_dev_server (hot reload)│  flutter.bzl                           │
│  • Toolchain model                │  toolchains/                           │
│  • Gazelle extension              │  gazelle/                              │
│  • IDE aspects (IntelliJ/VSCode)  │  aspects/                              │
│  • Hermetic SDK management        │  repositories.bzl, extensions.bzl     │
│  • Container support (OCI)        │  docker.bzl                            │
│  • Persistent workers             │  private/workers.bzl, workers/         │
│  • Platform transitions           │  defs.bzl                              │
│  • Cross-platform (100% MSYS-free)│  private/helpers.bzl                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Feature Parity Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                    Feature Comparison: Mature Rulesets                             │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  Feature Category          │ rules_go │ rules_rust │ rules_flutter                │
│  ─────────────────────────────────────────────────────────────────────────────────│
│  Toolchain Model           │    ✅    │     ✅     │     ✅                       │
│  IDE Aspects               │    ✅    │     ✅     │     ✅                       │
│  Provider Model            │    ✅    │     ✅     │     ✅                       │
│  Remote Build Execution    │    ✅    │     ✅     │     ✅                       │
│  Platform Transitions      │    ✅    │     ✅     │     ✅                       │
│  Persistent Workers        │    ✅    │     ✅     │     ✅                       │
│  Coverage Support          │    ✅    │     ✅     │     ✅                       │
│  Sandbox Hermeticity       │    ✅    │     ✅     │     ✅                       │
│  Gazelle Extension         │    ✅    │     ❌     │     ✅                       │
│  Documentation Generation  │    ✅    │     ✅     │     ✅                       │
│  Package Publishing        │    ❌    │     ✅     │     ✅                       │
│  Cross-compilation         │    ✅    │     ✅     │     ✅                       │
│  Action Caching            │    ✅    │     ✅     │     ✅                       │
│  Build Event Protocol      │    ✅    │     ✅     │     ✅                       │
│                                                                                    │
│  Legend: ✅ Complete  ❌ Not Applicable                                           │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

## Core Rules

| Feature | Status | Notes |
|---------|:------:|-------|
| flutter_library | ✅ | Reusable libraries with provider |
| flutter_binary | ✅ | Development mode runner |
| flutter_test | ✅ | Widget/unit tests |
| flutter_application | ✅ | Production builds |
| flutter_web_app | ✅ | Web with WASM support |
| flutter_analyze | ✅ | Static analysis |
| flutter_format_check | ✅ | Code formatting validation |
| flutter_pub_get | ✅ | Dependency resolution |
| flutter_pub_upgrade | ✅ | Dependency updates |
| flutter_pub_outdated | ✅ | Outdated package check |
| flutter_pub_publish | ✅ | Package publishing |
| flutter_build_runner | ✅ | Code generation |
| flutter_gen_l10n | ✅ | Localization |
| flutter_clean | ✅ | Build cleanup |
| flutter_doctor | ✅ | Installation check |
| flutter_dev_server | ✅ | Hot reload dev server |
| flutter_coverage | ✅ | Coverage with min % |
| flutter_coverage_report | ✅ | HTML coverage reports |

## Target Platforms

| Platform | Status | Build Command |
|----------|:------:|---------------|
| Android (APK) | ✅ | `flutter build apk` |
| Android (AAB) | ✅ | `flutter build appbundle` |
| iOS | ✅ | `flutter build ios` |
| Web (JS) | ✅ | `flutter build web` |
| Web (WASM) | ✅ | `flutter build web --wasm` |
| macOS | ✅ | `flutter build macos` |
| Linux | ✅ | `flutter build linux` |
| Windows | ✅ | `flutter build windows` |

## Bazel Integration Features

| Feature | Status | Notes |
|---------|:------:|-------|
| **Toolchain Model** | ✅ | Proper `toolchain()` registration |
| **IDE Aspects** | ✅ | IntelliJ/VSCode integration |
| **Provider Model** | ✅ | FlutterLibraryInfo, FlutterIdeInfo |
| **Coverage Support** | ✅ | lcov/genhtml integration |
| **Action Caching** | ✅ | Remote cache support |
| **Documentation Generation** | ✅ | flutter_doc rule |
| **Package Publishing** | ✅ | flutter_pub_publish |
| **Remote Build Execution** | ✅ | RBE-compatible hermetic actions |
| **Platform Transitions** | ✅ | Cross-compilation support |
| **Persistent Workers** | ✅ | Incremental builds |
| **Sandbox Hermeticity** | ✅ | Fully hermetic actions |
| **Gazelle Extension** | ✅ | Auto-generate BUILD files |
| **Cross-compilation** | ✅ | Build for different platforms |
| **Build Event Protocol** | ✅ | CI/CD integration |

---

## Implementation Phases

### Phase 1: Core Rules ✅ Complete
- [x] flutter_library rule
- [x] flutter_binary rule
- [x] flutter_test rule
- [x] flutter_application rule
- [x] flutter_web_app (with WASM)
- [x] flutter_analyze
- [x] flutter_format_check
- [x] flutter_pub_get
- [x] flutter_build_runner
- [x] flutter_gen_l10n
- [x] flutter_clean
- [x] flutter_doctor
- [x] FlutterLibraryInfo provider

### Phase 2: Platform Support ✅ Complete
- [x] Android APK/AAB builds
- [x] iOS builds
- [x] Web builds (JS and WASM)
- [x] macOS builds
- [x] Linux builds
- [x] Windows builds
- [x] Cross-platform scripts (no MSYS)

### Phase 3: SDK Management ✅ Complete
- [x] Hermetic SDK download
- [x] Platform/architecture detection
- [x] Local SDK support
- [x] Channel selection (stable/beta/dev)
- [x] Analytics opt-out

### Phase 4: Developer Experience ✅ Complete
- [x] gRPC example with Envoy proxy
- [x] Container support (Podman/Docker)
- [x] Demo mode
- [x] Worker protocol implementation
- [x] Hot reload worker
- [x] Analyzer worker
- [x] IDE aspects (IntelliJ)
- [x] IDE aspects (VS Code)
- [x] Incremental compilation

### Phase 5: Bazel Best Practices ✅ Complete
- [x] Formal toolchain model
- [x] RBE compatibility
- [x] Coverage support
- [x] Gazelle extension
- [x] Platform transitions
- [x] Build Event Protocol

### Phase 6: BCR Publication ✅ Ready
- [x] Full documentation
- [x] Compatibility testing
- [x] Release automation
- [x] BCR submission ready

---

## Architecture Diagrams

### Toolchain Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Toolchain Architecture                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MODULE.bazel                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  flutter = use_extension("@rules_flutter//extensions:flutter.bzl")  │   │
│  │  flutter.sdk(version = "3.22.0")                                    │   │
│  │  use_repo(flutter, "flutter_sdk")                                   │   │
│  │  register_toolchains("@rules_flutter//toolchains:all")              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Toolchain Resolution                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  @platforms//os:linux + @platforms//cpu:x86_64                      │   │
│  │      ↓                                                              │   │
│  │  flutter_toolchain(flutter_linux_x64)                               │   │
│  │      ↓                                                              │   │
│  │  FlutterToolchainInfo(flutter_bin, dart_bin, ...)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### IDE Aspect Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IDE Aspect Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  bazel build //app:my_app --aspects=@rules_flutter//aspects:ide.bzl%...    │
│                                                                             │
│  Outputs:                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  IntelliJ IDEA:                                                     │   │
│  │  ├── .idea/                                                         │   │
│  │  │   ├── modules.xml                                                │   │
│  │  │   ├── libraries/                                                 │   │
│  │  │   │   └── dart_sdk.xml                                           │   │
│  │  │   └── runConfigurations/                                         │   │
│  │  │       └── my_app.xml                                             │   │
│  │  └── my_app.iml                                                     │   │
│  │                                                                     │   │
│  │  VS Code:                                                           │   │
│  │  ├── .vscode/                                                       │   │
│  │  │   ├── settings.json                                              │   │
│  │  │   ├── launch.json                                                │   │
│  │  │   └── tasks.json                                                 │   │
│  │  └── analysis_options.yaml                                          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Provider Model

```python
# Providers for Flutter targets
FlutterLibraryInfo = provider(
    fields = {
        "sources": "depset of source files",
        "assets": "depset of asset files",
        "pubspec": "pubspec.yaml file",
        "transitive_sources": "all transitive sources",
        "transitive_assets": "all transitive assets",
        "transitive_deps": "all transitive pub dependencies",
        "package_config": "package_config.json for resolution",
    }
)

FlutterBinaryInfo = provider(
    fields = {
        "executable": "built executable",
        "target_platform": "target platform",
        "build_mode": "debug/profile/release",
        "vm_service_port": "port for hot reload",
    }
)

FlutterTestInfo = provider(
    fields = {
        "test_files": "test source files",
        "golden_files": "golden test images",
        "coverage_data": "lcov coverage data",
    }
)

# IDE integration providers
FlutterIdeInfo = provider(
    fields = {
        "source_roots": "source directories",
        "test_roots": "test directories",
        "asset_roots": "asset directories",
        "package_uri": "package: URI",
        "analysis_options": "analysis_options.yaml path",
    }
)
```

---

## File Reference

| File | Purpose |
|------|---------|
| `defs.bzl` | Core rules (flutter_library, flutter_binary, flutter_test, etc.) |
| `flutter.bzl` | Additional CLI rules (analyze, format, pub, etc.) |
| `coverage.bzl` | Coverage support rules |
| `docker.bzl` | OCI/Container rules |
| `extensions.bzl` | Module extension for SDK |
| `repositories.bzl` | Flutter SDK repository rule |
| `private/helpers.bzl` | Common utilities |
| `private/workers.bzl` | Persistent worker support |
| `workers/` | Dart worker implementations |
| `aspects/` | IDE aspects (IntelliJ, VS Code) |
| `toolchains/` | Toolchain definitions |
| `gazelle/` | Gazelle extension for BUILD file generation |

---

## Examples

| Example | Features |
|---------|----------|
| `hello_flutter/` | Basic flutter_library, flutter_application |
| `grpc_app/` | gRPC integration with Envoy proxy, container support |

---

## Recently Completed Enhancements

The following features were recently added:

### 1. ✅ Enhanced DevTools Integration

**File**: `devtools.bzl`

Launch DevTools with customizable features:

```python
flutter_devtools(
    name = "devtools",
    app = ":my_app",
    features = [
        "inspector",
        "performance",
        "memory",
        "network",
        "logging",
        "cpu_profiler",
    ],
    devtools_port = 9100,
)
```

Run with: `bazel run //:devtools`

### 2. ✅ Golden Test Support

**File**: `golden.bzl`

Automatic golden file management with visual diff reports:

```python
flutter_golden_test(
    name = "widget_golden_test",
    srcs = ["test/widget_golden_test.dart"],
    golden_dir = "test/goldens",
    threshold = 1,  # Allow 1% pixel difference
)

flutter_update_goldens(
    name = "update_goldens",
)
```

Features:
- Match widget screenshots against golden references
- Configurable pixel difference threshold
- Automatic diff image generation on failure
- One-command golden update: `bazel run //:update_goldens`

### 3. ✅ Additional IDE Support

Support for modern AI-powered editors:

| IDE | File | Features |
|-----|------|----------|
| Cursor | `aspects/cursor.bzl` | Flutter-specific AI rules, widget patterns |
| Zed | `aspects/zed.bzl` | Tasks for build, test, DevTools |
| Antigravity | `aspects/antigravity.bzl` | GEMINI.md with Flutter context |

Usage:
```bash
bazel build //my:target --aspects=@rules_flutter//aspects:antigravity.bzl%antigravity_flutter_aspect \
    --output_groups=antigravity_ide
```

