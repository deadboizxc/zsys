[🇬🇧 English](CHANGELOG.md) | [🇷🇺 Русский](CHANGELOG_RU.md)

# Журнал изменений

Все значимые изменения в zsys задокументированы здесь.  
Формат следует [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Версионирование следует [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-03-01

### Добавлено

#### Ядро (Core)
- `zsys.core.interfaces` — абстрактные интерфейсы: `IClient`, `IBot`, `IStorage`, `ICipher`, `IWallet`, `IBlockchain`
- `zsys.core.exceptions` — типизированная иерархия исключений: `ZsysError`, `ClientError`, `StorageError`, `ModuleError` и другие
- `zsys.core.dataclass_models` — платформенно-независимые модели данных: `BaseUser`, `BaseChat`, `BaseMessage`, `BaseWallet`, `BaseBot`
- `zsys.core.dataclass_models.context` — унифицированные `Context`, `User`, `Chat` для всех Telegram-платформ
- `zsys.core.logging` — `BaseLogger`, фабрика `get_logger`

#### C-ядро (`libzsys_core`)
- Чистая C-библиотека без внешних зависимостей (`zsys/src/zsys_core.c`)
- 30+ функций: обработка текста/HTML, маршрутизация, парсинг мета, логирование, терминал, время
- Чистый публичный API в `zsys/include/zsys_core.h` (без зависимости от `Python.h`)
- Компилируется в `libzsys_core.so` + `libzsys_core.a` через CMake
- Поддержка `pkg-config` и `find_package(zsys_core)`

#### Python C-расширение (`zsys._core`)
- CPython-расширение, оборачивающее функции `libzsys_core`
- 41 экспортируемая функция с чистыми Python-заглушками
- Флаг `C_AVAILABLE` для определения возможностей во время выполнения
- Файлы `bind_*.c` на уровне каждого модуля для будущих сборок на уровне модуля

#### i18n (`zsys.i18n`)
- `I18N` — менеджер многоязычных переводов с локалями JSON/CBOR
- `GlobalI18N` — синглтон с персистентностью SQLite и LRU-кэшем
- `register_i18n()` — регистрация внешнего экземпляра i18n как глобального
- Глобальный прокси `t` с корректным fallback (возвращает ключ, если не инициализирован)

#### Модули (`zsys.modules`)
- `ModuleLoader` — обнаружение и загрузка Python-модулей из директорий
- `ModuleRegistry` — центральный реестр с текстом справки и метаданными
- `ModuleRouter` — маршрутизация команд с сопоставлением префиксов/триггеров
- `ModuleWatcher` — горячая перезагрузка на основе `watchfiles`
- `modules_help` — глобальный словарь `{module_name: help_text}`
- Парсер мета-комментариев: `# @name:`, `# @description:`, `# @commands:`

#### Логирование (`zsys.log`)
- `printer` — цветной вывод в терминал: `info`, `warning`, `error`, `debug`, `success`
- `print_box`, `print_separator`, `print_table`, `print_progress` — UI для терминала
- Форматирование JSON-лога через C-ядро

#### Утилиты (`zsys.utils`)
- `text.py` — `escape_html`, `strip_html`, `truncate_text`, `split_text`, `format_bytes`, `format_duration`, `format_bold/italic/code/pre/link/mention/spoiler/quote`
- `time.py` — `human_time`, `parse_duration`
- `errors.py` — `format_exc`, `print_exc`, `ZsysError`, `BotError`
- `meta.py` — `parse_meta_comments`
- `decorators.py` — `with_reply`, `with_args`, `admin_only`, `error_handler`
- `filesystem.py`, `hash.py`, `cache.py`, `git.py`, `http.py`, `media.py`

#### Хранилища (`zsys.storage`)
- `SQLiteStorage`, `RedisStorage`, `MongoDBStorage`, `DuckDBStorage`, `LMDBStorage`, `TinyDBStorage`, `PickleDBStorage`
- `StorageFactory` — создание хранилища по имени бэкенда
- `BaseStorage` — абстрактный интерфейс

#### Telegram (`zsys.telegram`)
- **Pyrogram** — `PyrogramClient`, `PyrogramConfig`, контекст, декораторы, роутер, сессия, interact, мульти-клиент
- **aiogram** — `AiogramBot`, контекст, роутер
- **Telebot** — контекст, роутер
- **Telethon** — `TelethonClient`

#### Go-привязки (`zsys/go/`)
- `zsys.go` — CGO-привязки к `libzsys_core`: `EscapeHTML`, `FormatBytes`, `FormatDuration`, `HumanTime`, `ParseDuration`, `MatchPrefix`, `AnsiColor`
- Go-файлы на уровне модулей: `i18n/i18n.go`, `log/log.go`, `modules/modules.go`, `storage/storage.go`, `utils/utils.go`
- `storage/storage.go` — чистая Go-реализация `SQLiteStorage`

#### Крейт Rust (`zsys/rust/`)
- `src/lib.rs` — безопасные обёртки Rust: `escape_html`, `format_bytes`, `format_duration`, `human_time`, `parse_duration`, `format_bold`, `format_code`, `ansi_color`, `match_prefix`
- `build.rs` — автоматический bindgen из `zsys_core.h`
- Юнит-тесты для всех публичных функций

#### Система сборки
- `Makefile` — `build`, `build-c`, `build-py`, `build-go`, `test`, `install`, `clean`, `docs`, `fmt`, `lint`
- `CMakeLists.txt` — общая/статическая библиотека, `pkg-config`, `find_package`, `install`
- `setup_core.py` — скрипт сборки Python-расширения
- `cmake/zsys_core.pc.in` — шаблон pkg-config
- `cmake/zsys_coreConfig.cmake.in` — шаблон конфигурации CMake

### Архитектурные решения

- **Независимость модулей** — каждый модуль (`i18n`, `log`, `utils`, `storage`, `modules`, `telegram`) зависит только от `zsys.core`, никогда от соседних модулей
- **C-ядро** — чистый C без `Python.h` → один и тот же `.so` используется Python, Go (CGO), Rust (bindgen), Kotlin (JNI)
- **`bind_*.c` на уровне модуля** — Python C-привязка на модуль для будущей компиляции на уровне модуля
- **Полиглот-компоновка** — Go, Rust, C-файлы сосуществуют с Python-файлами внутри каждой директории модуля

[1.0.0]: https://github.com/deadboizxc/zsys/releases/tag/v1.0.0
