#!/usr/bin/env bash
# install_tdlib.sh — build TDLib from source and install into zsys/telegram/tdlib/c/tdlib/
#
# Usage:
#   ./scripts/install_tdlib.sh                  # build + install to ./tdlib/
#   TDLIB_VERSION=v1.8.29 ./scripts/install_tdlib.sh
#   TDLIB_INSTALL_PREFIX=/usr/local ./scripts/install_tdlib.sh
#
# After this, libtg CMakeLists.txt finds TDLib automatically via:
#   -DTDLIB_DIR=zsys/telegram/tdlib/c/tdlib
#
# Dependencies (Ubuntu/Debian):
#   sudo apt install -y cmake g++ libssl-dev zlib1g-dev gperf
# Dependencies (Arch):
#   sudo pacman -S cmake gcc openssl zlib gperf
# Dependencies (macOS):
#   brew install cmake openssl gperf

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZSYS_DIR="$(dirname "$SCRIPT_DIR")"
TDLIB_C_DIR="$ZSYS_DIR/zsys/telegram/tdlib/c"

TDLIB_VERSION="${TDLIB_VERSION:-v1.8.29}"
TDLIB_SRC_DIR="$TDLIB_C_DIR/tdlib-src"
TDLIB_BUILD_DIR="$TDLIB_C_DIR/tdlib-build"
TDLIB_INSTALL_PREFIX="${TDLIB_INSTALL_PREFIX:-$TDLIB_C_DIR/tdlib}"
JOBS="${JOBS:-$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)}"

echo "╔══════════════════════════════════════════════╗"
echo "║       TDLib build for zsys.telegram.tdlib    ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Version : $TDLIB_VERSION"
echo "  Source  : $TDLIB_SRC_DIR"
echo "  Install : $TDLIB_INSTALL_PREFIX"
echo "  Jobs    : $JOBS"
echo ""

# ── check deps ───────────────────────────────────────────────────────────────
for cmd in cmake git g++ openssl; do
    command -v "$cmd" >/dev/null 2>&1 || {
        echo "❌ Missing: $cmd"
        echo "   Ubuntu:  sudo apt install cmake g++ libssl-dev zlib1g-dev gperf"
        echo "   Arch:    sudo pacman -S cmake gcc openssl zlib gperf"
        echo "   macOS:   brew install cmake openssl gperf"
        exit 1
    }
done

# ── clone ─────────────────────────────────────────────────────────────────────
if [ ! -d "$TDLIB_SRC_DIR/.git" ]; then
    echo "📥 Cloning TDLib $TDLIB_VERSION..."
    git clone --depth 1 --branch "$TDLIB_VERSION" \
        https://github.com/tdlib/td.git "$TDLIB_SRC_DIR"
else
    echo "✅ Source already cloned at $TDLIB_SRC_DIR"
fi

# ── configure ────────────────────────────────────────────────────────────────
echo ""
echo "⚙️  Configuring..."
mkdir -p "$TDLIB_BUILD_DIR"
cmake -S "$TDLIB_SRC_DIR" -B "$TDLIB_BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$TDLIB_INSTALL_PREFIX" \
    -DTD_ENABLE_JNI=OFF \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON

# ── build ─────────────────────────────────────────────────────────────────────
echo ""
echo "🔨 Building with $JOBS jobs (this takes 5-20 min)..."
cmake --build "$TDLIB_BUILD_DIR" --target tdjson_static --parallel "$JOBS"

# ── install ───────────────────────────────────────────────────────────────────
echo ""
echo "📦 Installing to $TDLIB_INSTALL_PREFIX..."
cmake --install "$TDLIB_BUILD_DIR" --component development

echo ""
echo "✅ TDLib installed to: $TDLIB_INSTALL_PREFIX"
echo ""
echo "Now build libtg:"
echo "  make build-telegram"
echo "  # or:"
echo "  cmake -B zsys/telegram/tdlib/c/build zsys/telegram/tdlib/c \\"
echo "        -DTDLIB_DIR=$TDLIB_INSTALL_PREFIX"
echo "  cmake --build zsys/telegram/tdlib/c/build --target tg"
