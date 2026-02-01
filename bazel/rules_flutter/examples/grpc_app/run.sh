#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# Easy runner script for the gRPC Flutter example
# Usage: ./run.sh [client|server|proxy|all|bazel]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Bazel workspace root (go up from examples/grpc_app)
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}Flutter gRPC Example${NC}                                         ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  bazel     Build with Bazel (recommended for CI/CD)"
    echo "  all       Run server, proxy, and client together"
    echo "  client    Run Flutter client (Chrome)"
    echo "  server    Run Dart gRPC server"
    echo "  proxy     Run gRPC-Web proxy (Docker or grpcwebproxy)"
    echo "  build     Build Flutter web release"
    echo "  setup     Install dependencies and generate proto files"
    echo "  clean     Clean generated files"
    echo ""
    echo "Bazel Commands (hermetic builds):"
    echo "  $0 bazel build     # Build all targets with Bazel"
    echo "  $0 bazel test      # Run tests with Bazel"
    echo "  $0 bazel run       # Run the app using Bazel"
    echo "  $0 bazel server    # Run gRPC server with Bazel"
    echo "  $0 bazel web       # Build web app with Bazel"
    echo ""
    echo "Regular Commands (uses Flutter SDK directly):"
    echo "  $0 setup    # First time setup"
    echo "  $0 all      # Run everything (server + proxy + client)"
    echo "  $0 server   # Start gRPC server only"
    echo "  $0 client   # Start Flutter client only"
    echo ""
}

check_flutter() {
    if ! command -v flutter &> /dev/null; then
        echo -e "${RED}Error: Flutter is not installed${NC}"
        echo "Install from: https://docs.flutter.dev/get-started/install"
        exit 1
    fi
}

check_dart() {
    if ! command -v dart &> /dev/null; then
        echo -e "${RED}Error: Dart is not installed${NC}"
        echo "Dart comes with Flutter. Make sure flutter/bin is in your PATH."
        exit 1
    fi
}

check_bazel() {
    if ! command -v bazel &> /dev/null; then
        echo -e "${RED}Error: Bazel is not installed${NC}"
        echo "Install from: https://bazel.build/install"
        exit 1
    fi
}

check_container_runtime() {
    # Check for Podman first (rootless preferred)
    if command -v podman &> /dev/null; then
        return 0
    fi
    
    # Check for Docker
    if command -v docker &> /dev/null; then
        return 0
    fi
    
    echo -e "${YELLOW}Warning: Neither Podman nor Docker is installed${NC}"
    echo "A container runtime is required for the gRPC-Web proxy."
    echo "Install Podman: https://podman.io/getting-started/installation"
    echo "Or Docker: https://docs.docker.com/get-docker/"
    return 1
}

# =============================================================================
# Bazel Commands
# =============================================================================

run_bazel() {
    check_bazel
    local SUBCOMMAND="${1:-build}"
    
    cd "$WORKSPACE_ROOT"
    
    case "$SUBCOMMAND" in
        build)
            echo -e "${GREEN}Building all targets with Bazel...${NC}"
            echo ""
            echo "Building gRPC server..."
            bazel build //examples/grpc_app/server:server
            echo ""
            echo "Building Flutter web app..."
            bazel build //examples/grpc_app:web_app
            echo ""
            echo -e "${GREEN}✅ Bazel build complete!${NC}"
            ;;
        test)
            echo -e "${GREEN}Running tests with Bazel...${NC}"
            bazel test //examples/grpc_app:all
            ;;
        run)
            echo -e "${GREEN}Running Flutter app with Bazel...${NC}"
            echo ""
            bazel run //examples/grpc_app:dev_server
            ;;
        server)
            echo -e "${GREEN}Running gRPC server with Bazel...${NC}"
            echo ""
            bazel run //examples/grpc_app/server:server
            ;;
        web)
            echo -e "${GREEN}Building web app with Bazel...${NC}"
            echo ""
            bazel build //examples/grpc_app:web_app
            echo ""
            echo "Output in bazel-bin/examples/grpc_app/web_app/"
            ;;
        all)
            echo -e "${GREEN}Building and running all components with Bazel...${NC}"
            echo ""
            
            # Build all targets first
            echo -e "${BLUE}[1/3] Building all targets...${NC}"
            bazel build //examples/grpc_app/...
            
            # Start server in background
            echo -e "${BLUE}[2/3] Starting gRPC server...${NC}"
            bazel run //examples/grpc_app/server:server &
            SERVER_PID=$!
            sleep 2
            
            # Trap to clean up
            cleanup() {
                echo ""
                echo -e "${YELLOW}Stopping services...${NC}"
                kill $SERVER_PID 2>/dev/null || true
                echo -e "${GREEN}Services stopped.${NC}"
            }
            trap cleanup EXIT
            
            # Start Flutter dev server
            echo -e "${BLUE}[3/3] Starting Flutter dev server...${NC}"
            bazel run //examples/grpc_app:dev_server
            ;;
        *)
            echo -e "${RED}Unknown Bazel subcommand: $SUBCOMMAND${NC}"
            echo "Valid subcommands: build, test, run, server, web, all"
            exit 1
            ;;
    esac
}

# =============================================================================
# Regular (Non-Bazel) Commands
# =============================================================================

