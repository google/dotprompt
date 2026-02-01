# Changelog

## [0.1.0](https://github.com/google/dotprompt/releases/tag/rules_flutter-0.1.0) (2026-02-01)

### Features

* **flutter_library**: Reusable Flutter library rule with asset support
* **flutter_binary**: Development mode runner with hot-reload support
* **flutter_test**: Widget and unit test rule with shard_count support
* **flutter_application**: Production build rule for all platforms:
  * Android (APK and App Bundle)
  * iOS
  * Web
  * macOS
  * Linux
  * Windows
* **Hermetic SDK**: Automatic Flutter SDK download with platform detection
* **Local SDK support**: Use local Flutter SDK via `sdk_home` attribute
* **Channel selection**: stable, beta, dev, master channels
* **Cross-platform**: Native scripts for Windows (.bat) and Unix (.sh)

### Examples

* **grpc_app**: Flutter gRPC client with Dart server demonstrating:
  * Material 3 UI
  * gRPC connectivity
  * Multi-platform builds

### Documentation

* README with quick start guide
* ROADMAP with feature parity tracking
* GEMINI.md with development guidelines
