[🇬🇧 English](README.md) | [🇷🇺 Русский](README_RU.md)

<div align="center">

# zsys

**Модульная полиглот-библиотека для ботов, юзерботов и распределённых приложений.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![C Standard](https://img.shields.io/badge/C-C11-orange.svg)](zsys/include/zsys_core.h)

</div>

---

## Обзор

**zsys** — модульная библиотека, построенная по единственному принципу:  
**каждый модуль независим — он зависит только от `core/`, но никогда от соседних модулей.**

C-ядро (`libzsys_core`) предоставляет реализации горячих путей, используемые во всех языковых привязках. Python, Go и Rust используют одни и те же базовые C-функции — без дублирования.

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

## Возможности

| Модуль | Описание |
|--------|----------|
| `zsys._core` | Python C-расширение — 41 функция горячего пути |
| `zsys.i18n` | Интернационализация (CBOR + SQLite + LRU-кэш) |
| `zsys.modules` | Загрузчик модулей, реестр, роутер, наблюдатель горячей перезагрузки |
| `zsys.log` | Структурированное логирование с ANSI-цветами и JSON-выводом |
| `zsys.utils` | Текст, HTML, время, ошибки, декораторы, утилиты файловой системы |
| `zsys.storage` | Хранилища ключ-значение: SQLite, Redis, MongoDB, DuckDB, LMDB |
| `zsys.telegram` | Telegram-клиенты: Pyrogram, aiogram, Telethon, Telebot |
| `zsys.api` | FastAPI-адаптер для веб-интерфейсов |
| `zsys.crypto` | Утилиты шифрования AES, RSA, ECC |
| `zsys.core` | Интерфейсы, исключения, модели dataclass, базовое логирование |

---

## Быстрый старт

### Python

```bash
# Установка (Python-расширение компилируется автоматически)
pip install zsys

# Или из исходников
git clone https://github.com/deadboizxc/zsys
cd zsys
make install
```

```python
from zsys.utils.text import escape_html, format_bytes, truncate_text
from zsys.utils.time import human_time, parse_duration
from zsys.i18n import GlobalI18N
from zsys.log import printer

# C-расширение (в 41 раз быстрее чистого Python)
from zsys._core import C_AVAILABLE
print(f"C acceleration: {C_AVAILABLE}")  # True

# Утилиты для текста
print(escape_html("<b>Hello & World</b>"))  # &lt;b&gt;Hello &amp; World&lt;/b&gt;
print(format_bytes(1_500_000))              # 1.4 MB
print(human_time(3690, short=True))         # 1 ч. 1 мин.
print(parse_duration("1h30m"))              # 5400

# Интернационализация
i18n = GlobalI18N(locales_path="./locales", default_lang="en")
print(i18n.t("welcome"))
```

### Telegram-юзербот (Pyrogram)

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

### Модуль (команды с префиксом `.`)

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

### C-библиотека

```bash
# Сборка
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel

# Использование в C-проекте
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

## Архитектура

### Правило зависимостей

Каждый модуль зависит **только от `zsys.core`** — никогда от соседних модулей:

```
zsys.core          ← нет внешних зависимостей
zsys.i18n          ← только zsys.core
zsys.utils         ← только stdlib
zsys.log           ← только zsys.core.logging
zsys.storage       ← только stdlib
zsys.modules       ← только zsys.core
zsys.telegram.*    ← только zsys.core
zsys.services      ← может зависеть от нескольких (слой оркестрации)
```

### Структура проекта

```
zsys/
├── zsys/                    # Python-пакет
│   ├── include/
│   │   └── zsys_core.h      # Чистый C API (без Python.h)
│   ├── src/
│   │   ├── zsys_core.c      # Чистая C-реализация (libzsys_core)
│   │   └── _zsys_core.c     # Python C-расширение (CPython API)
│   ├── _core/               # Скомпилированный .so + Python-заглушки
│   ├── core/                # Интерфейсы, исключения, модели dataclass
│   ├── i18n/                # i18n (py + go)
│   ├── modules/             # Загрузчик/реестр/роутер модулей (py + go)
│   ├── log/                 # Логирование + printer (py + go)
│   ├── utils/               # Утилиты (py + go)
│   ├── storage/             # Бэкенды хранилищ (py + go)
│   ├── telegram/            # Telegram-клиенты (py)
│   │   ├── pyrogram/
│   │   ├── aiogram/
│   │   ├── telebot/
│   │   └── telethon/
│   ├── go/                  # Точка входа модуля Go
│   └── rust/                # Крейт Rust
│       ├── src/lib.rs
│       ├── build.rs
│       └── Cargo.toml
├── cmake/                   # Шаблоны конфигурации CMake
├── tests/                   # Набор тестов
├── examples/                # Примеры использования
├── CMakeLists.txt           # Сборка C-библиотеки
├── Makefile                 # Удобные цели сборки
├── setup_core.py            # Сборка Python-расширения
└── pyproject.toml           # Конфигурация Python-пакета
```

---

## Сборка из исходников

### Требования

- Python 3.10+
- GCC / Clang (для C-расширения)
- CMake 3.14+ (для C-библиотеки)
- Go 1.21+ (опционально, для Go-привязок)
- Rust 1.70+ (опционально, для крейта Rust)

### Сборка всего

```bash
make              # C-библиотека + Python-расширение
make test         # Запуск тестов
make install      # Установка Python-пакета (редактируемая)
make install-c    # Установка C-библиотеки в систему
make docs         # Сборка HTML-документации
make clean        # Очистка всех артефактов
```

### Только Python-расширение

```bash
make build-py
# или
python setup_core.py build_ext --inplace
```

### Только C-библиотека

```bash
make build-c
# или
cmake -B build/c -DCMAKE_BUILD_TYPE=Release
cmake --build build/c --parallel
```

---

## Тестирование

```bash
make test         # Python-тесты (pytest)
make test-c       # C-тесты (CTest)
make test-all     # Оба варианта
```

---

## Справочник C API

Все C-функции объявлены в `zsys/include/zsys_core.h`.  
Память: функции, возвращающие `char*`, должны освобождаться через `zsys_free()`.

| Функция | Описание |
|---------|----------|
| `zsys_escape_html(text, len)` | Экранирование `& < > "` |
| `zsys_strip_html(text, len)` | Удаление тегов, деэкранирование сущностей |
| `zsys_truncate_text(text, len, max, suffix)` | Обрезка с учётом UTF-8 |
| `zsys_split_text(text, len, max_chars)` | Разбивка на фрагменты |
| `zsys_format_bytes(size)` | `1536 → "1.5 KB"` |
| `zsys_format_duration(seconds)` | `3661.0 → "1h 1m 1s"` |
| `zsys_human_time(seconds, short)` | Человекочитаемое время по-русски |
| `zsys_parse_duration(text)` | `"1h30m" → 5400` |
| `zsys_format_bold/italic/code/pre/link/mention(...)` | HTML-форматировщики |
| `zsys_ansi_color(text, code)` | ANSI-цвета терминала |
| `zsys_format_json_log(level, msg, ts)` | Строка JSON-лога |
| `zsys_match_prefix(text, prefixes, triggers)` | Маршрутизация команд |
| `zsys_parse_meta_comments(source, len)` | Парсер мета-комментариев модуля |
| `zsys_build_help_text(name, cmds, prefix)` | Генератор текста справки |

---

## Участие в разработке

Смотрите [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Лицензия

MIT — смотрите [LICENSE](LICENSE).

---

<div align="center">
Сделано с ❤️ автором <a href="https://github.com/deadboizxc">deadboizxc</a>
</div>
