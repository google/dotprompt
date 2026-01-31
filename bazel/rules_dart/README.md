# rules_dart

Bazel rules for building Dart applications.

## Overview

This package provides Bazel rules for building and testing Dart code. The Dart
SDK is automatically downloaded from Google's official CDN, similar to how
`rules_go` and `rules_rust` work.

## Features

- **Hermetic Dart SDK**: Automatically downloads the Dart SDK for the host platform
- **Cross-platform**: Supports Linux, macOS, and Windows (x64 and arm64)
- **Bzlmod compatible**: Designed for modern Bazel module system
- **Simple API**: Easy-to-use rules for libraries, binaries, and tests

## Supported Platforms

| Platform     | Architecture |
|-------------|--------------|
| Linux       | x64, arm64   |
| macOS       | x64, arm64   |
| Windows     | x64          |

## Quick Start

### 1. Add to MODULE.bazel

```starlark
# In your MODULE.bazel
bazel_dep(name = "rules_dart", version = "0.1.0")

dart = use_extension("@rules_dart//:extensions.bzl", "dart")
dart.configure()
use_repo(dart, "dart_sdk")
```

### 2. Use in BUILD files

```starlark
load("@rules_dart//:defs.bzl", "dart_library", "dart_binary", "dart_test")

dart_library(
    name = "my_lib",
    srcs = glob(["lib/**/*.dart"]),
)

dart_binary(
    name = "my_app",
    main = "bin/main.dart",
    deps = [":my_lib"],
)

dart_test(
    name = "my_test",
    main = "test/my_test.dart",
    deps = [":my_lib"],
)
```

## Rules

### `dart_library`

Creates a Dart library target.

```starlark
dart_library(
    name = "my_lib",
    srcs = glob(["lib/**/*.dart"]),
    deps = [],
    visibility = ["//visibility:public"],
)
```

### `dart_binary`

Creates a Dart executable target.

```starlark
dart_binary(
    name = "my_app",
    main = "bin/main.dart",
    srcs = [],
    deps = [],
)
```

### `dart_test`

Creates a Dart test target.

```starlark
dart_test(
    name = "my_test",
    main = "test/my_test.dart",
    srcs = [],
    deps = [],
    data = [],
)
```



## Module Extension

### `dart.configure`

Configures the Dart SDK version.

```starlark
dart = use_extension("@rules_dart//:extensions.bzl", "dart")
dart.configure(version = "3.7.0")  # Optional, defaults to latest stable
use_repo(dart, "dart_sdk")
```

## SDK Version

The default SDK version is defined in `repositories.bzl`. Currently: **3.7.0**

To use a different version:

```starlark
dart.configure(version = "3.6.0")
```

## Roadmap

The following rules are planned for future releases to support full Dart package
publishing workflows:

| Rule | Description | Status |
|------|-------------|--------|
| `dart_library` | Create library targets | ✅ Done |
| `dart_binary` | Create executable targets | ✅ Done |
| `dart_test` | Run unit tests | ✅ Done |
| `dart_package` | Manage pubspec.yaml and dependencies | 🔜 Planned |
| `dart_analyze` | Run static analysis (`dart analyze`) | 🔜 Planned |
| `dart_format` | Check/format code (`dart format`) | 🔜 Planned |
| `dart_doc` | Generate documentation (`dart doc`) | 🔜 Planned |
| `dart_pub_get` | Resolve dependencies (`dart pub get`) | 🔜 Planned |
| `dart_pub_publish` | Publish to pub.dev | 🔜 Planned |

## License

Apache 2.0 - See [LICENSE](../../LICENSE) for details.
