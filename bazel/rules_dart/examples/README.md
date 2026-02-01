# rules_dart Examples

This directory contains working examples demonstrating various `rules_dart` features.

## Examples

| Directory | Features Demonstrated |
|-----------|----------------------|
| [hello_world](hello_world/) | Basic rules: dart_library, dart_binary, dart_test, dart_native_binary |
| [proto_example](proto_example/) | Protocol Buffers and gRPC code generation |
| [freezed_example](freezed_example/) | build_runner integration for freezed/json_serializable |

## Running Examples

Each example is a self-contained Bazel project. Navigate to the example directory and run:

```bash
# Build all targets
bazel build //...

# Run tests
bazel test //...

# Run binaries
bazel run //:app_name
```

## hello_world

Basic Dart compilation and testing:

```bash
cd hello_world
bazel build //:hello_native  # Native binary
bazel test //:hello_test     # Unit tests
bazel run //:hello_native    # Run the binary
```

## proto_example

Protocol Buffers and gRPC code generation:

```bash
cd proto_example
bazel build //:user_dart_proto  # Generate proto messages
bazel build //:user_dart_grpc   # Generate gRPC stubs
bazel build //:client           # Build gRPC client
bazel build //:server           # Build gRPC server
```

**Generated files:**
- `user.pb.dart` - Proto messages
- `user.pbenum.dart` - Proto enums
- `user.pbjson.dart` - JSON serialization
- `user.pbgrpc.dart` - gRPC service stubs

## freezed_example

build_runner integration for code generation:

```bash
cd freezed_example
bazel build //:generated    # Run build_runner
bazel build //:models       # Library with generated code
bazel run //:example        # Run example
```

**Generated files:**
- `user.freezed.dart` - Immutable classes, copyWith, ==, hashCode
- `user.g.dart` - JSON serialization (json_serializable)

## Creating New Examples

1. Create a new directory under `examples/`
2. Add `MODULE.bazel`:
   ```python
   module(name = "my_example", version = "0.1.0")
   
   bazel_dep(name = "rules_dart")
   local_path_override(module_name = "rules_dart", path = "../..")
   
   dart = use_extension("@rules_dart//:extensions.bzl", "dart")
   dart.configure(version = "3.7.0")
   use_repo(dart, "dart_sdk")
   ```
3. Add `BUILD.bazel` with your targets
4. Add `pubspec.yaml` with dependencies
