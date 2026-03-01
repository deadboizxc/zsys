# Changelog

All notable changes to zsys are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-01

### Added

#### Core
- `zsys.core.interfaces` — abstract interfaces: `IClient`, `IBot`, `IStorage`, `ICipher`, `IWallet`, `IBlockchain`
- `zsys.core.exceptions` — typed exception hierarchy: `ZsysError`, `ClientError`, `StorageError`, `ModuleError`, etc.
- `zsys.core.dataclass_models` — platform-agnostic data models: `BaseUser`, `BaseChat`, `BaseMessage`, `BaseWallet`, `BaseBot`
- `zsys.core.dataclass_models.context` — unified `Context`, `User`, `Chat` for all Telegram platforms
- `zsys.core.logging` — `BaseLogger`, `get_logger` factory

#### C Core (`libzsys_core`)
- Pure C library with 0 external dependencies (`zsys/src/zsys_core.c`)
- 30+ functions: text/HTML processing, routing, meta parsing, logging, terminal, time
- Clean public API in `zsys/include/zsys_core.h` (no `Python.h` dependency)
- Compiles to `libzsys_core.so` + `libzsys_core.a` via CMake
- `pkg-config` and `find_package(zsys_core)` support

#### Python C Extension (`zsys._core`)
- CPython extension wrapping `libzsys_core` functions
- 41 exported functions with pure-Python fallbacks
- `C_AVAILABLE` flag for runtime capability detection
- Per-module `bind_*.c` files for future per-module builds

#### i18n (`zsys.i18n`)
- `I18N` — multi-language translation manager with JSON/CBOR locales
- `GlobalI18N` — singleton with SQLite persistence and LRU cache
- `register_i18n()` — register external i18n instance as global
- Global `t` proxy with graceful fallback (returns key if not initialized)

#### Modules (`zsys.modules`)
- `ModuleLoader` — discovers and loads Python modules from directories
- `ModuleRegistry` — central registry with help text and metadata
- `ModuleRouter` — command routing with prefix/trigger matching
- `ModuleWatcher` — `watchfiles`-based hot reload
- `modules_help` — global dict `{module_name: help_text}`
- Meta comment parser: `# @name:`, `# @description:`, `# @commands:`

#### Logging (`zsys.log`)
- `printer` — colored terminal output: `info`, `warning`, `error`, `debug`, `success`
- `print_box`, `print_separator`, `print_table`, `print_progress` — terminal UI
- JSON log formatting via C core

#### Utils (`zsys.utils`)
- `text.py` — `escape_html`, `strip_html`, `truncate_text`, `split_text`, `format_bytes`, `format_duration`, `format_bold/italic/code/pre/link/mention/spoiler/quote`
- `time.py` — `human_time`, `parse_duration`
- `errors.py` — `format_exc`, `print_exc`, `ZsysError`, `BotError`
- `meta.py` — `parse_meta_comments`
- `decorators.py` — `with_reply`, `with_args`, `admin_only`, `error_handler`
- `filesystem.py`, `hash.py`, `cache.py`, `git.py`, `http.py`, `media.py`

#### Storage (`zsys.storage`)
- `SQLiteStorage`, `RedisStorage`, `MongoDBStorage`, `DuckDBStorage`, `LMDBStorage`, `TinyDBStorage`, `PickleDBStorage`
- `StorageFactory` — create storage by backend name
- `BaseStorage` — abstract interface

#### Telegram (`zsys.telegram`)
- **Pyrogram** — `PyrogramClient`, `PyrogramConfig`, context, decorators, router, session, interact, multi-client
- **aiogram** — `AiogramBot`, context, router
- **Telebot** — context, router
- **Telethon** — `TelethonClient`

#### Go bindings (`zsys/go/`)
- `zsys.go` — CGO bindings to `libzsys_core`: `EscapeHTML`, `FormatBytes`, `FormatDuration`, `HumanTime`, `ParseDuration`, `MatchPrefix`, `AnsiColor`
- Per-module Go files: `i18n/i18n.go`, `log/log.go`, `modules/modules.go`, `storage/storage.go`, `utils/utils.go`
- `storage/storage.go` — `SQLiteStorage` pure Go implementation

#### Rust crate (`zsys/rust/`)
- `src/lib.rs` — safe Rust wrappers: `escape_html`, `format_bytes`, `format_duration`, `human_time`, `parse_duration`, `format_bold`, `format_code`, `ansi_color`, `match_prefix`
- `build.rs` — automatic bindgen from `zsys_core.h`
- Unit tests for all public functions

#### Build system
- `Makefile` — `build`, `build-c`, `build-py`, `build-go`, `test`, `install`, `clean`, `docs`, `fmt`, `lint`
- `CMakeLists.txt` — shared/static library, `pkg-config`, `find_package`, `install`
- `setup_core.py` — Python extension build script
- `cmake/zsys_core.pc.in` — pkg-config template
- `cmake/zsys_coreConfig.cmake.in` — CMake config template

### Architecture decisions

- **Module independence** — each module (`i18n`, `log`, `utils`, `storage`, `modules`, `telegram`) depends only on `zsys.core`, never on sibling modules
- **C core** — pure C without `Python.h` → same `.so` used by Python, Go (CGO), Rust (bindgen), Kotlin (JNI)
- **Per-module `bind_*.c`** — Python C binding per module for future per-module compilation
- **Polyglot layout** — Go, Rust, C files coexist with Python files inside each module directory

[1.0.0]: https://github.com/deadboizxc/zsys/releases/tag/v1.0.0
