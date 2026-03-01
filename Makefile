# =============================================================================
# zsys — Makefile
# =============================================================================
# Targets:
#   make              — build everything (C lib + Python extension)
#   make build-c      — build pure C shared library (libzsys_core.so)
#   make build-lib    — build universal libzsys.so (router + registry + i18n)
#   make build-py     — build Python C extension (_zsys_core.so)
#   make build-go     — check Go bindings compile
#   make test         — run Python test suite
#   make test-c       — run C library tests (via CMake CTest)
#   make install      — install Python package (editable)
#   make install-c    — install C library system-wide (needs sudo)
#   make clean        — remove all build artifacts
#   make docs         — build HTML docs (requires pdoc)
#   make fmt          — auto-format Python code (ruff + black)
#   make lint         — lint Python code (ruff + mypy)
#   make version      — show current version

PYTHON      ?= python3
PIP         ?= pip3
CMAKE       ?= cmake
BUILD_DIR   := build
C_BUILD_DIR := $(BUILD_DIR)/c
PY_BUILD_DIR:= $(BUILD_DIR)/py
DOCS_DIR    := docs/_build

VERSION     := $(shell $(PYTHON) -c "import zsys; print(zsys.__version__)" 2>/dev/null || echo "1.0.0")

.PHONY: all build build-c build-lib build-py build-go test test-c test-all \
        install install-c clean clean-c clean-py docs fmt lint version help

# -----------------------------------------------------------------------------
all: build

build: build-c build-py
@echo "✅  zsys v$(VERSION) built successfully"

# --- C library ----------------------------------------------------------------
build-c:
@echo "⚙️   Building libzsys_core..."
@mkdir -p $(C_BUILD_DIR)
@cd $(C_BUILD_DIR) && $(CMAKE) ../.. -DCMAKE_BUILD_TYPE=Release \
-DCMAKE_INSTALL_PREFIX=/usr/local \
-DBUILD_SHARED_LIBS=ON \
-DCMAKE_C_FLAGS="-O3 -march=native" \
-DCMAKE_INSTALL_LIBDIR=lib \
2>&1 | tail -3
@cd $(C_BUILD_DIR) && $(CMAKE) --build . --parallel $$(nproc) 2>&1 | tail -5
@echo "✅  libzsys_core built → $(C_BUILD_DIR)/"

# --- Universal C shared library (router + registry + i18n, no Python deps) ---
build-lib:
	@echo "⚙️   Building libzsys.so (router + registry + i18n)..."
	$(CC) -std=c99 -Wall -Wextra -fPIC -shared -O2 \
	    zsys/src/zsys_router.c \
	    zsys/src/zsys_registry.c \
	    zsys/src/zsys_i18n.c \
	    -I zsys/include/ \
	    -o libzsys.so
	@echo "✅  libzsys.so built"

# --- Python extension ---------------------------------------------------------
build-py:
@echo "⚙️   Building Python C extension..."
@$(PYTHON) setup_core.py build_ext --inplace --quiet
@echo "✅  _zsys_core.so built → zsys/_core/"

# --- Go bindings check --------------------------------------------------------
build-go:
@echo "⚙️   Checking Go bindings..."
@which go > /dev/null 2>&1 || (echo "⚠️  Go not installed, skipping"; exit 0)
@cd zsys/go && go build ./... 2>&1 && echo "✅  Go bindings OK" || echo "❌  Go build failed"

# --- Tests --------------------------------------------------------------------
test: build-py
@echo "🧪  Running Python tests..."
@$(PYTHON) -m pytest tests/ -v --tb=short 2>&1 | tail -30

test-c: build-c
@echo "🧪  Running C tests..."
@cd $(C_BUILD_DIR) && ctest --output-on-failure 2>&1

test-all: test test-c
@echo "✅  All tests passed"

# --- Install ------------------------------------------------------------------
install: build-py
@echo "📦  Installing zsys (editable)..."
@$(PIP) install -e ".[dev]" --quiet
@echo "✅  zsys installed"

install-c: build-c
@echo "📦  Installing libzsys_core system-wide (may need sudo)..."
@cd $(C_BUILD_DIR) && $(CMAKE) --install . 2>&1
@echo "✅  libzsys_core installed"

# --- Clean --------------------------------------------------------------------
clean: clean-c clean-py
@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
@find . -name "*.pyc" -delete 2>/dev/null; true
@rm -rf $(DOCS_DIR) .pytest_cache .mypy_cache .ruff_cache
@echo "✅  Cleaned"

clean-c:
@rm -rf $(C_BUILD_DIR)
@echo "  Removed $(C_BUILD_DIR)"

clean-py:
@rm -rf $(PY_BUILD_DIR) dist *.egg-info
@find zsys/_core -name "*.so" -delete 2>/dev/null; true
@echo "  Removed Python build artifacts"

# --- Docs ---------------------------------------------------------------------
docs: build-py
@echo "📖  Building docs..."
@which pdoc > /dev/null 2>&1 || $(PIP) install pdoc --quiet
@mkdir -p $(DOCS_DIR)
@$(PYTHON) -m pdoc zsys --output-dir $(DOCS_DIR) --no-browser 2>&1
@echo "✅  Docs built → $(DOCS_DIR)/"

# --- Code quality -------------------------------------------------------------
fmt:
@echo "🖊️   Formatting code..."
@which ruff > /dev/null 2>&1 && ruff format zsys/ tests/ || true
@which black > /dev/null 2>&1 && black zsys/ tests/ --quiet || true
@echo "✅  Formatted"

lint:
@echo "🔍  Linting..."
@which ruff > /dev/null 2>&1 && ruff check zsys/ tests/ || true
@which mypy > /dev/null 2>&1 && mypy zsys/ --ignore-missing-imports || true

# --- Info ---------------------------------------------------------------------
version:
@echo "zsys v$(VERSION)"

help:
@echo "zsys v$(VERSION) — Build targets:"
@echo ""
@echo "  make              Build C lib + Python extension"
@echo "  make build-c      Build libzsys_core.so"
@echo "  make build-py     Build _zsys_core.so Python extension"
@echo "  make build-go     Check Go bindings"
@echo "  make test         Run Python tests"
@echo "  make test-c       Run C tests"
@echo "  make install      Install Python package (editable)"
@echo "  make install-c    Install C library system-wide"
@echo "  make clean        Remove all build artifacts"
@echo "  make docs         Build HTML documentation"
@echo "  make fmt          Auto-format code"
@echo "  make lint         Lint code"
@echo ""
