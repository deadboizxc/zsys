#!/bin/bash
# TDLib installation script for zsys.telegram
# Downloads and builds TDLib library from source
set -e

TDLIB_VERSION="${TDLIB_VERSION:-1.8.29}"
TDLIB_DIR="${TDLIB_DIR:-/usr/local}"
BUILD_DIR="${BUILD_DIR:-/tmp/tdlib-build}"
JOBS="${JOBS:-$(nproc)}"

echo "=== TDLib Installer for zsys.telegram ==="
echo "Version: $TDLIB_VERSION"
echo "Install prefix: $TDLIB_DIR"
echo ""

check_deps() {
    local missing=()
    for cmd in cmake g++ git gperf; do
        if ! command -v $cmd &>/dev/null; then
            missing+=($cmd)
        fi
    done
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing dependencies: ${missing[*]}"
        echo ""
        echo "Install on Ubuntu/Debian:"
        echo "  sudo apt install cmake g++ git gperf libssl-dev zlib1g-dev"
        echo ""
        echo "Install on Fedora/RHEL:"
        echo "  sudo dnf install cmake gcc-c++ git gperf openssl-devel zlib-devel"
        echo ""
        echo "Install on macOS:"
        echo "  brew install cmake gperf openssl"
        exit 1
    fi
}

download_tdlib() {
    echo ">>> Downloading TDLib $TDLIB_VERSION..."
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    git clone --depth 1 --branch "v$TDLIB_VERSION" https://github.com/tdlib/td.git
    cd td
}

build_tdlib() {
    echo ">>> Building TDLib..."
    mkdir -p build && cd build
    cmake .. \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$TDLIB_DIR" \
        -DTD_ENABLE_LTO=ON
    cmake --build . --target install -j "$JOBS"
}

verify_install() {
    echo ">>> Verifying installation..."
    if [ -f "$TDLIB_DIR/lib/libtdjson.so" ] || [ -f "$TDLIB_DIR/lib/libtdjson.dylib" ]; then
        echo "✓ TDLib installed successfully!"
        echo ""
        echo "Library location:"
        ls -la "$TDLIB_DIR/lib/libtdjson"* 2>/dev/null || true
        echo ""
        echo "For zsys.telegram, set:"
        echo "  export TDLIB_PATH=$TDLIB_DIR/lib"
        echo ""
        echo "Or add to ~/.bashrc / ~/.zshrc"
    else
        echo "✗ Installation failed - library not found"
        exit 1
    fi
}

cleanup() {
    echo ">>> Cleaning up..."
    rm -rf "$BUILD_DIR"
}

main() {
    check_deps
    download_tdlib
    build_tdlib
    verify_install
    cleanup
    echo "=== Done! ==="
}

case "${1:-install}" in
    install)
        main
        ;;
    check)
        check_deps
        echo "All dependencies satisfied"
        ;;
    clean)
        cleanup
        echo "Cleaned build directory"
        ;;
    *)
        echo "Usage: $0 [install|check|clean]"
        exit 1
        ;;
esac
