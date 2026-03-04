# =============================================================================
# zsys — Makefile
# =============================================================================
PYTHON      ?= python3
PIP         ?= pip3
CC          ?= gcc
CMAKE       ?= cmake
BUILD_DIR   := build
C_BUILD_DIR := $(BUILD_DIR)/c
PY_BUILD_DIR := $(BUILD_DIR)/py
DOCS_DIR    := docs/_build

TG_C_DIR    := zsys/telegram/tdlib/c
TG_BUILD_DIR := $(TG_C_DIR)/build
TDLIB_DIR   ?= $(TG_C_DIR)/tdlib          # set by install_tdlib.sh or manually
JOBS        ?= $(shell nproc 2>/dev/null || echo 4)

VERSION     := $(shell $(PYTHON) -c "import zsys; print(zsys.__version__)" 2>/dev/null || echo "1.0.0")

.PHONY: all build build-c build-lib build-py build-go build-telegram build-tdlib \
        test test-c test-all install install-c install-lib install-telegram \
        clean clean-c clean-py clean-telegram docs fmt lint version help

all: build

build: build-lib build-py
	@echo "zsys v$(VERSION) built"

build-lib:
	@echo "Building libzsys.so..."
	$(CC) -std=c99 -Wall -Wextra -fPIC -shared -O2 \
	    zsys/src/zsys_router.c \
	    zsys/src/zsys_registry.c \
	    zsys/src/zsys_i18n.c \
	    -I zsys/include/ \
	    -o libzsys.so
	@echo "OK libzsys.so built"

build-c:
	@mkdir -p $(C_BUILD_DIR)
	@cd $(C_BUILD_DIR) && $(CMAKE) ../.. -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON 2>&1 | tail -3
	@cd $(C_BUILD_DIR) && $(CMAKE) --build . --parallel $$(nproc) 2>&1 | tail -5

# ── TDLib + libtg ─────────────────────────────────────────────────────────────

## Step 1: build TDLib from source (≈10-20 min, run once)
build-tdlib:
	@echo "🔨 Building TDLib (this takes a while)..."
	@TDLIB_INSTALL_PREFIX=$(TDLIB_DIR) JOBS=$(JOBS) bash scripts/install_tdlib.sh

## Step 2: build libtg.so using the installed TDLib
build-telegram:
	@echo "🔨 Building libtg.so..."
	@mkdir -p $(TG_BUILD_DIR)
	@if [ -d "$(TDLIB_DIR)/lib" ]; then \
	    TDLIB_HINT="-DTDLIB_DIR=$(abspath $(TDLIB_DIR)) -DTDLIB_FETCH=OFF"; \
	else \
	    TDLIB_HINT="-DTDLIB_FETCH=OFF"; \
	fi; \
	$(CMAKE) -S $(TG_C_DIR) -B $(TG_BUILD_DIR) \
	    -DCMAKE_BUILD_TYPE=Release \
	    $$TDLIB_HINT 2>&1 | tail -5
	@$(CMAKE) --build $(TG_BUILD_DIR) --target tg --parallel $(JOBS) 2>&1 | tail -5
	@cp $(TG_BUILD_DIR)/libtg.so $(TG_C_DIR)/../libtg.so 2>/dev/null; true
	@echo "✅ libtg.so built → $(TG_C_DIR)/../libtg.so"

## Shortcut: build TDLib + libtg in one command
telegram: build-tdlib build-telegram

install-telegram: build-telegram
	@install -m 755 $(TG_C_DIR)/../libtg.so /usr/local/lib/libtg.so
	@install -m 644 $(TG_C_DIR)/include/tg.h /usr/local/include/tg.h
	@ldconfig
	@echo "✅ libtg.so installed system-wide"

clean-telegram:
	@rm -rf $(TG_BUILD_DIR) $(TG_C_DIR)/../libtg.so

build-py:
	@$(PYTHON) setup_core.py build_ext --inplace --quiet
	@echo "OK _zsys_core.so built"

build-go:
	@which go > /dev/null 2>&1 || (echo "Go not installed, skipping"; exit 0)
	@cd bindings/go && go build ./... 2>&1 && echo "OK Go bindings" || echo "FAIL Go build"

test: build-py
	@$(PYTHON) -m pytest tests/ -v --tb=short 2>&1 | tail -30

test-c: build-c
	@cd $(C_BUILD_DIR) && ctest --output-on-failure 2>&1

test-all: test test-c

install: build-py
	@$(PIP) install -e ".[dev]" --quiet

install-c: build-c
	@cd $(C_BUILD_DIR) && $(CMAKE) --install . 2>&1

install-lib: build-lib
	@install -m 755 libzsys.so /usr/local/lib/libzsys.so
	@install -m 644 zsys/include/zsys_core.h /usr/local/include/zsys_core.h
	@ldconfig

clean: clean-c clean-py clean-telegram
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	@rm -rf $(DOCS_DIR) .pytest_cache .mypy_cache .ruff_cache libzsys.so

clean-c:
	@rm -rf $(C_BUILD_DIR)

clean-py:
	@rm -rf $(PY_BUILD_DIR) dist *.egg-info
	@find zsys/_core -name "*.so" -delete 2>/dev/null; true

docs: build-py
	@mkdir -p $(DOCS_DIR)
	@$(PYTHON) -m pdoc zsys --output-dir $(DOCS_DIR) --no-browser 2>&1

fmt:
	@which ruff > /dev/null 2>&1 && ruff format zsys/ tests/ || true
	@which black > /dev/null 2>&1 && black zsys/ tests/ --quiet || true

lint:
	@which ruff > /dev/null 2>&1 && ruff check zsys/ tests/ || true
	@which mypy > /dev/null 2>&1 && mypy zsys/ --ignore-missing-imports || true

version:
	@echo "zsys v$(VERSION)"

help:
	@echo "zsys v$(VERSION) build targets:"
	@echo "  make build-lib    Build universal libzsys.so (router+registry+i18n)"
	@echo "  make build-c      Build libzsys_core.so (CMake)"
	@echo "  make build-py     Build _zsys_core.so Python extension"
	@echo "  make build-go     Check Go bindings"
	@echo "  make install      Install Python package (editable)"
	@echo "  make install-lib  Install libzsys.so to /usr/local/lib/"
	@echo "  make test         Run Python tests"
	@echo "  make clean        Remove all build artifacts"
