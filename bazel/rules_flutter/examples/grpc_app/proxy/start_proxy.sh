#!/bin/bash
# Copyright 2026 Google LLC
# SPDX-License-Identifier: Apache-2.0

# gRPC-Web Proxy startup script
# Supports Podman (preferred), Docker, and standalone grpcwebproxy
# Auto-installs and configures Podman on macOS if needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

GRPC_BACKEND_HOST="${GRPC_BACKEND_HOST:-localhost}"
GRPC_BACKEND_PORT="${GRPC_BACKEND_PORT:-50051}"
PROXY_PORT="${PROXY_PORT:-8080}"
CONTAINER_NAME="grpc-web-proxy"

# Container runtime detection
CONTAINER_RUNTIME=""

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  ${GREEN}gRPC-Web Proxy${NC}                                               ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

install_podman() {
    echo -e "${BLUE}Installing Podman...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            echo "Installing Podman via Homebrew..."
            brew install podman
            return 0
        else
            echo -e "${RED}Error: Homebrew is required to install Podman on macOS${NC}"
            echo "Install Homebrew from: https://brew.sh"
            return 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            echo "Installing Podman via apt..."
            sudo apt-get update && sudo apt-get install -y podman
            return 0
        elif command -v dnf &> /dev/null; then
            echo "Installing Podman via dnf..."
            sudo dnf install -y podman
            return 0
        elif command -v yum &> /dev/null; then
            echo "Installing Podman via yum..."
            sudo yum install -y podman
            return 0
        fi
    fi
    
    echo -e "${RED}Error: Cannot auto-install Podman on this system${NC}"
    echo "Install manually from: https://podman.io/getting-started/installation"
    return 1
}

ensure_podman_machine() {
    # On macOS/Windows, Podman needs a VM
    if [[ "$OSTYPE" != "darwin"* ]] && [[ "$OSTYPE" != "msys"* ]] && [[ "$OSTYPE" != "cygwin"* ]]; then
        # Linux doesn't need a machine
        return 0
    fi
    
    echo -e "${BLUE}Checking Podman machine...${NC}"
    
    # Check if any machine exists
    local machine_count
    machine_count=$(podman machine list --format "{{.Name}}" 2>/dev/null | wc -l | tr -d ' ')
    
    if [[ "$machine_count" == "0" ]]; then
        echo "No Podman machine found. Initializing..."
        podman machine init --cpus 2 --memory 2048 --disk-size 20
    fi
    
    # Check if machine is running
    local machine_status
    machine_status=$(podman machine list --format "{{.Running}}" 2>/dev/null | head -1)
    
    if [[ "$machine_status" != "true" ]] && [[ "$machine_status" != "Running" ]]; then
        echo "Starting Podman machine..."
        podman machine start
        
        # Wait for machine to be ready
        echo "Waiting for Podman machine to be ready..."
        local retries=30
        while ! podman info &> /dev/null && [[ $retries -gt 0 ]]; do
            sleep 1
            ((retries--))
        done
        
        if ! podman info &> /dev/null; then
            echo -e "${RED}Error: Podman machine failed to start${NC}"
            return 1
        fi
    fi
    
    echo -e "${GREEN}Podman machine is running${NC}"
    return 0
}

detect_container_runtime() {
    # Check for Podman first (rootless preferred)
    if command -v podman &> /dev/null; then
        CONTAINER_RUNTIME="podman"
        return 0
    fi
    
    # Check for Docker
    if command -v docker &> /dev/null; then
        CONTAINER_RUNTIME="docker"
        return 0
    fi
    
    return 1
}

check_grpcwebproxy() {
    command -v grpcwebproxy &> /dev/null
}

install_grpcwebproxy() {
    echo -e "${BLUE}Installing grpcwebproxy...${NC}"
    
    if command -v go &> /dev/null; then
        echo "Installing via Go..."
        go install github.com/nicksherron/grpcwebproxy@latest
        if ! check_grpcwebproxy; then
            # Try adding GOPATH/bin to PATH
            export PATH="$PATH:$(go env GOPATH)/bin"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install grpcwebproxy 2>/dev/null || {
                echo -e "${YELLOW}Homebrew formula not found. Trying Go install...${NC}"
                if command -v go &> /dev/null; then
                    go install github.com/nicksherron/grpcwebproxy@latest
                else
                    echo -e "${RED}Error: Go is required to install grpcwebproxy${NC}"
                    return 1
                fi
            }
        fi
    else
        echo -e "${RED}Error: Cannot auto-install grpcwebproxy${NC}"
        echo "Install manually:"
        echo "  go install github.com/nicksherron/grpcwebproxy@latest"
        return 1
    fi
}

