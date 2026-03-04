"""
README для модуля логирования ZSYS Core.

Этот модуль предоставляет основную систему логирования для всей экосистемы ZSYS.
"""

[🇬🇧 English](README.md) | [🇷🇺 Русский](README_RU.md)

# ===== Обзор BaseLogger =====

## Архитектура

```
zsys.core.logging
│
├── base.py              # Класс BaseLogger (основа)
└── __init__.py          # Экспорты публичного API

zsys.log
│
├── logger.py            # ColorLogger (расширяет BaseLogger с цветами и ротацией)
└── unified.py           # UnifiedLogger (расширяет BaseLogger с сокетами и памятью)
```

## Иерархия наследования

```
BaseLogger (core.logging.base)
    ├── ColorLogger (log.logger)
    └── UnifiedLogger (log.unified)
```

# ===== Базовое использование =====

## Простое логирование

```python
from zsys.core.logging import BaseLogger

logger = BaseLogger("myapp")
logger.info("Application started")
logger.error("Error occurred", exc_info=True)
logger.debug("Debug information")
```

## Уровни логирования

```python
logger = BaseLogger("myapp", level="DEBUG")  # Уровень строкой
logger = BaseLogger("myapp", level=10)       # Уровень числом

# Доступные уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.set_level("WARNING")  # Динамическая смена уровня
```

## Пользовательский формат

```python
logger = BaseLogger(
    "myapp",
    format_string="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
```

# ===== Расширенные возможности =====

## Контекстное логирование

Автоматическое добавление контекстной информации в логи:

```python
logger = BaseLogger("api")

# Временный контекст (context manager)
with logger.context(user_id=123, request_id="abc-def"):
    logger.info("Processing request")  # Лог: "Processing request [user_id=123 request_id=abc-def]"
    logger.error("Request failed")     # Лог: "Request failed [user_id=123 request_id=abc-def]"

# За пределами контекста — без дополнительной информации
logger.info("New request")  # Лог: "New request"
```

## Привязанные логгеры

Создание экземпляров логгера с постоянным контекстом:

```python
base_logger = BaseLogger("app")

# Создать логгер, специфичный для пользователя
user_logger = base_logger.bind(user_id=123, session="xyz")
user_logger.info("User logged in")    # Всегда включает user_id и session
user_logger.info("User action")       # Всегда включает user_id и session

# Создать логгер, специфичный для запроса
request_logger = base_logger.bind(request_id="req-456")
request_logger.info("Processing")     # Всегда включает request_id
```

## Дочерние логгеры

Создание иерархической структуры логгеров:

```python
app_logger = BaseLogger("myapp")
db_logger = app_logger.get_child("database")      # Имя: "myapp.database"
cache_logger = app_logger.get_child("cache")      # Имя: "myapp.cache"

db_logger.info("Connected to database")
cache_logger.info("Cache initialized")
```

## Управление обработчиками

```python
import logging
from logging.handlers import RotatingFileHandler

logger = BaseLogger("app")

# Добавить файловый обработчик
file_handler = RotatingFileHandler(
    "app.log",
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3
)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.add_handler(file_handler)

# Получить все обработчики
handlers = logger.get_handlers()

# Удалить конкретный обработчик
logger.remove_handler(file_handler)

# Очистить все обработчики
logger.clear_handlers()
```

## Управление состоянием

```python
logger = BaseLogger("app")

# Отключить логирование
logger.disable()
logger.info("This won't be logged")

# Включить логирование
logger.enable()
logger.info("This will be logged")

# Проверить состояние
if logger.is_disabled():
    print("Logger is disabled")
```

## Проверка уровней

```python
logger = BaseLogger("app", level="INFO")

# Проверить, включён ли уровень
if logger.is_enabled_for("DEBUG"):
    expensive_data = compute_debug_info()
    logger.debug(expensive_data)

# Получить текущий уровень
level = logger.get_level()  # Возвращает integer (20 для INFO)
```

# ===== Расширенные логгеры =====

## ColorLogger (с цветами и ротацией файлов)

```python
from zsys.log import ColorLogger

logger = ColorLogger(
    name="myapp",
    log_file="logs/app.log",
    level="debug",
    enable_console=True,
    max_bytes=5 * 1024 * 1024,  # 5 MB
    backup_count=3
)

logger.info("This will be green in console")
logger.error("This will be red in console")
logger.print_color("Custom colored text", color="cyan")
```

## UnifiedLogger (с сокетами и управлением памятью)

```python
from zsys.log import UnifiedLogger

logger = UnifiedLogger(
    name="api",
    log_file="logs/api.log",
    log_level="info",
    memory_limit_mb=10,
    socket_ip="127.0.0.1",
    socket_port=9999
)

# Подключиться к сокету для стриминга
await logger.connect_socket()

logger.info("This will be logged and streamed via socket")
```

# ===== Лучшие практики =====

## Логгер на уровне модуля

