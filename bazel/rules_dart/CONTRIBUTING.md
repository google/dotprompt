# Contributing to rules_dart

Thank you for your interest in contributing to `rules_dart`!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/google/rules_dart.git
   cd rules_dart
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
rules_dart/
├── defs.bzl              # Public API - all user-facing rules
├── extensions.bzl        # Bzlmod extensions for SDK configuration
├── repositories.bzl      # SDK download and repository rules
├── MODULE.bazel          # Bzlmod module definition
├── BUILD.bazel           # Package definition
│
├── private/              # Internal implementation (NOT public API)
│   ├── helpers.bzl       # Common utilities (runfiles_path, is_windows, etc.)
│   ├── windows.bzl       # Windows .bat script generators
│   └── unix.bzl          # Unix .sh script generators
│
├── gazelle/              # Gazelle extension for BUILD file generation
│   ├── dart_language.go  # Language interface implementation
│   ├── dart_generate.go  # BUILD file generation logic
│   └── dart_resolve.go   # Dependency resolution
│
├── examples/             # Working examples for testing
│   └── hello_world/      # Complete example project
│
└── scripts/              # CI and testing scripts
    ├── test_examples.sh  # Unix test runner
    └── test_examples.bat # Windows test runner
```

### Key Files

| File | Purpose |
|------|---------|
| `defs.bzl` | Entry point for users - `load("@rules_dart//:defs.bzl", ...)` |
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
2. ✅ Compilation targets (native, js, wasm, aot) work
3. ✅ Pub commands (get, publish) work
4. ✅ Unit tests pass
5. ✅ CI checks (format, analyze) pass
6. ✅ Native binary executes correctly

### Testing in the hello_world Example

```bash
cd examples/hello_world

# Build all targets
bazel build //...

# Run tests
bazel test //...

# Run specific targets
bazel run //:hello_native
bazel run //:hello_pub_get
```

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
   feat(rules_dart): add dart_compile rule

   Adds a new compilation rule for custom output formats.

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

Adds support for custom compilation targets.

## Changes

| Feature | Before | After |
|---------|--------|-------|
| dart_compile | ❌ | ✅ |

## Test Results

| Platform | Build | Tests |
|----------|-------|-------|
| macOS arm64 | ✅ | ✅ |
| Linux x64 | ✅ | ✅ |
| Windows x64 | ✅ | ✅ |
```

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## Adding a New Dart SDK Version

When a new Dart SDK is released, you can contribute support for it:

### 1. Get the Checksums

Download the SDK archives and compute SHA256 checksums:

```bash
# For each platform (linux-x64, linux-arm64, macos-x64, macos-arm64, windows-x64)
VERSION="3.8.0"

# Linux x64
curl -L "https://storage.googleapis.com/dart-archive/channels/stable/release/${VERSION}/sdk/dartsdk-linux-x64-release.zip" -o dart-linux-x64.zip
shasum -a 256 dart-linux-x64.zip

# Linux arm64
curl -L "https://storage.googleapis.com/dart-archive/channels/stable/release/${VERSION}/sdk/dartsdk-linux-arm64-release.zip" -o dart-linux-arm64.zip
shasum -a 256 dart-linux-arm64.zip

# macOS x64
curl -L "https://storage.googleapis.com/dart-archive/channels/stable/release/${VERSION}/sdk/dartsdk-macos-x64-release.zip" -o dart-macos-x64.zip
shasum -a 256 dart-macos-x64.zip

# macOS arm64
curl -L "https://storage.googleapis.com/dart-archive/channels/stable/release/${VERSION}/sdk/dartsdk-macos-arm64-release.zip" -o dart-macos-arm64.zip
shasum -a 256 dart-macos-arm64.zip

# Windows x64
curl -L "https://storage.googleapis.com/dart-archive/channels/stable/release/${VERSION}/sdk/dartsdk-windows-x64-release.zip" -o dart-windows-x64.zip
shasum -a 256 dart-windows-x64.zip
```

Or use the official checksums from https://dart.dev/get-dart/archive.

### 2. Update repositories.bzl

Add the new version to `DART_SDK_VERSIONS`:

```python
DART_SDK_VERSIONS = {
    # Existing versions...
    "3.7.0": { ... },
    
    # Add new version
    "3.8.0": {
        "linux-x64": "sha256-CHECKSUM_HERE",
        "linux-arm64": "sha256-CHECKSUM_HERE",
        "macos-x64": "sha256-CHECKSUM_HERE",
        "macos-arm64": "sha256-CHECKSUM_HERE",
        "windows-x64": "sha256-CHECKSUM_HERE",
    },
}
```

### 3. Update Files

| File | Update |
|------|--------|
| `repositories.bzl` | Add checksums in `DART_SDK_VERSIONS` |
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
feat(rules_dart): add Dart SDK 3.8.0 support

Adds checksums for Dart SDK 3.8.0 across all platforms.

- linux-x64
- linux-arm64
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

