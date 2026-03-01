# Architecture

## Dependency graph

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

All modules have a single direction of dependency — only downward to `zsys.core`.  
No sibling dependencies. `zsys.services` is the only permitted orchestration layer.

## Module overview

| Module | Language | Dependencies |
|--------|----------|-------------|
| `zsys.core` | Python | stdlib only |
| `zsys._core` | C (CPython ext) | CPython C API |
| `zsys.i18n` | Python + Go | zsys.core |
| `zsys.log` | Python + Go | zsys.core.logging |
| `zsys.utils` | Python + Go | stdlib only |
| `zsys.modules` | Python + Go | zsys.core |
| `zsys.storage` | Python + Go | stdlib only |
| `zsys.telegram.pyrogram` | Python | zsys.core |
| `zsys.telegram.aiogram` | Python | zsys.core |
| `zsys.telegram.telebot` | Python | zsys.core |
| `zsys.telegram.telethon` | Python | zsys.core |
| `zsys.services` | Python | multiple (orchestration) |

## C core layers

```
Python userbot
     │
zsys._core (Python C extension — _zsys_core.c)
     │
libzsys_core.so (pure C — zsys_core.c)
     │
zsys/include/zsys_core.h (public API)

Same header:
  ← Go    (CGO: #cgo LDFLAGS -lzsys_core)
  ← Rust  (bindgen from zsys_core.h)
  ← Kotlin/JNI (future)
```

## Hot-reload flow

```
watchfiles detects change
        │
ModuleWatcher callback
        │
ModuleLoader.reload(module_name)
        │
importlib.reload(module)
        │
ModuleRegistry.update(module_name, new_meta)
        │
ModuleRouter.rebuild_routes()
```

## Routing flow

```
incoming message
        │
ModuleRouter.match(message.text, prefix, triggers)
        │   uses C: zsys_match_prefix()
        │
matched handler coroutine
        │
await handler(client, message)
```