run_container_proxy() {
    local runtime="$1"
    echo -e "${GREEN}Starting Envoy gRPC-Web proxy ($runtime)...${NC}"
    echo ""
    
    cd "$SCRIPT_DIR"
    
    # For Podman on macOS/Windows, ensure machine is running
    if [[ "$runtime" == "podman" ]]; then
        ensure_podman_machine || return 1
    fi
    
    # Stop existing container if running
    $runtime stop "$CONTAINER_NAME" 2>/dev/null || true
    $runtime rm "$CONTAINER_NAME" 2>/dev/null || true
    
    # Build run command
    local run_args="-d --name $CONTAINER_NAME"
    run_args+=" -v $SCRIPT_DIR/envoy.yaml:/etc/envoy/envoy.yaml:ro"
    run_args+=" -p $PROXY_PORT:$PROXY_PORT -p 9901:9901"
    
    # Add host networking for backend access
    if [[ "$runtime" == "podman" ]]; then
        # Podman uses host-gateway for host.containers.internal
        run_args+=" --add-host=host.docker.internal:host-gateway"
    else
        # Docker uses host.docker.internal
        run_args+=" --add-host=host.docker.internal:host-gateway"
    fi
    
    $runtime run $run_args envoyproxy/envoy:distroless-v1.28-latest -c /etc/envoy/envoy.yaml
    
    echo ""
    echo -e "${GREEN}✅ Envoy proxy started with $runtime!${NC}"
    echo ""
    echo "Endpoints:"
    echo "  gRPC-Web Proxy: http://localhost:$PROXY_PORT"
    echo "  Envoy Admin:    http://localhost:9901"
}

run_grpcwebproxy() {
    echo -e "${GREEN}Starting grpcwebproxy (standalone)...${NC}"
    echo ""
    echo "Backend: $GRPC_BACKEND_HOST:$GRPC_BACKEND_PORT"
    echo "Proxy:   http://localhost:$PROXY_PORT"
    echo ""
    
    grpcwebproxy \
        --backend_addr="$GRPC_BACKEND_HOST:$GRPC_BACKEND_PORT" \
        --run_tls_server=false \
        --allow_all_origins \
        --server_http_debug_port="$PROXY_PORT"
}

stop_proxy() {
    echo -e "${YELLOW}Stopping gRPC-Web proxy...${NC}"
    
    # Stop Podman container
    podman stop "$CONTAINER_NAME" 2>/dev/null || true
    podman rm "$CONTAINER_NAME" 2>/dev/null || true
    
    # Stop Docker container
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    
    # Kill grpcwebproxy if running
    pkill -f grpcwebproxy 2>/dev/null || true
    
    echo -e "${GREEN}✅ Proxy stopped${NC}"
}

print_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start      Start the proxy (auto-installs Podman if needed)"
    echo "  podman     Force Podman mode (installs if needed)"
    echo "  docker     Force Docker mode"
    echo "  standalone Force grpcwebproxy mode"
    echo "  stop       Stop the proxy"
    echo "  install    Install Podman and configure machine"
    echo ""
    echo "Environment variables:"
    echo "  GRPC_BACKEND_HOST  gRPC backend host (default: localhost)"
    echo "  GRPC_BACKEND_PORT  gRPC backend port (default: 50051)"
    echo "  PROXY_PORT         Proxy listen port (default: 8080)"
    echo ""
}

# Main
print_header

case "${1:-start}" in
    start)
        if detect_container_runtime; then
            echo "$CONTAINER_RUNTIME detected."
            run_container_proxy "$CONTAINER_RUNTIME"
        elif check_grpcwebproxy; then
            echo "grpcwebproxy detected. Using standalone mode."
            run_grpcwebproxy
        else
            echo -e "${YELLOW}No container runtime found. Installing Podman...${NC}"
            if install_podman; then
                run_container_proxy "podman"
            else
                echo ""
                echo "Alternatives:"
                echo "  1. Install Podman: https://podman.io/getting-started/installation"
                echo "  2. Install Docker: https://docs.docker.com/get-docker/"
                echo "  3. Install grpcwebproxy: $0 install-grpcwebproxy"
                echo ""
                exit 1
            fi
        fi
        ;;
    podman)
        if ! command -v podman &> /dev/null; then
            echo -e "${YELLOW}Podman not found. Installing...${NC}"
            install_podman || exit 1
        fi
        run_container_proxy "podman"
        ;;
    docker)
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Error: Docker is not installed${NC}"
            echo "Install from: https://docs.docker.com/get-docker/"
            exit 1
        fi
        run_container_proxy "docker"
        ;;
    standalone)
        if ! check_grpcwebproxy; then
            echo -e "${YELLOW}grpcwebproxy not found. Attempting install...${NC}"
            install_grpcwebproxy || exit 1
        fi
        run_grpcwebproxy
        ;;
    stop)
        stop_proxy
        ;;
    install)
        if ! command -v podman &> /dev/null; then
            install_podman || exit 1
        fi
        ensure_podman_machine
        echo -e "${GREEN}✅ Podman is ready!${NC}"
        ;;
    install-grpcwebproxy)
        install_grpcwebproxy
        ;;
    -h|--help|help)
        print_usage
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
