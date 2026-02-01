# Flutter gRPC Client Example

A cross-platform Flutter app that demonstrates gRPC connectivity with a Dart server.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                Architecture                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Flutter Client              Envoy Proxy              Dart gRPC Server              │
│  (lib/main.dart)             (gRPC-Web)               (server/bin/server.dart)      │
│  ┌──────────────────┐       ┌────────────┐           ┌────────────────────────┐    │
│  │  Material 3 UI   │       │            │           │  gRPC Service          │    │
│  │  ├── Host input  │       │            │           │  ├── SayHello          │    │
│  │  ├── Port input  │──────▶│  :8080     │──────────▶│  ├── SayHelloAgain     │    │
│  │  ├── Name input  │ HTTP  │ gRPC-Web   │  HTTP/2   │  └── SayHelloStream    │    │
│  │  ├── Say Hello   │◀──────│ to gRPC    │◀──────────│                        │    │
│  │  └── Stream      │       │            │           │  Port: 50051           │    │
│  └──────────────────┘       └────────────┘           └────────────────────────┘    │
│                                                                                     │
│  Web Browser (Chrome)        Docker/Envoy             Pure Dart                     │
│  Native: Direct gRPC ────────────────────────────────▶ (skip proxy)                │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```


## Quick Start

### Easy Way (run.sh)

```bash
cd bazel/rules_flutter/examples/grpc_app

# First time setup
./run.sh setup

# Terminal 1: Start the gRPC server
./run.sh server

# Terminal 2: Start the Flutter client
./run.sh client

# Or run everything at once
./run.sh all
```

### Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) (3.0+)
- [Dart SDK](https://dart.dev/get-dart) (3.0+)
- [Podman](https://podman.io/getting-started/installation) or [Docker](https://docs.docker.com/get-docker/) (optional, for gRPC-Web proxy)

### Manual Setup

```bash
cd bazel/rules_flutter/examples/grpc_app

# Get dependencies
flutter pub get

# Add platform support (first time only)
flutter create --platforms=web,macos,linux,windows,android,ios .
```

### 2. Run the Flutter Client

```bash
# Web (easiest to test)
flutter run -d chrome

# macOS desktop
flutter run -d macos

# Linux desktop
flutter run -d linux

# Windows desktop (on Windows)
flutter run -d windows

# Android (with emulator or device connected)
flutter run

# iOS (on macOS with Xcode)
flutter run -d ios
```

### 3. Start the gRPC Server

```bash
# In a separate terminal
cd server
dart pub get
dart run bin/server.dart
```

### 4. (For Web) Start the gRPC-Web Proxy

Web browsers cannot make direct gRPC calls due to HTTP/2 limitations.
You need an Envoy proxy to translate gRPC-Web to gRPC:

```bash
# Requires Docker
cd proxy
./start_proxy.sh
```

Or manually with Docker:

```bash
docker run -d --name grpc-web-proxy \
    -v $(pwd)/proxy/envoy.yaml:/etc/envoy/envoy.yaml:ro \
    -p 8080:8080 -p 9901:9901 \
    --add-host=host.docker.internal:host-gateway \
    envoyproxy/envoy:v1.28-latest
```

Then in the Flutter app, connect to:
- **Host**: `localhost`
- **Port**: `8080`
- **Use gRPC-Web**: ✅ Enabled

### Native Platforms (No Proxy Needed)

For native platforms (macOS, Linux, Windows, iOS, Android), you can connect
directly to the gRPC server on port 50051. Toggle off "Use gRPC-Web" in the app.


## Using the App

1. **Server Address**: Enter the gRPC server address (default: `localhost:50051`)
2. **Your Name**: Enter your name
3. **Say Hello**: Click to send a unary gRPC request
4. **Say Hello Again**: Click for another greeting
5. **Stream**: Click to receive a stream of 5 messages

## Interactive Commands (Development Mode)

While `flutter run` is active:

| Key | Action |
|-----|--------|
| `r` | Hot reload (apply code changes) |
| `R` | Hot restart |
| `q` | Quit the app |
| `d` | Detach (keep app running) |

## Building Production Releases

```bash
# Android APK
flutter build apk

# Android App Bundle (for Play Store)
flutter build appbundle

# iOS (macOS only)
flutter build ios

# Web
flutter build web

# macOS
flutter build macos

# Linux
flutter build linux

# Windows
flutter build windows
```

## Using Bazel (Alternative)

If you want to use Bazel instead of the Flutter CLI:

```bash
# Development mode
bazel run //:dev

# Build for specific platforms
bazel run //:client_web
bazel run //:client_macos
bazel run //:client_android
bazel run //:client_linux
bazel run //:client_windows
bazel run //:client_ios
```

## Project Structure

```
grpc_app/
├── BUILD.bazel           # Bazel build rules
├── MODULE.bazel          # Bazel module configuration
├── pubspec.yaml          # Flutter dependencies
├── lib/
│   ├── main.dart         # Flutter app with Material 3 UI
│   └── generated/        # Generated proto files (gitignored)
├── proto/
│   └── helloworld.proto  # gRPC service definition
├── test/
│   └── widget_test.dart  # Widget tests
├── server/
│   ├── pubspec.yaml      # Server dependencies
│   ├── lib/generated/    # Generated proto files (gitignored)
│   └── bin/
│       └── server.dart   # Dart gRPC server
├── proxy/
│   ├── envoy.yaml        # Envoy gRPC-Web proxy config
│   ├── docker-compose.yaml
│   └── start_proxy.sh    # Start script
└── (platform dirs)       # Generated by flutter create (gitignored)
```

## Troubleshooting

### "This application is not configured to build on the web"

Run `flutter create .` to add missing platform files.

### Java/Gradle version conflict (Android)

See the Flutter output message for compatible versions, or run:
```bash
flutter config --jdk-dir=/path/to/jdk17
```

### gRPC connection failed

Ensure the server is running on the correct port:
```bash
cd server && dart run bin/server.dart
```

## License

Apache 2.0 - See [LICENSE](../../../../LICENSE)
