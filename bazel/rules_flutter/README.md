# Bazel Rules for Flutter

Hermetic, cross-platform Bazel rules for building and testing Flutter applications.
Designed for the [Bazel Central Registry (BCR)](https://registry.bazel.build/).

## Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         rules_flutter Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │   Mobile           │  │   Desktop          │  │   Web              │   │
│  ├────────────────────┤  ├────────────────────┤  ├────────────────────┤   │
│  │ flutter_android_apk│  │ flutter_macos_app  │  │ flutter_web_app    │   │
│  │ flutter_android_   │  │ flutter_linux_app  │  │ flutter_web_app    │   │
│  │   bundle           │  │ flutter_windows_app│  │   (wasm=True)      │   │
│  │ flutter_ios_app    │  │                    │  │                    │   │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│                                                                             │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│  │   Development      │  │   Quality          │  │   Publishing       │   │
│  ├────────────────────┤  ├────────────────────┤  ├────────────────────┤   │
│  │ flutter_dev_server │  │ flutter_analyze    │  │ flutter_pub_get    │   │
│  │ flutter_run        │  │ flutter_format_    │  │ flutter_pub_upgrade│   │
│  │ flutter_clean      │  │   check            │  │ flutter_pub_publish│   │
│  │ flutter_doctor     │  │ flutter_coverage   │  │                    │   │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                    Hermetic Flutter SDK                             │   │
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │  • Auto-downloaded for Windows/macOS/Linux (x64/arm64)             │   │
│  │  • Local SDK override via FLUTTER_HOME environment variable        │   │
│  │  • Analytics disabled by default for hermetic builds               │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Platform Support Matrix

| Feature | Windows | macOS | Linux | Notes |
|---------|:-------:|:-----:|:-----:|-------|
| flutter_library | ✅ | ✅ | ✅ | Reusable libraries |
| flutter_binary | ✅ | ✅ | ✅ | Development mode |
| flutter_test | ✅ | ✅ | ✅ | Widget/unit tests |
| flutter_analyze | ✅ | ✅ | ✅ | Static analysis |
| flutter_format_check | ✅ | ✅ | ✅ | Format validation |
| flutter_coverage | ✅ | ✅ | ✅ | LCOV output |
| **Mobile** |||||
| flutter_android_apk | ✅ | ✅ | ✅ | APK builds |
| flutter_android_bundle | ✅ | ✅ | ✅ | AAB for Play Store |
| flutter_ios_app | ❌ | ✅ | ❌ | Requires macOS |
| **Desktop** |||||
| flutter_macos_app | ❌ | ✅ | ❌ | Requires macOS |
| flutter_linux_app | ❌ | ❌ | ✅ | Requires Linux |
| flutter_windows_app | ✅ | ❌ | ❌ | Requires Windows |
| **Web** |||||
| flutter_web_app | ✅ | ✅ | ✅ | JavaScript bundle |
| flutter_web_app (WASM) | ✅ | ✅ | ✅ | WebAssembly |
| **Development** |||||
| flutter_dev_server | ✅ | ✅ | ✅ | Hot reload |
| flutter_pub_get | ✅ | ✅ | ✅ | Dependency fetch |
| flutter_build_runner | ✅ | ✅ | ✅ | Code generation |
| flutter_gen_l10n | ✅ | ✅ | ✅ | Localization |
| **Advanced** |||||
| Toolchain | ✅ | ✅ | ✅ | Multi-version SDK |
| IDE Aspects | ✅ | ✅ | ✅ | IntelliJ/VSCode |
| Remote Execution | ✅ | ✅ | ✅ | RBE compatible |

**Windows**: Native Batch (`.bat`) scripts - no MSYS/Git Bash required.

## Quick Start

### 1. Add to MODULE.bazel

```python
bazel_dep(name = "rules_flutter", version = "0.1.0")

flutter = use_extension("@rules_flutter//:extensions.bzl", "flutter")
flutter.configure(
    version = "3.27.0",        # Flutter SDK version
    channel = "stable",         # stable, beta, dev, master
    disable_analytics = True,   # Disable telemetry (default)
)
use_repo(flutter, "flutter_sdk")
```

### 2. Create BUILD.bazel

```python
load("@rules_flutter//:defs.bzl", "flutter_library", "flutter_test")
load("@rules_flutter//:flutter.bzl", 
     "flutter_android_apk", 
     "flutter_ios_app",
     "flutter_web_app",
     "flutter_dev_server")

flutter_library(
    name = "app_lib",
    srcs = glob(["lib/**/*.dart"]),
    assets = glob(["assets/**"]),
    pubspec = "pubspec.yaml",
)

# Android APK
flutter_android_apk(
    name = "app_apk",
    deps = [":app_lib"],
)

# iOS (macOS only)
flutter_ios_app(
    name = "app_ios",
    deps = [":app_lib"],
)

# Web
flutter_web_app(
    name = "app_web",
    deps = [":app_lib"],
)

# Development server with hot reload
flutter_dev_server(
    name = "dev",
    web_port = 8080,
)

flutter_test(
    name = "widget_tests",
    main = "test/widget_test.dart",
    deps = [":app_lib"],
)
```

### 3. Build and Run

```bash
# Build Android APK
bazel run //:app_apk

# Build iOS app (macOS only)
bazel run //:app_ios

# Build web app
bazel run //:app_web

# Start development server with hot reload
bazel run //:dev

# Run tests
bazel test //:widget_tests
```

## Rules Reference

### Core Rules

#### flutter_library

Creates a reusable Flutter library.

```python
flutter_library(
    name = "my_lib",
    srcs = glob(["lib/**/*.dart"]),
    assets = glob(["assets/**"]),
    pubspec = "pubspec.yaml",
    deps = [":other_lib"],
)
```

#### flutter_binary

Runs Flutter in development mode.

```python
flutter_binary(
    name = "dev",
    deps = [":my_lib"],
    device = "chrome",  # or "macos", "linux", "windows"
)
```

#### flutter_test

Runs Flutter widget and unit tests.

```python
flutter_test(
    name = "tests",
    main = "test/all_test.dart",
    deps = [":my_lib"],
    shard_count = 4,  # Parallel test shards
)
```

### Mobile App Rules

#### flutter_android_apk

Builds Android APK with comprehensive options.

```python
flutter_android_apk(
    name = "app_apk",
    deps = [":app_lib"],
    build_mode = "release",      # debug, profile, release
    split_per_abi = True,        # Separate APKs per architecture
    obfuscate = True,            # Code obfuscation
    split_debug_info = "symbols",
    flavor = "production",       # Build flavor
    dart_define = [              # Compile-time variables
        "API_URL=https://api.example.com",
    ],
)
```

#### flutter_android_bundle

Builds Android App Bundle (AAB) for Google Play.

```python
flutter_android_bundle(
    name = "app_bundle",
    deps = [":app_lib"],
    obfuscate = True,
    split_debug_info = "symbols",
)
```

#### flutter_ios_app

Builds iOS application (requires macOS).

```python
# Development build (no signing)
flutter_ios_app(
    name = "app_ios_debug",
    deps = [":app_lib"],
    build_mode = "debug",
)

# Release IPA for TestFlight/App Store
flutter_ios_app(
    name = "app_ios_release",
    deps = [":app_lib"],
    ipa = True,
    codesign = True,
    export_options_plist = "ios/ExportOptions.plist",
)
```

### Desktop App Rules

#### flutter_macos_app

Builds macOS desktop application (requires macOS).

```python
flutter_macos_app(
    name = "app_macos",
    deps = [":app_lib"],
    build_mode = "release",
)
```

#### flutter_linux_app

Builds Linux desktop application (requires Linux).

```python
flutter_linux_app(
    name = "app_linux",
    deps = [":app_lib"],
    build_mode = "release",
)
```

#### flutter_windows_app

Builds Windows desktop application (requires Windows).

```python
flutter_windows_app(
    name = "app_windows",
    deps = [":app_lib"],
    build_mode = "release",
)
```

### Web Rules

#### flutter_web_app

Builds Flutter web application.

```python
# Standard JavaScript build
flutter_web_app(
    name = "app_web",
    deps = [":app_lib"],
    build_mode = "release",
    tree_shake_icons = True,
    pwa_strategy = "offline-first",
)

# WebAssembly build (experimental)
flutter_web_app(
    name = "app_web_wasm",
    deps = [":app_lib"],
    wasm = True,
)
```

### Development Rules

#### flutter_dev_server

Starts development server with hot reload.

```python
flutter_dev_server(
    name = "dev",
    device = "chrome",          # chrome, edge, web-server
    web_port = 8080,            # Port for web server
    web_renderer = "canvaskit", # auto, canvaskit, html, skwasm
    dart_define = [
        "DEBUG=true",
    ],
)
```

Run with: `bazel run //:dev`

Press `r` for hot reload, `R` for hot restart, `q` to quit.

#### flutter_run

Runs Flutter on a specific device.

```python
flutter_run(
    name = "run_android",
    device = "emulator-5554",
)
```

### Quality Rules

#### flutter_analyze

Runs static analysis.

```python
flutter_analyze(
    name = "analyze",
    fatal_infos = True,
    fatal_warnings = True,
)
```

#### flutter_format_check

Validates code formatting.

```python
flutter_format_check(
    name = "format_check",
    srcs = glob(["lib/**/*.dart", "test/**/*.dart"]),
)
```

#### flutter_coverage

Runs tests with coverage collection.

```python
flutter_coverage(
    name = "coverage",
    minimum_coverage = 80,  # Fail if below 80%
    branch_coverage = True,
)
```

### Code Generation Rules

#### flutter_build_runner

Runs `build_runner` for code generation (freezed, json_serializable, etc.).

```python
flutter_build_runner(
    name = "codegen",
    delete_conflicting_outputs = True,
)
```

#### flutter_gen_l10n

Generates localization files.

```python
flutter_gen_l10n(
    name = "l10n",
)
```

### Dependency Rules

#### flutter_pub_get

Fetches dependencies.

```python
flutter_pub_get(
    name = "pub_get",
    offline = False,
)
```

#### flutter_pub_upgrade

Upgrades dependencies.

```python
flutter_pub_upgrade(
    name = "pub_upgrade",
    major_versions = True,  # Include major version upgrades
)
```

#### flutter_pub_publish

Publishes package to pub.dev.

```python
flutter_pub_publish(
    name = "publish",
    dry_run = True,  # Test without publishing
)
```

## Coverage

### Running Tests with Coverage

```bash
# Run with coverage collection
bazel run //:coverage

# Output: coverage/lcov.info
```

### Generating HTML Report

```bash
# After running coverage
bazel run //:coverage_report

# Or manually with genhtml
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

### Setting Minimum Coverage

```python
flutter_coverage(
    name = "coverage",
    minimum_coverage = 80,  # Build fails if below 80%
)
```

## Toolchain

### Using the Flutter Toolchain

```python
load("@rules_flutter//:toolchains/toolchain.bzl", "FlutterToolchainInfo")

def _my_rule_impl(ctx):
    tc = ctx.toolchains["@rules_flutter//:toolchain_type"]
    flutter_bin = tc.flutter_bin
    version = tc.version
```

### Multiple SDK Versions

```python
# MODULE.bazel
flutter = use_extension("@rules_flutter//:extensions.bzl", "flutter")
flutter.toolchain(version = "3.27.0", name = "flutter_stable")
flutter.toolchain(version = "3.28.0", channel = "beta", name = "flutter_beta")
```

## IDE Integration

### Generating IDE Metadata

```bash
# Generate IDE project files
bazel build //... --aspects=@rules_flutter//:aspects/ide.bzl%flutter_ide_aspect \
    --output_groups=flutter_ide_info
```

### IntelliJ IDEA / Android Studio

```bash
# Generate .iml files and run configurations
bazel build //... --aspects=@rules_flutter//:aspects/ide.bzl%flutter_intellij_aspect \
    --output_groups=flutter_intellij
```

### VS Code

```bash
# Generate launch.json, settings.json, tasks.json
bazel build //... --aspects=@rules_flutter//:aspects/ide.bzl%flutter_vscode_aspect \
    --output_groups=flutter_vscode
```

## Advanced Configuration

### Local Flutter SDK

```python
flutter.configure(
    sdk_home = "/path/to/flutter",
)
```

Or via environment variable:

```bash
export FLUTTER_HOME=/path/to/flutter
bazel build //...
```

### Disabling Analytics

By default, analytics are disabled for hermetic builds:

```python
flutter.configure(
    version = "3.27.0",
    disable_analytics = True,  # Default
)
```

### Gazelle Integration

Generate BUILD files automatically from `pubspec.yaml` using Gazelle.

1.  **Configure `MODULE.bazel`**:

    ```python
    bazel_dep(name = "gazelle", version = "0.41.0")
    ```

2.  **Configure `BUILD.bazel`**:

    ```python
    load("@gazelle//:def.bzl", "gazelle", "gazelle_binary")

    gazelle_binary(
        name = "gazelle_bin",
        languages = [
            "@rules_flutter//gazelle/language",
        ],
    )

    gazelle(
        name = "gazelle",
        gazelle = ":gazelle_bin",
    )
    ```

3.  **Run Gazelle**:

    ```bash
    bazel run //:gazelle
    ```

### Recommended .bazelrc

```bash
# .bazelrc

# Enable Bzlmod
common --enable_bzlmod

# Flutter-specific settings
build --experimental_enable_proto_toolchain_resolution

# Increase timeout for Flutter builds
build --test_timeout=600

# Enable verbose test output
test --test_output=errors

# Remote cache (optional)
build:ci --remote_cache=grpcs://remote.buildbuddy.io
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
│     │ set "FLUTTER_BIN=..."   │     │ FLUTTER_BIN="..."       │         │
│     │ %FLUTTER_BIN% build ... │     │ "$FLUTTER_BIN" build ...│         │
│     │ exit /b %errorlevel%    │     │ exit $?                 │         │
│     └─────────────────────────┘     └─────────────────────────┘         │
│                                                                          │
│  3. No external dependencies:                                            │
│     • Windows: Pure CMD/Batch - no MSYS, Git Bash, or Cygwin required   │
│     • Unix: Standard /bin/bash                                           │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
rules_flutter/
├── defs.bzl              # Core rules (flutter_library, flutter_test, etc.)
├── flutter.bzl           # CLI wrapper rules
├── coverage.bzl          # Coverage support
├── extensions.bzl        # Bzlmod extensions
├── repositories.bzl      # SDK download rules
├── ROADMAP.md            # Feature roadmap
├── private/              # Internal implementation
│   └── helpers.bzl       # Common utilities
├── toolchains/           # Toolchain abstraction
│   ├── toolchain.bzl     # Toolchain definitions
│   └── BUILD.bazel       # Toolchain declarations
├── aspects/              # IDE integration
│   ├── ide.bzl           # IDE aspects
│   └── BUILD.bazel
└── examples/             # Working examples
    └── hello_flutter/
```

## Comparison with rules_dart

`rules_flutter` builds on top of `rules_dart` with Flutter-specific features:

| Feature | rules_dart | rules_flutter |
|---------|:----------:|:-------------:|
| Dart libraries | ✅ | ✅ (via Flutter) |
| Native binaries | ✅ | ❌ (use rules_dart) |
| Widget tests | ❌ | ✅ |
| Mobile apps | ❌ | ✅ |
| Desktop apps | ❌ | ✅ |
| Web apps | ✅ (dart2js) | ✅ (Flutter web) |
| Hot reload | ❌ | ✅ |
| Assets | ❌ | ✅ |

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the feature roadmap and comparison with mature rulesets.

## Contributing

See [GEMINI.md](GEMINI.md) for development guidelines.

## License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.
