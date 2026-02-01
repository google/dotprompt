# Contributing to rules_flutter

Thank you for your interest in contributing to `rules_flutter`!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/google/rules_flutter.git
   cd rules_flutter
   ```

2. Run the tests:
   ```bash
   # Unix (macOS/Linux)
   ./scripts/test_examples.sh

   # Windows
   scripts\test_examples.bat
   ```

## Code Style

- Follow Starlark best practices
- Use descriptive function and variable names
- Add comprehensive docstrings to all public functions
- Include ASCII diagrams for complex logic

## Package Organization

```
rules_flutter/
├── defs.bzl              # Public API - all user-facing rules
├── flutter.bzl           # Core Flutter rules implementation
├── extensions.bzl        # Bzlmod extensions for SDK configuration
├── repositories.bzl      # SDK download and repository rules
├── MODULE.bazel          # Bzlmod module definition
├── BUILD.bazel           # Package definition
│
├── private/              # Internal implementation (NOT public API)
│   ├── helpers.bzl       # Common utilities
│   └── workers.bzl       # Persistent worker support
│
├── toolchains/           # Flutter toolchain definitions
│   ├── toolchain.bzl     # Toolchain rules
│   └── BUILD.bazel       # Toolchain declarations
│
├── workers/              # Persistent workers for accelerated builds
│   ├── protocol.dart     # Worker protocol implementation
│   ├── hot_reload_worker.dart
│   └── analyzer_worker.dart
│
├── examples/             # Working examples for testing
│   ├── hello_world/      # Basic Flutter app example
│   └── grpc_app/         # gRPC application example
│
└── scripts/              # CI and testing scripts
    ├── test_examples.sh  # Unix test runner
    └── test_examples.bat # Windows test runner
```

### Key Files

| File | Purpose |
|------|---------|
| `defs.bzl` | Entry point for users - `load("@rules_flutter//:defs.bzl", ...)` |
| `flutter.bzl` | Core Flutter rules (flutter_library, flutter_binary, etc.) |
| `repositories.bzl` | SDK version checksums and download logic |
| `private/*.bzl` | Platform-specific script generation (internal) |

## Testing

### Local Testing

Run the full test suite locally:

```bash
# Unix (macOS/Linux)
./scripts/test_examples.sh

# Windows
scripts\test_examples.bat
```

The test scripts verify:
1. ✅ All rules build successfully
2. ✅ Flutter build targets work (web, android, ios, etc.)
3. ✅ Unit tests pass
4. ✅ CI checks (format, analyze) pass
5. ✅ Hot reload worker functions correctly

### CI Testing

CI runs tests on all platforms:

| Platform | Tested Architectures |
|----------|---------------------|
| Windows | x64 |
| macOS | x64, arm64 |
| Linux | x64, arm64 |

Make sure your changes pass on all platforms before submitting a PR.

## Testing Requirements

All changes must:

1. **Pass on all platforms**: Windows, macOS, and Linux
2. **Include tests**: Add test coverage for new rules
3. **Update documentation**: Keep README.md and GEMINI.md current

### Test Scripts

Both Unix (.sh) and Windows (.bat) test scripts must exist and test the same functionality:

| Script | Platform |
|--------|----------|
| `scripts/test_examples.sh` | macOS, Linux |
| `scripts/test_examples.bat` | Windows |

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes
4. Run all tests on your platform
5. Commit with a descriptive message following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat(rules_flutter): add flutter_widget_test rule

   Adds a new rule for widget testing with golden tests support.

   - Supports all platforms
   - Includes comprehensive tests
   ```
6. Push to your fork and open a Pull Request

### PR Description Guidelines

Include in your PR description:

- **Summary**: What does this change do?
- **Tables**: Feature support, test results
- **Diagrams**: ASCII diagrams for architecture changes
- **Test Results**: Platform-specific test outcomes

Example:

```markdown
## Summary

Adds support for Flutter widget testing with golden tests.

## Changes

| Feature | Before | After |
|---------|--------|-------|
| flutter_widget_test | ❌ | ✅ |
| golden_test support | ❌ | ✅ |

## Test Results

| Platform | Build | Tests |
|----------|-------|-------|
| macOS arm64 | ✅ | ✅ |
| Linux x64 | ✅ | ✅ |
| Windows x64 | ✅ | ✅ |
```

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## Adding a New Flutter SDK Version

When a new Flutter SDK is released, you can contribute support for it:

### 1. Get the Checksums

Download the SDK archives and compute SHA256 checksums:

```bash
# For each platform
VERSION="3.27.0"

# Linux
curl -L "https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${VERSION}-stable.tar.xz" -o flutter-linux.tar.xz
shasum -a 256 flutter-linux.tar.xz

# macOS
curl -L "https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_${VERSION}-stable.zip" -o flutter-macos.zip
shasum -a 256 flutter-macos.zip

# Windows
curl -L "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_${VERSION}-stable.zip" -o flutter-windows.zip
shasum -a 256 flutter-windows.zip
```

Or use the official checksums from https://docs.flutter.dev/release/archive.

### 2. Update repositories.bzl

Add the new version to `FLUTTER_SDK_VERSIONS`:

```python
FLUTTER_SDK_VERSIONS = {
    # Existing versions...
    "3.26.0": { ... },
    
    # Add new version
    "3.27.0": {
        "linux-x64": "sha256-CHECKSUM_HERE",
        "macos-x64": "sha256-CHECKSUM_HERE",
        "macos-arm64": "sha256-CHECKSUM_HERE",
        "windows-x64": "sha256-CHECKSUM_HERE",
    },
}
```

### 3. Update Files

| File | Update |
|------|--------|
| `repositories.bzl` | Add checksums in `FLUTTER_SDK_VERSIONS` |
| `extensions.bzl` | Update default version if this is the new stable |
| `examples/*/MODULE.bazel` | Update example version references |
| `README.md` | Update Quick Start version if needed |
| `CHANGELOG.md` | Add entry for new SDK support |

### 4. Test

Run tests with the new SDK version:

```bash
# Unix
./scripts/test_examples.sh

# Windows
scripts\test_examples.bat
```

### 5. Submit PR

Use the commit format:

```
feat(rules_flutter): add Flutter SDK 3.27.0 support

Adds checksums for Flutter SDK 3.27.0 across all platforms.

- linux-x64
- macos-x64
- macos-arm64
- windows-x64
```

## Getting Help

- Read [GEMINI.md](GEMINI.md) for development guidelines
- File issues for bugs or feature requests
- Ask questions in discussions

## Code of Conduct

This project follows Google's [Open Source Community Guidelines](https://opensource.google/conduct/).
Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for more details.

## Security

Please read [SECURITY.md](SECURITY.md) for information on reporting security vulnerabilities.
