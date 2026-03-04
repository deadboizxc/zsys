[🇬🇧 English](architecture.md) | [🇷🇺 Русский](architecture_RU.md)

# Архитектура

## Граф зависимостей

```
stdlib / external libs
        │
    zsys.core
        │
  ┌─────┼──────┬──────────┬──────────┬────────────┐
  │     │      │          │          │            │
zsys. zsys. zsys.   zsys.      zsys.       zsys.
i18n   log  utils  modules   storage    telegram.*
```

Все модули имеют единственное направление зависимости — только вниз к `zsys.core`.  
Нет горизонтальных зависимостей. `zsys.services` — единственный допустимый слой оркестрации.

## Обзор модулей

| Модуль | Язык | Зависимости |
|--------|------|-------------|
| `zsys.core` | Python | только stdlib |
| `zsys._core` | C (CPython ext) | CPython C API |
| `zsys.i18n` | Python + Go | zsys.core |
| `zsys.log` | Python + Go | zsys.core.logging |
| `zsys.utils` | Python + Go | только stdlib |
| `zsys.modules` | Python + Go | zsys.core |
| `zsys.storage` | Python + Go | только stdlib |
| `zsys.telegram.pyrogram` | Python | zsys.core |
| `zsys.telegram.aiogram` | Python | zsys.core |
| `zsys.telegram.telebot` | Python | zsys.core |
| `zsys.telegram.telethon` | Python | zsys.core |
| `zsys.services` | Python | несколько (оркестрация) |

## Слои C-ядра

```
Python userbot
     │
zsys._core (Python C extension — _zsys_core.c)
     │
libzsys_core.so (pure C — zsys_core.c)
     │
zsys/include/zsys_core.h (public API)

Тот же заголовочный файл:
  ← Go    (CGO: #cgo LDFLAGS -lzsys_core)
  ← Rust  (bindgen from zsys_core.h)
  ← Kotlin/JNI (future)
```

## Поток горячей перезагрузки

```
watchfiles обнаруживает изменение
        │
обратный вызов ModuleWatcher
        │
ModuleLoader.reload(module_name)
        │
importlib.reload(module)
        │
ModuleRegistry.update(module_name, new_meta)
        │
ModuleRouter.rebuild_routes()
```

## Поток маршрутизации

```
входящее сообщение
        │
ModuleRouter.match(message.text, prefix, triggers)
        │   использует C: zsys_match_prefix()
        │
сопоставленная корутина обработчика
        │
await handler(client, message)
```