run_setup() {
    echo -e "${GREEN}Setting up the gRPC Flutter example...${NC}"
    echo ""
    
    # Flutter dependencies
    echo -e "${BLUE}[1/4]${NC} Installing Flutter dependencies..."
    flutter pub get
    
    # Add platform support
    echo -e "${BLUE}[2/4]${NC} Adding platform support..."
    flutter create --platforms=web,macos,linux,windows . 2>/dev/null || true
    
    # Server dependencies
    echo -e "${BLUE}[3/4]${NC} Installing server dependencies..."
    cd server
    dart pub get
    cd ..
    
    # Generate proto files
    echo -e "${BLUE}[4/4]${NC} Generating proto files..."
    if command -v protoc &> /dev/null; then
        mkdir -p lib/generated server/lib/generated
        
        # Check if protoc-gen-dart is available
        if ! command -v protoc-gen-dart &> /dev/null; then
            echo "Installing protoc_plugin..."
            dart pub global activate protoc_plugin
        fi
        
        export PATH="$HOME/.pub-cache/bin:$PATH"
        protoc --dart_out=grpc:lib/generated -Iproto proto/helloworld.proto
        cp lib/generated/*.dart server/lib/generated/
        echo "Proto files generated!"
    else
        echo -e "${YELLOW}Warning: protoc not found. Using pre-generated files if available.${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run with Bazel (recommended): $0 bazel all"
    echo "  2. Or run manually: $0 all"
}

run_server() {
    echo -e "${GREEN}Starting Dart gRPC server...${NC}"
    echo ""
    cd server
    dart run bin/server.dart
}

run_client() {
    echo -e "${GREEN}Starting Flutter client on Chrome...${NC}"
    echo ""
    flutter run -d chrome
}

run_proxy() {
    echo -e "${GREEN}Starting gRPC-Web proxy...${NC}"
    echo ""
    
    cd proxy
    ./start_proxy.sh
}

run_all() {
    echo -e "${GREEN}Starting all components...${NC}"
    echo ""
    
    # Check if we have a proxy available
    HAS_PROXY=false
    if check_container_runtime; then
        HAS_PROXY=true
        echo "Container runtime detected for gRPC-Web proxy."
    elif command -v grpcwebproxy &> /dev/null; then
        HAS_PROXY=true
        echo "grpcwebproxy detected."
    else
        echo -e "${YELLOW}No proxy available. Web clients will need native gRPC support.${NC}"
        echo "";
    fi
    
    # Start server in background
    echo -e "${BLUE}[1/3] Starting gRPC server...${NC}"
    cd server
    dart run bin/server.dart &
    SERVER_PID=$!
    cd ..
    
    # Give server time to start
    sleep 2
    
    # Start proxy if available
    if $HAS_PROXY; then
        echo -e "${BLUE}[2/3] Starting gRPC-Web proxy...${NC}"
        cd proxy
        ./start_proxy.sh start &
        PROXY_PID=$!
        cd ..
        sleep 2
    else
        PROXY_PID=""
    fi
    
    # Trap to clean up background processes
    cleanup() {
        echo ""
        echo -e "${YELLOW}Stopping all services...${NC}"
        kill $SERVER_PID 2>/dev/null || true
        if [ -n "$PROXY_PID" ]; then
            kill $PROXY_PID 2>/dev/null || true
        fi
        docker stop grpc-web-proxy 2>/dev/null || true
        pkill -f grpcwebproxy 2>/dev/null || true
        echo -e "${GREEN}All services stopped.${NC}"
    }
    trap cleanup EXIT
    
    echo ""
    echo -e "${GREEN}All backend services running!${NC}"
    echo ""
    echo "  Server: grpc://localhost:50051"
    if $HAS_PROXY; then
        echo "  Proxy:  http://localhost:8080"
    fi
    echo ""
    
    # Start Flutter client
    echo -e "${BLUE}[3/3] Starting Flutter client...${NC}"
    echo ""
    flutter run -d chrome
}

run_clean() {
    echo -e "${YELLOW}Cleaning generated files...${NC}"
    
    rm -rf lib/generated server/lib/generated
    rm -rf build .dart_tool
    rm -rf android ios linux macos windows web
    
    docker stop grpc-web-proxy 2>/dev/null || true
    docker rm grpc-web-proxy 2>/dev/null || true
    
    # Also clean Bazel outputs if in workspace
    if [ -f "$WORKSPACE_ROOT/MODULE.bazel" ]; then
        echo "Cleaning Bazel outputs..."
        cd "$WORKSPACE_ROOT"
        bazel clean 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Clean complete${NC}"
}

run_build() {
    echo -e "${GREEN}Building Flutter web release...${NC}"
    echo ""
    
    flutter build web
    
    echo ""
    echo -e "${GREEN}✅ Build complete!${NC}"
    echo ""
    echo "Output: build/web/"
    echo ""
    
    # Start HTTP server and open browser
    echo -e "${BLUE}Starting web server...${NC}"
    cd build/web
    
    # Open browser based on OS
    PORT=8000
    URL="http://localhost:$PORT"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$URL" &
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$URL" 2>/dev/null &
    elif command -v start &> /dev/null; then
        start "$URL" &
    fi
    
    echo ""
    echo -e "${GREEN}Web server running at: $URL${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    
    python3 -m http.server $PORT
}

# Main
print_header

case "${1:-}" in
    bazel)
        run_bazel "${2:-build}"
        ;;
    client)
        check_flutter
        run_client
        ;;
    server)
        check_dart
        run_server
        ;;
    proxy)
        run_proxy
        ;;
    all)
        check_flutter
        check_dart
        run_all
        ;;
    setup)
        check_flutter
        check_dart
        run_setup
        ;;
    build)
        check_flutter
        run_build
        ;;
    clean)
        run_clean
        ;;
    -h|--help|help)
        print_usage
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