```python
# mymodule.py
from zsys.core.logging import get_logger

logger = get_logger(__name__)  # Использует имя модуля

def my_function():
    logger.info("Function called")
```

## Структурированное логирование с контекстом

```python
logger = BaseLogger("api")

def handle_request(user_id: int, request_id: str):
    # Автоматически добавлять контекст ко всем логам в этой области
    with logger.context(user_id=user_id, request_id=request_id):
        logger.info("Request received")
        process_request()
        logger.info("Request completed")

def process_request():
    # Контекст распространяется автоматически
    logger.debug("Processing step 1")
    logger.debug("Processing step 2")
```

## Логирование ошибок

```python
logger = BaseLogger("app")

try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")  # Автоматически логирует traceback
    # или
    logger.error("Operation failed: %s", e, exc_info=True)
```

## Оптимизация производительности

```python
logger = BaseLogger("app", level="INFO")

# Плохо: всегда вычисляет debug-информацию
logger.debug(f"Debug: {expensive_computation()}")

# Хорошо: вычисляет только если DEBUG включён
if logger.is_enabled_for("DEBUG"):
    logger.debug(f"Debug: {expensive_computation()}")

# Лучше: ленивое форматирование строки
logger.debug("Debug: %s", expensive_computation)  # Форматирует только при логировании
```

# ===== Руководство по миграции =====

## От старого Logger к BaseLogger

Старый код:
```python
from zsys.core.logging import Logger

logger = Logger("myapp", level="INFO")
logger.info("Message")
```

Новый код (обратно совместимый):
```python
from zsys.core.logging import Logger  # Теперь псевдоним для BaseLogger

logger = Logger("myapp", level="INFO")
logger.info("Message")

# Или явно использовать BaseLogger
from zsys.core.logging import BaseLogger

logger = BaseLogger("myapp", level="INFO")
logger.info("Message")
```

Весь старый код продолжает работать! BaseLogger на 100% обратно совместим.

# ===== Справочник API =====

## Основные методы

- `debug(message, *args, **kwargs)` — Логировать отладочное сообщение
- `info(message, *args, **kwargs)` — Логировать информационное сообщение
- `warning(message, *args, **kwargs)` — Логировать предупреждение
- `error(message, *args, **kwargs)` — Логировать ошибку
- `critical(message, *args, **kwargs)` — Логировать критическое сообщение
- `exception(message, *args, **kwargs)` — Логировать исключение с traceback
- `log(level, message, *args, **kwargs)` — Логировать с конкретным уровнем

## Управление уровнями

- `set_level(level)` — Установить уровень логирования
- `get_level()` — Получить текущий уровень
- `is_enabled_for(level)` — Проверить, включён ли уровень

## Управление обработчиками

- `add_handler(handler)` — Добавить обработчик
- `remove_handler(handler)` — Удалить обработчик
- `clear_handlers()` — Удалить все обработчики
- `get_handlers()` — Получить список обработчиков

## Управление контекстом

- `context(**kwargs)` — Контекст-менеджер для временного контекста
- `bind(**kwargs)` — Создать новый логгер с постоянным контекстом

## Утилиты

- `get_child(suffix)` — Создать дочерний логгер
- `enable()` — Включить логирование
- `disable()` — Отключить логирование
- `is_disabled()` — Проверить, отключён ли логгер

# ===== Тестирование =====

```python
import pytest
from zsys.core.logging import BaseLogger

def test_basic_logging():
    logger = BaseLogger("test")
    logger.info("Test message")  # Не должно вызывать исключений

def test_context():
    logger = BaseLogger("test")
    with logger.context(key="value"):
        # Проверить добавление контекста (зависит от реализации)
        pass

def test_levels():
    logger = BaseLogger("test", level="WARNING")
    assert logger.get_level() == 30  # Уровень WARNING
    assert not logger.is_enabled_for("DEBUG")
    assert logger.is_enabled_for("ERROR")
```

# ===== Итог =====

BaseLogger предоставляет:
✅ Все стандартные методы логирования (debug, info, warning, error, critical, exception)
✅ Поддержку контекста для структурированного логирования
✅ Привязанные логгеры с постоянным контекстом
✅ Создание дочерних логгеров
✅ Управление обработчиками
✅ Управление состоянием (включить/отключить)
✅ Управление уровнями и их проверку
✅ Потокобезопасные операции
✅ 100% обратную совместимость со старым Logger

Используйте BaseLogger для:
- Основного логирования в приложении
- Создания пользовательских классов логгеров (наследование и расширение)
- Структурированного логирования с контекстом
- Логгеров на уровне модуля

Используйте ColorLogger для:
- Цветного вывода в консоль
- Ротации файлов
- Окружений разработки

Используйте UnifiedLogger для:
- Производственных окружений с мониторингом
- Стриминга логов через сокеты
- Буферизации логов с учётом памяти
- API-дашбордов
