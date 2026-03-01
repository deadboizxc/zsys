<div align="center">

# zsys

**A modular, polyglot systems library for bots, userbots, and distributed apps.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![C Standard](https://img.shields.io/badge/C-C11-orange.svg)](zsys/include/zsys_core.h)

</div>

---

## Overview

**zsys** is a modular library designed around a single principle:  
**each module is independent — it depends only on `core/`, never on sibling modules.**

The C core (`libzsys_core`) provides hot-path implementations shared across all language bindings. Python, Go, and Rust use the same underlying C functions — no duplication.

```
┌─────────────────────────────────────────────────────┐
│                      zsys v1.0.0                    │
├──────────┬──────────┬──────────┬────────────────────┤
│  Python  │    Go    │   Rust   │   Kotlin (future)  │
├──────────┴──────────┴──────────┴────────────────────┤
│              C core  (libzsys_core.so)               │
│   text · html · routing · i18n · log · meta · time  │
├─────────────────────────────────────────────────────┤
│                 zsys/include/zsys_core.h             │
└─────────────────────────────────────────────────────┘
```

---

## Features

| Module | Description |
|--------|-------------|
| `zsys._core` | Python C extension — 41 hot-path functions |
| `zsys.i18n` | Internationalization (CBOR + SQLite + LRU cache) |
| `zsys.modules` | Module loader, registry, router, hot-reload watcher |
| `zsys.log` | Structured logging with ANSI colors and JSON output |
| `zsys.utils` | Text, HTML, time, errors, decorators, filesystem utilities |
| `zsys.storage` | Key-value storage: SQLite, Redis, MongoDB, DuckDB, LMDB |
| `zsys.telegram` | Telegram clients: Pyrogram, aiogram, Telethon, Telebot |
| `zsys.api` | FastAPI adapter for web interfaces |
| `zsys.crypto` | AES, RSA, ECC encryption utilities |
| `zsys.core` | Interfaces, exceptions, dataclass models, base logging |

---

## Quick Start

### Python

```bash
# Install (Python extension auto-compiled)
pip install zsys

# Or from source
git clone https://github.com/deadboizxc/zsys
cd zsys
make install
```

```python
from zsys.utils.text import escape_html, format_bytes, truncate_text
from zsys.utils.time import human_time, parse_duration
from zsys.i18n import GlobalI18N
from zsys.log import printer

# C extension (41x faster than pure Python)
from zsys._core import C_AVAILABLE
print(f"C acceleration: {C_AVAILABLE}")  # True

# Text utilities
print(escape_html("<b>Hello & World</b>"))  # &lt;b&gt;Hello &amp; World&lt;/b&gt;
print(format_bytes(1_500_000))              # 1.4 MB
print(human_time(3690, short=True))         # 1 ч. 1 мин.
print(parse_duration("1h30m"))              # 5400

# Internationalization
i18n = GlobalI18N(locales_path="./locales", default_lang="en")
print(i18n.t("welcome"))
```

### Telegram userbot (Pyrogram)

```python
from zsys.telegram.pyrogram.client import PyrogramClient, PyrogramConfig
from zsys.modules.loader import ModuleLoader
from pathlib import Path

config = PyrogramConfig(
    api_id=12345,
    api_hash="your_hash",
    session_name="my_session",
    prefix=".",
)

client = PyrogramClient(config)
client.run()
```

### Module (`.` prefix commands)

```python
# modules/ping.py
# @name: ping
# @description: Simple ping command
# @commands: ping - Reply with pong

from zsys.telegram.pyrogram.decorators import zxc
from zsys.utils.time import human_time

@zxc("ping")
async def ping_cmd(client, message):
    await message.edit("🏓 Pong!")
```

### C library

```bash
# Build
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel

# Use in your C project
pkg-config --cflags --libs zsys_core
```

```c
#include <zsys/zsys_core.h>
#include <stdio.h>

int main(void) {
    char *result = zsys_escape_html("<b>Hello</b>", 12);
    printf("%s\n", result);  // &lt;b&gt;Hello&lt;/b&gt;
    zsys_free(result);
    return 0;
}
```

### Go

```go
import "github.com/deadboizxc/zsys/zsys/utils"

fmt.Println(utils.EscapeHTML("<b>Hello</b>"))
fmt.Println(utils.FormatBytes(1_500_000))
```

### Rust

```rust
use zsys::{escape_html, format_bytes};

fn main() {
    println!("{}", escape_html("<b>Hello</b>"));
    println!("{}", format_bytes(1_500_000));
}
```

---

## Architecture

### Dependency rule

Every module depends **only on `zsys.core`** — never on sibling modules:

```
zsys.core          ← no external dependencies
zsys.i18n          ← zsys.core only
zsys.utils         ← stdlib only
zsys.log           ← zsys.core.logging only
zsys.storage       ← stdlib only
zsys.modules       ← zsys.core only
zsys.telegram.*    ← zsys.core only
zsys.services      ← may depend on multiple (orchestration layer)
```

### Project structure

```
zsys/
├── zsys/                    # Python package
│   ├── include/
│   │   └── zsys_core.h      # Pure C API (no Python.h)
│   ├── src/
│   │   ├── zsys_core.c      # Pure C implementation (libzsys_core)
│   │   └── _zsys_core.c     # Python C extension (CPython API)
│   ├── _core/               # Compiled .so + Python fallbacks
│   ├── core/                # Interfaces, exceptions, dataclass models
│   ├── i18n/                # i18n (py + go)
│   ├── modules/             # Module loader/registry/router (py + go)
│   ├── log/                 # Logging + printer (py + go)
│   ├── utils/               # Utilities (py + go)
│   ├── storage/             # Storage backends (py + go)
│   ├── telegram/            # Telegram clients (py)
│   │   ├── pyrogram/
│   │   ├── aiogram/
│   │   ├── telebot/
│   │   └── telethon/
│   ├── go/                  # Go entry module
│   └── rust/                # Rust crate
│       ├── src/lib.rs
│       ├── build.rs
│       └── Cargo.toml
├── cmake/                   # CMake config templates
├── tests/                   # Test suite
├── examples/                # Usage examples
├── CMakeLists.txt           # C library build
├── Makefile                 # Convenience build targets
├── setup_core.py            # Python extension build
└── pyproject.toml           # Python package config
```

---

## Building from source

### Requirements

- Python 3.10+
- GCC / Clang (for C extension)
- CMake 3.14+ (for C library)
- Go 1.21+ (optional, for Go bindings)
- Rust 1.70+ (optional, for Rust crate)

### Build all

```bash
make              # C library + Python extension
make test         # Run tests
make install      # Install Python package (editable)
make install-c    # Install C library system-wide
make docs         # Build HTML docs
make clean        # Clean all artifacts
```

### Build only Python extension

```bash
make build-py
# or
python setup_core.py build_ext --inplace
```

### Build only C library

```bash
make build-c
# or
cmake -B build/c -DCMAKE_BUILD_TYPE=Release
cmake --build build/c --parallel
```

---

## Testing

```bash
make test         # Python tests (pytest)
make test-c       # C tests (CTest)
make test-all     # Both
```

---

## C API Reference

All C functions are declared in `zsys/include/zsys_core.h`.  
Memory: functions returning `char*` must be freed with `zsys_free()`.

| Function | Description |
|----------|-------------|
| `zsys_escape_html(text, len)` | Escape `& < > "` |
| `zsys_strip_html(text, len)` | Strip tags, unescape entities |
| `zsys_truncate_text(text, len, max, suffix)` | UTF-8 aware truncation |
| `zsys_split_text(text, len, max_chars)` | Split into chunks |
| `zsys_format_bytes(size)` | `1536 → "1.5 KB"` |
| `zsys_format_duration(seconds)` | `3661.0 → "1h 1m 1s"` |
| `zsys_human_time(seconds, short)` | Russian human time |
| `zsys_parse_duration(text)` | `"1h30m" → 5400` |
| `zsys_format_bold/italic/code/pre/link/mention(...)` | HTML formatters |
| `zsys_ansi_color(text, code)` | ANSI terminal colors |
| `zsys_format_json_log(level, msg, ts)` | JSON log line |
| `zsys_match_prefix(text, prefixes, triggers)` | Command routing |
| `zsys_parse_meta_comments(source, len)` | Module meta parser |
| `zsys_build_help_text(name, cmds, prefix)` | Help text builder |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
Made with ❤️ by <a href="https://github.com/deadboizxc">deadboizxc</a>
</div>
